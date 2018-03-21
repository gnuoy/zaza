import unittest
import zaza.model


def skipIfNotHA(service_name):
    def _skipIfNotHA_inner_1(f):
        def _skipIfNotHA_inner_2(*args, **kwargs):
            if len(zaza.model.unit_ips(service_name)) > 1:
                return f(*args, **kwargs)
            else:
                return unittest.skip("Skipping HA test for non-ha service {}".format(service_name))
        return _skipIfNotHA_inner_2

    return _skipIfNotHA_inner_1

