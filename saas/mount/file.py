"""File module."""

from __future__ import annotations
from saas.storage.refresh import RefreshRate
import saas.storage.index as idx
from typing import Optional, Type
import time
import os


class Path:
    """Path class."""

    RENDERING_EXTENSION = '.rendering.saas'

    def __init__(self, path: str):
        """Create path.

        Args:
            path: a string representing a path, for example
                /example.com/2019-01-13H20:00/some_dir/index.png
        """
        if len(path) == 0:
            raise InvalidPathException(
                f'path was invalid, must be longer than 0 chars'
            )

        if path[0] != '/':
            raise InvalidPathException('path must start with a slash \'/\'')

        path = path.replace(Path.RENDERING_EXTENSION, '')

        self.domain = self._parse_domain(path)
        self.captured_at = self._parse_captured_at(path)
        self.end = self._parse_end(path)

    def _parse_domain(self, path: str) -> str:
        """Parse domain from path.

        Args:
            path: Path to parse

        Returns:
            A domain name
            str
        """
        pieces = path.split('/')
        return pieces[1]

    def _parse_captured_at(self, path: str) -> str:
        """Parse captured_at from path.

        Args:
            path: A path to parse

        Returns:
            A captured_at value (see refresh module)
            str
        """
        pieces = path.split('/')
        if len(pieces) >= 3:
            return pieces[2]
        return ''

    def _parse_end(self, path: str) -> str:
        """Parse end from a path.

        Args:
            path: A path to parse

        Returns:
            Everything from path except from domain and
                captured_at
            str
        """
        pieces = path.split('/')
        piece = pieces[3:]
        path = '/' + '/'.join(piece)
        if len(piece) > 1:
            path = path.rstrip('/')
        return path

    def includes_domain(self) -> bool:
        """Check if path includes domain.

        Returns:
            True if path includes domain, otherwise False
            bool
        """
        if self.domain != '':
            return True
        return False

    def includes_captured_at(self) -> bool:
        """Check if path includes captured_at.

        Returns:
            True if path includes captured at, otherwise False
            bool
        """
        if self.captured_at != '':
            return True
        return False

    def includes_end(self) -> bool:
        """Check if path includes end.

        Returns:
            True if path includes end, otherwise False
            bool
        """
        if self.end == '':
            return False
        if self.end == '/':
            return False
        return True

    def end_as_file(self) -> str:
        """Get end of path as a file.

        Should never end with a slash

        Returns:
            End of path
            str
        """
        return self.end

    def end_as_directory(self) -> str:
        """Get end of path as a directory.

        Should always end with a slash

        Returns:
            End of path
            str
        """
        end = self.end.rstrip('/')
        end += '/'
        return end


class InvalidPathException(Exception):
    """Invalid path exception."""

    pass


class Directory:
    """Directory class."""

    ST_MODE = 0o40755

    TIME = 0.0

    def __init__(self, filename: str):
        """Create new directory.

        Args:
            filename: directory filename
        """
        self.filename = filename
        self.st_mode = Directory.ST_MODE  # Permissions
        if Directory.TIME == 0.0:
            Directory.TIME = time.time()

    def attributes(self: Optional['Directory']=None) -> dict:
        """Get attributes of file.

        Args:
            self: Self (default: {None})

        Returns:
            File attributes
            dict
        """
        return {
            'st_atime': Directory.TIME,
            'st_ctime': Directory.TIME,
            'st_gid': os.getgid(),
            'st_mode': Directory.ST_MODE,
            'st_mtime': Directory.TIME,
            'st_size': 0,
            'st_uid': os.getuid(),
        }


class File:
    """File class."""

    ST_MODE = 0o100644

    TIME = 0.0

    def __init__(self, filename: str):
        """Create new file.

        Args:
            filename: file's filename
        """
        self.filename = filename
        self.st_mode = File.ST_MODE  # Permissions
        if File.TIME == 0.0:
            File.TIME = time.time()

    def attributes(self: Optional['File']=None, filesize: int=0) -> dict:
        """Get attributes of file.

        Args:
            self: Self (default: {None})
            filesize: size of file on disk (default: {0})

        Returns:
            File attributes
            dict
        """
        return {
            'st_atime': File.TIME,
            'st_ctime': File.TIME,
            'st_gid': os.getgid(),
            'st_mode': File.ST_MODE,
            'st_mtime': File.TIME,
            'st_size': filesize,
            'st_uid': os.getuid(),
        }


class LastCapture:
    """Last captured class.

    The last capture is the most recent capture of a domain.
    This class helps convert last capture placeholder to
    real captured_at value.
    """

    FILENAME = 'latest'

    CACHE_AGE_LIMIT = 60

    captures = {}  # type: dict

    cached_at = {}  # type: dict

    @staticmethod
    def translate(
        captured_at: str,
        domain: str,
        index: idx.Index,
        refresh_rate: Type[RefreshRate]
    ) -> str:
        """Translate captured_at to cached value.

        If a captured_at value is FILENAME this will translate
        it to the most recent captured_at value for given
        domain and refresh_rate

        Args:
            captured_at: photos captured at
            domain: photos from a given domain
            index: Index photos are stored in
            refresh_rate: refresh rate capture should be for

        Returns:
            original value if captured_at was not FILENAME, if it
            was FILENAME then the most recent captured_at value is returned
            str
        """
        try:
            if captured_at == LastCapture.FILENAME:
                if not LastCapture._is_cached(domain):
                    LastCapture._update(domain, index, refresh_rate)
                captured_at = LastCapture._from_cache(domain)
        except idx.EmptySearchResultException:
            pass
        return captured_at

    @staticmethod
    def _from_cache(domain: str) -> str:
        """Get last capture of domain from cache.

        Args:
            domain: last capture of domain

        Returns:
            Last captured_at value
            str
        """
        captured_at = LastCapture.captures[domain]  # type: str
        return captured_at

    @staticmethod
    def _is_cached(domain: str) -> bool:
        """Check if last capture has a valid cache.

        Args:
            domain: last capture of domain

        Returns:
            True if a valid cache exists, otherwise False
            bool
        """
        if domain not in LastCapture.captures:
            return False

        cache_age = time.time() - LastCapture.cached_at[domain]

        if cache_age > LastCapture.CACHE_AGE_LIMIT:
            return False

        return True

    @staticmethod
    def _update(
        domain: str,
        index: idx.Index,
        refresh_rate: Type[RefreshRate]
    ):
        """Update cache.

        Args:
            domain: domain to cache
            index: Index photos are stored in
            refresh_rate: refresh rate capture should be for
        """
        capture = index.photos_most_recent_capture_of_domain(
            domain,
            refresh_rate
        )
        LastCapture.captures[domain] = capture
        LastCapture.cached_at[domain] = time.time()
