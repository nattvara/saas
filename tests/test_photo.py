"""Photo module test."""

from saas.photographer.photo import PhotoPath, LoadingPhoto
from saas.storage.datadir import DataDirectory
import saas.storage.refresh as refresh
from os.path import dirname, isfile
from saas.web.url import Url
import unittest


class TestPhoto(unittest.TestCase):
    """Test photo class."""

    def setUp(self):
        """Set up test."""
        self.datadir = DataDirectory(dirname(__file__) + '/datadir')

    def tearDown(self):
        """Tear down test."""
        self.datadir.remove_data_dir()

    def test_photo_path_can_be_created(self):
        """Pass."""
        path = PhotoPath(self.datadir)
        self.assertGreater(len(path.uuid), 20)
        self.assertIn(member=self.datadir.root, container=path.full_path())

    def test_loading_photo_can_be_saved_to_datadir(self):
        """Test a loading photo can be saved to data directory."""
        path = PhotoPath(self.datadir)
        url = Url.from_string('https://example.com')
        photo = LoadingPhoto(
            url=url,
            path=path,
            refresh_rate=refresh.Hourly
        )
        photo.save_loading_text()
        self.assertTrue(isfile(path.full_path()))
        self.assertEqual('loading', photo.get_raw())


if __name__ == '__main__':
    unittest.main()
