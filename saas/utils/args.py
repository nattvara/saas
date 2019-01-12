"""Arguments module."""

import argparse


def get_argument_parser():
    """Get argument parser."""
    parser = argparse.ArgumentParser(
        prog='saas',
        description='Screenshot as a service',
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        'url_file',
        type=str,
        default=None,
        help='''Path to input url file''',
    )

    parser.add_argument(
        '--data-dir',
        type=str,
        default='~/.saas-data-dir',
        help='''Path data directory''',
    )

    parser.add_argument(
        '--clear-elasticsearch',
        action='store_true',
        default=False,
        help='Use flag to clear elasticsearch on start',
    )

    parser.add_argument(
        '--component',
        type=str,
        nargs='?',
        default=None,
        help='''Used during development to run a specific component''',
    )

    return parser
