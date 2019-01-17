"""Crawler test."""

from saas.storage.index import Index, EmptySearchResultException
import saas.utils.console as console
from saas.crawler.crawler import Crawler
from os.path import dirname, realpath
from unittest.mock import MagicMock
from saas.web.url import Url
import unittest
import os


class TestCrawler(unittest.TestCase):
    """Test crawler class."""

    def setUp(self):
        """Set up test."""
        self.console = console
        self.path_to_url_source = dirname(realpath(__file__)) + '/urls'
        open(self.path_to_url_source, 'w+').close()

    def tearDown(self):
        """Tear down test."""
        self.crawler.stop()
        os.remove(self.path_to_url_source)

    def add_url_source(self, url: str):
        """Add a url to source list.

        Args:
            url: url string
        """
        f = open(self.path_to_url_source, 'a')
        f.write(url + '\n')
        f.close()

    def test_crawler_can_read_next_url_from_source(self):
        """Test crawler can read next url from source."""
        self.add_url_source('https://example.com')

        self.crawler = Crawler(self.path_to_url_source, Index())
        self.assertEqual(
            Url.from_string('https://example.com').to_string(),
            self.crawler._next_url().to_string()
        )

    def test_crawler_removes_urls_read_from_source(self):
        """Test crawler removes urls read from source."""
        self.add_url_source('https://example.com')
        self.add_url_source('https://example.com/foo')
        self.add_url_source('https://example.com/bar')

        self.crawler = Crawler(self.path_to_url_source, Index())

        # first line should now be https://example.com
        self.assertEqual(
            Url.from_string('https://example.com').to_string(),
            self.crawler._next_url().to_string()
        )

        # first line should now be https://example.com/foo
        self.assertEqual(
            Url.from_string('https://example.com/foo').to_string(),
            self.crawler._next_url().to_string()
        )

        # first line should now be https://example.com/bar
        self.assertEqual(
            Url.from_string('https://example.com/bar').to_string(),
            self.crawler._next_url().to_string()
        )

        self.crawler = Crawler(self.path_to_url_source, Index())

    def test_crawler_can_read_next_url_from_index(self):
        """Test crawler can read next url from source."""
        index = Index()
        url = Url.from_string('https://example.com/foo')
        index.remove_uncrawled_url = MagicMock()
        index.random_uncrawled_url = MagicMock(return_value=url)

        self.crawler = Crawler(self.path_to_url_source, index)

        self.assertEqual(
            Url.from_string('https://example.com/foo').to_string(),
            self.crawler._next_url().to_string()
        )
        index.remove_uncrawled_url.assert_called_with(url.hash())

    def test_next_url_returns_none_if_no_url_was_found(self):
        """Test _next_url() returns None if no url was found."""
        index = Index()
        index.random_uncrawled_url = MagicMock()
        index.random_uncrawled_url.side_effect = EmptySearchResultException()
        self.crawler = Crawler(self.path_to_url_source, index)

        self.assertEqual(
            None,
            self.crawler._next_url()
        )


if __name__ == '__main__':
    unittest.main()
