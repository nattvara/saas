"""Page module."""

from __future__ import annotations
from saas.web.url import Url


class Page:
    """Page class."""

    def __init__(self):
        """Create new page."""
        self.urls = []
        self.status_code = None

    def add_url(self, url: Url):
        """Add url.

        Args:
            url: Url to add
        """
        self.urls.append(url)
