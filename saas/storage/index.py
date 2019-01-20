"""Storage module."""

from __future__ import annotations
from saas.photographer.photo import Photo, PhotoPath, Screenshot
from elasticsearch.exceptions import RequestError
from saas.storage.datadir import DataDirectory
from saas.storage.refresh import RefreshRate
from urllib.error import HTTPError, URLError
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import saas.utils.console as console
from saas.web.url import Url, UrlId
import saas.mount.file as file
from typing import Type
import urllib.request
import random
import json
import time


class Index:
    """Index storage.

    Wrapper around elasticsearch api
    """

    UNCRAWLED = 'uncrawled'

    CRAWLED = 'crawled'

    PHOTOS = 'photos'

    def __init__(
        self,
        datadir: DataDirectory=None,
        es_client: Elasticsearch=None,
        host: str='localhost:9200'
    ):
        """Create new index.

        Args:
            datadir: Data directory (default: {None})
            es_client: Elasticsearch client,
                useful in testing (default: {None})
            host: elasticsearch host (default: {'localhost:9200'})
        """
        self.datadir = datadir
        self.host = host
        if es_client is not None:
            self.es = es_client
        else:
            self.es = Elasticsearch(
                [self.host],
                max_retries=2,
                retry_on_timeout=True
            )

    def ping(self) -> bool:
        """Ping elastic search server.

        Returns:
            returns True if elasticsearch responded, otherwise False
            bool
        """
        try:
            with urllib.request.urlopen(f'http://{self.host}') as response:
                response.read()
                return True
        except (HTTPError, URLError):
            pass
        return False

    def verify(self):
        """Verify elasticsearch is configured properly.

        Returns:
            True if configured correctly, otherwise False
            bool
        """
        url = f'http://{self.host}/_mapping'
        with urllib.request.urlopen(url) as response:
            mappings = json.loads(response.read())
            if Index.UNCRAWLED not in mappings:
                return False
            if Index.CRAWLED not in mappings:
                return False
            if Index.PHOTOS not in mappings:
                return False
        return True

    def clear(self):
        """Clear all documents."""
        console.p('clearing all indices')
        self.es.indices.delete(index='_all', request_timeout=1000000)
        console.p('indices cleared')

    def create_indices(self):
        """Create indices in elasticsearch."""
        console.p('creating indices')
        try:
            self.es.indices.create(Index.UNCRAWLED, body={
                'mappings': Mappings.uncrawled
            })
            self.es.indices.create(Index.CRAWLED, body={
                'mappings': Mappings.crawled
            })
            self.es.indices.create(Index.PHOTOS, body={
                'mappings': Mappings.photos,
                'settings': Settings.photos,
            })
            console.p('done.')
        except RequestError:
            console.p('indices already exist, skipping.')

    def calculate_throughput(self, timeframe: int) -> int:
        """Calculate throughput.

        Number of photos stored in index during timeframe

        Args:
            timeframe: timeframe in minutes

        Returns:
            number of photos stored in index during timeframe
            int
        """
        now = datetime.now()
        start = int((now - timedelta(minutes=timeframe)).timestamp())
        end = now.timestamp()

        res = self.es.search(index=Index.PHOTOS, size=0, body={
            'query': {
                'range': {
                    'timestamp': {
                        'gte': start,
                        'lte': end,
                    },
                }
            }
        })
        throughput = res['hits']['total']  # type: int
        return throughput

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
        prepared = self._prepare_urls(urls, Index.CRAWLED)
        bulk(self.es, prepared, request_timeout=80)

    def timestamp_of_most_recent_document(self, index: str) -> int:
        """Get timestamp of most recent document in given index.

        Args:
            index: the index the most recent document should be in

        Returns:
            Timestamp of most recent document in given index
            int

        Raises:
            EmptySearchResultException: if index is empty
        """
        res = self.es.search(index=index, size=1, body={
            'query': {
                'match_all': {}
            },
            'sort': [
                {
                    'timestamp': {
                        'order': 'desc'
                    }
                }
            ],
            '_source': ['timestamp']
        })

        if res['hits']['total'] == 0:
            raise EmptySearchResultException('index is empty')

        doc = res['hits']['hits'][0]  # type: dict
        timestamp = doc['_source']['timestamp']  # type: int
        return timestamp

    def add_uncrawled_urls(self, urls: list):
        """Add uncrawled urls.

        Args:
            urls: A list of urls that have NOT been crawled yet
        """
        urls = self.remove_already_crawled_urls(urls)
        prepared = self._prepare_urls(urls, Index.UNCRAWLED)
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
        res = self.es.search(index=Index.CRAWLED, body={
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

    def _prepare_urls(self, urls: list, index: str) -> list:
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
            if index == Index.CRAWLED:
                source = {
                    'url': url.to_string(),
                    'timestamp': int(time.time()),
                    'lock_value': '',
                    'lock_format': ''
                }
            else:
                source = {
                    'url': url.to_string(),
                    'timestamp': int(time.time()),
                }
            prepared.append({
                '_type': 'url',
                '_index': index,
                '_id': url.hash(),
                '_source': source
            })
        return prepared

    def random_uncrawled_url(self) -> Url:
        """Get random uncrawled url.

        Returns:
            An uncrawled url
            Url

        Raises:
            EmptySearchResultException: if index is empty
        """
        res = self.es.search(index=Index.UNCRAWLED, size=1, body={
            'query': {
                'function_score': {
                    'query': {
                        'bool': {
                            'must_not': {
                                'term': {
                                    'crawled': True
                                }
                            }
                        }
                    },
                    'random_score': {}
                }
            }
        })

        if res['hits']['total'] == 0:
            raise EmptySearchResultException('uncrawled index is empty')

        url = Url.from_string(res['hits']['hits'][0]['_source']['url'])
        return url

    def recently_crawled_url(self, refresh_rate=RefreshRate):
        """Get recently crawled url.

        Picks from the last 5 crawled to prevent two running
        photograpers to fetch the same one.

        Args:
            refresh_rate: the refresh reate to search for and
                use to avoid locked urls

        Returns:
            A url that has been crawled with status code 200
            Url

        Raises:
            EmptySearchResultException: if no url was found
        """
        res = self.es.search(index=Index.CRAWLED, size=5, body={
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

        hits = res['hits']['hits']

        return Url.from_string(random.choice(hits)['_source']['url'])

    def crawled_urls_count(self, refresh_rate=RefreshRate) -> int:
        """Crawled url count.

        Args:
            refresh_rate: the refresh reate to search for and
                use to avoid locked urls

        Returns:
            number of crawled urls with status code 200
            int
        """
        res = self.es.search(index=Index.CRAWLED, size=0, body={
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

        count = res['hits']['total']  # type: int
        return count

    def remove_uncrawled_url(self, id: str):
        """Remove url from uncrawled index.

        Args:
            id: Id of url to delete
        """
        self.es.delete(
            index=Index.UNCRAWLED,
            doc_type='url',
            id=id,
            ignore=404
        )

    def set_status_code_for_crawled_url(self, url: Url, status_code: int):
        """Set status code for a crawled url.

        Args:
            url: Url to set status code of
            status_code: the status code of the http request to the url
        """
        self.es.update(
            index=Index.CRAWLED,
            doc_type='url',
            id=url.hash(),
            retry_on_conflict=3,
            body={
                'doc': {
                    'status_code': status_code
                }
            }
        )

    def lock_crawled_url(self, url: Url, refresh_rate: Type[RefreshRate]):
        """Lock a crawld url.

        Place a lock on a crawled url for a given refresh rate.

        Args:
            url: Url to lock
            refresh_rate: Refresh rate to use (Hourly, Daily, etc.)
        """
        self.es.update(
            index=Index.CRAWLED,
            doc_type='url',
            id=url.hash(),
            retry_on_conflict=3,
            body={
                'doc': {
                    'lock_format': refresh_rate.lock_format(),
                    'lock_value': refresh_rate().lock(),
                }
            }
        )

    def save_photo(self, photo: Photo):
        """Save photo in index.

        Will not store the actual photo data, this should be stored
        in the data directory.

        Args:
            photo: Photo to store
        """
        self.es.index(
            index=Index.PHOTOS,
            doc_type='photo',
            id=photo.path.uuid,
            body={
                'url_id': photo.url.hash(),
                'refresh_rate': photo.refresh_rate.lock_format(),
                'captured_at': photo.refresh_rate().lock(),
                'filesize': photo.filesize(),
                'filename': photo.filename(),
                'directory': photo.directory(),
                'domain': photo.domain(),
                'timestamp': int(time.time())
            }
        )

    def photos_unique_domains(self, refresh_rate: Type[RefreshRate]) -> list:
        """Get unique domains that pictures have been taken of.

        Args:
            refresh_rate: Given refresh rate photo was taken with
        """
        res = self.es.search(index=Index.PHOTOS, size=0, body={
            'query': {
                'bool': {
                    'must': {
                        'term': {
                            'refresh_rate': refresh_rate.lock_format(),
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
        })
        unique = []
        for bucket in res['aggregations']['photos']['buckets']:
            unique.append(bucket['key'])
        return unique

    def photos_unique_captures_of_domain(
        self,
        domain: str,
        refresh_rate: Type[RefreshRate]
    ) -> list:
        """Get unique captures for a domain.

        Args:
            domain: The given domain to check
            refresh_rate: Given refresh rate photo was taken with
        """
        res = self.es.search(index=Index.PHOTOS, size=0, body={
            'query': {
                'bool': {
                    'must': [
                        {
                            'term': {
                                'domain': domain,
                            }
                        },
                        {
                            'term': {
                                'refresh_rate': refresh_rate.lock_format(),
                            }
                        },
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
        })
        unique = []
        for bucket in res['aggregations']['photos']['buckets']:
            unique.append(bucket['key'])
        return unique

    def photos_most_recent_capture_of_domain(
        self,
        domain: str,
        refresh_rate: Type[RefreshRate]
    ) -> str:
        """Get most recently captured_at value of domain.

        Args:
            domain: domain to check
            refresh_rate: Given refresh rate photo was taken with

        Returns:
            The most recent capture_at value in photos index
            str

        Raises:
            EmptySearchResultException: if no capture_at value was found
        """
        res = self.es.search(index=Index.PHOTOS, size=1, body={
            'query': {
                'bool': {
                    'must': [
                        {
                            'term': {
                                'domain': domain
                            }
                        },
                        {
                            'term': {
                                'refresh_rate': refresh_rate.lock_format()
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
            raise EmptySearchResultException(
                f'no capture for given refresh rate and {domain} was found'
            )

        doc = res['hits']['hits'][0]  # type: dict
        captured_at = doc['_source']['captured_at']  # type: str
        return captured_at

    def photos_get_photo(
        self,
        domain: str,
        captured_at: str,
        full_filename: str,
        refresh_rate: Type[RefreshRate]
    ) -> Photo:
        """Get photo from photos index.

        Args:
            domain: domain photo belongs to
            captured_at: when photo was captured
            full_filename: full filename of photo
                eg. /some/path/some-filename.png
            refresh_rate: Given refresh rate photo was taken with

        Returns:
            Requested photo metadata
            Photo

        Raises:
            PhotoNotFoundException: If photo was not found
        """
        directory = '/'.join(full_filename.split('/')[:-1])
        directory = directory.rstrip('/') + '/'
        filename = full_filename.split('/')[-1:][0]

        captured_at = file.LastCapture.translate(
            captured_at,
            domain,
            self,
            refresh_rate
        )

        res = self.es.search(index=Index.PHOTOS, size=1, body={
            'query': {
                'bool': {
                    'must': [
                        {
                            'term': {
                                'domain': domain
                            }
                        },
                        {
                            'term': {
                                'refresh_rate': refresh_rate.lock_format()
                            }
                        },
                        {
                            'term': {
                                'captured_at': captured_at
                            }
                        },
                        {
                            'term': {
                                'directory': directory
                            }
                        },
                        {
                            'term': {
                                'filename': filename
                            }
                        }
                    ]
                }
            },
        })

        if res['hits']['total'] == 0:
            raise PhotoNotFoundException('no photo was found')

        res = res['hits']['hits'][0]
        uuid = res['_id']

        if self.datadir is None:
            raise Exception('Cannot get photo from Index without a data dir')

        path = PhotoPath(self.datadir, uuid=uuid)

        photo = Screenshot(
            url=UrlId(res['_source']['url_id']),
            path=path,
            refresh_rate=refresh_rate,
            index_filesize=res['_source']['filesize']
        )

        return photo

    def photos_file_exists(
        self,
        domain: str,
        captured_at: str,
        full_filename: str,
        refresh_rate: Type[RefreshRate]
    ):
        """Check if photo exists in photos index.

        Args:
            domain: domain photo belongs to
            captured_at: when photo was captured
            full_filename: full filename of photo
                eg. /some/path/some-filename.png
            refresh_rate: Given refresh rate photo was taken with

        Returns:
            False if file was not found, if found it's filesize
            is returned
            bool or int
        """
        captured_at = file.LastCapture.translate(
            captured_at,
            domain,
            self,
            refresh_rate
        )
        try:
            photo = self.photos_get_photo(
                domain,
                captured_at,
                full_filename,
                refresh_rate
            )
            return photo.filesize()
        except PhotoNotFoundException:
            return False

    def photos_directory_exists(
        self,
        domain: str,
        captured_at: str,
        directory: str,
        refresh_rate: Type[RefreshRate]
    ) -> bool:
        """Check if directory exists in photos index.

        Args:
            domain: domain photo belongs to
            captured_at: when photo was captured
            directory: directory path eg. /some/path/to/dir/
            refresh_rate: Given refresh rate photo was taken with

        Returns:
            True if photo was found, else False
            bool
        """
        captured_at = file.LastCapture.translate(
            captured_at,
            domain,
            self,
            refresh_rate
        )
        res = self.es.search(index=Index.PHOTOS, size=0, body={
            'query': {
                'bool': {
                    'must': [
                        {
                            'term': {
                                'domain': domain,
                            }
                        },
                        {
                            'term': {
                                'refresh_rate': refresh_rate.lock_format(),
                            }
                        },
                        {
                            'term': {
                                'captured_at': captured_at,
                            }
                        },
                        {
                            'wildcard': {
                                'directory': directory + '*',
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
        })
        for bucket in res['aggregations']['photos']['buckets']:
            if directory in bucket['key']:
                return True
        return False

    def photos_list_files_in_directory(
        self,
        domain: str,
        captured_at: str,
        directory: str,
        refresh_rate: Type[RefreshRate]
    ) -> list:
        """List photos in a directory.

        Args:
            domain: domain photos should belong to
            captured_at: when photos should have been captured
            directory: directory files should be located in
            refresh_rate: Given refresh rate photo was taken with

        Returns:
            A list of files
            list
        """
        captured_at = file.LastCapture.translate(
            captured_at,
            domain,
            self,
            refresh_rate
        )
        res = self.es.search(index=Index.PHOTOS, size=10000, body={
            'query': {
                'bool': {
                    'must': [
                        {
                            'term': {
                                'domain': domain
                            }
                        },
                        {
                            'term': {
                                'refresh_rate': refresh_rate.lock_format()
                            }
                        },
                        {
                            'term': {
                                'captured_at': captured_at
                            }
                        },
                        {
                            'term': {
                                'directory': directory
                            }
                        }
                    ]
                }
            }
        })
        files = []
        for doc in res['hits']['hits']:
            if doc['_source']['filesize'] < 100:
                files.append(
                    doc['_source']['filename'] + file.Path.RENDERING_EXTENSION
                )
            else:
                files.append(doc['_source']['filename'])
        return files

    def photos_list_directories_in_directory(
        self,
        domain: str,
        captured_at: str,
        directory: str,
        refresh_rate: Type[RefreshRate]
    ) -> list:
        """List directories in a directory.

        Args:
            domain: domain directory should belong to
            captured_at: when directory should have been captured
            directory: directory should be located in
            refresh_rate: given refresh rate photo was taken with

        Returns:
            A list of directories
            list
        """
        captured_at = file.LastCapture.translate(
            captured_at,
            domain,
            self,
            refresh_rate
        )
        res = self.es.search(index=Index.PHOTOS, size=0, body={
            'query': {
                'bool': {
                    'must': [
                        {
                            'term': {
                                'domain': domain,
                            }
                        },
                        {
                            'term': {
                                'refresh_rate': refresh_rate.lock_format(),
                            }
                        },
                        {
                            'term': {
                                'captured_at': captured_at,
                            }
                        },
                        {
                            'wildcard': {
                                'directory': directory + '*',
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
        })
        directories = []  # type: list
        for bucket in res['aggregations']['photos']['buckets']:
            # trim the parent directories from the path,
            # and strip it's child directories
            path = bucket['key']
            path = path.replace(directory, '', 1)
            path = path.split('/')[0]
            if path not in directories and path != '':
                directories.append(path)
        return directories


class PhotoNotFoundException(Exception):
    """Photo was not found exception."""

    pass


class Mappings:
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

    photos = {
        'photo': {
            'properties': {
                'url_id': {
                    'type': 'text',
                },
                'refresh_rate': {
                    'type': 'text'
                },
                'captured_at': {
                    'type': 'text',
                    'fielddata': True
                },
                'filesize': {
                    'type': 'integer',
                },
                'filename': {
                    'type': 'text',
                    'analyzer': 'analyzer_filename',
                },
                'directory': {
                    'type': 'text',
                    'analyzer': 'analyzer_directory',
                    'fielddata': True
                },
                'domain': {
                    'type': 'text',
                    'analyzer': 'analyzer_domain',
                    'fielddata': True
                },
                'timestamp': {
                    'type': 'date',
                    'format': 'epoch_second',
                }
            }
        }
    }


class Settings:
    """Settings for elasticsearch indices."""

    photos = {
        'index': {
            'analysis': {
                'analyzer': {
                    'analyzer_domain': {
                        'tokenizer': 'whitespace',
                        'filter': 'lowercase'
                    },
                    'analyzer_directory': {
                        'tokenizer': 'path_hierarchy'
                    },
                    'analyzer_filename': {
                        'tokenizer': 'whitespace',
                        'filter': 'lowercase'
                    }
                }
            }
        }
    }


class EmptySearchResultException(Exception):
    """Empty search result."""

    pass
