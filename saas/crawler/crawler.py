"""Crawler module."""

from __future__ import annotations
from saas.storage.index import Index, EmptySearchResultException
import saas.utils.console as console
from saas.web.browser import Browser
from saas.web.url import Url
import time
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
        ignore_found_urls: bool=False,
        stay_at_domain: bool=False,
    ):
        """Create crawler.

        Args:
            url_file: path to url file
            index: Index storage for queued urls
            ignore_found_urls: if crawler should ignore new urls found on
                pages it crawls
            stay_at_domain: if crawler should ignore urls from a different
                domain than the one it was found at
        """
        self.source_is_open = False
        self.source_path = ''
        self.source_mode = ''
        self._open_source('r', url_file)
        self.ignore_found_urls = ignore_found_urls
        self.stay_at_domain = stay_at_domain
        self.index = index

    def _open_source(self, mode: str, url_file: str=''):
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
            self._close_source()
        self.source_is_open = True

        if self.source_path == '':
            file = self._real_path(url_file)
            if not os.path.isfile(file):
                raise UrlFileNotFoundError(f'url file was not found at {file}')
            self.source_path = file

        self.source_mode = mode
        self.source = open(self.source_path, mode)

    def _close_source(self):
        """Close url source file."""
        self.source_is_open = False
        self.source.close()

    def _real_path(self, url_file: str) -> str:
        """Real path.

        Args:
            url_file: relative path

        Returns:
            Absolute oath
            str
        """
        if url_file[0] == '~':
            root = os.path.expanduser('~')
            url_file = url_file[1:]
        elif url_file[0] == '/':
            root = '/'
        else:
            root = os.getcwd()
        return f'{root}/{url_file}'.replace('//', '/').replace('//', '/')

    def tick(self):
        """Tick.

        Check if there are any uncrawled urls, if none exists
        then sleep for a second, otherwise crawl url.
        """
        url = self._next_url()

        if not url:
            time.sleep(1)
            return

        if url is not None:
            self.index.add_crawled_url(url)

            console.dcr(f'crawling {url.to_string()}')

            page = Browser.get_page(url)
            if 'text/html' not in page.content_type:
                page.status_code = 0

            console.dcr(f'{url.to_string()} responded with {page.status_code}')

            self.index.set_status_code_for_crawled_url(
                url,
                page.status_code
            )

            if self.ignore_found_urls:
                return

            if page.status_code != 200:
                return

            if self.stay_at_domain:
                page.remove_urls_not_from_domain(url.domain)

            console.dcr(f'found {len(page.urls)} links at {url.to_string()}')

            self.index.add_uncrawled_urls(page.urls)

    def _next_url(self):
        """Get next url to crawl.

        Returns:
            A url to crawl, None if no url was found
            Url or None
        """
        self._open_source('r')
        lines = sum(1 for line in self.source)

        if lines == 0:
            return self._next_url_in_index()

        self.source.seek(0)
        lines = self.source.read().split('\n')

        if lines[0] == '':
            return self._next_url_in_index()

        self._open_source('w')
        for line in lines:
            if line != lines[0] and line.strip() != '':
                self.source.write(line + '\n')
        self._close_source()

        url = Url.from_string(lines[0])
        return url

    def _next_url_in_index(self):
        """Get next url to crawl from index.

        Returns:
            A url to crawl, None if no url was found
            Url or None
        """
        try:
            url = self.index.random_uncrawled_url()
        except EmptySearchResultException:
            return None
        self.index.remove_uncrawled_url(url.hash())
        return url

    def stop(self):
        """Stop crawler."""
        self._close_source()


class UrlFileNotFoundError(ValueError):
    """Url file not found error."""

    pass
