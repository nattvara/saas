"""Data directory module."""

from __future__ import annotations
import saas.photographer.photo as PhotoPath
from saas.utils.files import create_dir
import saas.utils.console as console
import shutil
import os


class DataDirectory:
    """Data directory class."""

    def __init__(self, path: str, optimize_storage: bool=False):
        """Create new data directory instance.

        Args:
            path: path to root of data directory
            optimize_storage: if photo files should be optimized
        """
        self.root = path
        self.root = create_dir(self.root)
        self.optimize_storage = optimize_storage

    def remove_data_dir(self):
        """Remove data directory root."""
        shutil.rmtree(self.root)

    def clear(self):
        """Clear data directory."""
        console.p(f'clearing data directory at: {self.root}')
        shutil.rmtree(self.root)
        create_dir(self.root)

    def path_for_photo(self, photo_path: PhotoPath.PhotoPath) -> str:
        """Get path for photo in data directory.

        Args:
            photo_path: A photo path object

        Returns:
            An absolute path to the file in data dir where photo is stored
            str
        """
        first_char = photo_path.uuid[0]
        second_char = photo_path.uuid[1]
        directory = self.root + '/' + first_char + second_char + '/'
        if not os.path.exists(directory):
            os.mkdir(directory)
        return directory + photo_path.uuid + '.png'

    def optimize_file(self, path: str):
        """Optimize file at path.

        Args:
            path: full path to file in data directory

        Raises:
            MissingDependencyException: if imagemagick is not installed
        """
        if os.system('command -v mogrify > /dev/null') != 0:
            raise MissingDependencyException('missing dependency imagemagick')

        cmd = 'mogrify -filter Triangle -define filter:support=2'
        cmd += ' -unsharp 0.25x0.08+8.3+0.045 -dither None -posterize 136'
        cmd += ' -quality 82 -define png:compression-filter=5'
        cmd += ' -define png:compression-level=9'
        cmd += ' -define png:compression-strategy=1'
        cmd += ' -define png:exclude-chunk=all -interlace none'
        cmd += ' -colorspace sRGB'
        cmd += ' ' + path

        os.system(cmd)


class MissingDependencyException(Exception):
    """Missing dependency exception."""

    pass
