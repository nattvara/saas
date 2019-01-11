"""Storage module."""

from __future__ import annotations
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from saas.storage.refresh import RefreshRate
import saas.utils.console as console
from saas.web.url import Url
import time


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

    def create_indices(self):
        """Create indices in elasticsearch."""
        console.p('creating indices')
        self.es.indices.create('uncrawled', body={
            'mappings': Mappings.uncrawled
        })
        self.es.indices.create('crawled', body={
            'mappings': Mappings.crawled
        })
        console.p('done.')

    def add_crawled_url(self, url: Url):
        """Add crawled url.

        Args:
            url: A url that have been crawled
        """
        self.add_crawled_urls([url])

    def add_crawled_urls(self, urls: list):
        """Add crawled urls.

        Args:
            urls: A list of urls that have been crawled
        """
        prepared = self.prepare_urls(urls, 'crawled')
        bulk(self.es, prepared, request_timeout=80)

    def add_uncrawled_urls(self, urls: Url):
        """Add uncrawled urls.

        Args:
            urls: A list of urls that have NOT been crawled yet
        """
        urls = self.remove_already_crawled_urls(urls)
        prepared = self.prepare_urls(urls, 'uncrawled')
        bulk(self.es, prepared, request_timeout=80)

    def remove_already_crawled_urls(self, urls: list) -> list:
        """Remove already crawled urls from a list of urls.

        Args:
            urls: A list of urls

        Returns:
            A cleaned list of uncrawled urls
            list
        """
        hashes = []
        for url in urls:
            hashes.append(url.hash())
        res = self.es.search(index='crawled', body={
            'query': {
                'bool': {
                    'filter': {
                        'terms': {
                            '_id': hashes
                        }
                    }
                }
            },
            'stored_fields': []
        })
        for doc in res['hits']['hits']:
            while doc['_id'] in hashes:
                hashes.remove(doc['_id'])
        out = []
        for url in urls:
            if url.hash() in hashes:
                out.append(url)
        return out

    def prepare_urls(self, urls: list, index: str) -> list:
        """Prepare urls for bulk add.

        Args:
            urls: list of Urls
            index: index to add urls to

        Returns:
            Prepared list of urls
            list
        """
        prepared = []
        for url in urls:
            prepared.append({
                '_type': 'url',
                '_index': index,
                '_id': url.hash(),
                '_source': {
                    'url': url.to_string(),
                    'timestamp': int(time.time()),
                }
            })
        return prepared

    def get_most_recent_uncrawled_url(self):
        """Get the most recently uncrawled url.

        Fetches the most recently added uncrawled url.

        Returns:
            Most recent url found like the following,
                {
                  "_index": "uncrawled",
                  "_type": "url",
                  "_id": "xxx...", sha256
                  "_score": null,
                  "_source": {
                    "url": "http://example.com",
                    "timestamp": 1547145709
                  },
                  "sort": [
                    1547145709
                  ]
                }
            dict or None
        """
        res = self.es.search(index='uncrawled', size=1, body={
            'query': {
                'match_all': {}
            },
            'sort': [
                {
                    'timestamp': {
                        'order': 'desc'
                    }
                }
            ]
        })

        if res['hits']['total'] == 0:
            return None

        return res['hits']['hits'][0]

    def most_recent_crawled_url(self, refresh_rate=RefreshRate):
        """Get most the url that was most recently crawled.

        Args:
            refresh_rate: the refresh reate to search for and
                use to avoid locked urls

        Returns:
            A url that has been crawled with status code 200
            Url

        Raises:
            EmptySearchResultException: if no url was found
        """
        res = self.es.search(index='crawled', size=1, body={
            'query': {
                'bool': {
                    'must': {
                        'term': {
                            'status_code': 200,
                        }
                    },
                    'must_not': [
                        {
                            'term': {
                                'lock_value': refresh_rate().lock(),
                            }
                        },
                        {
                            'term': {
                                'lock_format': refresh_rate.lock_format(),
                            }
                        }
                    ]
                }
            },
            'sort': [
                {
                    'timestamp': {
                        'order': 'desc'
                    }
                }
            ]
        })

        if res['hits']['total'] == 0:
            raise EmptySearchResultException('no crawled url was found')

        return Url.from_string(res['hits']['hits'][0]['_source']['url'])

    def remove_uncrawled_url(self, id: str):
        """Remove url from uncrawled index.

        Args:
            id: Id of url to delete
        """
        self.es.delete(index='uncrawled', doc_type='url', id=id, ignore=404)

    def set_status_code_for_crawled_url(self, url: Url, status_code: int):
        """Set status code for a crawled url.

        Args:
            url: Url to set status code of
            status_code: the status code of the http request to the url
        """
        self.es.update(index='crawled', doc_type='url', id=url.hash(), body={
            'doc': {
                'status_code': status_code
            }
        })

    def lock_crawled_url(self, url: Url, refresh_rate: RefreshRate):
        """Lock a crawld url.

        Place a lock on a crawled url for a given refresh rate.

        Args:
            url: Url to lock
            refresh_rate: Refresh rate to use (Hourly, Daily, etc.)
        """
        self.es.update(index='crawled', doc_type='url', id=url.hash(), body={
            'doc': {
                'lock_format': refresh_rate.lock_format(),
                'lock_value': refresh_rate().lock(),
            }
        })


class Mappings():
    """Mappings for elasticsearch indices."""

    uncrawled = {
        'url': {
            'properties': {
                'url': {
                    'type': 'text',
                    'fields': {
                        'keyword': {
                            'type': 'keyword',
                            'ignore_above': 256
                        }
                    }
                },
                'timestamp': {
                    'type': 'date',
                    'format': 'epoch_second',
                },
                'status_code': {
                    'type': 'short'
                }
            }
        }
    }

    crawled = {
        'url': {
            'properties': {
                'url': {
                    'type': 'text',
                    'fields': {
                        'keyword': {
                            'type': 'keyword',
                            'ignore_above': 256
                        }
                    }
                },
                'timestamp': {
                    'type': 'date',
                    'format': 'epoch_second',
                },
                'lock_format': {
                    'type': 'text'
                },
                'lock_value': {
                    'type': 'text'
                }
            }
        }
    }


class EmptySearchResultException(Exception):
    """Empty search result."""

    pass
