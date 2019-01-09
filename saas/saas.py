"""saas entry point."""

import sys
import saas.utils.console as console


def main():
    """Entry point for saas."""
    try:
        console.p('run saas')
    except KeyboardInterrupt:
        console.pp('terminating.')
        sys.exit()


if __name__ == '__main__':
    main()
