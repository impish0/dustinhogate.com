#!/usr/bin/env python3
"""Core build logic for Tailoza static site generator"""
import os
import sys
import shutil
import json
from pathlib import Path
from .parser import parse_frontmatter, markdown_to_html, get_post_date, extract_headings, generate_toc, add_heading_ids
from .templates import post_template, index_template, category_template, error_404_template
from .rss_generator import generate_rss
from .sitemap_generator import generate_sitemap
from .utils import category_slug, copy_asset
from .categorize import analyze_post_content, load_category_rules
import re
import html

SAFE_LINK_TARGETS = {'_self', '_blank', '_parent', '_top'}
UNSAFE_URL_SCHEMES = ('javascript:', 'data:', 'vbscript:')


def _is_safe_href(url):
    """Allow normal relative URLs and common safe absolute schemes."""
    normalized_url = url.strip().lower()
    return normalized_url and not normalized_url.startswith(UNSAFE_URL_SCHEMES)


def _build_safe_link(attrs_text, link_text):
    """Build a sanitized anchor tag from a raw attribute string."""
    attrs = {}
    for name, _, value in re.findall(r'([a-zA-Z_:][-\w:.]*)\s*=\s*(["\'])(.*?)\2', attrs_text):
        attrs[name.lower()] = value

    href = attrs.get('href')
    if not href or not _is_safe_href(href):
        return None

    safe_attrs = [f'href="{html.escape(href, quote=True)}"']

    target = attrs.get('target')
    if target in SAFE_LINK_TARGETS:
        safe_attrs.append(f'target="{html.escape(target, quote=True)}"')

    rel = attrs.get('rel', '').split()
    if target == '_blank':
        for token in ('noopener', 'noreferrer'):
            if token not in rel:
                rel.append(token)
    if rel:
        safe_attrs.append(f'rel="{html.escape(" ".join(rel), quote=True)}"')

    safe_link_text = html.escape(link_text)
    return f'<a {" ".join(safe_attrs)}>{safe_link_text}</a>'


def process_config_html(text):
    """Safely process HTML links in config text while escaping other content"""
    if not text:
        return ''

    # Extract safe HTML patterns before escaping
    # Pattern for anchor tags with plain-text bodies.
    link_pattern = r'<a\s+([^>]*?)>([^<]+)</a>'
    links = []

    def extract_link(match):
        proper_link = _build_safe_link(match.group(1), match.group(2))
        if not proper_link:
            return match.group(0)

        # Store the link with a placeholder
        placeholder = f'__LINK_{len(links)}__'
        links.append(proper_link)
        return placeholder

    # Extract links and replace with placeholders
    text_with_placeholders = re.sub(link_pattern, extract_link, text, flags=re.IGNORECASE)

    # Escape everything else
    escaped_text = html.escape(text_with_placeholders)

    # Restore links as proper HTML
    for i, proper_link in enumerate(links):
        placeholder = f'__LINK_{i}__'
        escaped_text = escaped_text.replace(placeholder, proper_link)

    return escaped_text

def validate_config(config):
    """Validate configuration values"""
    required_fields = ['site_title', 'site_url', 'site_description']
    for field in required_fields:
        if not config.get(field):
            raise ValueError(f"Config error: '{field}' is required and cannot be empty")

    # Validate URL format
    url = config.get('site_url', '')
    if not url.startswith(('http://', 'https://')):
        raise ValueError("Config error: 'site_url' must start with http:// or https://")

    # Remove trailing slash from site_url for consistency
    config['site_url'] = config['site_url'].rstrip('/')

    return config

def load_config():
    """Load configuration from config.json or use defaults"""
    default_config = {
        "site_title": "My Blog",
        "site_url": "https://example.com",
        "site_description": "A simple static blog",
        "author": "Your Name",
        "footer_text": "Built with a simple static site generator",
        "posts_per_page": 20,
        "timezone": "+0000"
    }

    config_path = Path('config.json')
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config.json: {e}")

    validated_config = validate_config(default_config)

    # Process HTML in footer_text if it exists
    if 'footer_text' in validated_config:
        validated_config['footer_text_html'] = process_config_html(validated_config['footer_text'])

    return validated_config

