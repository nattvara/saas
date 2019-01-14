"""File module."""

from __future__ import annotations
import time
import os


class Path:
    """Path class."""

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
        path = path.split('/')
        return path[1]

    def _parse_captured_at(self, path: str) -> str:
        """Parse captured_at from path.

        Args:
            path: A path to parse

        Returns:
            A captured_at value (see refresh module)
            str
        """
        path = path.split('/')
        if len(path) >= 3:
            return path[2]
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
        path = path.split('/')
        path = path[3:]
        path = '/' + '/'.join(path)
        if len(path) > 1:
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

    def __init__(self, filename: str):
        """Create new directory.

        Args:
            filename: directory filename
        """
        self.filename = filename
        self.st_mode = Directory.ST_MODE  # Permissions

    def attributes(self=None) -> dict:
        """Get attributes of file.

        Args:
            self: Self (default: {None})

        Returns:
            File attributes
            dict
        """
        return {
            'st_atime': time.time(),
            'st_ctime': time.time(),
            'st_gid': os.getgid(),
            'st_mode': Directory.ST_MODE,
            'st_mtime': time.time(),
            'st_size': 0,
            'st_uid': os.getuid(),
        }


class File:
    """File class."""

    ST_MODE = 0o100644

    def __init__(self, filename: str):
        """Create new file.

        Args:
            filename: file's filename
        """
        self.filename = filename
        self.st_mode = File.ST_MODE  # Permissions

    def attributes(self=None, filesize: int=0) -> dict:
        """Get attributes of file.

        Args:
            self: Self (default: {None})
            filesize: size of file on disk (default: {0})

        Returns:
            File attributes
            dict
        """
        return {
            'st_atime': time.time(),
            'st_ctime': time.time(),
            'st_gid': os.getgid(),
            'st_mode': File.ST_MODE,
            'st_mtime': time.time(),
            'st_size': filesize,
            'st_uid': os.getuid(),
        }
