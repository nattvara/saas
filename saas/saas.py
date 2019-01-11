"""saas entry point."""

from saas.photographer.photographer import Photographer
from saas.crawler.crawler import Crawler
import saas.storage.refresh as refresh
import saas.utils.console as console
from saas.storage.index import Index
import saas.utils.args as arguments
import sys


def main():
    """Entry point for saas."""
    try:

        parser = arguments.get_argument_parser()
        args = parser.parse_args(sys.argv[1:])

        crawler = Crawler(
            url_file=args.url_file,
            index=Index(),
            clear_elasticsearch=args.clear_elasticsearch
        )

        photographer = Photographer(
            index=Index(),
            refresh_rate=refresh.Hourly
        )

        if args.component == 'crawler':
            crawler.start()

        if args.component == 'photographer':
            photographer.start()

    except KeyboardInterrupt:
        console.p('')
        console.p('terminating.')
        crawler.stop()
        sys.exit()


if __name__ == '__main__':
    main()
