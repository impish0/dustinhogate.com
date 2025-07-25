#!/usr/bin/env python3
import os
import sys
import shutil
import json
from pathlib import Path
from parser import parse_frontmatter, markdown_to_html, get_post_date, extract_headings, generate_toc, add_heading_ids
from templates import post_template, index_template, category_template
from rss_generator import generate_rss
from sitemap_generator import generate_sitemap
import re

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
    
    return validate_config(default_config)

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
            'url': f'{post_url_path}{post["filename"]}',
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
        
        dirs = ['posts', 'output', post_output_dir, 'output/assets', 'output/assets/js', 'output/images', 'output/categories', 'output/page', 'images', 'assets', 'assets/js']
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Verify critical directories exist
        critical_dirs = ['posts', 'assets']
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
            
            # Generate HTML filename
            html_filename = filename.replace('.md', '.html')
            
            # Create post HTML
            post_url = f"{config['site_url']}/{post_url_path}{html_filename}"
            post_html = post_template(title, html_content, date, description, keywords, author, image, toc_html, post_url, config, post_categories, reading_time, post_prefix)
            
            # Write post HTML file
            with open(Path(post_output_dir) / html_filename, 'w', encoding='utf-8') as f:
                f.write(post_html)
            
            # Add to posts list for index and RSS
            posts.append({
                'title': title,
                'date': date,
                'description': description,
                'filename': html_filename,
                'content': html_content,
                'categories': post_categories,
                'reading_time': reading_time
            })
            
            # Track posts by category
            for category in post_categories:
                if category not in categories:
                    categories[category] = []
                categories[category].append({
                    'title': title,
                    'date': date,
                    'description': description,
                    'filename': html_filename,
                    'reading_time': reading_time
                })
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    # Sort posts by date (newest first)
    posts.sort(key=lambda x: x['date'], reverse=True)
    
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
            # Create page directory
            Path('output/page').mkdir(exist_ok=True)
            with open(f'output/page/{page_num + 1}.html', 'w', encoding='utf-8') as f:
                f.write(index_html)
    
    # Generate category pages with pagination
    for category_name, category_posts in categories.items():
        # Sort posts in category by date
        category_posts.sort(key=lambda x: x['date'], reverse=True)
        
        # Paginate category posts
        total_category_pages = (len(category_posts) + posts_per_page - 1) // posts_per_page
        category_slug = category_name.lower().replace(' ', '-')
        
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
                'category_slug': category_slug
            }
            
            # Generate category page
            category_html = category_template(category_name, page_posts, config, pagination_info, post_prefix)
            
            if page_num == 0:
                # First page at regular location
                with open(Path('output/categories') / f'{category_slug}.html', 'w', encoding='utf-8') as f:
                    f.write(category_html)
            else:
                # Additional pages in subdirectory
                category_page_dir = Path('output/categories') / category_slug
                category_page_dir.mkdir(exist_ok=True)
                with open(category_page_dir / f'{page_num + 1}.html', 'w', encoding='utf-8') as f:
                    f.write(category_html)
    
    print(f"✓ Generated {len(categories)} category pages")
    
    # Generate RSS feed
    rss_xml = generate_rss(posts, config['site_title'], config['site_url'], config['site_description'], config.get('timezone', '+0000'), post_prefix)
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
    
    # Copy static assets
    copy_errors = []
    
    # Copy CSS files
    try:
        style_css = Path('assets/style.css')
        if not style_css.exists():
            copy_errors.append("Required file 'assets/style.css' not found")
        else:
            shutil.copy2(style_css, 'output/assets/style.css')
            print("✓ Copied style.css")
    except Exception as e:
        copy_errors.append(f"Failed to copy style.css: {e}")
    
    # Copy optional CSS files
    prism_css = Path('assets/prism.css')
    if prism_css.exists():
        try:
            shutil.copy2(prism_css, 'output/assets/prism.css')
            print("✓ Copied prism.css")
        except Exception as e:
            copy_errors.append(f"Failed to copy prism.css: {e}")
    
    # Copy JS files
    prism_js = Path('assets/js/prism.js')
    if prism_js.exists():
        try:
            shutil.copy2(prism_js, 'output/assets/js/prism.js')
            print("✓ Copied prism.js")
        except Exception as e:
            copy_errors.append(f"Failed to copy prism.js: {e}")
    
    # Copy code-copy.js
    code_copy_js = Path('assets/js/code-copy.js')
    if code_copy_js.exists():
        try:
            shutil.copy2(code_copy_js, 'output/assets/js/code-copy.js')
            print("✓ Copied code-copy.js")
        except Exception as e:
            copy_errors.append(f"Failed to copy code-copy.js: {e}")
    
    # Copy search.js
    search_js = Path('assets/js/search.js')
    if search_js.exists():
        try:
            shutil.copy2(search_js, 'output/assets/js/search.js')
            print("✓ Copied search.js")
        except Exception as e:
            copy_errors.append(f"Failed to copy search.js: {e}")
    
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
    print("✓ Copied CSS files")
    print("\nSite built successfully in 'output' directory!")
    return True

if __name__ == "__main__":
    try:
        success = build_site()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nBuild cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"Error building site: {e}")
        sys.exit(1)