import argparse
import datetime
import unittest
import logging
import os
import subprocess
import sys

import juju_wait

BUNDLE_DIR = "./tests/bundles/"

def deploy_bundle(bundle, model):
    logging.info("Deploying bundle {}".format(bundle))    
    subprocess.check_call(['juju', 'deploy', '-m', model, bundle])

def add_model(model_name):
    logging.info("Adding model {}".format(model_name))
    subprocess.check_call(['juju', 'add-model', model_name])

def run_tests(tests):
    for testcase in tests:
        suite = unittest.TestLoader().loadTestsFromTestCase(testcase)
        test_result = unittest.TextTestRunner(verbosity=2).run(suite)
        assert test_result.wasSuccessful(), "Test run failed"

def deploy():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("test_dir", help="Test directory")
    args = parser.parse_args()
    sys.path.append(args.test_dir)
    import tests
    for t in tests.GATE_BUNDLES:
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        model_name = '{}{}{}'.format(tests.CHARM_NAME, t, timestamp)
        add_model(model_name)
        deploy_bundle(os.path.join(BUNDLE_DIR, '{}.yaml'.format(t)), model_name)
        logging.info("Waiting for environment to settle")
        juju_wait.wait()
        run_tests(tests.TESTS)
