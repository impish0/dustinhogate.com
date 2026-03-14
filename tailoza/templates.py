#!/usr/bin/env python3
import html
from .utils import category_slug, favicon_link

# Pagination display constants
MAX_PAGES_SHOW_ALL = 7  # Show all page numbers when total pages <= this value
PAGES_NEAR_EDGE = 3     # How close to start/end to trigger edge display mode


def _build_pagination_url(page_num, current_page, is_category_page):
    """Build the URL for a specific page number.

    Args:
        page_num: The page number to link to
        current_page: The current page being viewed
        is_category_page: True for category pages, False for index pages

    Returns:
        Relative URL string for the page
    """
    is_on_first_page = current_page == 1

    if page_num == 1:
        # Link to first/index page
        if is_category_page:
            return "../"
        return "index.html" if is_on_first_page else "../../index.html"

    # Link to numbered page (page 2+)
    if is_on_first_page:
        return f"../../page/{page_num}/"
    return f"../{page_num}/"


def _render_page_link(page_num, current_page, url):
    """Render a single page link or current page indicator."""
    if page_num == current_page:
        return f'<span class="pagination-current">{page_num}</span>'
    return f'<a href="{url}">{page_num}</a>'


def _render_page_numbers(current, total, is_category_page):
    """Generate page number elements with ellipsis where appropriate.

    Returns a list of HTML strings for page numbers and ellipsis.
    """
    def link(page_num):
        url = _build_pagination_url(page_num, current, is_category_page)
        return _render_page_link(page_num, current, url)

    ellipsis = '<span class="pagination-ellipsis">…</span>'

    # Show all pages when there are few enough
    if total <= MAX_PAGES_SHOW_ALL:
        return [link(i) for i in range(1, total + 1)]

    # Near beginning: [1] [2] [3] [4] ... [last]
    if current <= PAGES_NEAR_EDGE:
        return [link(i) for i in range(1, 5)] + [ellipsis, link(total)]

    # Near end: [1] ... [last-3] [last-2] [last-1] [last]
    if current >= total - PAGES_NEAR_EDGE + 1:
        return [link(1), ellipsis] + [link(i) for i in range(total - 3, total + 1)]

    # Middle: [1] ... [curr-1] [curr] [curr+1] ... [last]
    return [link(1), ellipsis] + [link(i) for i in range(current - 1, current + 2)] + [ellipsis, link(total)]


def _render_nav_button(label, url, css_class, is_disabled):
    """Render a previous/next navigation button."""
    if is_disabled:
        return f'<span class="{css_class} disabled">{label}</span>'
    return f'<a href="{url}" class="{css_class}">{label}</a>'


def generate_pagination_html(pagination, base_url=''):
    """Generate pagination navigation HTML.

    Args:
        pagination: Dict with keys: current_page, total_pages, has_prev, has_next,
                   prev_page, next_page
        base_url: Category slug for category pages, empty string for index pages

    Returns:
        HTML string for pagination navigation, or empty string if not needed
    """
    if not pagination or pagination['total_pages'] <= 1:
        return ''

    current = pagination['current_page']
    total = pagination['total_pages']
    is_category_page = bool(base_url)

    # Build previous button
    prev_url = _build_pagination_url(pagination['prev_page'], current, is_category_page) if pagination['has_prev'] else ''
    prev_button = _render_nav_button('← Previous', prev_url, 'pagination-prev', not pagination['has_prev'])

    # Build next button
    next_url = _build_pagination_url(pagination['next_page'], current, is_category_page) if pagination['has_next'] else ''
    next_button = _render_nav_button('Next →', next_url, 'pagination-next', not pagination['has_next'])

    # Build page numbers
    page_numbers = _render_page_numbers(current, total, is_category_page)

    html_parts = [
        '<nav class="pagination">',
        prev_button,
        '<div class="pagination-numbers">',
        *page_numbers,
        '</div>',
        next_button,
        '</nav>'
    ]

    return '\n'.join(html_parts)

