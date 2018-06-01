# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

version = "0.0.1.dev1"
install_require = [
    'async_generator',
    'cryptography',
    'hvac',
    'jinja2',
    'juju',
    'jujucrashdump==1.0.0',
    'juju-wait',
    'PyYAML',
    'tenacity',
    'oslo.config',
    'python-keystoneclient',
    'python-novaclient',
    'python-neutronclient',
]
dependency_links = [
    "git+https://github.com/juju/juju-crashdump.git#egg=jujucrashdump-1.0.0"
]
tests_require = [
    'tox >= 2.3.1',
]


class Tox(TestCommand):
    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import tox
        import shlex
        args = self.tox_args
        # remove the 'test' arg from argv as tox passes it to ostestr which
        # breaks it.
        sys.argv.pop()
        if args:
            args = shlex.split(self.tox_args)
        errno = tox.cmdline(args=args)
        sys.exit(errno)


if sys.argv[-1] == 'publish':
    os.system("python setup.py sdist upload")
    os.system("python setup.py bdist_wheel upload")
    sys.exit()


if sys.argv[-1] == 'tag':
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()


setup(
    entry_points={
        'console_scripts': [
            'functest-run-suite = zaza.charm_lifecycle.func_test_runner:main',
            'functest-deploy = zaza.charm_lifecycle.deploy:main',
            'functest-configure = zaza.charm_lifecycle.configure:main',
            'functest-destroy = zaza.charm_lifecycle.destroy:main',
            'functest-prepare = zaza.charm_lifecycle.prepare:main',
            'functest-test = zaza.charm_lifecycle.test:main',
            'functest-collect = zaza.charm_lifecycle.collect:main',
            'current-apps = zaza.model:main',
            'tempest-config = zaza.tempest_config:main',
        ]
    },
    use_scm_version=True,
    license='Apache-2.0: http://www.apache.org/licenses/LICENSE-2.0',
    packages=find_packages(exclude=["unit_tests"]),
    zip_safe=False,
    cmdclass={'test': Tox},
    install_requires=install_require,
    dependency_links=dependency_links,
    extras_require={
        'testing': tests_require,
    },
    tests_require=tests_require,
)
