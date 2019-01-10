"""Url module."""

from __future__ import annotations
from urllib.parse import urlparse
import hashlib


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

    def hash(self):
        """Get sha256 hash of url.

        Returns:
            A sha256 hash of the url
            str
        """
        if self.sha256 != '':
            return self.sha256
        self.sha256 = hashlib.sha256(self.to_string().encode()).hexdigest()
        return self.sha256

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
        if uri[0] == '/':
            return Url.from_string(f'{self.scheme}://{self.domain}{uri}')
        if uri[0] == '#':
            return Url.from_string(f'{self.scheme}://{self.domain}{uri}')
        return Url.from_string(
            f'{self.scheme}://{self.domain}{self.path}/{uri}'
        )


class InvalidUrlException(ValueError):
    """Invalid url exception."""

    pass