def _generate_post_navigation(prev_post, next_post, post_prefix):
    """Generate previous/next post navigation HTML."""
    if not prev_post and not next_post:
        return ''

    nav_parts = ['<nav class="post-nav">']

    if prev_post:
        prev_url = f"/{post_prefix}/{html.escape(prev_post['filename'], quote=True)}/" if post_prefix else f"/{html.escape(prev_post['filename'], quote=True)}/"
        nav_parts.append(f'''<a href="{prev_url}" class="post-nav-link post-nav-prev">
            <span class="post-nav-label">Previous</span>
            <span class="post-nav-title">{html.escape(prev_post['title'])}</span>
        </a>''')
    else:
        nav_parts.append('<span class="post-nav-link post-nav-prev disabled"></span>')

    if next_post:
        next_url = f"/{post_prefix}/{html.escape(next_post['filename'], quote=True)}/" if post_prefix else f"/{html.escape(next_post['filename'], quote=True)}/"
        nav_parts.append(f'''<a href="{next_url}" class="post-nav-link post-nav-next">
            <span class="post-nav-label">Next</span>
            <span class="post-nav-title">{html.escape(next_post['title'])}</span>
        </a>''')
    else:
        nav_parts.append('<span class="post-nav-link post-nav-next disabled"></span>')

    nav_parts.append('</nav>')
    return '\n'.join(nav_parts)


def post_template(title, content, date, description="", keywords="", author="", image="", toc="", url="", config={}, categories=[], reading_time=0, post_prefix="posts", prev_post=None, next_post=None):
    """Generate HTML for a blog post with enhanced SEO"""
    theme = config.get('theme', 'light')
    post_nav = _generate_post_navigation(prev_post, next_post, post_prefix)
    
    # Build absolute image URL if image is provided
    image_url = ""
    if image:
        if image.startswith(('http://', 'https://')):
            image_url = image
        else:
            # Remove any leading slashes or 'images/' prefix
            clean_image = image.replace('images/', '').lstrip('/')
            image_url = f"{config.get('site_url', '')}/images/{clean_image}"
    
    # Escape all user-provided content
    safe_title = html.escape(title)
    safe_description = html.escape(description or title)
    safe_author = html.escape(author or config.get('author', ''))
    safe_keywords = html.escape(keywords)
    
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="{theme}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{safe_description}">
    <title>{safe_title}</title>
    
    <!-- SEO Meta Tags -->
    <meta name="robots" content="index, follow">
    <meta name="author" content="{safe_author}">
    {f'<meta name="keywords" content="{safe_keywords}">' if keywords else ''}
    {f'<link rel="canonical" href="{html.escape(url, quote=True)}">' if url else ''}
    
    <!-- Open Graph -->
    <meta property="og:title" content="{safe_title}">
    <meta property="og:description" content="{safe_description}">
    <meta property="og:type" content="article">
    {f'<meta property="og:url" content="{html.escape(url, quote=True)}">' if url else ''}
    {f'<meta property="og:image" content="{html.escape(image_url, quote=True)}">' if image_url else ''}
    <meta property="article:published_time" content="{date}">
    {f'<meta property="article:author" content="{safe_author}">' if author else ''}
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{safe_title}">
    <meta name="twitter:description" content="{safe_description}">
    {f'<meta name="twitter:image" content="{html.escape(image_url, quote=True)}">' if image_url else ''}
    
    <link rel="stylesheet" href="../../assets/style.css">
    <link rel="stylesheet" href="../../assets/prism.css">
    <link rel="alternate" type="application/rss+xml" title="RSS Feed" href="../../rss.xml">
    {favicon_link(config, "../../")}

    <!-- Structured Data -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "{safe_title}",
        "description": "{safe_description}",
        "datePublished": "{date}",
        "dateModified": "{date}",
        {f'"image": "{html.escape(image_url, quote=True)}",' if image_url else ''}
        "author": {{
            "@type": "Person",
            "name": "{safe_author or config.get('author', 'Author')}"
        }},
        "publisher": {{
            "@type": "Person",
            "name": "{safe_author or config.get('author', 'Author')}"
        }},
        "mainEntityOfPage": {{
            "@type": "WebPage",
            "@id": "{html.escape(url, quote=True)}"
        }}
    }}
    </script>
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to content</a>
    <header>
        <nav>
            <a href="../../index.html">← Home</a>
        </nav>
    </header>
    <main id="main-content">
        <article>
            <h1>{safe_title}</h1>
            <div class="post-meta">
                <time datetime="{date}">{date}</time>
                {f' • <span class="reading-time">{reading_time} min read</span>' if reading_time else ''}
                {f' • <span class="author">{safe_author}</span>' if author else ''}
                {' • <span class="categories">' + ', '.join([f'<a href="../../categories/{html.escape(category_slug(cat), quote=True)}/">{html.escape(cat)}</a>' for cat in categories]) + '</span>' if categories else ''}
            </div>
            {toc}
            {content}
            {post_nav}
        </article>
    </main>
    <footer>
        <p>{config.get('footer_text_html', html.escape(config.get('footer_text', '')))}</p>
    </footer>

    <!-- Back to top button -->
    <button id="back-to-top" class="back-to-top" aria-label="Back to top" data-threshold="300">↑</button>

    <!-- Code copy functionality (runs first to set up DOM) -->
    <script src="../../assets/js/code-copy.js"></script>
    <!-- Prism.js for syntax highlighting -->
    <script src="../../assets/js/prism.js"></script>
    <!-- Back to top script -->
    <script>
    (function() {{
        var btn = document.getElementById('back-to-top');
        if (!btn) return;
        var threshold = parseInt(btn.dataset.threshold || '300', 10);
        window.addEventListener('scroll', function() {{
            btn.classList.toggle('visible', window.scrollY > threshold);
        }});
        btn.addEventListener('click', function() {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});
    }})();
    </script>
