"""Photographer module."""

from __future__ import annotations
from saas.storage.refresh import RefreshRate
import saas.utils.console as console
from saas.storage.index import Index
from saas.storage.index import EmptySearchResultException
from saas.web.url import Url
import time


class Photographer:
    """Photographer class."""

    def __init__(self, index: Index, refresh_rate: RefreshRate):
        """Create new photographer.

        Args:
            index: Index where crawled urls are stored and
                photos should be indexed.
            refresh_rate: How often photographs should be refreshed,
                more exactly defines which lock should be placed on
                crawled urls
        """
        self.index = index
        self.refresh_rate = refresh_rate

    def start(self):
        """Start photographer."""
        while True:
            try:
                url = self.checkout_url()
                console.pp(url)
            except EmptySearchResultException as e:
                pass
            finally:
                time.sleep(1)
                console.p('.', end='')

    def checkout_url(self) -> Url:
        """Checkout url.

        A checkout pulls the most recently added url from
        the "crawled" index. A lock is placed on the url
        for the given refresh rate.

        Returns:
            A url ready to take a picture of
            Url
        """
        url = self.index.most_recent_crawled_url(self.refresh_rate)
        self.index.lock_crawled_url(url, self.refresh_rate)
        return url
