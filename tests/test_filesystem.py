"""Filesystem test."""

from saas.photographer.photo import PhotoPath, Screenshot
from saas.mount.file import Directory, File, LastCapture
from saas.storage.datadir import DataDirectory
from saas.mount.filesystem import Filesystem
from unittest.mock import MagicMock, call
import saas.storage.refresh as refresh
from saas.storage.index import Index
import saas.utils.console as console
from saas.web.url import Url
from os.path import dirname
import unittest
import time
import os


class TestFilesystem(unittest.TestCase):
    """Test filesystem class."""

    def setUp(self):
        """Set up test."""
        self.console = console
        self.refresh_rate = refresh.Hourly
        self.datadir = DataDirectory(dirname(__file__) + '/datadir')
        self.index = Index(self.datadir, MagicMock())
        self.filesystem = Filesystem(self.index, self.refresh_rate)

    def tearDown(self):
        """Tear down test."""
        self.datadir.remove_data_dir()

    def assertListOfFilesEqual(self, expected: list, actual: list):
        """Assert list of files equal.

        Args:
            expected: Expected list of files
            actual: Actual list of files
        """
        msg = 'Failed asserting list of files where equal expected'
        self.assertEqual(len(expected), len(actual), msg=msg)
        for i, file in enumerate(expected):
            self.assertEqual(file.filename, actual[i].filename, msg=msg)
            self.assertIsInstance(cls=file.__class__, obj=actual[i], msg=msg)

    def test_filesystem_can_list_contents_of_root_directory(self):
        """Test filesystem can list root directory."""
        self.index.photos_unique_domains = MagicMock(return_value=[
            'example.com',
            'example.net'
        ])

        files = self.filesystem._list('/')

        self.assertListOfFilesEqual(
            [
                Directory('.'),
                Directory('..'),
                Directory('example.com'),
                Directory('example.net'),
            ],
            files
        )
        self.index.photos_unique_domains.assert_called_with(self.refresh_rate)

    def test_filesystem_can_list_contents_of_domain(self):
        """Test filesystem can list contents of domain."""
        self.index.photos_unique_captures_of_domain = MagicMock(return_value=[
            '2019-01-13H20:00',
            '2019-01-13H21:00',
            '2019-01-13H22:00',
        ])

        expected = [
            Directory('.'),
            Directory('..'),
            Directory('2019-01-13H20:00'),
            Directory('2019-01-13H21:00'),
            Directory('2019-01-13H22:00'),
            Directory(LastCapture.FILENAME),
        ]

        files = self.filesystem._list('/example.com')
        self.assertListOfFilesEqual(expected, files)

        files = self.filesystem._list('/example.com/')
        self.assertListOfFilesEqual(expected, files)

        self.index.photos_unique_captures_of_domain.assert_called_with(
            'example.com',
            self.refresh_rate
        )

    def test_filesystem_can_list_contents_of_capture_at_given_path(self):
        """Test filesystem can list contents of capture at given path."""
        self.index.photos_list_files_in_directory = MagicMock(return_value=[
            'index.png',
            'contact.png',
            'about.png',
        ])
        self.index.photos_list_directories_in_directory = MagicMock(
            return_value=[
                'sub_dir_1',
                'sub_dir_2',
            ]
        )

        expected = [
            Directory('.'),
            Directory('..'),
            File('index.png'),
            File('contact.png'),
            File('about.png'),
            Directory('sub_dir_1'),
            Directory('sub_dir_2'),
        ]

        files = self.filesystem._list('/example.com/2019-01-13H20:00/')
        self.assertListOfFilesEqual(expected, files)

        files = self.filesystem._list('/example.com/2019-01-13H20:00')
        self.assertListOfFilesEqual(expected, files)

        files = self.filesystem._list('/example.com/2019-01-13H20:00/foo/bar/')
        self.assertListOfFilesEqual(expected, files)

        calls = [
            call('example.com', '2019-01-13H20:00', '/', self.refresh_rate),
            call('example.com', '2019-01-13H20:00', '/', self.refresh_rate),
            call(
                'example.com',
                '2019-01-13H20:00',
                '/foo/bar/',
                self.refresh_rate
            ),
        ]
        self.index.photos_list_files_in_directory.assert_has_calls(calls)
        self.index.photos_list_directories_in_directory.assert_has_calls(calls)

    def test_filesystem_can_get_attributes_of_directory(self):
        """Test filesystem can get attributes of directory."""
        time.time = MagicMock(return_value=time.time())
        self.index.photos_directory_exists = MagicMock(return_value=True)
        self.index.photos_unique_domains = MagicMock(
            return_value=['example.com']
        )
        self.index.photos_unique_captures_of_domain = MagicMock(
            return_value=['2019-01-13H20:00']
        )

        expected = {
            'st_atime': time.time(),
            'st_ctime': time.time(),
            'st_gid': os.getgid(),
            'st_mode': Directory('').ST_MODE,
            'st_mtime': time.time(),
            'st_size': 0,
            'st_uid': os.getuid(),
        }

        attr = self.filesystem._attributes('/')
        self.assertEqual(expected, attr)

        attr = self.filesystem._attributes('/example.com/')
        self.assertEqual(expected, attr)

        attr = self.filesystem._attributes('/example.com/2019-01-13H20:00')
        self.assertEqual(expected, attr)

        attr = self.filesystem._attributes('/example.com/2019-01-13H20:00/')
        self.assertEqual(expected, attr)

        attr = self.filesystem._attributes(
            '/example.com/2019-01-13H20:00/foo/bar'
        )
        self.assertEqual(expected, attr)
        self.index.photos_directory_exists.assert_called_with(
            domain='example.com',
            captured_at='2019-01-13H20:00',
            directory='/foo/bar/',
            refresh_rate=self.refresh_rate
        )

    def test_filesystem_can_get_attributes_of_file(self):
        """Test filesystem can get attributes of file."""
        time.time = MagicMock(return_value=time.time())
        self.index.photos_directory_exists = MagicMock(return_value=False)
        self.index.photos_file_exists = MagicMock(
            return_value=123000  # returns filesize
        )

        expected = {
            'st_atime': time.time(),
            'st_ctime': time.time(),
            'st_gid': os.getgid(),
            'st_mode': File('').ST_MODE,
            'st_mtime': time.time(),
            'st_size': 123000,
            'st_uid': os.getuid(),
        }

        attr = self.filesystem._attributes(
            '/example.com/2019-01-13H20:00/index.png'
        )
        self.assertEqual(expected, attr)
        self.index.photos_file_exists.assert_called_with(
            domain='example.com',
            captured_at='2019-01-13H20:00',
            full_filename='/index.png',
            refresh_rate=self.refresh_rate
        )

    def test_filesystem_can_translate_path_to_file_in_datadir(self):
        """Test filesystem can translate path to file in datadir."""
        datadir_path = PhotoPath(self.datadir)
        url = Url.from_string('https://example.com/foo/bar')
        photo = Screenshot(url, datadir_path, self.refresh_rate)
        self.index.es.index = MagicMock()
        photo.path.filesize = MagicMock(return_value=10000)
        self.index.save_photo(photo)

        self.index.photos_file_exists = MagicMock(return_value=123000)
        self.index.photos_get_photo = MagicMock(return_value=photo)

        path = self.filesystem._translate_path(
            '/example.com/2019-01-13H20:00/foo/bar.png'
        )
        self.assertEqual(datadir_path.full_path(), path)


if __name__ == '__main__':
    unittest.main()
