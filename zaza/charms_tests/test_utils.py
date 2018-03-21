import unittest
import zaza.model


def skipIfNotHA(service_name):
    """Skip test if there is 1 or less units of a service"""
    if len(zaza.model.unit_ips(service_name)) > 1:
        return lambda func: func
    return unittest.skip(
        "Skipping HA test for non-ha service {}".format(service_name))
