"""Camera test."""

from saas.photographer.camera import Camera, Limits
from saas.photographer.javascript import JavascriptSnippets
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from saas.storage.datadir import DataDirectory
from saas.photographer.photo import PhotoPath
from unittest.mock import MagicMock, call
from selenium import webdriver
from saas.web.url import Url
from os.path import dirname
import unittest
import time


class TestCamera(unittest.TestCase):
    """Test camera class."""

    def setUp(self):
        """Set up test."""
        self.camera = Camera()
        webdriver.Firefox.__init__ = MagicMock(return_value=None)
        self.url = Url.from_string('https://example.com')
        self.datadir = DataDirectory(dirname(__file__) + '/datadir')

    def tearDown(self):
        """Tear down test."""
        self.datadir.remove_data_dir()

    def creates_webdriver(self):
        """Test creates a webdriver."""
        FirefoxBinary.__init__ = MagicMock(return_value=None)
        self.webdriver_profile = self.camera._create_webdriver_profile()
        self.camera.webdriver = self.camera._create_webdriver(
            self.webdriver_profile
        )

    def routes_to_url(self):
        """Test routes camera to a url."""
        self.camera.webdriver.set_page_load_timeout = MagicMock()
        self.camera.webdriver.get = MagicMock()

    def uses_javascript_snippets(self):
        """Test uses javascript snippets."""
        JavascriptSnippets.load()

    def test_camera_can_create_webdriver_profile(self):
        """Test camerea can create webdriver profile."""
        self.creates_webdriver()
        self.assertIsInstance(
            obj=self.webdriver_profile,
            cls=webdriver.FirefoxProfile
        )

    def test_camera_can_create_webdriver(self):
        """Test camera can create webdriver."""
        self.creates_webdriver()
        self.webdriver_profile.set_preference = MagicMock()

        self.camera.webdriver = self.camera._create_webdriver(
            self.webdriver_profile,
        )

        self.assertIsInstance(obj=self.camera.webdriver, cls=webdriver.Firefox)
        self.webdriver_profile.set_preference.assert_any_call(
            'dom.popup_maximum',
            0
        )
        self.webdriver_profile.set_preference.assert_any_call(
            'privacy.popups.showBrowserMessage',
            False
        )

    def test_camera_can_route_to_url(self):
        """Test camera can be routed to url."""
        self.creates_webdriver()
        self.routes_to_url()

        self.camera._route(self.url)
        self.camera.webdriver.get.assert_called_with(self.url.to_string())

    def test_camera_resolution_can_be_set(self):
        """Test camera resolution can be set."""
        self.creates_webdriver()
        self.camera.webdriver.set_window_size = MagicMock()

        self.camera._set_resolution(100, 200)
        self.camera.webdriver.set_window_size.assert_called_with(100, 200)

    def test_camera_can_get_document_height(self):
        """Test camera can get document size."""
        self.creates_webdriver()
        self.uses_javascript_snippets()
        self.camera.webdriver.execute_script = MagicMock(return_value=10000)

        self.camera._document_height()
        self.camera.webdriver.execute_script.assert_called_with(
            JavascriptSnippets.DOCUMENT_HEIGHT
        )

    def test_camera_can_get_image_count(self):
        """Test camera can get image count."""
        self.creates_webdriver()
        self.uses_javascript_snippets()
        self.camera.webdriver.execute_script = MagicMock(return_value=123)

        images = self.camera._image_count()
        self.assertEqual(123, images)
        self.camera.webdriver.execute_script.assert_called_with(
            JavascriptSnippets.IMAGE_COUNT
        )

    def test_camera_can_get_script_count(self):
        """Test camera can get script count."""
        self.creates_webdriver()
        self.uses_javascript_snippets()
        self.camera.webdriver.execute_script = MagicMock(return_value=20)

        scripts = self.camera._script_count()
        self.assertEqual(20, scripts)
        self.camera.webdriver.execute_script.assert_called_with(
            JavascriptSnippets.SCRIPT_COUNT
        )

    def test_camera_can_get_stylesheet_count(self):
        """Test camera can get stylesheet count."""
        self.creates_webdriver()
        self.uses_javascript_snippets()
        self.camera.webdriver.execute_script = MagicMock(return_value=10)

        stylesheets = self.camera._stylesheet_count()
        self.assertEqual(10, stylesheets)
        self.camera.webdriver.execute_script.assert_called_with(
            JavascriptSnippets.STYLESHEET_COUNT
        )

    def test_camera_can_start_images_monitor(self):
        """Test camera can start images monitor."""
        self.creates_webdriver()
        self.uses_javascript_snippets()
        self.camera.webdriver.execute_script = MagicMock()

        self.camera._start_images_monitor()
        self.camera.webdriver.execute_script.assert_called_with(
            JavascriptSnippets.IMAGES_MONITOR
        )

    def test_camera_can_check_if_all_images_have_loaded(self):
        """Test camera can check if all images have finished loading."""
        self.creates_webdriver()
        self.uses_javascript_snippets()
        time.sleep = MagicMock()
        self.camera.webdriver.execute_script = MagicMock()
        self.camera.webdriver.execute_script.side_effect = [
            None,  # start images monitor
            0,
            0,
            0,
            1,
            1,
            2,
            3,
            4,
            Limits.ALL_IMAGES_LOADED,  # All images loaded at this limit
        ]

        self.camera._start_images_monitor()
        self.camera.webdriver.execute_script.assert_called_with(
            JavascriptSnippets.IMAGES_MONITOR
        )

        self.camera._wait_for_images_to_load()
        calls = [
            call(JavascriptSnippets.IMAGES_LOADED),
            call(JavascriptSnippets.IMAGES_LOADED),
            call(JavascriptSnippets.IMAGES_LOADED),
            call(JavascriptSnippets.IMAGES_LOADED),
            call(JavascriptSnippets.IMAGES_LOADED),
            call(JavascriptSnippets.IMAGES_LOADED),
            call(JavascriptSnippets.IMAGES_LOADED),
            call(JavascriptSnippets.IMAGES_LOADED),
            call(JavascriptSnippets.IMAGES_LOADED),
        ]
        self.camera.webdriver.execute_script.assert_has_calls(calls)

    def test_camera_can_scroll_page(self):
        """Test camera can scroll page."""
        self.creates_webdriver()
        self.uses_javascript_snippets()
        self.camera.webdriver.execute_script = MagicMock()

        self.camera._scroll_y_axis(100)  # scroll down 100px

        script = JavascriptSnippets.SCROLL_Y_AXIS.replace('Y_PIXELS', '100')
        self.camera.webdriver.execute_script.assert_called_with(
            script
        )

    def test_camera_can_wait_for_resize_of_document(self):
        """Test camera can wait for resize in proportion to doc height."""
        time.sleep = MagicMock()
        self.creates_webdriver()
        self.camera.webdriver.execute_script = MagicMock()
        self.camera.webdriver.set_window_size = MagicMock()
        self.camera._image_count = MagicMock(return_value=50)
        self.camera._script_count = MagicMock(return_value=3)
        self.camera._stylesheet_count = MagicMock(return_value=2)

        self.camera._set_resolution(200, 10000)
        self.camera._wait_for_resize()

        calls = [
            call(Limits.RESIZE_WAIT_TIME),
            call(Limits.RESIZE_WAIT_TIME),
            call(Limits.RESIZE_WAIT_TIME),
            call(Limits.RESIZE_WAIT_TIME),
            call(Limits.RESIZE_WAIT_TIME),
            call(Limits.RESIZE_WAIT_TIME),
        ]
        time.sleep.assert_has_calls(calls)

    def test_camera_can_save_screenshot(self):
        """Test camera can save screenshot."""
        self.creates_webdriver()
        self.camera.webdriver.get_window_size = MagicMock()
        self.camera.webdriver.save = MagicMock()
        self.camera.webdriver.save_screenshot = MagicMock()

        path = PhotoPath(self.datadir)
        self.camera._save(path)

        self.camera.webdriver.save_screenshot.assert_called_with(
            path.full_path()
        )


if __name__ == '__main__':
    unittest.main()
