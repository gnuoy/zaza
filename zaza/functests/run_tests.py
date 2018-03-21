import unittest

BUNDLE_DIR = "./tests/bundles/"

sys.path.append('./tests')
import tests

def run_tests():
    for testcase in tests.TESTS:
        suite = unittest.TestLoader().loadTestsFromTestCase(testcase)
        test_result = unittest.TextTestRunner(verbosity=2).run(suite)
        assert test_result.wasSuccessful(), "Test run failed"
