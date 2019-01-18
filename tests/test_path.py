"""Path test."""

from saas.mount.file import Path
import unittest


class TestPath(unittest.TestCase):
    """Test path class."""

    def test_path_can_parse_parts_of_path(self):
        """Test path can parse parts."""
        path = '/example.com/2019-01-13H20:00/foo/bar/baz.png'
        path = Path(path)
        self.assertEqual('example.com', path.domain)
        self.assertEqual('2019-01-13H20:00', path.captured_at)
        self.assertEqual('/foo/bar/baz.png', path.end)

    def test_path_can_parse_end_correctly(self):
        """Test path can parse end correctly."""
        path = Path('/example.com/2019-01-13H20:00')
        self.assertEqual('/', path.end)

        path = Path('/example.com/2019-01-13H20:00/')
        self.assertEqual('/', path.end)

        path = Path('/example.com/2019-01-13H20:00/foo')
        self.assertEqual('/foo', path.end)

        path = Path('/example.com/2019-01-13H20:00/foo/')
        self.assertEqual('/foo', path.end)

        path = Path('/example.com/2019-01-13H20:00/foo/bar')
        self.assertEqual('/foo/bar', path.end)

        path = Path('/example.com/2019-01-13H20:00/foo/bar/')
        self.assertEqual('/foo/bar', path.end)

        path = Path('/example.com/2019-01-13H20:00/foo/bar/baz.png')
        self.assertEqual('/foo/bar/baz.png', path.end)

    def test_check_for_domain(self):
        """Test check for domain."""
        path = Path('/example.com/2019-01-13H20:00')
        self.assertTrue(path.includes_domain())

        path = Path('/example.com/')
        self.assertTrue(path.includes_domain())

        path = Path('/example.com')
        self.assertTrue(path.includes_domain())

        path = Path('/')
        self.assertFalse(path.includes_domain())

    def test_check_for_captured_at(self):
        """Test check for captured_at."""
        path = Path('/example.com/2019-01-13H20:00/foo/bar')
        self.assertTrue(path.includes_captured_at())

        path = Path('/example.com/2019-01-13H20:00/foo')
        self.assertTrue(path.includes_captured_at())

        path = Path('/example.com/2019-01-13H20:00/')
        self.assertTrue(path.includes_captured_at())

        path = Path('/example.com/2019-01-13H20:00')
        self.assertTrue(path.includes_captured_at())

        path = Path('/example.com/')
        self.assertFalse(path.includes_captured_at())

        path = Path('/')
        self.assertFalse(path.includes_captured_at())

    def test_check_for_end(self):
        """Test check for end."""
        path = Path('/example.com/2019-01-13H20:00/foo/bar')
        self.assertTrue(path.includes_end())

        path = Path('/example.com/2019-01-13H20:00/foo')
        self.assertTrue(path.includes_end())

        path = Path('/example.com/2019-01-13H20:00/')
        self.assertFalse(path.includes_end())

        path = Path('/example.com/2019-01-13H20:00')
        self.assertFalse(path.includes_end())

        path = Path('/example.com/')
        self.assertFalse(path.includes_end())

        path = Path('/')
        self.assertFalse(path.includes_captured_at())

    def test_end_can_be_treated_as_file(self):
        """Test end can be treated as file."""
        path = Path('/example.com/2019-01-13H20:00/foo/bar')
        self.assertEqual('/foo/bar', path.end_as_file())

        path = Path('/example.com/2019-01-13H20:00/foo/bar/')
        self.assertEqual('/foo/bar', path.end_as_file())

        path = Path('/example.com/2019-01-13H20:00/')
        self.assertEqual('/', path.end_as_file())

    def test_end_can_be_treated_as_directory(self):
        """Test end can be treated as directory."""
        path = Path('/example.com/2019-01-13H20:00/foo/bar')
        self.assertEqual('/foo/bar/', path.end_as_directory())

        path = Path('/example.com/2019-01-13H20:00/foo/bar/')
        self.assertEqual('/foo/bar/', path.end_as_directory())

        path = Path('/example.com/2019-01-13H20:00/')
        self.assertEqual('/', path.end_as_directory())


if __name__ == '__main__':
    unittest.main()