def generate_search_index(posts, config):
    """Generate search index for client-side search"""
    post_prefix = config.get('post_url_prefix', '/posts').strip('/')
    post_url_path = f'{post_prefix}/' if post_prefix else ''

    search_index = []

    for post in posts:
        # Extract plain text from HTML content for searching
        text_content = re.sub(r'<[^>]+>', '', post['content'])
        # Limit content length for search index
        text_content = ' '.join(text_content.split()[:100])  # First 100 words

        search_index.append({
            'title': post['title'],
            'description': post.get('description', ''),
            'content': text_content,
            'url': f'{post_url_path}{post["filename"]}/',  # Add trailing slash for directory URLs
            'date': post['date'],
            'categories': post.get('categories', []),
            'reading_time': post.get('reading_time', 1)
        })

    return json.dumps(search_index, separators=(',', ':'))

def calculate_reading_time(text):
    """Calculate reading time in minutes based on word count"""
    # Remove HTML tags for accurate word count
    text = re.sub(r'<[^>]+>', '', text)
    # Remove code blocks to avoid counting code as reading content
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`[^`]+`', '', text)

    # Count words
    words = len(text.split())

    # Average reading speed is 200-250 WPM, we'll use 200 for a comfortable pace
    minutes = max(1, round(words / 200))

    return minutes

def ensure_directories(config=None):
    """Clean output directory and ensure all required directories exist"""
    try:
        # First, remove the output directory if it exists
        output_path = Path('output')
        if output_path.exists():
            shutil.rmtree(output_path)
            print("✓ Cleaned output directory")

        # Now create all required directories
        # Get post URL prefix and create corresponding output directory
        if config:
            post_prefix = config.get('post_url_prefix', '/posts').strip('/')
            post_output_dir = f'output/{post_prefix}' if post_prefix else 'output'
        else:
            post_output_dir = 'output/posts'

        dirs = ['posts', 'output', post_output_dir, 'output/assets', 'output/assets/js', 'output/images', 'output/categories', 'output/page', 'images', 'assets']
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

        # Verify critical directories exist
        critical_dirs = ['posts']
        for dir_path in critical_dirs:
            if not Path(dir_path).exists():
                raise FileNotFoundError(f"Critical directory '{dir_path}' is missing")

    except (OSError, PermissionError) as e:
        raise RuntimeError(f"Failed to create directories: {e}")

def build_site():
    """Build the static site from markdown files"""
    config = load_config()
    ensure_directories(config)
    posts = []
    categories = {}

    # Get post URL configuration
    post_prefix = config.get('post_url_prefix', '/posts').strip('/')
    post_url_path = f'{post_prefix}/' if post_prefix else ''
    post_output_dir = f'output/{post_prefix}' if post_prefix else 'output'

    # Check for favicon early
    favicon_files = ['favicon.ico', 'favicon.png', 'favicon.svg']
    for favicon in favicon_files:
        favicon_path = Path('assets') / favicon
        if favicon_path.exists():
            config['favicon'] = favicon
            break

    if 'favicon' not in config:
        # Check in root directory as well
        for favicon in favicon_files:
            favicon_path = Path(favicon)
            if favicon_path.exists():
                config['favicon'] = favicon
                break

    # Process all markdown files in posts directory
    posts_dir = Path('posts')
    if not posts_dir.exists():
        print("Error: 'posts' directory not found")
        return False

    # First pass: collect all post data
    post_data = []
    for post_file in sorted(posts_dir.glob('*.md')):
        filename = post_file.name

        # Skip draft posts (files starting with underscore)
        if filename.startswith('_'):
            continue

        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse frontmatter and content
            frontmatter, body = parse_frontmatter(content)

            # Get post metadata
            title = frontmatter.get('title', filename.replace('.md', '').replace('-', ' ').title())
            date = get_post_date(frontmatter, filename)
            description = frontmatter.get('description', '')
            keywords = frontmatter.get('keywords', '')
            author = frontmatter.get('author', '')
            image = frontmatter.get('image', '')
            post_categories = frontmatter.get('categories', [])

            # Auto-categorize if no categories are specified
            if not post_categories:
                category_rules = load_category_rules()
                post_categories = analyze_post_content(content, category_rules)

            # Convert markdown to HTML
            html_content = markdown_to_html(body)

            # Calculate reading time
            reading_time = calculate_reading_time(body)

            # Generate TOC if enabled in frontmatter
            toc_html = ""
            if frontmatter.get('toc', '').lower() == 'true':
                headings = extract_headings(html_content)
                # Only show TOC if there are at least 3 headings (excluding H1)
                MIN_HEADINGS_FOR_TOC = 3
                if len([h for h in headings if h['level'] > 1]) >= MIN_HEADINGS_FOR_TOC:
                    toc_html = generate_toc(headings)
                    html_content = add_heading_ids(html_content, headings)

            # Generate directory name for clean URLs (no .html extension)
            post_dir_name = filename.replace('.md', '')

            post_data.append({
                'title': title,
                'date': date,
                'description': description,
                'keywords': keywords,
                'author': author,
                'image': image,
                'filename': post_dir_name,
                'content': html_content,
                'categories': post_categories,
                'reading_time': reading_time,
                'toc_html': toc_html
            })

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

    # Sort posts by date (newest first)
    post_data.sort(key=lambda x: x['date'], reverse=True)

    # Second pass: generate HTML with prev/next navigation
    for i, post in enumerate(post_data):
        # Previous post is newer (lower index), next post is older (higher index)
        prev_post = post_data[i - 1] if i > 0 else None
        next_post = post_data[i + 1] if i < len(post_data) - 1 else None

        # Create post HTML
        post_url = f"{config['site_url']}/{post_url_path}{post['filename']}/"
        post_html = post_template(
            post['title'], post['content'], post['date'],
            post['description'], post['keywords'], post['author'],
            post['image'], post['toc_html'], post_url, config,
            post['categories'], post['reading_time'], post_prefix,
            prev_post, next_post
        )

        # Create post directory and write index.html inside it
        post_directory = Path(post_output_dir) / post['filename']
        post_directory.mkdir(parents=True, exist_ok=True)
        with open(post_directory / 'index.html', 'w', encoding='utf-8') as f:
            f.write(post_html)

        # Add to posts list for index and RSS
        posts.append({
            'title': post['title'],
            'date': post['date'],
            'description': post['description'],
            'filename': post['filename'],
            'content': post['content'],
            'categories': post['categories'],
            'reading_time': post['reading_time']
        })

        # Track posts by category
        for category in post['categories']:
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'title': post['title'],
                'date': post['date'],
                'description': post['description'],
                'filename': post['filename'],
                'reading_time': post['reading_time']
            })

    # Generate index pages with pagination
    posts_per_page = config.get('posts_per_page', 20)
    total_pages = (len(posts) + posts_per_page - 1) // posts_per_page

    for page_num in range(total_pages):
        start_idx = page_num * posts_per_page
        end_idx = min(start_idx + posts_per_page, len(posts))
        page_posts = posts[start_idx:end_idx]

        pagination_info = {
            'current_page': page_num + 1,
            'total_pages': total_pages,
            'has_prev': page_num > 0,
            'has_next': page_num < total_pages - 1,
            'prev_page': page_num,
            'next_page': page_num + 2
        }

        index_html = index_template(page_posts, config, sorted(categories.keys()), pagination_info, post_prefix)

        if page_num == 0:
            with open('output/index.html', 'w', encoding='utf-8') as f:
                f.write(index_html)
        else:
            # Create page directory with index.html inside
            page_dir = Path('output/page') / str(page_num + 1)
            page_dir.mkdir(parents=True, exist_ok=True)
            with open(page_dir / 'index.html', 'w', encoding='utf-8') as f:
                f.write(index_html)

    # Generate category pages with pagination
    for category_name, category_posts in categories.items():
        # Sort posts in category by date
        category_posts.sort(key=lambda x: x['date'], reverse=True)

        # Paginate category posts
        total_category_pages = (len(category_posts) + posts_per_page - 1) // posts_per_page
        cat_slug = category_slug(category_name)

        for page_num in range(total_category_pages):
            start_idx = page_num * posts_per_page
            end_idx = min(start_idx + posts_per_page, len(category_posts))
            page_posts = category_posts[start_idx:end_idx]

            pagination_info = {
                'current_page': page_num + 1,
                'total_pages': total_category_pages,
                'has_prev': page_num > 0,
                'has_next': page_num < total_category_pages - 1,
                'prev_page': page_num,
                'next_page': page_num + 2,
                'category_slug': cat_slug
            }

            # Generate category page
            category_html = category_template(category_name, page_posts, config, pagination_info, post_prefix)

            if page_num == 0:
                # First page - create category directory with index.html
                category_dir = Path('output/categories') / cat_slug
                category_dir.mkdir(parents=True, exist_ok=True)
                with open(category_dir / 'index.html', 'w', encoding='utf-8') as f:
                    f.write(category_html)
            else:
                # Additional pages - create numbered subdirectory with index.html
                category_page_dir = Path('output/categories') / cat_slug / str(page_num + 1)
                category_page_dir.mkdir(parents=True, exist_ok=True)
                with open(category_page_dir / 'index.html', 'w', encoding='utf-8') as f:
                    f.write(category_html)

    print(f"✓ Generated {len(categories)} category pages")

    # Generate RSS feed
    rss_xml = generate_rss(posts, config['site_title'], config['site_url'], config['site_description'], config.get('timezone', '+0000'), post_prefix, config.get('rss_full_content', True))
    with open('output/rss.xml', 'w', encoding='utf-8') as f:
        f.write(rss_xml)

    # Generate sitemap
    sitemap_xml = generate_sitemap(posts, config)
    with open('output/sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap_xml)

    # Generate search index
    search_index_json = generate_search_index(posts, config)
    with open('output/search-index.json', 'w', encoding='utf-8') as f:
        f.write(search_index_json)

    # Generate robots.txt
    robots_txt = f"""User-agent: *
Allow: /

Sitemap: {config['site_url']}/sitemap.xml"""
    with open('output/robots.txt', 'w', encoding='utf-8') as f:
        f.write(robots_txt)

    # Generate 404.html
    error_404_html = error_404_template(config)
    with open('output/404.html', 'w', encoding='utf-8') as f:
        f.write(error_404_html)
    # Copy static assets
    copy_errors = []

    # Get tailoza package directory for core assets
    tailoza_dir = Path(__file__).parent
    core_assets_dir = tailoza_dir / 'assets'

    # Check for required style.css from tailoza package
    style_css = core_assets_dir / 'style.css'
    if not style_css.exists():
        copy_errors.append("Required file 'tailoza/assets/style.css' not found")
    else:
        copy_asset(style_css, 'output/assets/style.css', copy_errors)

    # Copy core application assets from tailoza package
    core_assets = [
        (core_assets_dir / 'prism.css', 'output/assets/prism.css'),
        (core_assets_dir / 'js' / 'prism.js', 'output/assets/js/prism.js'),
        (core_assets_dir / 'js' / 'code-copy.js', 'output/assets/js/code-copy.js'),
        (core_assets_dir / 'js' / 'search.js', 'output/assets/js/search.js'),
        (core_assets_dir / 'js' / 'dropdown.js', 'output/assets/js/dropdown.js'),
    ]

    for src, dest in core_assets:
        copy_asset(src, dest, copy_errors)

    # Copy images
    images_dir = Path('images')
    if images_dir.exists() and any(images_dir.iterdir()):
        try:
            image_count = 0
            for img in images_dir.glob('*'):
                if img.is_file():
                    shutil.copy2(img, f'output/images/{img.name}')
                    image_count += 1
            if image_count > 0:
                print(f"✓ Copied {image_count} images")
        except Exception as e:
            copy_errors.append(f"Failed to copy some images: {e}")

    # Copy favicon if it exists
    if 'favicon' in config:
        favicon = config['favicon']
        favicon_copied = False

        # Try assets directory first
        favicon_path = Path('assets') / favicon
        if favicon_path.exists():
            try:
                shutil.copy2(favicon_path, f'output/{favicon}')
                print(f"✓ Copied {favicon}")
                favicon_copied = True
            except Exception as e:
                copy_errors.append(f"Failed to copy favicon from assets: {e}")

        # Try root directory if not found in assets
        if not favicon_copied:
            favicon_path = Path(favicon)
            if favicon_path.exists():
                try:
                    shutil.copy2(favicon_path, f'output/{favicon}')
                    print(f"✓ Copied {favicon}")
                except Exception as e:
                    copy_errors.append(f"Failed to copy favicon from root: {e}")

    # Report any errors
    if copy_errors:
        print("\nWarning: Some assets could not be copied:")
        for error in copy_errors:
            print(f"  - {error}")
        if any("Required file" in error for error in copy_errors):
            return False

    print(f"✓ Built {len(posts)} posts")
    print("✓ Generated index.html")
    print("✓ Generated rss.xml")
    print("✓ Generated sitemap.xml")
    print("✓ Generated search-index.json")
    print("✓ Generated 404.html")
    print("✓ Copied CSS files")
    print("\nSite built successfully in 'output' directory!")
    return True
