"""Refresh rate module."""

from __future__ import annotations
from abc import ABCMeta, abstractmethod
import datetime


class RefreshRate(metaclass=ABCMeta):
    """Refresh class."""

    @abstractmethod
    def lock_format():
        """Get the human readable format of lock."""
        pass

    @abstractmethod
    def lock_datetime_format(self):
        """Get the format of lock used to make lock."""
        pass

    def lock(self) -> str:
        """Make lock.

        Returns:
            Lock to store in index.
            str
        """
        return datetime.datetime.today().strftime(self.lock_datetime_format())


class Hourly(RefreshRate):
    """Hourly refresh.

    Refresh photographs every hour.
    """

    def lock_format():
        """Get the human readable format of lock."""
        return 'hourly'

    def lock_datetime_format(self):
        """Get the format of lock used to make lock."""
        return '%Y-%m-%d @%H'
