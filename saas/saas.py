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

        index = Index()
        datadir = DataDirectory(args.data_dir)

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
            refresh_rate=refresh.Hourly
        ):
            sys.exit()

        Controller.start_stats()

        Controller.start_crawlers(
            amount=args.crawler_threads,
            url_file=args.url_file,
            ignore_found_urls=args.ignore_found_urls,
            stay_at_domain=args.stay_at_domain,
        )

        Controller.start_photographers(
            amount=args.photographer_threads,
            refresh_rate=refresh.Hourly,
            datadir=DataDirectory(args.data_dir)
        )

        while True:
            time.sleep(10)

    except KeyboardInterrupt:
        console.p(' terminating.')
        Controller.stop_all()
        console.p('')


if __name__ == '__main__':
    main()
