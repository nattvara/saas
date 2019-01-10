"""Browser module."""

from __future__ import annotations
from saas.web.url import Url, InvalidUrlException
from html.parser import HTMLParser
from urllib.error import HTTPError
from saas.web.page import Page
import urllib.request


class Browser:
    """Browser class.

    The browser class retrieves web pages
    from urls.
    """

    def get_page(url: Url):
        """Get page.

        Fetch page at url

        Args:
            url: Url page is located at

        Returns:
            The requested page if response is 200 otherwise None
            Page or None
        """
        parser = LinkParser()
        try:
            with urllib.request.urlopen(url.to_string()) as response:
                html = response.read()
        except HTTPError as error:
            return None

        links = parser.parse(str(html))
        page = Page()

        for link in links:
            try:
                page.add_url(Url.from_string(link))
            except InvalidUrlException as e:
                page.add_url(Url.from_string(url.to_string() + link))
        return page


class LinkParser(HTMLParser):
    """Link parser."""

    def parse(self, html: str) -> list:
        """Parse links in html string.

        Args:
            html: html document

        Returns:
            List of the found links
            list
        """
        self.links = []
        self.feed(html)
        return self.links

    def handle_starttag(self, tag, attrs):
        """Handle starttag.

        Called by parse method

        Args:
            tag: element tag
            attrs: element attributes
        """
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                    self.links.append(value)
