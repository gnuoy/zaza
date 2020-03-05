# Copyright 2018 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities to support running lifecycle phases."""
import collections
import importlib
import logging
import os
import subprocess
import uuid
import sys
import yaml

BUNDLE_DIR = "./tests/bundles/"
DEFAULT_TEST_CONFIG = "./tests/tests.yaml"
DEFAULT_MODEL_ALIAS = "default_alias"
DEFAULT_DEPLOY_NAME = 'default{}'

RAW_BUNDLE = "raw-bundle"
SINGLE_ALIASED = "single-aliased"
MUTLI_UNORDERED = "multi-unordered"
MUTLI_ORDERED = "multi-ordered"
# BUNDLE_GROUP = "bundle-group"

"""
  A ModelDeploy represents a deployment of one bundle to one model. An
  EnvironmentDeploy consists of ModelDeploys. Some tests, such as cross model
  relation tests, require two or more ModelDeploys.

  ModelDeploy   ModelDeploy         ModelDeploy
    |               |                   |
    ----------------                    |
            |                           |
    EnvironmentDeploy               EnvironmentDeploy
            |                           |
            -----------------------------
                        |
                EnvironmentDeploys

"""
ModelDeploy = collections.namedtuple(
    'ModelDeploy', ['model_alias', 'model_name', 'bundle', 'overlays'])
EnvironmentDeploy = collections.namedtuple(
    'EnvironmentDeploy', ['name', 'model_deploys', 'run_in_series'])

default_deploy_number = 0


def _concat_model_alias_maps(data):
    """Iterate over list and construct single dict of model alias maps.

    Any elements in list which are not dicts are added to a list and assigned
    to DEFAULT_MODEL_ALIAS.

    eg If input is ['e1', 'e2', {'alias1': ['e3'], 'alias2': ['e4']}]
       this function will return:
       {
           DEFAULT_MODEL_ALIAS: ['e1', 'e2'],
           'alias1': ['e3'],
           'alias2': ['e4']}

    :param data: List comprised of str elements or dict elements.
    :type data: List[Union[str, Dict[str, List[str]]]]
    :returns: Model Alias to data map
    :rtype: Dict[str, List[str]]
    """
    new_data = {DEFAULT_MODEL_ALIAS: []}
    for item in data:
        if isinstance(item, collections.Mapping):
            new_data.update(item)
        else:
            new_data[DEFAULT_MODEL_ALIAS].append(item)
    return new_data


def get_default_env_deploy_name(reset_count=False):
    """Generate a default name for the environment deploy.

    :returns: Environment name
    :rtype: str
    """
    global default_deploy_number
    if reset_count:
        default_deploy_number = 0
    default_deploy_number = default_deploy_number + 1
    return DEFAULT_DEPLOY_NAME.format(default_deploy_number)

#def get_bundle_group(group_name):
#    for group in get_bundle_groups():
#        logging.info("{} = {} ?".format(group['group'], group_name))
#        if group['group'] == group_name:
#            return group
# 
def get_bundle_groups(bundle_key):
    groups = {}
    for entry in get_charm_config()[bundle_key]:
        try:
            if 'group' in entry.keys():
                groups[entry['group']] = entry
        except AttributeError:
            pass
    return groups

def get_bundle_group_names(bundle_key):
    return get_bundle_groups(bundle_key).keys()
#
#def get_bundle_group_namess():
#    return [g['group_name'] for g in get_bundle_groups()]

#def get_bundle_groups():
#    logging.info("Bundles: ")
#    bundle_groups = []
#    for deploy_directive in  get_charm_config()['gate_bundles']:
#        logging.info(deploy_directive)
#        if is_bundle_group(deploy_directive):
#            bundle_groups.append(deploy_directive)
#    return bundle_groups

def is_bundle_group(deployment_directive, bundle_key):
    return deployment_directive in get_bundle_group_names(bundle_key)

def is_bundle_group_definition(deployment_directive):
    try:
        return 'group' in deployment_directive.keys()
    except AttributeError:
        return False
#    print(get_bundle_groups(bundle_key))
#    assert 1 == 2
#    try:
#        return 'group' in deployment_directive.keys()
#    except AttributeError:
#        return False

def get_deployment_type(deployment_directive, bundle_key):
    """Given a deployment directive reverse engineer the type.

    :returns: The type of the deployment_directive
    :rtype: str
    """
#    if is_bundle_group(deployment_directive, bundle_key):
#        return BUNDLE_GROUP
    if isinstance(deployment_directive, str):
        return RAW_BUNDLE
    if isinstance(deployment_directive, collections.Mapping):
        if len(deployment_directive) == 1:
            first_value = deployment_directive[list(deployment_directive)[0]]
            if isinstance(first_value, list):
                return MUTLI_ORDERED
            else:
                return SINGLE_ALIASED
        else:
            return MUTLI_UNORDERED


