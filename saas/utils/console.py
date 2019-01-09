"""Console module.

Collection of console helpers.
"""

import sys
import beeprint


def pp(var):
    """Pretty print.

    Wrapper around beeprint

    Args:
        var: some variable
    """
    beeprint.pp(var)


def p(var, end=None):
    """Print.

    Wrapper around print.

    Args:
        var: some variable
        end: end of line character (default: {None})
    """
    if end is not None:
        print(var, end=end)
    else:
        print(var)
    sys.stdout.flush()
