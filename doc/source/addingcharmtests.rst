Enabling zaza tests in a charm
==============================

Update requirements and tox
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add zaza in the charms test-requirements.txt::

    git+https://github.com/openstack-charmers/zaza.git#egg=zaza


Add targets to tox.ini should include a target like::

    [testenv:func]
    basepython = python3
    commands =
        functest-run-suite --keep-model
    
    [testenv:func-smoke]
    basepython = python3
    commands =
        functest-run-suite --keep-model --smoke

Add Bundles
~~~~~~~~~~~

The bundles live in tests/bundles of the built charm, eg::

    tests/bundles/xenial.yaml
    tests/bundles/xenial-ha.yaml
    tests/bundles/bionic.yaml


The bundle may include overlay templates which are, currently, populated from
environment variables. For example the xenial-ha template needs a VIP but
the VIP will depend on the setup of the juju provider so will be different
between test environments. To accommodate this an overlay is added::

    tests/bundles/overlays/xenial-ha.yaml.j2

The overlay is in jinja2 format and the variables correspond to environment
variables::

    applications:
      vault:
        options:
            vip: '{{ OS_VIP00 }}'

Add tests.yaml
~~~~~~~~~~~~~~

A tests/tests.yaml file that describes the bundles to be run and the tests::

    charm_name: vault
    tests:
      - zaza.charm_tests.vault.VaultTest
    configure:
      - zaza.charm_tests.vault.setup.basic_setup
    gate_bundles:
      - base-xenial
      - base-bionic
    dev_bundles:
      - base-xenial-ha
    smoke_bundles:
      - base-bionic

When deploying zaza will wait for the deployment to settle and for the charms
to display a workload status which indicates that they are ready. Sometimes
one or more of the applications being deployed may have a non-standard workload
status target state or message. To inform the deployment step what to
wait for an optional target\_deploy\_status stanza can be added::

    target_deploy_status:
      vault:
        workload-status: blocked
        workload-status-message: Vault needs to be initialized
      ntp:
        workload-status-message: Go for it

Adding tests to zaza
~~~~~~~~~~~~~~~~~~~~

The setup and tests for a charm should live in zaza, this enables the code to
be shared between multiple charms. To add support for a new charm create a
directory, named after the charm, inside **zaza/charm_tests**. Within the new
directory define the tests in **tests.py** and any setup code in **setup.py**
This code can then be referenced in the charms **tests.yaml**

e.g. to add support for a new congress charm create a new directory in zaza::

    mkdir zaza/charm_tests/congress

Add setup code into setup.py::

    $ cat zaza/charm_tests/congress/setup.py
    def basic_setup():
        congress_client(run_special_setup)

Add test code into tests.py::

    class CongressTest(unittest.TestCase):

        def test_policy_create(self):
            policy = congress.create_policy()
            self.assertTrue(policy)

These now need to be referenced in the congress charms tests.yaml. Additional
setup is needed to run a useful congress tests, so congress' tests.yaml might
look like::

    charm_name: congress
    configure:
      - zaza.charm_tests.nova.setup.flavor_setup
      - zaza.charm_tests.nova.setup.image_setup
      - zaza.charm_tests.neutron.setup.create_tenant_networks
      - zaza.charm_tests.neutron.setup.create_ext_networks
      - zaza.charm_tests.congress.setup.basic_setup
    tests:
      - zaza.charm_tests.keystone.KeystoneBasicTest
      - zaza.charm_tests.congress.CongressTest
    gate_bundles:
      - base-xenial
      - base-bionic
    dev_bundles:
      - base-xenial-ha
