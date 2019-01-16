"""Threads module."""

from __future__ import annotations
from saas.storage.datadir import DataDirectory
import saas.photographer.photographer as p
import saas.mount.filesystem as Filesystem
from saas.crawler.crawler import Crawler
from saas.utils.files import real_path
import saas.storage.refresh as refresh
import saas.utils.console as console
from saas.storage.index import Index
from threading import Thread
import signal
import time
import uuid
import os


class Controller:
    """Thread Controller class."""

    SHOULD_RUN = True

    PHOTOGRAPHER_PROCESSES = 0

    FUSE_PID = None

    threads = {}

    webdrivers = []

    def start_crawlers(
        amount: int,
        url_file: str,
        ignore_found_urls: bool
    ):
        """Start crawler threads.

        Args:
            amount: amount of crawlers to start
            url_file: path to urls file
            ignore_found_urls: if crawler should ignore new urls found on
                pages it crawls
        """
        console.p(f'starting {amount} crawler threads')
        while amount > 0:
            thread_id = str(uuid.uuid4())
            thread = Thread(target=_crawler_thread, args=(
                url_file,
                ignore_found_urls,
                thread_id
            ))
            thread.start()
            Controller.threads[thread_id] = {
                'running': True
            }
            amount -= 1

    def start_photographers(
        amount: int,
        refresh_rate: refresh.RefreshRate,
        datadir: DataDirectory
    ):
        """Start photographer threads.

        Args:
            amount: amount of crawlers to start
            refresh_rate: How often photographs should be refreshed,
                more exactly defines which lock should be placed on
                crawled urls
            datadir: Data directory to store pictures in
        """
        console.p(f'starting {amount} photographer threads')
        Controller.PHOTOGRAPHER_PROCESSES = amount
        while amount > 0:
            thread_id = str(uuid.uuid4())
            thread = Thread(target=_photographer_thread, args=(
                refresh_rate,
                datadir,
                thread_id
            ))
            thread.start()
            Controller.threads[thread_id] = {
                'running': True
            }
            amount -= 1

    def start_filesystem(
        mountpoint: str,
        datadir: DataDirectory,
        refresh_rate: refresh.RefreshRate
    ):
        """Start filesystem process.

        FUSE python library will kill the main process,
        forking main process and mounts the filesystem
        from that process instead.

        Args:
            mountpoint: where to mount filesystem
            datadir: Data directory to store pictures in
            refresh_rate: Which refresh rate filesystem should use
                for fetching photos

        Returns:
            True if main process, False if the forked process
            bool
        """
        console.p(f'mounting filesystem at: {real_path(mountpoint)}')

        pid = os.fork()
        if pid != 0:
            Controller.FUSE_PID = pid
            return True

        try:
            Filesystem.mount(mountpoint, Index(datadir), refresh_rate)
        except RuntimeError as e:
            console.p(f'failed to mount FUSE filesystem: {e}')

        return False

    def stop_all():
        """Stop all threads."""
        try:
            Controller.SHOULD_RUN = False

            i = 0
            while not Controller._any_thread_is_running():
                if i % 10 == 0:
                    console.p('waiting for saas to stop')
                i += 1
                time.sleep(0.5)

            console.p('cleaning up')
            try:
                for pid in Controller.webdrivers:
                    os.kill(pid, signal.SIGTERM)

                if Controller.FUSE_PID:
                    os.kill(Controller.FUSE_PID, signal.SIGTERM)
            except ProcessLookupError:
                pass
        except KeyboardInterrupt:
            Controller.stop_all()

    def _any_thread_is_running() -> bool:
        """Check if any thread is running.

        Returns:
            True if one or more thread is running, otherwise False
            bool
        """
        for thread_id in Controller.threads:
            if Controller.threads[thread_id]['running']:
                return False
        return True


def _crawler_thread(
    url_file: str,
    ignore_found_urls: bool,
    thread_id: str
):
    """Crawler thread.

    Args:
        url_file: path to url file
        ignore_found_urls: if crawler should ignore new urls found on
            pages it crawls
        thread_id: id of thread
    """
    try:
        crawler = Crawler(
            url_file=url_file,
            index=Index(),
            ignore_found_urls=ignore_found_urls,
        )
        while Controller.SHOULD_RUN:
            crawler.tick()
    except Exception as e:
        console.p(f'error occured in crawler thread {thread_id}: {e}')
    finally:
        Controller.threads[thread_id]['running'] = False


def _photographer_thread(
    refresh_rate: refresh.RefreshRate,
    datadir: DataDirectory,
    thread_id: str
):
    """Photographer thread.

    Args:
        refresh_rate: How often photographs should be refreshed
        datadir: Data directory to store pictures in
        thread_id: id of thread
    """
    try:
        photographer = p.Photographer(
            Index(),
            refresh_rate,
            datadir
        )
        while Controller.SHOULD_RUN:
            photographer.tick()
    except Exception as e:
        console.p(f'error occured in photographer thread {thread_id}: {e}')
    finally:
        Controller.threads[thread_id]['running'] = False
