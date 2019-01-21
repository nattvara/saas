"""Photo module."""

from __future__ import annotations
import saas.storage.datadir as DataDirectory
import saas.storage.refresh as refresh
from saas.web.url import Url
from abc import ABCMeta
from typing import Type
import uuid
import os


class Photo(metaclass=ABCMeta):
    """Base Photo class."""

    def __init__(
        self,
        url: Url,
        path: 'PhotoPath',
        refresh_rate: Type[refresh.RefreshRate],
        index_filesize: int=None
    ):
        """Create new photo.

        Args:
            url: The photo is taken of given Url
            path: Path to photo in data directory
            refresh_rate: The refresh rate of the photo (hourly, daily, etc.)
            index_filesize: If photo have been stored in index, filesize is
                already stored there. To speed up performance this takes
                priority over filesize in datadir. see self.filesize()
        """
        self.url = url
        self.path = path
        self.refresh_rate = refresh_rate
        self.index_filesize = index_filesize

    def get_raw(self) -> str:
        """Get raw content of photos file in data directory.

        Returns:
            Raw source
            str
        """
        file = open(self.path.full_path(), 'r')
        content = file.read()
        file.close()
        return content

    def filename(self) -> str:
        """Get photo filename.

        Returns:
            A filename based on the photos url
            str
        """
        return self.url.make_filename()

    def directory(self) -> str:
        """Get photo directory.

        Returns:
            A directory based on the photos url
            str
        """
        return self.url.make_directory()

    def domain(self) -> str:
        """Get photo domain.

        Returns:
            Domain photo belongs to
            str
        """
        return self.url.domain

    def filesize(self) -> int:
        """Get photo filesize.

        Returns:
            Size in bytes
            int
        """
        if self.index_filesize:
            return self.index_filesize
        return self.path.filesize()


class LoadingPhoto(Photo):
    """Loading photo class.

    A loading photo is created once photographer do a
    checkout of a url. This is used to display a webpage
    that is being rendered in the mounted filesystem.
    """

    def save_loading_text(self):
        """Write loading text to photo source."""
        file = open(self.path.full_path(), 'w+')
        file.write('loading')
        file.close()


class Screenshot(Photo):
    """Screenshot photo class."""

    pass


class PhotoPath:
    """Photopath class."""

    def __init__(
        self,
        datadir: DataDirectory.DataDirectory,
        uuid: str=''
    ):
        """Create new path to a photo.

        Args:
            datadir: Data directory to store photo in
            uuid: If an PhotoPath should represent an existing
                path, use uuid argument, otherwise a new uuid
                will be generated
        """
        self.datadir = datadir
        if uuid != '':
            self.uuid = uuid
        else:
            self.uuid = self.make_uuid()

    def make_uuid(self) -> str:
        """Make uuid.

        Returns:
            A unique id
            str
        """
        return str(uuid.uuid4())

    def full_path(self) -> str:
        """Get full path to photo's file in datadir.

        Returns:
            An absolute path to the photo
            str
        """
        return self.datadir.path_for_photo(self)

    def filesize(self) -> int:
        """Get filesize.

        Returns:
            Size in bytes
            int
        """
        return os.path.getsize(self.full_path())

    def should_optimize(self) -> bool:
        """If photo file should be optimized.

        Returns:
            True if should be optimize, otherwise False
            bool
        """
        return self.datadir.optimize_storage

    def optimize(self):
        """Optimize png file in data directory."""
        self.datadir.optimize_file(self.full_path())
