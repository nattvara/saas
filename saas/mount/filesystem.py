"""Filesystem module."""

from __future__ import annotations
from saas.mount.file import Path, Directory, File, LastCapture
from saas.storage.index import Index, PhotoNotFoundException
from saas.storage.refresh import RefreshRate
from saas.utils.files import real_path
from fuse import FUSE, Operations
import errno
import os


def mount(mountpoint: str, index: Index, refresh_rate: RefreshRate):
    """Mount filesystem.

    Mount filesystem at given path.

    Args:
        mountpoint: where to mount filesystem
        index: index to read data from
        refresh_rate: Which refresh rate filesystem should use
                for fetching photos
    """
    filesystem = Filesystem(index, refresh_rate)
    FUSE(filesystem, real_path(mountpoint), nothreads=True, foreground=True)


class Filesystem(Operations):
    """Filesystem.

    The filesystem class can respond to requests for files
    from the kernel using FUSE

    See:
        https://github.com/libfuse/libfuse
    """

    ROOT_PATH = '/'

    def __init__(self, index: Index, refresh_rate: RefreshRate):
        """Create new filesystem.

        Args:
            index: Index where photos are stored
            refresh_rate: Which refresh rate filesystem should use
                for fetching photos
        """
        self.index = index
        self.refresh_rate = refresh_rate

    def write(self, path: str, data: str, offset: int, fh: int):
        """Write to file.

        Disabled.

        Args:
            path: path to file
            data: data to write
            length: number of bytes to read
            offset: where to start in file

        Raises:
            IOError: will always raise this exception
        """
        raise IOError(
            errno.EPERM,
            os.strerror(errno.EPERM),
            path
        )

    def getattr(self, path: str, fh=None) -> dict:
        """Get attributes of file.

        Args:
            path: path to file
            fh: file descriptor

        Returns:
            Dictionary with file attributes
            dict

        Raises:
            FileNotFoundError: If a file was not found at path
        """
        try:
            return self._attributes(path)
        except PhotoNotFoundException:
            pass
        except FileNotFoundError:
            pass
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)

    def readdir(self, path: str, fh: int) -> str:
        """Read directory.

        List directory contents.

        Args:
            path: path to directory
            fh: file descriptor

        Yields:
            File in directory
            str
        """
        for file in self._list(path):
            yield file.filename

    def open(self, path: str, flags: int) -> int:
        """Open file for low level io.

        Args:
            path: path to file
            flags: flags

        Returns:
            Returns a file descriptor id
            int
        """
        return os.open(self._translate_path(path), flags)

    def read(self, path: str, length: int, offset: int, fh: int) -> str:
        """Read from file.

        Args:
            path: path to file
            length: number of bytes to read
            offset: where to start in file
            fh: file descriptor

        Returns:
            Contents of file
            str
        """
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def _attributes(self, path: str) -> dict:
        """Get attributes of file at path.

        Args:
            path: path to file

        Returns:
            Dictionary with file attributes, see files module
            dict

        Raises:
            FileNotFoundError: if no file exists at given path
        """
        if path == Filesystem.ROOT_PATH:
            return Directory.attributes()

        path = Path(path)

        if path.includes_domain() and not path.includes_captured_at():
            domains = self.index.photos_unique_domains(self.refresh_rate)
            if path.domain not in domains:
                raise FileNotFoundError(f'Unkown domain: {path.domain}')
            return Directory.attributes()

        if path.includes_captured_at() and not path.includes_end():
            captures = self.index.photos_unique_captures_of_domain(
                path.domain,
                self.refresh_rate
            )
            captures.append(LastCapture.FILENAME)
            if path.captured_at not in captures:
                raise FileNotFoundError(f'Unkown capture: {path.captured_at}')
            return Directory.attributes()

        if self.index.photos_directory_exists(
            domain=path.domain,
            captured_at=path.captured_at,
            directory=path.end_as_directory(),
            refresh_rate=self.refresh_rate
        ):
            return Directory.attributes()

        file_exists = self.index.photos_file_exists(
            domain=path.domain,
            captured_at=path.captured_at,
            full_filename=path.end_as_file(),
            refresh_rate=self.refresh_rate
        )
        if file_exists:
            return File.attributes(None, file_exists)

        raise FileNotFoundError(f'No file at path: {path}')

    def _list(self, path: str) -> list:
        """List directory.

        Args:
            path: path to directory

        Returns:
            List of directory content
            list
        """
        if path == Filesystem.ROOT_PATH:
            return self._list_root()

        path = Path(path)

        if not path.includes_captured_at():
            return self._list_unique_captures(path.domain)

        return self._list_directory(
            path.domain,
            path.captured_at,
            path.end_as_directory()
        )

    def _list_root(self) -> list:
        """List root directory.

        Returns:
            List of domains
            list
        """
        files = self._current_and_parent_dirs()
        for domain in self.index.photos_unique_domains(self.refresh_rate):
            files.append(Directory(domain))
        return files

    def _list_unique_captures(self, domain: str) -> list:
        """List unique captures of domain.

        Args:
            domain: domain name to list

        Returns:
            List of captures.
            list
        """
        files = self._current_and_parent_dirs()

        captures = self.index.photos_unique_captures_of_domain(
            domain,
            self.refresh_rate
        )
        for file in captures:
            files.append(Directory(file))

        files.append(Directory(LastCapture.FILENAME))

        return files

    def _list_directory(
        self,
        domain: str,
        captured_at: str,
        directory: str
    ) -> list:
        """List contents of a directory.

        Args:
            domain: filter by domain
            captured_at: filter by capture time
            directory: directory path

        Returns:
            A list of files and directories
            list
        """
        files = self._current_and_parent_dirs()

        result = self.index.photos_list_files_in_directory(
            domain,
            captured_at,
            directory,
            self.refresh_rate
        )
        for file in result:
            files.append(File(file))

        result = self.index.photos_list_directories_in_directory(
            domain,
            captured_at,
            directory,
            self.refresh_rate
        )
        for file in result:
            files.append(Directory(file))

        return files

    def _current_and_parent_dirs(self) -> list:
        """Get current and parent directory.

        Returns:
            List of directories
            list
        """
        return [
            Directory('.'),
            Directory('..'),
        ]

    def _translate_path(self, path: str) -> str:
        """Translate path to path in data dir.

        Args:
            path: Path in mounted directory eg.
                /example.com/2019-01-13H20:00/foo/bar.png

        Returns:
            Path in data directory to raw data
            str

        Raises:
            FileNotFoundError: If file at given path does not exist
        """
        path = Path(path)
        exists = self.index.photos_file_exists(
            domain=path.domain,
            captured_at=path.captured_at,
            full_filename=path.end_as_file(),
            refresh_rate=self.refresh_rate
        )
        if not exists:
            raise FileNotFoundError('photo do not exist in index')

        photo = self.index.photos_get_photo(
            domain=path.domain,
            captured_at=path.captured_at,
            full_filename=path.end_as_file(),
            refresh_rate=self.refresh_rate
        )

        return photo.path.full_path()
