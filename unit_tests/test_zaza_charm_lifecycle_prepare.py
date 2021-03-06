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

import copy
import mock

import zaza.charm_lifecycle.prepare as lc_prepare
import unit_tests.utils as ut_utils


class TestCharmLifecyclePrepare(ut_utils.BaseTestCase):

    MODEL_CONFIG_DEFAULTS = lc_prepare.MODEL_DEFAULTS

    def base_parse_option_list_string(self, env, expect):
        with mock.patch.dict(lc_prepare.os.environ, env):
            self.assertEqual(lc_prepare.get_model_settings(), expect)

    def test_parse_option_list_string_empty_config(self):
        self.assertEqual(
            lc_prepare.parse_option_list_string(option_list=""),
            {})

    def test_parse_option_list_string_single_value(self):
        self.assertEqual(
            lc_prepare.parse_option_list_string(
                option_list='image-stream=released'),
            {'image-stream': 'released'})

    def test_parse_option_list_string_multiple_values(self):
        self.assertEqual(
            lc_prepare.parse_option_list_string(
                option_list='image-stream=released;no-proxy=jujucharms.com'),
            {
                'image-stream': 'released',
                'no-proxy': 'jujucharms.com'})

    def test_parse_option_list_string_whitespace(self):
        self.assertEqual(
            lc_prepare.parse_option_list_string(
                option_list=' test-mode= false ; image-stream=  released'),
            {
                'test-mode': 'false',
                'image-stream': 'released'})

    def test_get_model_settings_no_config(self):
        self.base_parse_option_list_string({}, self.MODEL_CONFIG_DEFAULTS)

    def test_get_model_settings_multiple_values_override(self):
        expect_config = copy.deepcopy(self.MODEL_CONFIG_DEFAULTS)
        expect_config.update({'test-mode': 'false'})
        self.base_parse_option_list_string(
            {'MODEL_SETTINGS': 'test-mode=false'},
            expect_config)

    def test_prepare(self):
        self.patch_object(lc_prepare.zaza.controller, 'add_model')
        self.patch_object(lc_prepare, 'get_model_settings')
        self.patch_object(lc_prepare, 'get_model_constraints')
        self.patch_object(lc_prepare.zaza.model, 'set_model_constraints')
        self.get_model_settings.return_value = lc_prepare.MODEL_DEFAULTS
        self.get_model_constraints.return_value = {'image-stream': 'released'}
        lc_prepare.prepare('newmodel')
        self.add_model.assert_called_once_with(
            'newmodel',
            config={
                'default-series': 'xenial',
                'image-stream': 'daily',
                'test-mode': 'true',
                'transmit-vendor-metrics': 'false',
                'enable-os-upgrade': 'false',
                'automatically-retry-hooks': 'false',
                'use-default-secgroup': 'true'})
        self.set_model_constraints.assert_called_once_with(
            constraints={'image-stream': 'released'},
            model_name='newmodel')

    def test_parser(self):
        args = lc_prepare.parse_args([])
        self.assertTrue(args.model_name.startswith('zaza-'))

    def test_parser_model(self):
        args = lc_prepare.parse_args(['-m', 'newmodel'])
        self.assertEqual(args.model_name, 'newmodel')

    def test_parser_logging(self):
        # Using defaults
        args = lc_prepare.parse_args(['-m', 'model'])
        self.assertEqual(args.loglevel, 'INFO')
        # Using args
        args = lc_prepare.parse_args(['-m', 'model', '--log', 'DEBUG'])
        self.assertEqual(args.loglevel, 'DEBUG')
