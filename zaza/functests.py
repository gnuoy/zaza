import argparse
import unittest
import logging
import os
import subprocess
import sys

import juju_wait

BUNDLE_DIR = "./tests/bundles/"

sys.path.append('./tests')
import tests

def deploy_bundle(bundle):
    logging.info("Deploying bundle {}".format(bundle))    
    subprocess.check_call(['juju', 'deploy', bundle])

def deploy():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", help="Bundle to deploy")
    args = parser.parse_args()
    deploy_bundle(os.path.join(BUNDLE_DIR, args.bundle))
    logging.info("Waiting for environment to settle")
    juju_wait.wait()

def run_tests():
    for testcase in tests.TESTS:
        suite = unittest.TestLoader().loadTestsFromTestCase(testcase)
        test_result = unittest.TextTestRunner(verbosity=2).run(suite)
        assert test_result.wasSuccessful(), "Test run failed"

if __name__ == '__main__':
    main()
