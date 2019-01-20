"""Arguments module."""

from pkg_resources import get_distribution
import argparse


def get_argument_parser():
    """Get argument parser."""
    parser = argparse.ArgumentParser(
        prog='saas',
        description='Screenshot as a service',
        formatter_class=argparse.HelpFormatter,
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s {}'.format(get_distribution('saas').version),
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help='Display debugging information',
    )

    parser.add_argument(
        'url_file',
        type=str,
        default=None,
        help='Path to input url file',
    )

    parser.add_argument(
        'mountpoint',
        type=str,
        default=None,
        help='Where to mount filesystem via FUSE',
    )

    parser.add_argument(
        '--refresh-rate',
        metavar='',
        type=str,
        default='hour',
        choices=['day', 'hour', 'minute'],
        help='''
            Refresh captures of urls every 'day', 'hour'
            or 'minute' (default: %(default)s)
        ''',
    )

    parser.add_argument(
        '--crawler-threads',
        metavar='',
        type=int,
        default=1,
        help='''
            Number of crawler threads, usually not
            neccessary with more than one (default: %(default)s)
        ''',
    )

    parser.add_argument(
        '--photographer-threads',
        metavar='',
        type=int,
        default=1,
        help='''
            Number of photographer threads, beaware that
            increasing too much won't neccessarily speed up
            performance and hog the system (default: %(default)s)
        '''
    )

    parser.add_argument(
        '--data-dir',
        metavar='',
        type=str,
        default='~/.saas-data-dir',
        help='Path to data directory (default: %(default)s)'
    )

    parser.add_argument(
        '--clear-data-dir',
        action='store_true',
        default=False,
        help='Use flag to clear data directory on start',
    )

    parser.add_argument(
        '--elasticsearch-host',
        metavar='',
        type=str,
        default='localhost:9200',
        help='Elasticsearch host (default: %(default)s)',
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
        ''',
    )

    parser.add_argument(
        '--stay-at-domain',
        action='store_true',
        default=False,
        help='''
            Use flag to ignore urls from a different
            domain than the one it was found at
        ''',
    )

    parser.add_argument(
        '--ignore-found-urls',
        action='store_true',
        default=False,
        help='Use flag to ignore urls found on crawled urls',
    )

    parser.add_argument(
        '--viewport-width',
        metavar='',
        type=int,
        default=1920,
        help='Width of camera viewport in pixels (default: %(default)s)',
    )

    parser.add_argument(
        '--viewport-height',
        metavar='',
        type=int,
        default=0,
        help='''
            Height of camera viewport in pixels, if set to 0 camera will
            try to take a full height high quality screenshot,
            which is way slower than fixed size (default: %(default)s)
        ''',
    )

    parser.add_argument(
        '--viewport-max-height',
        metavar='',
        type=int,
        help='''
            Max height of camera viewport in pixels, if --viewport-height
            is set this will be ignored
        ''',
    )

    parser.add_argument(
        '--optimize-storage',
        action='store_true',
        default=False,
        help='''
            Image files should be optimized to take up
            less storage (takes longer time to render)
        ''',
    )

    parser.add_argument(
        '--stop-if-idle',
        metavar='',
        type=int,
        default=0,
        help='''
            If greater than 0 saas will stop if it is idle for more
            than the provided number of minutes
        ''',
    )

    return parser
