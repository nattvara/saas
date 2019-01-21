"""Refresh rate module."""

from __future__ import annotations
from abc import ABCMeta, abstractmethod
import datetime


class RefreshRate(metaclass=ABCMeta):
    """Refresh class."""

    @staticmethod
    @abstractmethod
    def lock_format():
        """Get the human readable format of lock."""
        pass

    @abstractmethod
    def _lock_datetime_format(self):
        """Get the format of lock used to make lock."""
        pass

    def lock(self) -> str:
        """Make lock.

        Returns:
            Lock to store in index.
            str
        """
        return datetime.datetime.today().strftime(self._lock_datetime_format())


class Daily(RefreshRate):
    """Daily refresh.

    Refresh photographs every day.
    """

    @staticmethod
    def lock_format():
        """Get the human readable format of lock."""
        return 'daily'

    def _lock_datetime_format(self):
        """Get the format of lock used to make lock."""
        return '%Y%m%d'


class Hourly(RefreshRate):
    """Hourly refresh.

    Refresh photographs every hour.
    """

    @staticmethod
    def lock_format():
        """Get the human readable format of lock."""
        return 'hourly'

    def _lock_datetime_format(self):
        """Get the format of lock used to make lock."""
        return '%Y%m%d%H'


class EveryMinute(RefreshRate):
    """Refresh every minute.

    Refresh photographs every minute.
    """

    @staticmethod
    def lock_format():
        """Get the human readable format of lock."""
        return 'minute'

    def _lock_datetime_format(self):
        """Get the format of lock used to make lock."""
        return '%Y%m%d%H%M'
