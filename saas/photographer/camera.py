"""Camera module."""

from __future__ import annotations
from urllib3.exceptions import ProtocolError, MaxRetryError
from saas.photographer.javascript import JavascriptSnippets
from selenium.common.exceptions import JavascriptException
from saas.photographer.photo import PhotoPath, Screenshot
from saas.storage.refresh import RefreshRate
from http.client import RemoteDisconnected
import saas.utils.console as console
from typing import Type, Optional
from selenium import webdriver
import saas.threads as threads
from saas.web.url import Url
from os.path import dirname
import pkg_resources
import time
import os


class Camera:
    """Camera class."""

    def __init__(
        self,
        viewport_width: int=1920,
        viewport_height: int=0,
        viewport_max_height: Optional[int]=None
    ):
        """Create new camera.

        Args:
            viewport_width: width of camera viewport (default: {1920})
            viewport_height: height of camera viewport, if set to 0 camera
                will try to take a full height high quality screenshot,
                which is way slower than fixed size (default: {0})
            viewport_max_height: max height of camera viewport if
                viewport_height is not default value this will be ignored
        """
        self.webdriver = None  # type: webdriver.FirefoxProfile
        self.width = 0
        self.height = 0
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.viewport_max_height = viewport_max_height

    def take_picture(
        self, url: Url,
        path: PhotoPath,
        refresh_rate: Type[RefreshRate]
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
        try:
            console.dca('launching firefox, camera: {}x{}'.format(
                self.viewport_width,
                self.viewport_height if self.viewport_height != 0 else 'full'
            ))

            profile = self._create_webdriver_profile()
            self.webdriver = self._create_webdriver(
                profile,
                UserAgents.GOOGLEBOT
            )
            self._install_webdriver_addons()

            threads.Controller.webdrivers.append(
                self.webdriver.service.process.pid
            )

            console.dca(f'routing camera to {url.to_string()}')

            self._route_to_blank()
            self._route(url)

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
                    if self.viewport_max_height is not None:
                        if scroll_to >= self.viewport_max_height:
                            break
                    self._scroll_y_axis(scroll_to)
                    self._wait_for_images_to_load()

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
                self._set_resolution(self.viewport_width, height)
                self._wait_for_images_to_load()
                self._scroll_y_axis(-500)
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

                # fixes bug where webdriver would never quit
                self._stop_webdriver_service_process()

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
        profile.set_preference('dom.push.enabled', False)
        return webdriver.Firefox()

    def _install_webdriver_addons(self):
        """Install webdriver addons.

        The extensions that are installed either improve rendering
        performance. Or let firefox bypass paywalls or cookie/GDPR
        concent forms.
        """
        self.webdriver.install_addon(Addons.REFERER_HEADER, temporary=True)
        self.webdriver.install_addon(Addons.IDCAC)
        self.webdriver.install_addon(Addons.UBLOCK_ORIGIN, temporary=True)

    def _stop_webdriver_service_process(self):
        """Stop seleniums "service" process.

        The "stop" method in the module selenium.webdriver.common.service
        has a call to process.wait(), which for some reason seems to wait
        indefinitely and prevent camera from ever exiting take_photo().

        Terminating the process here instead, will prevent the service
        from calling process.wait() and hanging the entire camera.
        """
        try:
            self.webdriver.service.send_remote_shutdown_command()
        except TypeError:
            pass

        try:
            for stream in [
                self.webdriver.service.process.stdin,
                self.webdriver.service.process.stdout,
                self.webdriver.service.process.stderr
            ]:
                try:
                    stream.close()
                except AttributeError:
                    pass
            self.webdriver.service.process.terminate()

            # this is the call that causes the webdriver to never
            # finish quitting
            # self.webdriver.service.process.wait()

            self.webdriver.service.process.kill()
            self.webdriver.service.process = None
        except OSError:
            pass

    def _route(self, url: Url):
        """Route camera to url.

        Args:
            url: A Url to route camera to
        """
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


class Addons:
    """Firefox addons."""

    REFERER_HEADER = pkg_resources.resource_filename(
        'extensions',
        'referer_header.xpi'
    )

    # https://github.com/gorhill/uBlock/releases
    UBLOCK_ORIGIN = pkg_resources.resource_filename(
        'extensions',
        'uBlock0_1.17.7rc0.xpi'
    )

    # https://www.i-dont-care-about-cookies.eu/
    IDCAC = pkg_resources.resource_filename(
        'extensions',
        'idcac_2.9.5.xpi'
    )


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