def get_environment_deploy(deployment_directive, bundle_key):
    """Get the EnvironmentDeploy object from the deployment directive.

    :returns: The EnvironmentDeploy for the give deployment directive.
    :rtype: EnvironmentDeploy
    """
    env_deploy_f = {
        RAW_BUNDLE: get_environment_deploy_raw,
        MUTLI_ORDERED: get_environment_deploy_multi_ordered,
        SINGLE_ALIASED: get_environment_deploy_single_aliased,
        MUTLI_UNORDERED: get_environment_deploy_multi_unordered}
    return env_deploy_f[get_deployment_type(deployment_directive, bundle_key)](
        deployment_directive, bundle_key)


def get_environment_deploy_raw(deployment_directive, bundle_key):
    """Get the EnvironmentDeploy object for a raw deployment_directive.

    :returns: The EnvironmentDeploy for the give deployment directive.
    :rtype: EnvironmentDeploy
    """
    env_alias = get_default_env_deploy_name()
    env_deploys = []
    if is_bundle_group(deployment_directive, bundle_key):
        model_deploys = []
        group_config = get_bundle_groups(bundle_key)[deployment_directive]
        for run_overlay in group_config['run_overlays']:
            overlays = []
            if group_config.get('overlays'):
                overlays.extend(group_config.get('overlays'))
            overlays.append(run_overlay)
            md = ModelDeploy(
                DEFAULT_MODEL_ALIAS,
                generate_model_name(),
                group_config['group'],
                overlays)
            env_deploys.append(
                EnvironmentDeploy(env_alias, [md], False))
    else:
        model_deploys = [
            ModelDeploy(
                DEFAULT_MODEL_ALIAS,
                generate_model_name(),
                deployment_directive,
                [])]
        env_deploys.append(
            EnvironmentDeploy(env_alias, model_deploys, False))
    return env_deploys


def get_environment_deploy_multi_ordered(deployment_directive, bundle_key):
    """Get EnvironmentDeploy for a multi model ordered deployment_directive.

    :returns: The EnvironmentDeploy for the give deployment directive.
    :rtype: EnvironmentDeploy
    """
    env_alias = list(deployment_directive)[0]
    model_deploys = []
    group_deploys = []
    env_deploys = []
    for model_alias_map in deployment_directive[env_alias]:
        if is_bundle_group(model_alias_map, bundle_key):
            group_deploys.append(model_alias_map)
        else:
            for alias, bundle in model_alias_map.items():
                model_deploys.append(
                    ModelDeploy(
                        alias,
                        generate_model_name(),
                        bundle,
                        []))
    if model_deploys:
        env_deploys.append(EnvironmentDeploy(env_alias, model_deploys, True))
    if group_deploys:
        for group in group_deploys:
            group_config = get_bundle_groups(bundle_key)[group]
            for run_overlay in group_config['run_overlays']:
                overlays = []
                if group_config.get('overlays'):
                    overlays.extend(group_config.get('overlays'))
                overlays.append(run_overlay)
                md = ModelDeploy(
                    env_alias,
                    generate_model_name(),
                    group_config['group'],
                    overlays)
                model_deploys.append(
                    ModelDeploy(
                        env_alias,
                        generate_model_name(),
                        group_config['group'],
                        overlays))
                env_deploys.append(
                    EnvironmentDeploy(env_alias, [md], True)
                )
    return env_deploys


def get_model_deploy_bundle_group(deployment_directive):
    env_alias = get_default_env_deploy_name()
    model_deploys = []
    for run_overlay in deployment_directive['run_overlays']:
        overlays = []
        if deployment_directive.get('overlays'):
            overlays.extend(deployment_directive.get('overlays'))
        overlays.append(run_overlay)
        model_deploys.append(
            ModelDeploy(
                deployment_directive.get(
                    'model_alias',
                    DEFAULT_MODEL_ALIAS),
                generate_model_name(),
                deployment_directive['group'],
                overlays))
    return model_deploys


def get_environment_deploy_multi_unordered(deployment_directive, bundle_key):
    """Get EnvironmentDeploy for a multi model unordered deployment_directive.

    :returns: The EnvironmentDeploy for the give deployment directive.
    :rtype: EnvironmentDeploy
    """
    env_alias = get_default_env_deploy_name()
    model_deploys = []
    for alias, bundle in deployment_directive.items():
        model_deploys.append(
            ModelDeploy(
                alias,
                generate_model_name(),
                bundle,
                []))
    return [EnvironmentDeploy(env_alias, model_deploys, True)]


def get_environment_deploy_single_aliased(deployment_directive):
    """Get EnvironmentDeploy for a single_aliased deployment_directive.

    :returns: The EnvironmentDeploy for the give deployment directive.
    :rtype: EnvironmentDeploy
    """
    env_alias = get_default_env_deploy_name()
    (alias, bundle) = list(deployment_directive.items())[0]
    return [EnvironmentDeploy(
        env_alias,
        [ModelDeploy(
            alias,
            generate_model_name(),
            bundle,
            [])],
        True)]


