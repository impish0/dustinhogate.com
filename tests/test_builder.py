#!/usr/bin/env python3
"""Unit tests for HTML processing in builder.py"""
import unittest
import sys
from pathlib import Path

# Add parent directory to path so we can import tailoza
sys.path.insert(0, str(Path(__file__).parent.parent))

from tailoza.builder import process_config_html


class TestProcessConfigHtml(unittest.TestCase):
    """Tests for footer HTML sanitization."""

    def test_basic_link_is_preserved(self):
        result = process_config_html('Built with <a href="https://example.com">Tailoza</a>')
        self.assertEqual(result, 'Built with <a href="https://example.com">Tailoza</a>')

    def test_target_blank_is_preserved_and_rel_is_added(self):
        result = process_config_html(
            'Built with <a href="https://example.com" target="_blank">Tailoza</a>'
        )
        self.assertEqual(
            result,
            'Built with <a href="https://example.com" target="_blank" rel="noopener noreferrer">Tailoza</a>'
        )

    def test_existing_rel_is_retained_when_target_blank_is_used(self):
        result = process_config_html(
            'Built with <a href="https://example.com" target="_blank" rel="external">Tailoza</a>'
        )
        self.assertEqual(
            result,
            'Built with <a href="https://example.com" target="_blank" rel="external noopener noreferrer">Tailoza</a>'
        )

    def test_unsafe_link_is_escaped(self):
        result = process_config_html(
            'Built with <a href="javascript:alert(1)" target="_blank">Tailoza</a>'
        )
        self.assertIn('&lt;a href=&quot;javascript:alert(1)&quot; target=&quot;_blank&quot;&gt;', result)


if __name__ == '__main__':
    unittest.main()
