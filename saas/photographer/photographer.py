"""Photographer module."""

from __future__ import annotations
from saas.photographer.photo import PhotoPath, LoadingPhoto
from saas.storage.index import EmptySearchResultException
from saas.storage.datadir import DataDirectory
from saas.photographer.camera import Camera
import saas.storage.refresh as refresh
import saas.utils.console as console
from saas.storage.index import Index
from saas.web.url import Url
import time


class Photographer:
    """Photographer class."""

    def __init__(
        self,
        index: Index,
        refresh_rate: refresh.RefreshRate,
        datadir: DataDirectory
    ):
        """Create new photographer.

        Args:
            index: Index where crawled urls are stored and
                photos should be indexed.
            refresh_rate: How often photographs should be refreshed,
                more exactly defines which lock should be placed on
                crawled urls
            datadir: Data directory to store pictures in
        """
        self.index = index
        self.refresh_rate = refresh_rate
        self.datadir = datadir

    def start(self):
        """Start photographer."""
        while True:
            console.p('.', end='')
            try:
                url = self._checkout_url()
                console.pp(url.to_string())

                path = PhotoPath(self.datadir)
                photo = LoadingPhoto(
                    url=url,
                    path=path,
                    refresh_rate=refresh.Hourly
                )
                photo.save_loading_text()
                self.index.save_photo(photo)

                self.index.save_photo(photo)
                camera = Camera()
                photo = camera.take_picture(url, path, refresh.Hourly)
                self.index.save_photo(photo)

            except EmptySearchResultException as e:
                pass
            finally:
                time.sleep(1)

    def _checkout_url(self) -> Url:
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