def get_environment_deploys(bundle_key, deployment_name=None):
    """Describe environment deploys for a given set of bundles.

    Get a list of test bundles with their model alias. If no model alias is
    supplied then DEFAULT_MODEL_ALIAS is used.

    eg if test.yaml contained:

        gate_bundles:
          - bundle1
          - bundle2
          - model_alias1: bundle_3
            model_alias2: bundle_4
          - my-cmr-test:
            - model_alias3: bundle_5
            - model_alias4: bundle_6

       then get_test_bundles('gate_bundles') would return:

            [
                {'default_alias': 'bundle1'},
                {'default_alias': 'bundle2'},
                {'model_alias1': 'bundle_3', 'model_alias2': 'bundle_5'},
                {'model_alias3': 'bundle_4', 'model_alias2': 'bundle_6'}]

    :param bundle_key: Name of group of bundles eg gate_bundles
    :type bundle_key: str
    :returns: A list of dicts where the dict contain a model alias to bundle
              mapping.
    :rtype: List[EnvironmentDeploy, EnvironmentDeploy, ...]
    """
    environment_deploys = []
    for bundle_mapping in get_charm_config()[bundle_key]:
        if is_bundle_group_definition(bundle_mapping):
            continue
#        elif is_calling_bundle_group(bundle_mapping):
#            model_deploys = get_model_deploy_bundle_group(bundle_mapping)
#            env_alias = get_default_env_deploy_name()
#            for model_deploy in model_deploys:
#                environment_deploys.append(
#                    EnvironmentDeploy(
#                        env_alias,
#                        [model_deploy],
#                        True))
        else:
            logging.info("Adding {}".format(bundle_mapping))
            environment_deploys.extend(get_environment_deploy(bundle_mapping, bundle_key))
    return environment_deploys


def get_config_steps():
    """Get configuration steps and their associated model aliases.

    Get a map of configuration steps to model aliases. If there are
    configuration steps which are not mapped to a model alias then these are
    associated with the the DEFAULT_MODEL_ALIAS.

    eg if test.yaml contained:

        configure:
        - conf.class1
        - conf.class2
        - model_alias1:
          - conf.class3

       then get_config_steps() would return:

        {
            'default_alias': ['conf.class1', 'conf.class2'],
            'model_alias1': ['conf.class3']}

    :returns: A dict mapping config steps to model aliases
    :rtype: Dict[str, List[str]]
    """
    return _concat_model_alias_maps(get_charm_config().get('configure', []))


def get_test_steps():
    """Get test steps and their associated model aliases.

    Get a map of test steps to model aliases. If there are test
    steps which are not mapped to a model alias then these are associated with
    the the DEFAULT_MODEL_ALIAS.

    eg if test.yaml contained:

        test:
        - test.class1
        - test.class2
        - model_alias1:
          - test.class3

       then get_test_steps() would return:

        {
            'default_alias': ['test.class1', 'test.class2'],
            'model_alias1': ['test.class3']}

    :returns: A dict mapping test steps to model aliases
    :rtype: Dict[str, List[str]]
    """
    return _concat_model_alias_maps(get_charm_config().get('tests', []))


def get_charm_config(yaml_file=None, fatal=True):
    """Read the yaml test config file and return the resulting config.

    :param yaml_file: File to be read
    :type yaml_file: str
    :param fatal: Whether failure to load file should be fatal or not
    :type fatal: bool
    :returns: Config dictionary
    :rtype: dict
    """
    if not yaml_file:
        yaml_file = DEFAULT_TEST_CONFIG
    try:
        with open(yaml_file, 'r') as stream:
            return yaml.safe_load(stream)
    except OSError:
        if not fatal:
            charm_name = os.path.basename(os.getcwd())
            if charm_name.startswith('charm-'):
                charm_name = charm_name[6:]
            logging.warning('Unable to load charm config, deducing '
                            'charm_name from cwd: "{}"'
                            .format(charm_name))
            return {'charm_name': charm_name}
        raise


def get_class(class_str):
    """Get the class represented by the given string.

    For example, get_class('zaza.charms_tests.svc.TestSVCClass1')
    returns zaza.charms_tests.svc.TestSVCClass1

    :param class_str: Class to be returned
    :type class_str: str
    :returns: Test class
    :rtype: class
    """
    old_syspath = sys.path
    sys.path.insert(0, '.')
    module_name = '.'.join(class_str.split('.')[:-1])
    class_name = class_str.split('.')[-1]
    module = importlib.import_module(module_name)
    sys.path = old_syspath
    return getattr(module, class_name)


def generate_model_name():
    """Generate a unique model name.

    :returns: Model name
    :rtype: str
    """
    return 'zaza-{}'.format(str(uuid.uuid4())[-12:])


def check_output_logging(cmd):
    """Run command and log output.

    :param cmd: Shell command to run
    :type cmd: List
    :raises: subprocess.CalledProcessError
    """
    popen = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True)
    for line in iter(popen.stdout.readline, ""):
        # popen.poll checks if child process has terminated. If it has it
        # returns the returncode. If it has not it returns None.
        if popen.poll() is not None:
            break
        logging.info(line.strip())
    popen.stdout.close()
    return_code = popen.poll()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)
