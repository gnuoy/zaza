import argparse
import jujucrashdump.crashdump as crashdump
import logging
import os
import sys
import tempfile


def parse_args(args):
    """Parse command line arguments

    :param args: List of configure functions functions
    :type list: [str1, str2,...] List of command line arguments
    :returns: Parsed arguments
    :rtype: Namespace
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model-name', help='Name of model to remove',
                        required=True)
    parser.add_argument('-f', '--max-file-size', default=5000000,
                        help='The max file size (bytes) for included files')
    parser.add_argument('-o', '--output-dir',
                        help="Store the completed crash dump in this dir.")
    parser.add_argument('-t', '--timeout', type=int, default='45',
                        help='Timeout in seconds for creating unit tarballs.')
    return parser.parse_args(args)


def collect(model_name, output_dir=None, timeout=45, max_file_size=5000000):
    """Run all post-deployment configuration steps

    :param model_name: Name of model to collect data from
    :type model_name: str
    """
    if not output_dir:
        if os.getenv('WORKSPACE'):
            # If running in Jenkins there should be a workspace env variable
            # set
            output_dir = os.getenv('WORKSPACE')
        else:
            output_dir = tempfile.mkdtemp(prefix='zaza_crashdump_')
    collector = crashdump.CrashCollector(
        model=model_name,
        max_size=max_file_size,
        extra_dirs=[],
        output_dir=output_dir,
        uniq=None,
        addons=None,
        addons_file=None,
        exclude=None,
        compression='xz',
        timeout=timeout,
    )
    filename = collector.collect()
    logging.info("Crash dump created: {}/{}".format(output_dir, filename))


def main():
    """Collect artifacts from the deployed application for debug"""
    logging.basicConfig(level=logging.INFO)
    args = parse_args(sys.argv[1:])
    collect(
        args.model_name,
        output_dir=args.output_dir,
        timeout=args.timeout,
        max_file_size=args.max_file_size)
