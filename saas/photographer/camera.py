"""Camera module."""

from __future__ import annotations
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from urllib3.exceptions import ProtocolError, MaxRetryError
from saas.photographer.javascript import JavascriptSnippets
from selenium.common.exceptions import JavascriptException
from saas.photographer.photo import PhotoPath, Screenshot
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options
from saas.storage.refresh import RefreshRate
from http.client import RemoteDisconnected
import saas.utils.console as console
from typing import Type, Optional
from selenium import webdriver
import saas.threads as threads
from saas.web.url import Url
import time


class Camera:
    """Camera class."""

    def __init__(
        self,
        viewport_width: int=1920,
        viewport_height: int=0,
        viewport_max_height: Optional[int]=None,
        addons: dict={},
        dpi: float=1.0,
        user_agent: str=None,
        profile: str=None,
        headless: bool=True
    ):
        """Create new camera.

        Args:
            viewport_width: width of camera viewport (default: {1920})
            viewport_height: height of camera viewport, if set to 0 camera
                will try to take a full height high quality screenshot,
                which is way slower than fixed size (default: {0})
            viewport_max_height: max height of camera viewport if
                viewport_height is not default value this will be ignored
            addons: optional dictionary with paths to firefox
                addons (default: {{}})
            dpi: Modifies firefox's layout.css.devPixelsPerPx setting
                (default: 1.0)
            user_agent: User agent string to use for requests
            profile: Optional path to existing firefox profile eg.
                ~/Library/Application Support/Firefox/profiles/xxxx.default
            headless: If camera should start firefox in headless mode or not,
                note captures larger than display is not possible if not in
                headless mode
        """
        self.webdriver = None  # type: webdriver.FirefoxProfile
        self.width = 0
        self.height = 0
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.viewport_max_height = viewport_max_height
        self.addons = addons
        self.dpi = dpi
        self.profile = profile
        if user_agent is None:
            user_agent = UserAgents.DEFAULT
        self.user_agent = user_agent
        self.headless = headless

    def take_picture(
        self,
        url: Url,
        path: PhotoPath,
        refresh_rate: Type[RefreshRate],
        retry: int=5
    ) -> Screenshot:
        """Take picture of url.

        Uses the selenium webdriver to load url in firefox,
        make sure the entire page and it's assets are loaded
        then write it to data directory as a png.

        Args:
            url: Url to take picture of
            path: Path to store url at
            refresh_rate: Refresh rate for photo
            retry: Number of times to retry if a timeout exception is
                thrown (default: 5)

        Returns:
            A picture of the given url
            Screenshot
        """
        try:
            console.dca('launching firefox, camera: {}x{} [{}]'.format(
                self.viewport_width,
                self.viewport_height if self.viewport_height != 0 else 'full',
                self.dpi
            ))

            profile = self._create_webdriver_profile()
            self.webdriver = self._create_webdriver(profile)
            self._install_webdriver_addons(self.addons)

            threads.Controller.webdrivers.append(
                self.webdriver.service.process.pid
            )

            console.dca(f'routing camera to {url.to_string()}')

            try:
                self._route_to_blank()
                self._route(url)
                self._route(url)
                self._route(url)
            except TimeoutException as e:
                retry = retry - 1
                if retry < 0:
                    raise e
                console.dca('routing reached timeout, retrying')
                self.webdriver.quit()
                return self.take_picture(url, path, refresh_rate, retry)

            if self.viewport_height != 0:
                # fixed height
                console.dca('taking fixed screenshot')
                self._set_resolution(self.viewport_width, self.viewport_height)
                self._start_images_monitor()
                self._wait_for_images_to_load()
            else:
                # fullpage screenshot
                console.dca('taking fullpage screenshot')
                self._set_resolution(self.viewport_width, 1080)
                self._start_images_monitor()
                self._wait_for_images_to_load()

                # scroll down the page to trigger load of images
                console.dca('making sure all images have loaded')
                steps = int(self._document_height() / 800)
                for i in range(1, steps):
                    scroll_to = i * 800
                    self._scroll_y_axis(scroll_to)
                    self._wait_for_images_to_load()
                    time.sleep(0.5)

                # resize the viewport and make sure that it's scrolled
                # all the way to the top
                console.dca(f'resizing camera viewport for {url.to_string()}')
                self._scroll_y_axis(self._document_height() * -1)
                if self.viewport_max_height is None:
                    height = self._document_height()
                elif self._document_height() > self.viewport_max_height:
                    height = self.viewport_max_height
                else:
                    height = self._document_height()
                self._wait_for_images_to_load()
                self._set_resolution(self.viewport_width, height)
                self._wait_for_images_to_load()
                self._scroll_y_axis(-height)
                self._wait_for_resize()

            console.dca(f'saving screenshot of {url.to_string()}')
            self._save(path)
        except RemoteDisconnected:
            pass
        except ProtocolError:
            pass
        except MaxRetryError:
            pass
        finally:
            if self.webdriver:
                self.webdriver.quit()

        if path.should_optimize():
            console.dca(f'optimizing screenshot of {url.to_string()}')
            timer = time.time()
            path.optimize()
            seconds = int(time.time() - timer)
            console.dca(f'optimizing of {url.to_string()} took {seconds}s')

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
        if self.profile:
            return webdriver.FirefoxProfile(self.profile)
        return webdriver.FirefoxProfile()

    def _create_webdriver(
        self,
        profile: webdriver.FirefoxProfile
    ) -> webdriver.Firefox:
        """Create webdriver.

        Args:
            profile: FirefoxProfile with configuration options
            user_agent: User agent string to use

        Returns:
            A webdriver that can be used to interact with the firefox browser
            webdriver.Firefox
        """
        if self.user_agent != UserAgents.DEFAULT:
            profile.set_preference(
                'general.useragent.override',
                self.user_agent
            )
        profile.set_preference('dom.popup_maximum', 0)
        profile.set_preference('layout.css.devPixelsPerPx', str(self.dpi))
        profile.set_preference('privacy.popups.showBrowserMessage', False)
        profile.set_preference('dom.push.enabled', False)

        options = Options()
        options.headless = self.headless

        driver = webdriver.Firefox(
            firefox_profile=profile,
            options=options,
            firefox_binary=FirefoxBinary()
        )
        return driver

    def _install_webdriver_addons(self, addons: dict={}):
        """Install webdriver addons.

        The extensions that are installed either improve rendering
        performance. Or let firefox bypass paywalls or cookie/GDPR
        concent forms.

        Args:
            addons: optional dictionary with paths to addons (default: {{}})
        """
        if 'REFERER_HEADER' in addons:
            self.webdriver.install_addon(
                addons['REFERER_HEADER'], temporary=True
            )

        if 'IDCAC' in addons:
            self.webdriver.install_addon(addons['IDCAC'])

        if 'UBLOCK_ORIGIN' in addons:
            self.webdriver.install_addon(
                addons['UBLOCK_ORIGIN'], temporary=True
            )

    def _route(self, url: Url):
        """Route camera to url.

        Args:
            url: A Url to route camera to
        """
        self.webdriver.set_page_load_timeout(10)
        self.webdriver.get(url.to_string())

    def _route_to_blank(self):
        """Route to blank page."""
        self.webdriver.get('about:blank')

    def _save(self, path: PhotoPath):
        """Save screen shot.

        Args:
            path: PhotoPath object used to retrieve path in data directory
            to save png file in
        """
        height = self.webdriver.get_window_size()['height']
        width = self.webdriver.get_window_size()['width']
        console.dca(f'saving png with viewport resolution [{width}x{height}]')
        console.dca('png output resolution [{}x{}]'.format(
            int(width * self.dpi),
            int(height * self.dpi)
        ))
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

    def _execute_script(self, script: str, retry: int=40):
        """Execute script in browser.

        Args:
            script: javascript to execute
            retry: number of times script can fail and retry

        Returns:
            Result of script
        """
        try:
            return self.webdriver.execute_script(script)
        except JavascriptException as e:
            if retry < 1:
                raise e
            time.sleep(0.75)
            return self._execute_script(script, retry - 1)

    def _document_height(self) -> int:
        """Get document height from webdriver.

        Returns:
            The height of the document at the page routed to
            int
        """
        height = self._execute_script(
            JavascriptSnippets.DOCUMENT_HEIGHT
        )  # type: int
        return height

    def _image_count(self) -> int:
        """Get number of images on page.

        Returns:
            The number of images the webpage has requested
            int
        """
        images = self._execute_script(
            JavascriptSnippets.IMAGE_COUNT
        )  # type: int
        return images

    def _script_count(self) -> int:
        """Get number of scripts page uses.

        Returns:
            The number of scripts the page has requested
            int
        """
        scripts = self._execute_script(
            JavascriptSnippets.SCRIPT_COUNT
        )  # type: int
        return scripts

    def _stylesheet_count(self) -> int:
        """Get number of stylesheets page uses.

        Returns:
            The number of stylesheets the page has requested
            int
        """
        stylesheets = self._execute_script(
            JavascriptSnippets.STYLESHEET_COUNT
        )  # type: int
        return stylesheets

    def _scroll_y_axis(self, pixels: int):
        """Scroll page on the y axis.

        Args:
            pixels: The number of pixels to scroll vertically
        """
        self._execute_script(
            JavascriptSnippets.SCROLL_Y_AXIS.replace('Y_PIXELS', str(pixels))
        )

    def _start_images_monitor(self):
        """Start images monitor script on page."""
        self._execute_script(
            JavascriptSnippets.IMAGES_MONITOR
        )

    def _wait_for_images_to_load(self):
        """Wait for all images to load on page."""
        while self._execute_script(
            JavascriptSnippets.IMAGES_LOADED
        ) is None:
            time.sleep(Limits.SLEEP_BETWEEN_IMAGE_LOAD_CHECK)

        try:
            while self._execute_script(
                JavascriptSnippets.IMAGES_LOADED
            ) < Limits.ALL_IMAGES_LOADED:
                time.sleep(Limits.SLEEP_BETWEEN_IMAGE_LOAD_CHECK)
        except TypeError:
            self._start_images_monitor()

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

    ALL_IMAGES_LOADED = 15

    SLEEP_BETWEEN_IMAGE_LOAD_CHECK = 1

    RESIZE_WAIT_TIME = 1

    RESIZE_MAX_WAIT_TIME = 25


class UserAgents:
    """User agents."""

    # masquerading as google bot can trick some website to not serve
    # tons of ads and load faster
    GOOGLEBOT = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'

    DEFAULT = 'deafult'

    MAC_FIREFOX = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0'
