"""Addons module."""

from __future__ import annotations
import pkg_resources


class Addons:
    """Firefox addons."""

    REFERER_HEADER = pkg_resources.resource_filename(
        'extensions',
        'referer_header.xpi'
    )

    # https://github.com/gorhill/uBlock/releases
    UBLOCK_ORIGIN = pkg_resources.resource_filename(
        'extensions',
        'uBlock0_1.18.14.xpi'
    )

    # https://www.i-dont-care-about-cookies.eu/
    IDCAC = pkg_resources.resource_filename(
        'extensions',
        'idcac_2.9.8.xpi'
    )
