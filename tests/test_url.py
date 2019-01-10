"""Crawler test."""

from saas.web.url import Url
import unittest
import hashlib


class TestCrawler(unittest.TestCase):
    """Test crawler class."""

    def test_url_can_be_created_from_string(self):
        """Test url can be created from string."""
        url = 'https://example.com/foo/bar/baz?bax=bat&moo=loo#hello'
        url = Url.from_string(url)
        self.assertEqual('https', url.scheme)
        self.assertEqual('example.com', url.domain)
        self.assertEqual('/foo/bar/baz', url.path)
        self.assertEqual('bax=bat&moo=loo', url.query)
        self.assertEqual('hello', url.fragment)

    def test_url_can_be_converted_back_to_string(self):
        """Test url can be converted back to string."""
        url = 'https://example.com/foo/bar/baz?bax=bat&moo=loo#hello'
        parsed = Url.from_string(url)
        self.assertEqual(url, parsed.to_string())

    def test_url_can_be_hashed(self):
        """Test url can be hashed."""
        url = 'https://example.com/foo/bar/baz?bax=bat&moo=loo#hello'
        hash = hashlib.sha256(url.encode()).hexdigest()

        parsed = Url.from_string(url)
        self.assertEqual(hash, parsed.hash())

    def test_fully_qualified_url_can_be_created_from_uri(self):
        """Test fully qualified url can be created from a uri and url."""
        root = 'https://example.com/foo'
        root = Url.from_string(root)

        self.assertEqual(
            'https://example.com/foo/bar',
            root.create_child_url('bar').to_string()
        )

        self.assertEqual(
            'https://example.com/bar',
            root.create_child_url('/bar').to_string()
        )

        root = 'https://example.com?foo=bar'
        root = Url.from_string(root)

        self.assertEqual(
            'https://example.com/bar#foo',
            root.create_child_url('/bar#foo').to_string()
        )


if __name__ == '__main__':
    unittest.main()
