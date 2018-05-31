import mock

import zaza.charm_lifecycle.collect as lc_collect
import unit_tests.utils as ut_utils


class TestCharmLifecycleCollect(ut_utils.BaseTestCase):

    def test_parser(self):
        args = lc_collect.parse_args(
            [
                '-m', 'modelname',
                '-f', '128',
                '-o', '/tmp/bespoke',
                '-t', '23',
            ])
        self.assertEqual(args.model_name, 'modelname')
        self.assertEqual(args.max_file_size, '128')
        self.assertEqual(args.timeout, 23)
        self.assertEqual(args.output_dir, '/tmp/bespoke')

    def test_collect(self):
        self.patch_object(lc_collect.crashdump, 'CrashCollector')
        collector_mock = mock.MagicMock()
        self.CrashCollector.return_value = collector_mock
        lc_collect.collect('modelname', output_dir='/tmp/bespoke')
        self.CrashCollector.assert_called_once_with(
            addons=None,
            addons_file=None,
            compression='xz',
            exclude=None,
            extra_dirs=[],
            max_size=5000000,
            model='modelname',
            output_dir='/tmp/bespoke',
            timeout=45,
            uniq=None)
        collector_mock.collect.assert_called_once_with()

    def test_collect_jenkins(self):
        self.patch_object(lc_collect.crashdump, 'CrashCollector')
        self.patch_object(lc_collect.os, 'getenv')
        self.getenv.return_value = '/tmp/jenkins_workspace'
        collector_mock = mock.MagicMock()
        self.CrashCollector.return_value = collector_mock
        lc_collect.collect('modelname')
        self.CrashCollector.assert_called_once_with(
            addons=None,
            addons_file=None,
            compression='xz',
            exclude=None,
            extra_dirs=[],
            max_size=5000000,
            model='modelname',
            output_dir='/tmp/jenkins_workspace',
            timeout=45,
            uniq=None)
        collector_mock.collect.assert_called_once_with()

    def test_collect_tmpdir(self):
        self.patch_object(lc_collect.crashdump, 'CrashCollector')
        self.patch_object(lc_collect.os, 'getenv')
        self.getenv.return_value = None
        self.patch_object(lc_collect.tempfile, 'mkdtemp')
        self.mkdtemp.return_value = '/tmp/random_tmp_dir'
        collector_mock = mock.MagicMock()
        self.CrashCollector.return_value = collector_mock
        lc_collect.collect('modelname')
        self.CrashCollector.assert_called_once_with(
            addons=None,
            addons_file=None,
            compression='xz',
            exclude=None,
            extra_dirs=[],
            max_size=5000000,
            model='modelname',
            output_dir='/tmp/random_tmp_dir',
            timeout=45,
            uniq=None)
        collector_mock.collect.assert_called_once_with()
