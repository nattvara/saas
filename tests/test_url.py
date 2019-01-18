"""Url test."""

from saas.web.url import Url
import unittest
import hashlib


class TestUrl(unittest.TestCase):
    """Test url class."""

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

        self.assertEqual(
            'https://foo.com',
            root.create_child_url('//foo.com').to_string()
        )

        root = 'https://example.com?foo=bar'
        root = Url.from_string(root)

        self.assertEqual(
            'https://example.com/bar#foo',
            root.create_child_url('/bar#foo').to_string()
        )

    def test_trailing_slash_is_removed_from_path(self):
        """Test trailing slash of path is treated the same as without slash."""
        url1 = 'https://example.com/foo/bar/'  # with trailing slash
        url2 = 'https://example.com/foo/bar'  # without trailing slash
        url1 = Url.from_string(url1)
        url2 = Url.from_string(url2)

        self.assertEqual('https://example.com/foo/bar', url1.to_string())
        self.assertEqual('https://example.com/foo/bar', url2.to_string())

    def test_filename_can_be_created(self):
        """Test filename can be created from url."""
        url = Url.from_string('https://example.com/foo/BAR-baz-bAt')
        self.assertEqual('bar-baz-bat.png', url.make_filename())

        url = Url.from_string('https://example.com/')
        self.assertEqual('index.png', url.make_filename())

        url = Url.from_string('https://example.com?someid=123&otherid=FOO')
        self.assertEqual('someid-123-and-otherid-foo.png', url.make_filename())

        url = Url.from_string('https://example.com?someid=123456#foobarbaz')
        self.assertEqual('foobarbaz.png', url.make_filename())

    def test_directory_can_be_created(self):
        """Test directory can be created from url."""
        url = Url.from_string('https://example.com/foo/baz/BAR-123/index.html')
        self.assertEqual('/foo/baz/bar-123/', url.make_directory())

        url = Url.from_string('https://example.com')
        self.assertEqual('/', url.make_directory())

        url = Url.from_string('https://example.com/')
        self.assertEqual('/', url.make_directory())

        url = Url.from_string('https://example.com/foo?someid=123&otherid=FOO')
        self.assertEqual('/foo/?/', url.make_directory())

        url = Url.from_string('https://example.com/1/2?id=123&param#foo')
        self.assertEqual('/1/2/?/id-123-and-param/#/', url.make_directory())


if __name__ == '__main__':
    unittest.main()
