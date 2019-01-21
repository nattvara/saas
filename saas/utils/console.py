"""Console module.

Collection of console helpers.
"""

import sys
import beeprint


DEBUG = False


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


def dcr(message: str):
    """Print crawler debug info.

    Args:
        message: debug message
    """
    if DEBUG:
        p('debug [crawler]: ' + message)


def dp(message: str):
    """Print photographer debug info.

    Args:
        message: debug message
    """
    if DEBUG:
        p('debug [photographer]: ' + message)


def dca(message: str):
    """Print camera debug info.

    Args:
        message: debug message
    """
    if DEBUG:
        p('debug [camera]: ' + message)


def df(message: str):
    """Print filesystem debug info.

    Args:
        message: debug message
    """
    if DEBUG:
        p('debug [filesystem]: ' + message)


def eol():
    """Print end of line character."""
    p('')