</body>
</html>"""

def index_template(posts, config, categories=None, pagination=None, post_prefix="posts"):
    """Generate HTML for the index page"""
    theme = config.get('theme', 'light')
    post_list = ""
    for post in posts:
        categories_html = ""
        if post.get('categories'):
            category_links = [f'<a href="categories/{html.escape(category_slug(cat), quote=True)}/">{html.escape(cat)}</a>' for cat in post['categories']]
            categories_html = f' • <span class="categories">{", ".join(category_links)}</span>'
        
        reading_time_html = f' • <span class="reading-time">{post.get("reading_time", 1)} min read</span>' if post.get("reading_time") else ''
        
        post_list += f"""
        <article class="post-preview">
            <h2><a href="{post_prefix + '/' + html.escape(post['filename'], quote=True) + '/' if post_prefix else html.escape(post['filename'], quote=True) + '/'}">{html.escape(post['title'])}</a></h2>
            <time datetime="{post['date']}">{post['date']}</time>{reading_time_html}{categories_html}
            {f"<p>{html.escape(post['description'])}</p>" if post.get('description') else ""}
        </article>"""
    
    # Build category navigation
    category_nav = ""
    if categories:
        category_items = []
        for category in categories:
            category_url = f"categories/{html.escape(category_slug(category), quote=True)}/"
            category_items.append(f'<a href="{category_url}">{html.escape(category)}</a>')
        
        category_nav = f'''<div class="dropdown">
            <button class="dropdown-toggle">Categories</button>
            <div class="dropdown-menu">
                {''.join(category_items)}
            </div>
        </div>
        <span class="nav-separator">|</span>'''
    
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="{theme}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{html.escape(config['site_description'])}">
    <title>{html.escape(config['site_title'])}</title>
    <link rel="stylesheet" href="assets/style.css">
    <link rel="alternate" type="application/rss+xml" title="RSS Feed" href="rss.xml">
    {favicon_link(config)}
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to content</a>
    <header>
        <h1>{html.escape(config['site_title'])}</h1>
        <nav>
            {category_nav}
            <a href="#" id="search-toggle">Search</a>
            <span class="nav-separator">|</span>
            <a href="rss.xml">RSS</a>
        </nav>
    </header>
    <main id="main-content">
        <section class="posts">
            {post_list}
        </section>
        {generate_pagination_html(pagination) if pagination else ''}
    </main>
    <footer>
        <p>{config.get('footer_text_html', html.escape(config.get('footer_text', '')))}</p>
    </footer>

    <!-- Search overlay -->
    <div id="search-overlay" class="search-overlay" role="dialog" aria-modal="true" aria-label="Search posts">
        <div class="search-container">
            <div class="search-header">
                <input type="text" id="search-input" class="search-input" placeholder="Search posts..." autocomplete="off" aria-label="Search query">
                <button id="search-close" class="search-close" aria-label="Close search">✕</button>
            </div>
            <div id="search-results" class="search-results" role="region" aria-live="polite">
                <p class="search-hint">Type at least 2 characters to search...</p>
            </div>
        </div>
    </div>

    <script src="/assets/js/dropdown.js"></script>
    <script src="/assets/js/search.js"></script>
</body>
</html>"""

