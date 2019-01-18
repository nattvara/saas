"""Files helper module."""

import errno
import os


def create_dir(directory: str) -> str:
    """Create directory.

    Args:
        directory: path to directory

    Returns:
        Absolute path to created directory
        str
    """
    path = real_path(directory)
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    return path


def real_path(path: str) -> str:
    """Real path.

    Args:
        path: relative or absolute path

    Returns:
        Absolute path to provided path
        str
    """
    if path[0] == '~':
        root = os.path.expanduser('~')
        path = path[1:]
    elif path[0] == '/':
        root = '/'
    else:
        root = os.getcwd()
    return f'{root}/{path}'.replace('//', '/').replace('//', '/')
