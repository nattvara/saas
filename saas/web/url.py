"""Url module."""

from __future__ import annotations
from urllib.parse import urlparse
import unicodedata
import hashlib
import re


class Url:
    """Url class."""

    def __init__(
            self,
            scheme: str,
            domain: str,
            path: str,
            query: str,
            fragment: str
    ):
        """Create new url.

        Args:
            scheme: eg. https
            domain: example.com
            path: /path/to/page.html
            query: ?some_param=value
            fragment: #some_string
        """
        self.scheme = scheme
        self.domain = domain
        self.path = path
        self.query = query
        self.fragment = fragment
        self.sha256 = ''

    @staticmethod
    def from_string(url: str) -> 'Url':
        """Create url from string.

        Args:
            url: string

        Returns:
            A url
            Url
        """
        parse = urlparse(url)
        if parse.scheme != 'http' and parse.scheme != 'https':
            raise InvalidUrlException('invalid url scheme')
        if '.' not in parse.netloc:
            raise InvalidUrlException('invalid domain scheme')
        path = parse.path
        while '//' in path:
            path = path.replace('//', '/')
        if len(path) > 0:
            if path[-1:] == '/':
                path = path[:-1]
        return Url(
            scheme=parse.scheme,
            domain=parse.netloc,
            path=path,
            query=parse.query,
            fragment=parse.fragment,
        )

    def to_string(self) -> str:
        """Convert url to string.

        Returns:
            The url as a string
            str
        """
        url = f'{self.scheme}://{self.domain}{self.path}'
        if self.query:
            url = f'{url}?{self.query}'
        if self.fragment:
            url = f'{url}#{self.fragment}'
        return url

    def hash(self) -> str:
        """Get sha256 hash of url.

        Returns:
            A sha256 hash of the url
            str
        """
        if self.sha256 != '':
            return self.sha256
        self.sha256 = hashlib.sha256(self.to_string().encode()).hexdigest()
        return self.sha256

    def make_filename(self) -> str:
        """Make filename.

        Make the filename used in filesystem.

        Returns:
            A safe filename to use in filesystem
            str
        """
        if self.fragment:
            with_fragment_filename = ''  # type: str
            with_fragment_filename = self._safe_filename(
                self.fragment
            ) + '.png'
            return with_fragment_filename

        if self.query:
            with_query_filename = ''  # type: str
            with_query_filename = self._safe_filename(self.query) + '.png'
            return with_query_filename

        filename = ''  # type: str
        filename = self._safe_filename(self.path.split('/')[-1:][0])
        if filename == '':
            filename = 'index'
        return filename + '.png'

    def make_directory(self) -> str:
        """Make directory.

        Make the relative path from data directory root directly
        above the result from make_filename().

        Returns:
            A path to url in data directory that is safe to use
            str
        """
        if self.path:
            dirs = self.path.split('/')
            for i, dir in enumerate(dirs):
                dirs[i] = self._safe_filename(dir)
            directory = '/'.join(dirs)
        else:
            directory = '/'

        if directory[-1:] != '/':
            directory += '/'

        if self.query:
            directory += '?/' + self._safe_filename(self.query) + '/'

        if self.fragment:
            directory += '#/' + self._safe_filename(self.fragment) + '/'

        directory = '/'.join(directory.split('/')[:-2])

        if directory[-1:] != '/':
            directory += '/'

        return directory

    def _safe_filename(self, value: str):
        """Make safe filename.

        Source:
            https://github.com/django/django/blob/master/django/utils/text.py
            basically copied the slugify function and added some handling
            of query params

        Args:
            value: A string value that might be unsafe for a filename

        Returns:
            A safe string to use as filename
            str
        """
        value = str(value)
        value = value.replace('=', '-')
        value = value.replace('&', '-and-')
        value = unicodedata.normalize(
            'NFKD',
            value
        ).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()
        return re.sub(r'[-\s]+', '-', value)

    def create_child_url(self, uri: str) -> 'Url':
        """Create child url from string.

        eg the child login of https://example.com with the uri
        /login would be https://example.com/login

        Args:
            uri: a path to a resource

        Returns:
            A fully qualified url
            Url
        """
        if len(uri) == 0:
            raise InvalidUrlException('uri was empty')
        if len(uri) > 1:
            if f'{uri[0]}{uri[1]}' == '//':
                return Url.from_string(f'{self.scheme}:{uri}')
        if uri[0] == '/':
            return Url.from_string(f'{self.scheme}://{self.domain}{uri}')
        if uri[0] == '#':
            return Url.from_string(f'{self.scheme}://{self.domain}{uri}')
        return Url.from_string(
            f'{self.scheme}://{self.domain}{self.path}/{uri}'
        )


class UrlId(Url):
    """Url id class.

    The url id class is used when creating a photo and
    it might not be neccessary to load all url properties
    yet, but might be neccessary in the future.
    """

    def __init__(self, id: str):
        """Create new url.

        Args:
            id: Url id (same as the hash of a real url)
        """
        self.id = id


class InvalidUrlException(ValueError):
    """Invalid url exception."""

    pass
