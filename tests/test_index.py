"""Index test."""

import saas.storage.refresh as refresh
from saas.storage.index import Index
from unittest.mock import MagicMock
from saas.web.url import Url
import unittest


class TestIndex(unittest.TestCase):
    """Test index class."""

    def setUp(self):
        """Set up test."""
        self.index = Index()

    def search_returns_doc(self, doc: dict):
        """Search to elastic search returns doc.

        Args:
            doc: document or partial document to return

        Mock search method of self.index.es to return given doc
        """
        self.index.es.search = MagicMock(return_value={
            'hits': {
                'total': 1,
                'hits': [
                    doc
                ]
            }
        })

    def test_most_recent_crawled_url_can_be_fetched(self):
        """Test most recent crawled url can be fetched."""
        self.search_returns_doc({
            '_id': 'xxx...',
            '_source': {
                'url': 'http://example.com',
                'timestamp': 1547229873.257901
            }
        })

        url = self.index.most_recent_crawled_url(refresh.Hourly)
        self.assertIsInstance(cls=Url, obj=url)
        self.assertEqual('http://example.com', url.to_string())
        self.index.es.search.assert_called_with(
            index='crawled',
            size=1,
            body={
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
                                    'lock_value': refresh.Hourly().lock(),
                                }
                            },
                            {'term': {
                                'lock_format': refresh.Hourly.lock_format(),
                            }}
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
            }
        )

    def test_lock_can_be_placed_on_crawled_url(self):
        """Test lock can be placed on crawled url."""
        url = Url.from_string('http://example.com')
        self.index.es.update = MagicMock()

        self.index.lock_crawled_url(url, refresh.Hourly)
        self.index.es.update.assert_called_with(
            index='crawled',
            doc_type='url',
            id=url.hash(),
            body={
                'doc': {
                    'lock_format': refresh.Hourly.lock_format(),
                    'lock_value': refresh.Hourly().lock(),
                }
            }
        )


if __name__ == '__main__':
    unittest.main()
