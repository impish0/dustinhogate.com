#!/usr/bin/env python3
"""Unit tests for pagination functions in templates.py"""
import unittest
import sys
from pathlib import Path

# Add parent directory to path so we can import tailoza
sys.path.insert(0, str(Path(__file__).parent.parent))

from tailoza.templates import (
    _build_pagination_url,
    _render_page_link,
    _render_page_numbers,
    _render_nav_button,
    generate_pagination_html,
    post_template,
    MAX_PAGES_SHOW_ALL,
    PAGES_NEAR_EDGE,
)


class TestBuildPaginationUrl(unittest.TestCase):
    """Tests for _build_pagination_url()"""

    def test_first_page_from_first_page_index(self):
        """Link to page 1 when on page 1 (index)"""
        url = _build_pagination_url(page_num=1, current_page=1, is_category_page=False)
        self.assertEqual(url, "index.html")

    def test_first_page_from_other_page_index(self):
        """Link to page 1 when on page 2+ (index)"""
        url = _build_pagination_url(page_num=1, current_page=2, is_category_page=False)
        self.assertEqual(url, "../../index.html")

    def test_first_page_category(self):
        """Link to page 1 on category page"""
        url = _build_pagination_url(page_num=1, current_page=2, is_category_page=True)
        self.assertEqual(url, "../")

    def test_numbered_page_from_first_page(self):
        """Link to page 3 when on page 1"""
        url = _build_pagination_url(page_num=3, current_page=1, is_category_page=False)
        self.assertEqual(url, "../../page/3/")

    def test_numbered_page_from_other_page(self):
        """Link to page 3 when on page 2"""
        url = _build_pagination_url(page_num=3, current_page=2, is_category_page=False)
        self.assertEqual(url, "../3/")

    def test_numbered_page_category_from_first(self):
        """Link to page 3 when on page 1 (category)"""
        url = _build_pagination_url(page_num=3, current_page=1, is_category_page=True)
        self.assertEqual(url, "../../page/3/")


class TestRenderPageLink(unittest.TestCase):
    """Tests for _render_page_link()"""

    def test_current_page(self):
        """Current page renders as span, not link"""
        result = _render_page_link(page_num=2, current_page=2, url="../2/")
        self.assertEqual(result, '<span class="pagination-current">2</span>')

    def test_other_page(self):
        """Non-current page renders as link"""
        result = _render_page_link(page_num=3, current_page=2, url="../3/")
        self.assertEqual(result, '<a href="../3/">3</a>')


class TestRenderNavButton(unittest.TestCase):
    """Tests for _render_nav_button()"""

    def test_enabled_button(self):
        """Enabled button renders as link"""
        result = _render_nav_button("← Previous", "../1/", "pagination-prev", is_disabled=False)
        self.assertEqual(result, '<a href="../1/" class="pagination-prev">← Previous</a>')

    def test_disabled_button(self):
        """Disabled button renders as span"""
        result = _render_nav_button("← Previous", "", "pagination-prev", is_disabled=True)
        self.assertEqual(result, '<span class="pagination-prev disabled">← Previous</span>')


class TestRenderPageNumbers(unittest.TestCase):
    """Tests for _render_page_numbers()"""

    def test_few_pages_shows_all(self):
        """When total <= MAX_PAGES_SHOW_ALL, show all page numbers"""
        result = _render_page_numbers(current=1, total=5, is_category_page=False)
        self.assertEqual(len(result), 5)
        # Check page 1 is current
        self.assertIn('pagination-current', result[0])
        # Check others are links
        for i in range(1, 5):
            self.assertIn('<a href=', result[i])

    def test_many_pages_near_beginning(self):
        """Near beginning: [1] [2] [3] [4] ... [10]"""
        result = _render_page_numbers(current=2, total=10, is_category_page=False)
        # Should have 4 page links + ellipsis + last page = 6 elements
        self.assertEqual(len(result), 6)
        self.assertIn('pagination-ellipsis', result[4])
        self.assertIn('>10</a>', result[5])

    def test_many_pages_near_end(self):
        """Near end: [1] ... [7] [8] [9] [10]"""
        result = _render_page_numbers(current=9, total=10, is_category_page=False)
        # Should have: first + ellipsis + 4 pages = 6 elements
        self.assertEqual(len(result), 6)
        self.assertIn('>1</a>', result[0])
        self.assertIn('pagination-ellipsis', result[1])

    def test_many_pages_middle(self):
        """Middle: [1] ... [4] [5] [6] ... [10]"""
        result = _render_page_numbers(current=5, total=10, is_category_page=False)
        # Should have: first + ellipsis + 3 pages + ellipsis + last = 7 elements
        self.assertEqual(len(result), 7)
        self.assertIn('>1</a>', result[0])
        self.assertIn('pagination-ellipsis', result[1])
        self.assertIn('pagination-ellipsis', result[5])
        self.assertIn('>10</a>', result[6])


