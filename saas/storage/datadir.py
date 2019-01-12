"""Data directory module."""

from __future__ import annotations
import saas.photographer.photo as PhotoPath
import shutil
import errno
import os


class DataDirectory:
    """Data directory class."""

    def __init__(self, path: str):
        """Create new data directory instance.

        Args:
            path: paath to root of data directory
        """
        self.root = path
        self.root = self.create_dir(self.root)

    def create_dir(self, directory: str) -> str:
        """Create directory.

        Args:
            directory: path to directory

        Returns:
            Absolute path to root directory
            str
        """
        root = self.real_path(directory)
        try:
            os.makedirs(root)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        return root

    def remove_data_dir(self):
        """Remove data directory root."""
        shutil.rmtree(self.root)

    def real_path(self, path: str) -> str:
        """Real path.

        Args:
            path: relative or absolute path

        Returns:
            Absolute path
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

    def path_for_photo(self, photo_path: PhotoPath.PhotoPath) -> str:
        """Get path for photo in data directory.

        Args:
            photo_path: A photo path object

        Returns:
            An absolute path to the file in data dir where photo is stored
            str
        """
        first_char = photo_path.uuid[0]
        directory = self.root + '/' + first_char + '/'
        if not os.path.exists(directory):
            os.mkdir(directory)
        return directory + photo_path.uuid
