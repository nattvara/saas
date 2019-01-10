"""Storage module."""

from __future__ import annotations
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import saas.utils.console as console
from saas.web.page import Page
import hashlib


class Index:
    """Index storage.

    Wrapper around elasticsearch api
    """

    def __init__(self):
        """Create new index."""
        self.es = Elasticsearch(max_retries=2, retry_on_timeout=True)

    def clear(self):
        """Clear all documents."""
        console.p('clearing all indices')
        self.es.indices.delete(index='_all', request_timeout=1000000)
        console.p('indices cleared')

    def store_urls(self, page: Page):
        """Store urls in elasticsearch.

        Args:
            page: the page with the urls
        """
        prepared = self.prepare_urls(page.urls)
        bulk(
            self.es,
            prepared,
            request_timeout=80
        )

    def prepare_urls(self, urls: list) -> list:
        prepared = []
        for url in urls:
            prepared.append({
                '_type': 'url',
                '_index': 'queue',
                '_id': hashlib.sha224(url.to_string().encode()).hexdigest(),
                '_source': {
                    'url': url.to_string()
                }
            })
        return prepared
