"""Photographer test."""

from saas.photographer.photographer import Photographer
from saas.storage.datadir import DataDirectory
import saas.storage.refresh as refresh
from saas.storage.index import Index
from unittest.mock import MagicMock
from saas.web.url import Url
from os.path import dirname
import unittest


class TestPhotographer(unittest.TestCase):
    """Test photographer class."""

    def setUp(self):
        """Set up test."""
        self.index = Index()
        self.datadir = DataDirectory(dirname(__file__) + '/datadir')
        self.photographer = Photographer(
            self.index,
            refresh.Hourly,
            self.datadir
        )

    def tearDown(self):
        """Tear down test."""
        self.datadir.remove_data_dir()

    def does_url_checkout(self):
        """Test does checkut of url.

        Add mock to affected index methods.
        """
        url = Url.from_string('https://example.com')
        self.index.recently_crawled_url = MagicMock(return_value=url)
        self.index.crawled_urls_count = MagicMock(return_value=1)
        self.index.lock_crawled_url = MagicMock()

    def test_photographer_can_checkout_url_from_crawled_index(self):
        """Test photographer can checkout url from "crawled" index."""
        self.does_url_checkout()

        url = self.photographer._checkout_url()
        self.assertIsInstance(cls=Url, obj=url)

    def test_photographer_locks_the_url_on_checkout(self):
        """Test photographer locks url on checkout."""
        self.does_url_checkout()

        url = self.photographer._checkout_url()
        self.index.lock_crawled_url.assert_called_with(
            url,
            refresh.Hourly
        )


if __name__ == '__main__':
    unittest.main()
