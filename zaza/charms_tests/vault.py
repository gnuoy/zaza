#!/usr/bin/env python3

import unittest

import os
import hvac
import time
import requests
import urllib3
import uuid
import yaml

import zaza.model

class VaultUtils(object):

    def get_client(self, vault_url):
        return hvac.Client(url=vault_url)
    
    
    def init_vault(self, client, shares=1, threshold=1):
        return client.initialize(shares, threshold)
    
    
    def get_clients(self, units):
        clients = []
        for unit in units:
            print("Creating client for {}".format(unit))
            vault_url = 'http://{}:8200'.format(unit)
            print(vault_url)
            clients.append((unit, get_client(vault_url)))
        return clients
    
    
    def is_initialized(self, client):
        initialized = False
        print("Checking if vault is initialized")
        for i in range(1, 10):
            try:
                initialized = client[1].is_initialized()
            except (ConnectionRefusedError, urllib3.exceptions.NewConnectionError,
                    urllib3.exceptions.MaxRetryError,
                    requests.exceptions.ConnectionError):
                print("{} / 10".format(i))
                time.sleep(2)
            else:
                break
        else:
            raise Exception("Cannot connect")
        return initialized
    
    
    def get_credentails(self, auth_file):
        print("Reading credentails from disk")
        with open(auth_file, 'r') as stream:
            vault_creds = yaml.load(stream)
        return vault_creds
    
    
    def write_credentails(self, auth_file, vault_creds):
        with open(auth_file, 'w') as outfile:
            yaml.dump(vault_creds, outfile, default_flow_style=False)
    
    
    def unseal_all(self, clients, key):
        for (addr, client) in clients:
            if client.is_sealed():
                print("Unsealing {}".format(addr))
                client.unseal(key)
    
    
    def auth_all(self, clients, token):
        for (addr, client) in clients:
            client.token = token


class VaultTest(unittest.TestCase):
    
    
    def setUp(self):
        vutils = VaultUtils() 
        self.clients = vutils.get_clients(units)
        auth_file = "{}/tests/data.yaml".format(os.getcwd())
        self.unseal_client = self.clients[0]
        print("Picked {} for performing unseal".format(self.unseal_client[0]))
        initialized = vutils.is_initialized(self.unseal_client)
        if initialized:
            self.vault_creds = vutils.get_credentails(auth_file)
        else:
            print("Initializing vault")
            self.vault_creds = vutils.init_vault(unseal_client[1])
            vutils.write_credentails(auth_file, self.vault_creds)
        self.keys = self.vault_creds['keys']
        vutils.unseal_all(self.clients, keys[0])
        vutils.auth_all(self.clients, vault_creds['root_token'])

    def test_check_authenticated(self):
        for (addr, client) in self.clients:
            for i in range(1, 10):
                try:
                    assert client.is_authenticated()
                except hvac.exceptions.InternalServerError:
                    print("{} / 10".format(i))
                    time.sleep(2)
                else:
                    break
            else:
                raise hvac.exceptions.InternalServerError
    
    
    def check_read(key, value):
        for (addr, client) in self.clients:
            print("    {} reading secret".format(addr))
            assert client.read('secret/uuids')['data']['uuid'] == value
    
    
    def test_check_read_write(self):
        key = 'secret/uuids'
        for (addr, client) in self.clients:
            value = str(uuid.uuid1())
            print("{} writing a secret".format(addr))
            client.write(key, uuid=value, lease='1h')
            # Now check all clients read the same value back
            self.check_read(key, value)
    
    
    def test_check_vault_ha_statuses(self):
        if len(self.clients) <= 1:
            return
        print("Checking HA stauses")
        leader = []
        leader_address = []
        leader_cluster_address = []
        for (addr, client) in self.clients:
            assert client.ha_status['ha_enabled']
            leader_address.append(
                client.ha_status['leader_address'])
            leader_cluster_address.append(
                client.ha_status['leader_cluster_address'])
            if client.ha_status['is_self']:
                leader.append(addr)
                print("    {} is leader".format(addr))
            else:
                print("    {} is standby".format(addr))
        # Check there is exactly one leader
        assert len(leader) == 1
        # Check both cluster addresses match accross the cluster
        assert len(set(leader_address)) == 1
        assert len(set(leader_cluster_address)) == 1
    
    
    def test_check_vault_status(self):
        for (addr, client) in self.clients:
            assert not client.seal_status['sealed']
            assert client.seal_status['cluster_name']

if __name__ == '__main__':
    unittest.main()
