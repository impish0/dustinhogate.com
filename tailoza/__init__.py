"""Tailoza - A minimal static site generator with zero dependencies"""

__version__ = "1.0.0"

from .parser import parse_frontmatter, markdown_to_html, get_post_date, extract_headings, generate_toc, add_heading_ids
from .templates import post_template, index_template, category_template, error_404_template
from .rss_generator import generate_rss
from .sitemap_generator import generate_sitemap
from .utils import category_slug, copy_asset, favicon_link
from .categorize import suggest_categories, analyze_post_content

__all__ = [
    'parse_frontmatter',
    'markdown_to_html',
    'get_post_date',
    'extract_headings',
    'generate_toc',
    'add_heading_ids',
    'post_template',
    'index_template',
    'category_template',
    'error_404_template',
    'generate_rss',
    'generate_sitemap',
    'category_slug',
    'copy_asset',
    'favicon_link',
    'suggest_categories',
    'analyze_post_content',
]
