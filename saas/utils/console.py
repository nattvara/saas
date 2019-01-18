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


def dd(var):
    """Pretty print and die.

    Args:
        var: some variable
    """
    pp(var)
    exit()


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


def eol():
    """Print end of line character."""
    p('')
