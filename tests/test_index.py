"""Index test."""

from saas.photographer.photo import PhotoPath, LoadingPhoto
from saas.storage.datadir import DataDirectory
from saas.photographer.photo import Photo
import saas.storage.refresh as refresh
from saas.storage.index import Index
from unittest.mock import MagicMock
from saas.web.url import Url
from os.path import dirname
import unittest
import time


class TestIndex(unittest.TestCase):
    """Test index class."""

    def setUp(self):
        """Set up test."""
        self.datadir = DataDirectory(dirname(__file__) + '/datadir')
        self.index = Index(self.datadir, MagicMock())

    def tearDown(self):
        """Tear down test."""
        self.datadir.remove_data_dir()

    def search_returns_doc(self, doc: dict):
        """Search to elastic search returns doc.

        Mock search method of self.index.es to return given doc

        Args:
            doc: document or partial document to return
        """
        self.index.es.search = MagicMock(return_value={
            'hits': {
                'total': 1,
                'hits': [
                    doc
                ]
            }
        })

    def search_returns_aggregation(self, index: str, buckets: list):
        """Search to elastic search returns aggregation.

        Args:
            index: index being searched
            buckets: buckets that's returned
        """
        self.index.es.search = MagicMock(return_value={
            'aggregations': {
                index: {
                    'buckets': buckets
                }
            }
        })

    def test_recently_crawled_url_can_be_fetched(self):
        """Test recently crawled url can be fetched."""
        self.search_returns_doc({
            '_id': 'xxx...',
            '_source': {
                'url': 'http://example.com',
                'timestamp': 1547229873.257901
            }
        })

        url = self.index.recently_crawled_url(refresh.Hourly)
        self.assertIsInstance(cls=Url, obj=url)
        self.assertEqual('http://example.com', url.to_string())
        self.index.es.search.assert_called_with(
            index='crawled',
            size=5,
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
            retry_on_conflict=3,
            body={
                'doc': {
                    'lock_format': refresh.Hourly.lock_format(),
                    'lock_value': refresh.Hourly().lock(),
                }
            }
        )

    def test_index_can_store_photo(self):
        """Test index can store a photo."""
        self.index.es.index = MagicMock()
        time.time = MagicMock(return_value=time.time())

        url = Url.from_string('http://example.com')
        path = PhotoPath(self.datadir)
        path.filesize = MagicMock(return_value=10000)

        photo = LoadingPhoto(
            url=url,
            path=path,
            refresh_rate=refresh.Hourly
        )

        self.index.save_photo(photo)
        self.index.es.index.assert_called_with(
            index='photos',
            doc_type='photo',
            id=path.uuid,
            body={
                'url_id': url.hash(),
                'refresh_rate': refresh.Hourly.lock_format(),
                'captured_at': refresh.Hourly().lock(),
                'filesize': photo.filesize(),
                'filename': photo.filename(),
                'directory': photo.directory(),
                'domain': photo.domain(),
                'timestamp': int(time.time())
            }
        )

    def test_index_can_list_unique_photo_domains(self):
        """Test index can list unique photos."""
        self.search_returns_aggregation('photos', [
            {
                'key': 'example.com',
            },
            {
                'key': 'example.net',
            }
        ])

        domains = self.index.photos_unique_domains(refresh.Hourly)

        self.assertEqual(['example.com', 'example.net'], domains)
        self.index.es.search.assert_called_with(
            index='photos',
            size=0,
            body={
                'query': {
                    'bool': {
                        'must': {
                            'term': {
                                'refresh_rate': refresh.Hourly.lock_format(),
                            }
                        },
                    }
                },
                'aggs': {
                    'photos': {
                        'terms': {
                            'field': 'domain',
                            'size': 10000
                        }
                    }
                }
            }
        )

    def test_index_can_list_unique_captures_of_domains(self):
        """Test index can list unique captures of domain."""
        self.search_returns_aggregation('photos', [
            {
                'key': '2019-01-13H20:00',
            },
            {
                'key': '2019-01-13H21:00',
            }
        ])

        domains = self.index.photos_unique_captures_of_domain(
            'example.com',
            refresh.Hourly
        )

        format = refresh.Hourly.lock_format()
        self.assertEqual(['2019-01-13H20:00', '2019-01-13H21:00'], domains)
        self.index.es.search.assert_called_with(
            index='photos',
            size=0,
            body={
                'query': {
                    'bool': {
                        'must': [
                            {
                                'term': {
                                    'domain': 'example.com',
                                }
                            },
                            {
                                'term': {
                                    'refresh_rate': format,
                                }
                            }
                        ],
                    }
                },
                'aggs': {
                    'photos': {
                        'terms': {
                            'field': 'captured_at',
                            'size': 10000
                        }
                    }
                }
            }
        )

    def test_photo_can_be_retrieved(self):
        """Test photo can be retrieved."""
        format = refresh.Hourly.lock_format()
        capture = refresh.Hourly().lock()
        self.search_returns_doc({
            '_id': 'uuid-xxx...',
            '_source': {
                'url_id': 'xxx...',
                'refresh_rate': format,
                'captured_at': capture,
                'filename': 'some-filename.png',
                'directory': '/some/path/',
                'domain': 'example.com',
                'filesize': 12300,
                'timestamp': time.time(),
            }
        })

        photo = self.index.photos_get_photo(
            domain='example.com',
            captured_at=capture,
            full_filename='/some/path/some-filename.png',
            refresh_rate=refresh.Hourly
        )

        self.assertIsInstance(cls=Photo, obj=photo)
        self.assertEqual('uuid-xxx...', photo.path.uuid)
        self.index.es.search.assert_called_with(
            index='photos',
            size=1,
            body={
                'query': {
                    'bool': {
                        'must': [
                            {
                                'term': {
                                    'domain': 'example.com',
                                }
                            },
                            {
                                'term': {
                                    'refresh_rate': format,
                                }
                            },
                            {
                                'term': {
                                    'captured_at': capture,
                                }
                            },
                            {
                                'term': {
                                    'directory': '/some/path/',
                                }
                            },
                            {
                                'term': {
                                    'filename': 'some-filename.png',
                                }
                            }
                        ],
                    }
                }
            }
        )

    def test_directories_within_a_directory_can_be_fetched(self):
        """Test directories within a directory can be fetched."""
        format = refresh.Hourly.lock_format()
        capture = refresh.Hourly().lock()
        self.search_returns_aggregation('photos', [
            {
                'key': '/path/to/some/dir/',
            },
            {
                'key': '/path/to/some/other/dir/',
            },
            {
                'key': '/path/to/not/same/other/dir/',
            },
            {
                'key': '/path/to/a/dir/',
            }
        ])

        directories = self.index.photos_list_directories_in_directory(
            domain='example.com',
            captured_at=capture,
            directory='/path/to/',
            refresh_rate=refresh.Hourly
        )

        self.assertEqual(['some', 'not', 'a'], directories)
        self.index.es.search.assert_called_with(
            index='photos',
            size=0,
            body={
                'query': {
                    'bool': {
                        'must': [
                            {
                                'term': {
                                    'domain': 'example.com',
                                }
                            },
                            {
                                'term': {
                                    'refresh_rate': format,
                                }
                            },
                            {
                                'term': {
                                    'captured_at': capture,
                                }
                            },
                            {
                                'wildcard': {
                                    'directory': '/path/to/*',
                                }
                            }
                        ],
                    }
                },
                'aggs': {
                    'photos': {
                        'terms': {
                            'field': 'directory',
                            'size': 10000
                        }
                    }
                }
            }
        )


if __name__ == '__main__':
    unittest.main()
