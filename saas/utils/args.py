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
        'mountpoint',
        type=str,
        default=None,
        help='''Where to mount filesystem via FUSE''',
    )

    parser.add_argument(
        '--crawler-threads',
        type=int,
        default=1,
        help='''
            Number of crawler threads, usually not
            neccessary with more than one
        '''.replace('  ', ''),
    )

    parser.add_argument(
        '--photographer-threads',
        type=int,
        default=2,
        help='''
            Number of photographer threads, beaware that
            increasing too much won't neccessarily speed up
            performance and hog the system
        '''.replace('  ', ''),
    )

    parser.add_argument(
        '--data-dir',
        type=str,
        default='~/.saas-data-dir',
        help='''Path data directory''',
    )

    parser.add_argument(
        '--clear-data-dir',
        action='store_true',
        default=False,
        help='Use flag to clear data directory on start',
    )

    parser.add_argument(
        '--setup-elasticsearch',
        action='store_true',
        default=False,
        help='Use flag to create indices in elasticsearch',
    )

    parser.add_argument(
        '--clear-elasticsearch',
        action='store_true',
        default=False,
        help='''
            Use flag to clear elasticsearch on start,
            WARNING: this will clear all indices found
            in elasticsearch instance
        '''.replace('  ', ''),
    )

    parser.add_argument(
        '--ignore-found-urls',
        action='store_true',
        default=False,
        help='Use flag to ignore urls found on crawled urls',
    )

    return parser
