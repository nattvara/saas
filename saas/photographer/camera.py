"""Camera module."""

from __future__ import annotations
from saas.photographer.javascript import JavascriptSnippets
from saas.photographer.photo import PhotoPath, Screenshot
from saas.storage.refresh import RefreshRate
from selenium import webdriver
from saas.web.url import Url
import time
import os


class Camera:
    """Camera class."""

    def __init__(self):
        """Create new camera."""
        self.webdriver = None
        self.width = 0
        self.height = 0

    def take_picture(
        self, url: Url,
        path: PhotoPath,
        refresh_rate: RefreshRate
    ) -> Screenshot:
        """Take picture of url.

        Uses the selenium webdriver to load url in firefox,
        make sure the entire page and it's assets are loaded
        then write it to data directory as a png.

        Args:
            url: Url to take picture of
            path: Path to store url at
            refresh_rate: Refresh rate for photo

        Returns:
            A picture of the given url
            Screenshot
        """
        os.environ['MOZ_HEADLESS'] = '1'
        profile = self._create_webdriver_profile()
        self.webdriver = self._create_webdriver(profile, UserAgents.GOOGLEBOT)
        self._route(url)
        self._set_resolution(1920, 1080)
        self._start_images_monitor()

        # scroll down the page to trigger load of images
        steps = 2 * int(self._document_height() / self.height)
        for i in range(1, steps):
            self._scroll_y_axis((self.height / 2) * i)
            self._wait_for_images_to_load()

        # resize the viewport and make sure that it's scrolled
        # all the way to the top
        self._scroll_y_axis(0)
        self._set_resolution(1920, self._document_height())
        self._wait_for_images_to_load()
        self._scroll_y_axis(-500)
        self._wait_for_resize()

        self._save(path)
        self.webdriver.quit()

        return Screenshot(
            url=url,
            path=path,
            refresh_rate=refresh_rate
        )

    def _create_webdriver_profile(self) -> webdriver.FirefoxProfile:
        """Create webdriver profile.

        Returns:
            An empty profile Firefox Profile to use when
            creating webdriver.
            webdriver.FirefoxProfile
        """
        return webdriver.FirefoxProfile()

    def _create_webdriver(
        self,
        profile: webdriver.FirefoxProfile,
        user_agent: str
    ) -> webdriver.Firefox:
        """Create webdriver.

        Args:
            profile: FirefoxProfile with configuration options
            user_agent: User agent string to use

        Returns:
            A webdriver that can be used to interact with the firefox browser
            webdriver.Firefox
        """
        profile.set_preference('general.useragent.override', user_agent)
        profile.set_preference('dom.popup_maximum', 0)
        profile.set_preference('privacy.popups.showBrowserMessage', False)
        return webdriver.Firefox()

    def _route(self, url: Url):
        """Route camera to url.

        Args:
            url: A Url to route camera to
        """
        self.webdriver.get(url.to_string())

    def _save(self, path: PhotoPath):
        """Save screen shot.

        Args:
            path: PhotoPath object used to retrieve path in data directory
            to save png file in
        """
        self.webdriver.save_screenshot(path.full_path())

    def _set_resolution(self, width: int, height: int):
        """Set camera resolution.

        Args:
            width: Width in pixels
            height: Height in pixels
        """
        self.width = width
        self.height = height
        self.webdriver.set_window_size(width, height)

    def _document_height(self) -> int:
        """Get document height from webdriver.

        Returns:
            The height of the document at the page routed to
            int
        """
        return self.webdriver.execute_script(
            JavascriptSnippets.DOCUMENT_HEIGHT
        )

    def _image_count(self) -> int:
        """Get number of images on page.

        Returns:
            The number of images the webpage has requested
            int
        """
        return self.webdriver.execute_script(
            JavascriptSnippets.IMAGE_COUNT
        )

    def _script_count(self) -> int:
        """Get number of scripts page uses.

        Returns:
            The number of scripts the page has requested
            int
        """
        return self.webdriver.execute_script(
            JavascriptSnippets.SCRIPT_COUNT
        )

    def _stylesheet_count(self) -> int:
        """Get number of stylesheets page uses.

        Returns:
            The number of stylesheets the page has requested
            int
        """
        return self.webdriver.execute_script(
            JavascriptSnippets.STYLESHEET_COUNT
        )

    def _scroll_y_axis(self, pixels: int):
        """Scroll page on the y axis.

        Args:
            pixels: The number of pixels to scroll vertically
        """
        self.webdriver.execute_script(
            JavascriptSnippets.SCROLL_Y_AXIS.replace('Y_PIXELS', str(pixels))
        )

    def _start_images_monitor(self):
        """Start images monitor script on page."""
        self.webdriver.execute_script(
            JavascriptSnippets.IMAGES_MONITOR
        )

    def _wait_for_images_to_load(self):
        """Wait for all images to load on page."""
        while self.webdriver.execute_script(
            JavascriptSnippets.IMAGES_LOADED
        ) < Limits.ALL_IMAGES_LOADED:
            time.sleep(Limits.SLEEP_BETWEEN_IMAGE_LOAD_CHECK)

    def _wait_for_resize(self):
        """Wait for resoultion resize to be completed.

        When the camera resizes and the entire page is shown
        in the viewport all assets will be loaded. This takes
        longer time to complete for more complex pages.

        Some examples:

            Tabloids (generally filled with crap)
            https://www.dailymail.co.uk/        score: 321
            https://www.expressen.se/           score: 124
            https://aftonbladet.se/             score: 35

            Image heavy news sites
            https://dn.se/                      score: 39
            https://www.di.se/                  score: 44
            https://svd.se/                     score: 31

            Non image heavy news sites
            https://wsj.com/                    score: 12
            https://www.nytimes.com/            score: 10

            Blogs and non image + script heavy news sites
            https://www.ft.com/                 score: 3
            https://daringfireball.net/         score: 3
            https://www.recode.net/             score: 7
            https://www.schneier.com/           score: 2

            Zero or next to zero images
            https://news.ycombinator.com/       score: 0
            https://example.com/                score: 0

            * These are only examples and may change,
              captured at Sun Jan 13 00:37:26 CET 2019

        """
        images = self._image_count()
        scripts = self._script_count()
        stylesheets = self._stylesheet_count()
        height = self.height

        complexity = (images * 10) + (scripts / 5) + (stylesheets / 10)
        score = complexity * (height * 10)
        score = round(score / 8000000)  # arbitrary number

        if score > Limits.RESIZE_MAX_WAIT_TIME:
            score = Limits.RESIZE_MAX_WAIT_TIME

        # The score can generally be thought of as the number
        # of seconds to wait
        while score > 0:
            time.sleep(Limits.RESIZE_WAIT_TIME)
            score -= 1


class Limits:
    """Limits class.

    Various limits used in rendering page.
    """

    ALL_IMAGES_LOADED = 5

    SLEEP_BETWEEN_IMAGE_LOAD_CHECK = 1

    RESIZE_WAIT_TIME = 1

    RESIZE_MAX_WAIT_TIME = 25


class UserAgents:
    """User agents."""

    # masquerading as google bot can trick some website to not serve
    # tons of ads and load faster
    GOOGLEBOT = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'