def category_template(category_name, posts, config, pagination=None, post_prefix="posts"):
    """Generate HTML for a category page"""
    theme = config.get('theme', 'light')
    post_list = ""
    for post in posts:
        reading_time_html = f' • <span class="reading-time">{post.get("reading_time", 1)} min read</span>' if post.get("reading_time") else ''
        
        post_list += f"""
        <article class="post-preview">
            <h2><a href="{'../../' + post_prefix + '/' + html.escape(post['filename'], quote=True) + '/' if post_prefix else '../../' + html.escape(post['filename'], quote=True) + '/'}">{html.escape(post['title'])}</a></h2>
            <time datetime="{post['date']}">{post['date']}</time>{reading_time_html}
            {f"<p>{html.escape(post['description'])}</p>" if post.get('description') else ""}
        </article>"""
    
    safe_category = html.escape(category_name)
    
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="{theme}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Posts in {safe_category} category">
    <title>{safe_category} - {html.escape(config['site_title'])}</title>
    <link rel="stylesheet" href="../../assets/style.css">
    <link rel="alternate" type="application/rss+xml" title="RSS Feed" href="../../rss.xml">
    {favicon_link(config, "../../")}
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to content</a>
    <header>
        <nav>
            <a href="../../index.html">← Home</a>
        </nav>
    </header>
    <main id="main-content">
        <h1>Category: {safe_category}</h1>
        <section class="posts">
            {post_list}
        </section>
        {generate_pagination_html(pagination, pagination.get('category_slug') if pagination else None) if pagination else ''}
    </main>
    <footer>
        <p>{config.get('footer_text_html', html.escape(config.get('footer_text', '')))}</p>
    </footer>
</body>
</html>"""
def error_404_template(config):
    """Generate HTML for 404 error page"""
    theme = config.get('theme', 'light')

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="{theme}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Page not found">
    <title>404 - Page Not Found | {html.escape(config['site_title'])}</title>
    <link rel="stylesheet" href="/assets/style.css">
    <link rel="alternate" type="application/rss+xml" title="RSS Feed" href="/rss.xml">
    <base href="/">
    {favicon_link(config, "/")}

    <style>
        .error-page {{
            text-align: center;
            padding: 4rem 2rem;
            max-width: 600px;
            margin: 0 auto;
        }}
        .error-code {{
            font-size: 8rem;
            font-weight: bold;
            color: var(--muted-foreground);
            line-height: 1;
            margin-bottom: 1rem;
        }}
        .error-title {{
            font-size: 2rem;
            margin-bottom: 1rem;
            color: var(--foreground);
        }}
        .error-description {{
            font-size: 1.1rem;
            color: var(--muted-foreground);
            margin-bottom: 2rem;
            line-height: 1.6;
        }}
        .error-actions {{
            display: flex;
            gap: 1rem;
            justify-content: center;
            flex-wrap: wrap;
        }}
        .error-actions a {{
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: var(--primary);
            color: var(--primary-foreground);
            text-decoration: none;
            border-radius: var(--radius);
            transition: background-color 0.2s, opacity 0.2s;
        }}
        .error-actions a:hover {{
            opacity: 0.9;
        }}
        .error-actions a.secondary {{
            background: transparent;
            border: 1px solid var(--border);
            color: var(--foreground);
        }}
        .error-actions a.secondary:hover {{
            background: var(--muted);
            opacity: 1;
        }}
    </style>
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to content</a>
    <header>
        <nav>
            <a href="/">← Home</a>
        </nav>
    </header>
    <main id="main-content">
        <div class="error-page">
            <div class="error-code">404</div>
            <h1 class="error-title">Page Not Found</h1>
            <p class="error-description">
                The page you're looking for doesn't exist. It might have been moved, deleted, or you entered the wrong URL.
            </p>
            <div class="error-actions">
                <a href="/">← Back to Home</a>
                <a href="#" id="search-toggle" class="secondary">Search Posts</a>
            </div>
        </div>
    </main>
    <footer>
        <p>{config.get('footer_text_html', html.escape(config.get('footer_text', '')))}</p>
    </footer>

    <!-- Search overlay -->
    <div id="search-overlay" class="search-overlay" role="dialog" aria-modal="true" aria-label="Search posts">
        <div class="search-container">
            <div class="search-header">
                <input type="text" id="search-input" class="search-input" placeholder="Search posts..." autocomplete="off" aria-label="Search query">
                <button id="search-close" class="search-close" aria-label="Close search">✕</button>
            </div>
            <div id="search-results" class="search-results" role="region" aria-live="polite">
                <p class="search-hint">Type at least 2 characters to search...</p>
            </div>
        </div>
    </div>

    <script src="/assets/js/dropdown.js"></script>
    <script src="/assets/js/search.js"></script>
</body>
</html>"""
