"""saas entry point."""

from saas.photographer.javascript import JavascriptSnippets
from saas.storage.datadir import DataDirectory
import saas.storage.refresh as refresh
import saas.utils.console as console
from saas.storage.index import Index
import saas.utils.args as arguments
from saas.threads import Controller
import sys
import time


def main():
    """Entry point for saas."""
    try:

        parser = arguments.get_argument_parser()
        args = parser.parse_args(sys.argv[1:])

        JavascriptSnippets.load()

        index = Index(host=args.elasticsearch_host)
        datadir = DataDirectory(args.data_dir)

        if not index.ping():
            console.p('ERROR: failed to connect to elasticsearch')
            sys.exit()

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
            refresh_rate=refresh.Hourly,
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
            elasticsearch_host=args.elasticsearch_host
        )

        Controller.start_photographers(
            amount=args.photographer_threads,
            refresh_rate=refresh.Hourly,
            datadir=DataDirectory(args.data_dir),
            viewport_width=args.viewport_width,
            viewport_height=args.viewport_height,
            elasticsearch_host=args.elasticsearch_host
        )

        while True:
            time.sleep(10)

    except KeyboardInterrupt:
        console.p(' terminating.')
        Controller.stop_all()
        console.p('')


if __name__ == '__main__':
    main()
