"""Data directory module."""

from __future__ import annotations
import saas.photographer.photo as PhotoPath
from saas.utils.files import create_dir
import shutil
import os


class DataDirectory:
    """Data directory class."""

    def __init__(self, path: str):
        """Create new data directory instance.

        Args:
            path: paath to root of data directory
        """
        self.root = path
        self.root = create_dir(self.root)

    def remove_data_dir(self):
        """Remove data directory root."""
        shutil.rmtree(self.root)

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
        return directory + photo_path.uuid + '.png'
