"""Photographer module."""

from __future__ import annotations
from saas.photographer.photo import PhotoPath, LoadingPhoto
from saas.storage.index import EmptySearchResultException
from saas.storage.datadir import DataDirectory
from saas.photographer.addons import Addons
import saas.storage.refresh as refresh
import saas.photographer.camera as c
import saas.utils.console as console
from saas.storage.index import Index
from typing import Type, Optional
import saas.threads as threads
from saas.web.url import Url
import random
import time


class Photographer:
    """Photographer class."""

    def __init__(
        self,
        index: Index,
        refresh_rate: Type[refresh.RefreshRate],
        datadir: DataDirectory,
        viewport_width: int=1920,
        viewport_height: int=0,
        viewport_max_height: Optional[int]=None
    ):
        """Create new photographer.

        Args:
            index: Index where crawled urls are stored and
                photos should be indexed.
            refresh_rate: How often photographs should be refreshed,
                more exactly defines which lock should be placed on
                crawled urls
            datadir: Data directory to store pictures in
            viewport_width: width of camera viewport
            viewport_height: height of camera viewport
            viewport_max_height: max height of camera viewport
        """
        self.index = index
        self.refresh_rate = refresh_rate
        self.datadir = datadir
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.viewport_max_height = viewport_max_height

    def tick(self):
        """Tick.

        Checkout a url from index, take photo of url,
        save to datadir and update index with photo
        metadata
        """
        try:
            timer = time.time()
            url = self._checkout_url()

            console.dp(f'taking photo of {url.to_string()}')

            path = PhotoPath(self.datadir)
            photo = LoadingPhoto(
                url=url,
                path=path,
                refresh_rate=self.refresh_rate
            )
            photo.save_loading_text()
            self.index.save_photo(photo)

            camera = c.Camera(
                viewport_width=self.viewport_width,
                viewport_height=self.viewport_height,
                viewport_max_height=self.viewport_max_height,
                addons={
                    'IDCAC': Addons.IDCAC,
                    'REFERER_HEADER': Addons.REFERER_HEADER,
                    'UBLOCK_ORIGIN': Addons.UBLOCK_ORIGIN,
                }
            )
            photo = camera.take_picture(url, path, self.refresh_rate)
            self.index.save_photo(photo)

            timer = int(time.time() - timer)
            console.p(
                f'photo was taken of {url.to_string()} took: {timer}s'
            )

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
        crawled_urls = self.index.crawled_urls_count(self.refresh_rate)
        processes = threads.Controller.PHOTOGRAPHER_PROCESSES
        if crawled_urls < processes and processes > 1:
            # to prevent checkout of same url when number of urls
            # to take photographs of are small
            time.sleep(round(random.uniform(10, 0), 2))

        url = self.index.recently_crawled_url(self.refresh_rate)  # type: Url
        self.index.lock_crawled_url(url, self.refresh_rate)
        return url
