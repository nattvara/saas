"""Threads module."""

from __future__ import annotations
from saas.crawler.crawler import Crawler, UrlFileNotFoundError
from saas.storage.datadir import DataDirectory
import saas.photographer.photographer as p
import saas.mount.filesystem as Filesystem
from saas.utils.files import real_path
import saas.storage.refresh as refresh
import saas.utils.console as console
from saas.storage.index import Index
from typing import Type, Optional
import saas.utils.stats as stats
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

    threads = {}  # type: dict

    webdrivers = []  # type: list

    @staticmethod
    def start_crawlers(
        amount: int,
        url_file: str,
        ignore_found_urls: bool,
        stay_at_domain: bool,
        elasticsearch_host: str,
        debug: bool
    ):
        """Start crawler threads.

        Args:
            amount: amount of crawlers to start
            url_file: path to urls file
            ignore_found_urls: if crawler should ignore new urls found on
                pages it crawls
            stay_at_domain: if crawler should ignore urls from a different
                domain than the one it was found at
            elasticsearch_host: elasticsearch host
            debug: Display debugging information
        """
        console.p(f'starting {amount} crawler threads')
        while amount > 0:
            thread_id = str(uuid.uuid4())
            thread = Thread(target=_crawler_thread, args=(
                url_file,
                ignore_found_urls,
                stay_at_domain,
                elasticsearch_host,
                debug,
                thread_id
            ))
            thread.start()
            Controller.threads[thread_id] = {
                'running': True
            }
            amount -= 1

    @staticmethod
    def start_stats(elasticsearch_host: str):
        """Start stats thread.

        Args:
            elasticsearch_host: elasticsearch host
        """
        thread = Thread(target=_stats_thread, args=(elasticsearch_host,))
        thread.start()

    @staticmethod
    def start_photographers(
        amount: int,
        refresh_rate: Type[refresh.RefreshRate],
        datadir: DataDirectory,
        viewport_width: int,
        viewport_height: int,
        viewport_max_height: Optional[int],
        elasticsearch_host: str,
        debug: bool
    ):
        """Start photographer threads.

        Args:
            amount: amount of crawlers to start
            refresh_rate: How often photographs should be refreshed,
                more exactly defines which lock should be placed on
                crawled urls
            datadir: Data directory to store pictures in
            viewport_width: width of camera viewport
            viewport_height: height of camera viewport
            viewport_max_height: max height of camera viewport
            elasticsearch_host: elasticsearch host
            debug: Display debugging information
        """
        console.p(f'starting {amount} photographer threads')
        Controller.PHOTOGRAPHER_PROCESSES = amount
        while amount > 0:
            thread_id = str(uuid.uuid4())
            thread = Thread(target=_photographer_thread, args=(
                refresh_rate,
                datadir,
                viewport_width,
                viewport_height,
                viewport_max_height,
                elasticsearch_host,
                debug,
                thread_id
            ))
            thread.start()
            Controller.threads[thread_id] = {
                'running': True
            }
            amount -= 1

    @staticmethod
    def start_filesystem(
        mountpoint: str,
        datadir: DataDirectory,
        refresh_rate: Type[refresh.RefreshRate],
        elasticsearch_host: str
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
            elasticsearch_host: elasticsearch host

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
            Filesystem.mount(
                mountpoint,
                Index(datadir, host=elasticsearch_host),
                refresh_rate
            )
        except RuntimeError as e:
            console.p(f'failed to mount FUSE filesystem: {e}')

        return False

    @staticmethod
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

    @staticmethod
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
    stay_at_domain: bool,
    elasticsearch_host: str,
    debug: bool,
    thread_id: str
):
    """Crawler thread.

    Args:
        url_file: path to url file
        ignore_found_urls: if crawler should ignore new urls found on
            pages it crawls
        stay_at_domain: if crawler should ignore urls from a different
            domain than the one it was found at
        elasticsearch_host: elasticsearch host
        debug: Display debugging information
        thread_id: id of thread
    """
    try:
        crawler = Crawler(
            url_file=url_file,
            index=Index(host=elasticsearch_host),
            ignore_found_urls=ignore_found_urls,
            stay_at_domain=stay_at_domain,
        )
        while Controller.SHOULD_RUN:
            crawler.tick()
    except UrlFileNotFoundError:
        console.p(f'ERROR: url_file was not found at \'{url_file}\'')
        time.sleep(2)
        Controller.threads[thread_id]['running'] = False
        Controller.stop_all()
    except Exception as e:
        console.p(f'error occured in crawler thread {thread_id}: {e}')
        if debug:
            raise e
    finally:
        Controller.threads[thread_id]['running'] = False


def _stats_thread(elasticsearch_host: str):
    """Stats thread.

    Prints system and saas statistics every 5th minute

    Args:
        elasticsearch_host: elasticsearch host
    """
    start = time.time()
    last_print = 1
    while Controller.SHOULD_RUN:

        time.sleep(1)
        mins = int(int(time.time() - start) / 60)
        if mins % 5 != 0 or mins <= last_print:
            continue

        index = Index(host=elasticsearch_host)
        last_print = mins

        t = '[throughput]           5m: {}, 15m: {}, 30min: {}, 1h: {}'.format(
            stats.throughput(index, 5),
            stats.throughput(index, 15),
            stats.throughput(index, 30),
            stats.throughput(index, 60),
        )
        ta = '{}  5m: {}, 15m: {}, 30min: {}, 1h: {}'.format(
            '[throughput 1min avg]',
            round(stats.throughput(index, 5) / 5, 2) if mins > 4 else 'n/a',
            round(stats.throughput(index, 15) / 15, 2) if mins > 14 else 'n/a',
            round(stats.throughput(index, 30) / 30, 2) if mins > 29 else 'n/a',
            round(stats.throughput(index, 60) / 60, 2) if mins > 59 else 'n/a',
        )
        load = '[load avg]             1m: {}, 5m: {}, 15min: {}'.format(
            stats.load_avg(1),
            stats.load_avg(5),
            stats.load_avg(15),
        )
        cpu = f'[current cpu usage]    {stats.cpu_usage(10)}%'
        mem = f'[memory usage]         {stats.memory_usage(10)}%'

        for msg in [t, ta, load, cpu, mem]:
            console.p(msg)


def _photographer_thread(
    refresh_rate: Type[refresh.RefreshRate],
    datadir: DataDirectory,
    viewport_width: int,
    viewport_height: int,
    viewport_max_height: Optional[int],
    elasticsearch_host: str,
    debug: bool,
    thread_id: str
):
    """Photographer thread.

    Args:
        refresh_rate: How often photographs should be refreshed
        datadir: Data directory to store pictures in
        viewport_width: width of camera viewport
        viewport_height: height of camera viewport
        viewport_max_height: max height of camera viewport
        elasticsearch_host: elasticsearch host
        debug: Display debugging information
        thread_id: id of thread
    """
    try:
        photographer = p.Photographer(
            Index(host=elasticsearch_host),
            refresh_rate,
            datadir,
            viewport_width,
            viewport_height,
            viewport_max_height
        )
        while Controller.SHOULD_RUN:
            photographer.tick()
    except Exception as e:
        console.p(f'error occured in photographer thread {thread_id}: {e}')
        if debug:
            raise e
    finally:
        Controller.threads[thread_id]['running'] = False