class TestGeneratePaginationHtml(unittest.TestCase):
    """Tests for generate_pagination_html()"""

    def test_single_page_returns_empty(self):
        """Single page should return empty string"""
        pagination = {
            'current_page': 1,
            'total_pages': 1,
            'has_prev': False,
            'has_next': False,
            'prev_page': 0,
            'next_page': 2,
        }
        result = generate_pagination_html(pagination)
        self.assertEqual(result, '')

    def test_none_pagination_returns_empty(self):
        """None pagination should return empty string"""
        result = generate_pagination_html(None)
        self.assertEqual(result, '')

    def test_two_pages_first_page(self):
        """Two pages, on first page"""
        pagination = {
            'current_page': 1,
            'total_pages': 2,
            'has_prev': False,
            'has_next': True,
            'prev_page': 0,
            'next_page': 2,
        }
        result = generate_pagination_html(pagination)
        # Should have nav wrapper
        self.assertIn('<nav class="pagination">', result)
        # Previous should be disabled
        self.assertIn('pagination-prev disabled', result)
        # Next should be enabled
        self.assertIn('class="pagination-next"', result)
        self.assertIn('Next →</a>', result)

    def test_two_pages_second_page(self):
        """Two pages, on second page"""
        pagination = {
            'current_page': 2,
            'total_pages': 2,
            'has_prev': True,
            'has_next': False,
            'prev_page': 1,
            'next_page': 3,
        }
        result = generate_pagination_html(pagination)
        # Previous should be enabled
        self.assertIn('class="pagination-prev"', result)
        self.assertIn('← Previous</a>', result)
        # Next should be disabled
        self.assertIn('pagination-next disabled', result)

    def test_category_page_urls(self):
        """Category pages use different URL structure"""
        pagination = {
            'current_page': 2,
            'total_pages': 3,
            'has_prev': True,
            'has_next': True,
            'prev_page': 1,
            'next_page': 3,
        }
        result = generate_pagination_html(pagination, base_url='technology')
        # Category page 1 link should use "../"
        self.assertIn('href="../"', result)

    def test_many_pages_has_ellipsis(self):
        """Many pages should show ellipsis"""
        pagination = {
            'current_page': 5,
            'total_pages': 10,
            'has_prev': True,
            'has_next': True,
            'prev_page': 4,
            'next_page': 6,
        }
        result = generate_pagination_html(pagination)
        self.assertIn('pagination-ellipsis', result)

    def test_output_structure(self):
        """Verify overall HTML structure"""
        pagination = {
            'current_page': 2,
            'total_pages': 3,
            'has_prev': True,
            'has_next': True,
            'prev_page': 1,
            'next_page': 3,
        }
        result = generate_pagination_html(pagination)
        # Check structure
        self.assertTrue(result.startswith('<nav class="pagination">'))
        self.assertTrue(result.endswith('</nav>'))
        self.assertIn('<div class="pagination-numbers">', result)
        self.assertIn('</div>', result)


class TestConstants(unittest.TestCase):
    """Tests for pagination constants"""

    def test_max_pages_show_all(self):
        """MAX_PAGES_SHOW_ALL should be 7"""
        self.assertEqual(MAX_PAGES_SHOW_ALL, 7)

    def test_pages_near_edge(self):
        """PAGES_NEAR_EDGE should be 3"""
        self.assertEqual(PAGES_NEAR_EDGE, 3)


class TestPostTemplate(unittest.TestCase):
    """Tests for post template rendering"""

    def test_footer_uses_config_footer_text(self):
        """Post pages should use the configured footer text"""
        result = post_template(
            title="Example",
            content="<p>Hello</p>",
            date="2024-01-01",
            config={
                "site_url": "https://example.com",
                "footer_text": "Fallback footer",
                "footer_text_html": 'Custom footer <a href="https://example.com">Link</a>',
            },
        )
        self.assertIn('Custom footer <a href="https://example.com">Link</a>', result)
        self.assertNotIn('© 2024 | <a href="../../rss.xml">RSS</a>', result)


if __name__ == '__main__':
    unittest.main()
