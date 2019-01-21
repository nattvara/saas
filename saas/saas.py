"""saas entry point."""

from saas.storage.index import Index, EmptySearchResultException
from saas.photographer.javascript import JavascriptSnippets
from saas.storage.datadir import DataDirectory
import saas.storage.refresh as refresh
import saas.utils.console as console
import saas.utils.args as arguments
from saas.threads import Controller
import time
import sys


def main():
    """Entry point for saas."""
    try:

        parser = arguments.get_argument_parser()
        args = parser.parse_args(sys.argv[1:])

        console.DEBUG = args.debug

        JavascriptSnippets.load()

        index = Index(host=args.elasticsearch_host)

        if not index.ping():
            console.p('ERROR: failed to connect to elasticsearch')
            sys.exit()

        if not index.verify():
            if not args.setup_elasticsearch and not args.clear_elasticsearch:
                console.p('ERROR: elasticsearch is not configured')
                console.p('       {} {}'.format(
                    'start saas with --setup-elasticsearch',
                    'to configure elasticsearch'
                ))
                sys.exit()

        datadir = DataDirectory(args.data_dir, args.optimize_storage)

        refresh_rate = {
            'day': refresh.Daily,
            'hour': refresh.Hourly,
            'minute': refresh.EveryMinute,
        }[args.refresh_rate]

        if args.setup_elasticsearch:
            index.create_indices()

        if args.clear_elasticsearch:
            index.clear()
            index.create_indices()

        if args.clear_data_dir:
            datadir.clear()

        if not Controller.start_filesystem(
            mountpoint=args.mountpoint,
            datadir=datadir,
            refresh_rate=refresh_rate,
            elasticsearch_host=args.elasticsearch_host
        ):
            sys.exit()

        Controller.start_stats(
            elasticsearch_host=args.elasticsearch_host
        )

        Controller.start_crawlers(
            amount=args.crawler_threads,
            url_file=args.url_file,
            ignore_found_urls=args.ignore_found_urls,
            stay_at_domain=args.stay_at_domain,
            elasticsearch_host=args.elasticsearch_host,
            debug=args.debug
        )

        Controller.start_photographers(
            amount=args.photographer_threads,
            refresh_rate=refresh_rate,
            datadir=datadir,
            viewport_width=args.viewport_width,
            viewport_height=args.viewport_height,
            viewport_max_height=args.viewport_max_height,
            elasticsearch_host=args.elasticsearch_host,
            debug=args.debug
        )

        while True:

            if args.stop_if_idle == 0:
                time.sleep(10)
                continue

            try:
                crawled = index.timestamp_of_most_recent_document(
                    index.CRAWLED
                )
                photos = index.timestamp_of_most_recent_document(
                    index.PHOTOS
                )

                timestamp = photos
                if crawled > timestamp:
                    timestamp = crawled

                seconds = int(time.time()) - timestamp
                mins = int(seconds / 60)
                if mins >= args.stop_if_idle:
                    console.p(f'was idle for {mins} minutes', end='')
                    raise StopIfIdleTimeoutExpired

            except EmptySearchResultException:
                pass
            finally:
                time.sleep(2)

    except (KeyboardInterrupt, StopIfIdleTimeoutExpired):
        console.p(' terminating.')
        Controller.stop_all()
        console.p('')


class StopIfIdleTimeoutExpired(Exception):
    """Idle timeout expired."""

    pass


if __name__ == '__main__':
    main()
