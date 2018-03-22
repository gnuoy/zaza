import argparse

import zaza.charm_testing.utils as utils

def run_configure_list(functions):
    """Run the configure scripts as defined in the list of test classes in
       series.

    :param functions: List of functions
    :type tests: ['zaza.charms_tests.svc.TestSVCClass1', ...]
    :raises: AssertionError if test run fails
    """
    for func in functions:
        utils.get_class(func)()

def configure(functions):
    run_configure_list(functions)

def main():
    """Run the tests defined by the command line args or if none were provided
       read the tests from the charms tests.yaml config file"""
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--configfuncs', nargs='+',
                        help='Space sperated list of config functions',
                        required=False)
    args = parser.parse_args()
    funcs = args.configfuncs or get_test_config()['configure']
    configure(funcs)
