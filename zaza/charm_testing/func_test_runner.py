import datetime
import logging

import zaza.charm_testing.configure as configure
import zaza.charm_testing.destroy as destroy
import zaza.charm_testing.utils as utils
import zaza.charm_testing.prepare as prepare
import zaza.charm_testing.deploy as deploy
import zaza.charm_testing.test as test

def func_test_runner():
    """Deploy the bundles and run the tests as defined by the charms tests.yaml
    """
    test_config = utils.get_test_config()
    for t in test_config['gate_bundles']:
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        model_name = '{}{}{}'.format(test_config['charm_name'], t, timestamp)
        # Prepare
        prepare.add_model(model_name)
        # Deploy
        deploy.deploy_bundle(
            os.path.join(BUNDLE_DIR, '{}.yaml'.format(t)),
            model_name)
        # Configure
        configure.run_configure_list(test_config['configure'])
        # Test
        test.run_test_list(test_config['tests'])
        # Destroy
        destroy.clean_up(model=model_name)

def main():
    func_test_runner()
