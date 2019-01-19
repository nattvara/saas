"""Javascript module."""

from __future__ import annotations
from os.path import dirname


class JavascriptSnippets:
    """Javascript snippets class."""

    DOCUMENT_HEIGHT = ''

    IMAGES_MONITOR = ''

    IMAGES_LOADED = ''

    SCROLL_Y_AXIS = ''

    IMAGE_COUNT = ''

    SCRIPT_COUNT = ''

    STYLESHEET_COUNT = ''

    @staticmethod
    def load():
        """Load javscript snippets."""
        JavascriptSnippets.DOCUMENT_HEIGHT = JavascriptSnippets._load_snippet(
            'document_height.js'
        )
        JavascriptSnippets.IMAGES_MONITOR = JavascriptSnippets._load_snippet(
            'images_monitor.js'
        )
        JavascriptSnippets.IMAGES_LOADED = JavascriptSnippets._load_snippet(
            'images_loaded.js'
        )
        JavascriptSnippets.SCROLL_Y_AXIS = JavascriptSnippets._load_snippet(
            'scroll_y.js'
        )
        JavascriptSnippets.IMAGE_COUNT = JavascriptSnippets._load_snippet(
            'image_count.js'
        )
        JavascriptSnippets.SCRIPT_COUNT = JavascriptSnippets._load_snippet(
            'script_count.js'
        )
        JavascriptSnippets.STYLESHEET_COUNT = JavascriptSnippets._load_snippet(
            'stylesheet_count.js'
        )

    def _load_snippet(filename) -> str:
        """Load snippet from file.

        Args:
            filename: name of script eg. filename.js

        Returns:
            The content of the script file
            str
        """
        fullpath = f'{dirname(__file__)}/js/{filename}'
        file = open(fullpath, 'r')
        script = file.read()
        file.close()
        return script
