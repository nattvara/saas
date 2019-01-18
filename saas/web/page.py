"""Page module."""

from __future__ import annotations
from saas.web.url import Url


class Page:
    """Page class."""

    def __init__(self):
        """Create new page."""
        self.urls = []
        self.status_code = None
        self.content_type = ''

    def add_url(self, url: Url):
        """Add url.

        Args:
            url: Url to add
        """
        self.urls.append(url)

    def remove_urls_not_from_domain(self, domain: str):
        """Remove urls not from given domain.

        Args:
            domain: domain urls should be from
        """
        cleaned = []
        for url in self.urls:
            if url.domain == domain:
                cleaned.append(url)
        self.urls = cleaned
