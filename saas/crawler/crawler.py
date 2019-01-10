"""Crawler module."""

from __future__ import annotations
import saas.utils.console as console
from saas.web.browser import Browser
from saas.storage.index import Index
from saas.web.url import Url
import os


class Crawler:
    """Crawler.

    The crawler crawls the world wide web
    for websites.
    """

    def __init__(
        self,
        url_file: str,
        index: Index,
        clear_elasticsearch: bool = False
    ):
        """Create crawler.

        Args:
            url_file: path to url file
            index: Index storage for queued urls
            clear_elasticsearch: elasticsearch cluster should cleared on start
        """
        self.source_is_open = False
        self.source_path = ''
        self.open_source('r', url_file)
        self.clear_elasticsearch = clear_elasticsearch
        self.index = index

    def open_source(self, mode: str, url_file: str=''):
        """Open source file.

        Args:
            mode: read or write
            url_file: path to url file

        Raises:
            UrlFileNotFoundError: if file wasn't found
        """
        if self.source_is_open and self.source_mode == mode:
            return
        if self.source_is_open and self.source_mode != mode:
            self.close_source()
        self.source_is_open = True

        if self.source_path == '':
            file = self.real_path(url_file)
            if not os.path.isfile(file):
                raise UrlFileNotFoundError(f'url file was not found at {file}')
            self.source_path = file

        self.source_mode = mode
        self.source = open(self.source_path, mode)

    def close_source(self):
        """Close url source file."""
        self.source_is_open = False
        self.source.close()

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
        if self.clear_elasticsearch:
            self.index.clear()
            self.index.create_indices()

        while True:
            url = self.next_url()
            if not url:
                continue

            if url is not None:
                console.p(url.to_string(), end='')
                self.index.add_crawled_url(url)

                page = Browser.get_page(url)
                if page:
                    page.add_url(url)
                    self.index.add_uncrawled_urls(page.urls)
            console.p('.')

    def next_url(self):
        """Get next url to crawl.

        Returns:
            A url to crawl, None if no url was found
            Url or None
        """
        self.open_source('r')
        lines = sum(1 for line in self.source)

        if lines == 0:
            return self.next_url_in_index()

        self.source.seek(0)
        lines = self.source.read().split('\n')

        if lines[0] == '':
            return self.next_url_in_index()

        self.open_source('w')
        for line in lines:
            if line != lines[0]:
                self.source.write(line + '\n')
        self.close_source()

        url = Url.from_string(lines[0])
        return url

    def next_url_in_index(self):
        """Get next url to crawl from index.

        Returns:
            A url to crawl, None if no url was found
            Url or None
        """
        doc = self.index.get_most_recent_uncrawled_url()
        if doc is None:
            return None
        self.index.remove_uncrawled_url(doc['_id'])
        return Url.from_string(doc['_source']['url'])

    def stop(self):
        """Stop crawler."""
        self.close_source()


class UrlFileNotFoundError(ValueError):
    """Url file not found error."""

    pass
