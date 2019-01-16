"""Stats module."""

from saas.storage.index import Index
import psutil
import time
import os


def throughput(index: Index, timeframe: int) -> int:
    """Get current throughput.

    Args:
        index: Index photos are stored in
        timeframe: timeframe in minutes

    Returns:
        number of photos stored in index during timeframe
        int
    """
    return index.calculate_throughput(timeframe)


def cpu_usage(sample: int) -> float:
    """Calculate average cpu usage.

    Waits 1s between samples.

    Args:
        sample: number of times to measure

    Returns:
        average cpu usage
        float
    """
    samples = []
    while sample > 0:
        sample -= 1
        samples.append(psutil.cpu_percent())
        time.sleep(1)
    return round(sum(samples) / len(samples), 1)


def memory_usage(sample: int) -> float:
    """Calculate average memory usage.

    Waits 1s between samples.

    Args:
        sample: number of times to measure

    Returns:
        average memory usage
        float
    """
    samples = []
    while sample > 0:
        sample -= 1
        samples.append(psutil.virtual_memory().percent)
        time.sleep(1)
    return round(sum(samples) / len(samples), 1)


def load_avg(timeframe: int) -> float:
    """Load average.

    Args:
        timeframe: last 1min, 5mins or 15mins

    Returns:
        cpu load
        float

    Raises:
        ValueError: if timeframe is unsupported
    """
    if timeframe == 1:
        return round(os.getloadavg()[0], 2)

    if timeframe == 5:
        return round(os.getloadavg()[1], 2)

    if timeframe == 15:
        return round(os.getloadavg()[2], 2)

    raise ValueError(f'unsupported timeframe {timeframe}')
