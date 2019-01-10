"""Crawler module."""

from __future__ import annotations
import saas.utils.console as console
from _io import TextIOWrapper
from saas.web.url import Url
from saas.web.browser import Browser
import time
import os


class Crawler:
    """Crawler.

    The crawler crawls the world wide web
    for websites.
    """

    def __init__(self, url_file: str):
        """Create crawler.

        Args:
            url_file: path to url file
        """
        self.source, self.source_path = self.open_source(url_file)

    def open_source(self, url_file: str) -> TextIOWrapper:
        """Open source file.

        Args:
            url_file: path to url file

        Returns:
            Source file resource
            TextIOWrapper

        Raises:
            UrlFileNotFoundError: if file wasn't found
        """
        file = self.real_path(url_file)
        if not os.path.isfile(file):
            raise UrlFileNotFoundError(f'url file was not found at {file}')
        return open(file, 'r+'), file

    def real_path(self, url_file: str) -> str:
        """Real path.

        Args:
            url_file: relative path

        Returns:
            Absolute oath
            str
        """
        if url_file[0] == '~':
            root = os.path.expanduser('~')
        elif url_file[0] == '/':
            root = '/'
        else:
            root = os.getcwd()
        return f'{root}/{url_file}'.replace('//', '/').replace('//', '/')

    def start(self):
        """Start crawler."""
        while True:
            console.p('.', end='')
            url = self.next_url()
            doc = Browser.get_page(url)
            console.pp(doc)
            time.sleep(1)

    def next_url(self):
        """Get next url to crawl.

        Returns:
            A url to parse
            Url
        """
        lines = sum(1 for line in open(self.source_path))
        if lines == 0:
            return
        line = self.source.read().strip()
        self.source.seek(0)
        url = Url.from_string(line)
        return url

    def stop(self):
        """Stop crawler."""
        pass


class UrlFileNotFoundError(ValueError):
    """Url file not found error."""

    pass
