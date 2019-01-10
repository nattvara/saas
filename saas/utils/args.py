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

    return parser
