"""saas entry point."""

import sys
import saas.utils.args as arguments
import saas.utils.console as console
from saas.crawler.crawler import Crawler


def main():
    """Entry point for saas."""
    try:

        parser = arguments.get_argument_parser()
        args = parser.parse_args(sys.argv[1:])

        crawler = Crawler(args.url_file)
        crawler.start()

    except KeyboardInterrupt:
        console.p('')
        console.p('terminating.')
        crawler.stop()
        sys.exit()


if __name__ == '__main__':
    main()
