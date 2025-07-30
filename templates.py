#!/usr/bin/env python3
import html

def generate_pagination_html(pagination, base_url=''):
    """Generate pagination navigation HTML"""
    if not pagination or pagination['total_pages'] <= 1:
        return ''
    
    current = pagination['current_page']
    total = pagination['total_pages']
    
    # Build pagination URLs
    def page_url(page_num):
        if base_url:
            # For category pages (categories/name/index.html structure)
            if page_num == 1:
                return "../" 
            else:
                return f"../../page/{page_num}/" if current == 1 else f"../{page_num}/"
        else:
            # For index pages (page/N/index.html structure)
            if page_num == 1:
                return "../../index.html" if current > 1 else "index.html"
            else:
                return f"../../page/{page_num}/" if current == 1 else f"../{page_num}/"
    
    html_parts = ['<nav class="pagination">']
    
    # Previous button
    if pagination['has_prev']:
        html_parts.append(f'<a href="{page_url(pagination["prev_page"])}" class="pagination-prev">← Previous</a>')
    else:
        html_parts.append('<span class="pagination-prev disabled">← Previous</span>')
    
    # Page numbers
    html_parts.append('<div class="pagination-numbers">')
    
    # Show page numbers with ellipsis for many pages
    if total <= 7:
        # Show all pages
        for i in range(1, total + 1):
            if i == current:
                html_parts.append(f'<span class="pagination-current">{i}</span>')
            else:
                html_parts.append(f'<a href="{page_url(i)}">{i}</a>')
    else:
        # Show first, last, and pages around current
        if current <= 3:
            # Near beginning
            for i in range(1, 5):
                if i == current:
                    html_parts.append(f'<span class="pagination-current">{i}</span>')
                else:
                    html_parts.append(f'<a href="{page_url(i)}">{i}</a>')
            html_parts.append('<span class="pagination-ellipsis">…</span>')
            html_parts.append(f'<a href="{page_url(total)}">{total}</a>')
        elif current >= total - 2:
            # Near end
            html_parts.append(f'<a href="{page_url(1)}">1</a>')
            html_parts.append('<span class="pagination-ellipsis">…</span>')
            for i in range(total - 3, total + 1):
                if i == current:
                    html_parts.append(f'<span class="pagination-current">{i}</span>')
                else:
                    html_parts.append(f'<a href="{page_url(i)}">{i}</a>')
        else:
            # Middle
            html_parts.append(f'<a href="{page_url(1)}">1</a>')
            html_parts.append('<span class="pagination-ellipsis">…</span>')
            for i in range(current - 1, current + 2):
                if i == current:
                    html_parts.append(f'<span class="pagination-current">{i}</span>')
                else:
                    html_parts.append(f'<a href="{page_url(i)}">{i}</a>')
            html_parts.append('<span class="pagination-ellipsis">…</span>')
            html_parts.append(f'<a href="{page_url(total)}">{total}</a>')
    
    html_parts.append('</div>')
    
    # Next button
    if pagination['has_next']:
        html_parts.append(f'<a href="{page_url(pagination["next_page"])}" class="pagination-next">Next →</a>')
    else:
        html_parts.append('<span class="pagination-next disabled">Next →</span>')
    
    html_parts.append('</nav>')
    
    return '\n'.join(html_parts)

def post_template(title, content, date, description="", keywords="", author="", image="", toc="", url="", config={}, categories=[], reading_time=0, post_prefix="posts"):
    """Generate HTML for a blog post with enhanced SEO"""
    theme = config.get('theme', 'light')
    
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
    {f'<link rel="icon" type="image/x-icon" href="../../favicon.ico">' if config.get('favicon') == 'favicon.ico' else ''}
    {f'<link rel="icon" type="image/png" href="../../favicon.png">' if config.get('favicon') == 'favicon.png' else ''}
    {f'<link rel="icon" type="image/svg+xml" href="../../favicon.svg">' if config.get('favicon') == 'favicon.svg' else ''}
    
    <!-- Plausible Analytics -->
    {f'<script defer data-domain="{html.escape(config["plausible_domain"], quote=True)}" src="{config.get("plausible_script_url", "https://plausible.io/js/script.js")}"></script>' if config.get('plausible_domain') else ''}
    
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
    <header>
        <nav>
            <a href="../../index.html">← Home</a>
        </nav>
    </header>
    <main>
        <article>
            <h1>{safe_title}</h1>
            <div class="post-meta">
                <time datetime="{date}">{date}</time>
                {f' • <span class="reading-time">{reading_time} min read</span>' if reading_time else ''}
                {f' • <span class="author">{safe_author}</span>' if author else ''}
                {' • <span class="categories">' + ', '.join([f'<a href="../../categories/{html.escape(cat.lower().replace(" ", "-"), quote=True)}/">{html.escape(cat)}</a>' for cat in categories]) + '</span>' if categories else ''}
            </div>
            {toc}
            {content}
        </article>
    </main>
    <footer>
        <p>© {date[:4]} | <a href="../../rss.xml">RSS</a></p>
    </footer>
    
    <!-- Prism.js for syntax highlighting -->
    <script src="../../assets/js/prism.js"></script>
    <!-- Code copy functionality -->
    <script src="../../assets/js/code-copy.js"></script>
</body>
</html>"""

def index_template(posts, config, categories=None, pagination=None, post_prefix="posts"):
    """Generate HTML for the index page"""
    theme = config.get('theme', 'light')
    post_list = ""
    for post in posts:
        categories_html = ""
        if post.get('categories'):
            category_links = [f'<a href="categories/{html.escape(cat.lower().replace(" ", "-"), quote=True)}/">{html.escape(cat)}</a>' for cat in post['categories']]
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
            category_url = f"categories/{html.escape(category.lower().replace(' ', '-'), quote=True)}/"
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
    {f'<link rel="icon" type="image/x-icon" href="favicon.ico">' if config.get('favicon') == 'favicon.ico' else ''}
    {f'<link rel="icon" type="image/png" href="favicon.png">' if config.get('favicon') == 'favicon.png' else ''}
    {f'<link rel="icon" type="image/svg+xml" href="favicon.svg">' if config.get('favicon') == 'favicon.svg' else ''}
    
    <!-- Plausible Analytics -->
    {f'<script defer data-domain="{html.escape(config["plausible_domain"], quote=True)}" src="{config.get("plausible_script_url", "https://plausible.io/js/script.js")}"></script>' if config.get('plausible_domain') else ''}
</head>
<body>
    <header>
        <h1>{html.escape(config['site_title'])}</h1>
        <nav>
            {category_nav}
            <a href="#" id="search-toggle">Search</a>
            <span class="nav-separator">|</span>
            <a href="rss.xml">RSS</a>
        </nav>
    </header>
    <main>
        <section class="posts">
            {post_list}
        </section>
        {generate_pagination_html(pagination) if pagination else ''}
    </main>
    <footer>
        <p>{config.get('footer_text_html', html.escape(config.get('footer_text', '')))}</p>
    </footer>
    
    <!-- Search overlay -->
    <div id="search-overlay" class="search-overlay">
        <div class="search-container">
            <div class="search-header">
                <input type="text" id="search-input" class="search-input" placeholder="Search posts..." autocomplete="off">
                <button id="search-close" class="search-close">✕</button>
            </div>
            <div id="search-results" class="search-results">
                <p class="search-hint">Type at least 2 characters to search...</p>
            </div>
        </div>
    </div>
    
    <script src="assets/js/search.js"></script>
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
    {f'<link rel="icon" type="image/x-icon" href="../../favicon.ico">' if config.get('favicon') == 'favicon.ico' else ''}
    {f'<link rel="icon" type="image/png" href="../../favicon.png">' if config.get('favicon') == 'favicon.png' else ''}
    {f'<link rel="icon" type="image/svg+xml" href="../../favicon.svg">' if config.get('favicon') == 'favicon.svg' else ''}
    
    <!-- Plausible Analytics -->
    {f'<script defer data-domain="{html.escape(config["plausible_domain"], quote=True)}" src="{config.get("plausible_script_url", "https://plausible.io/js/script.js")}"></script>' if config.get('plausible_domain') else ''}
</head>
<body>
    <header>
        <nav>
            <a href="../../index.html">← Home</a>
        </nav>
    </header>
    <main>
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
    <link rel="stylesheet" href="assets/style.css">
    <link rel="alternate" type="application/rss+xml" title="RSS Feed" href="rss.xml">
    {f'<link rel="icon" type="image/x-icon" href="favicon.ico">' if config.get('favicon') == 'favicon.ico' else ''}
    {f'<link rel="icon" type="image/png" href="favicon.png">' if config.get('favicon') == 'favicon.png' else ''}
    {f'<link rel="icon" type="image/svg+xml" href="favicon.svg">' if config.get('favicon') == 'favicon.svg' else ''}
    
    <!-- Plausible Analytics -->
    {f'<script defer data-domain="{html.escape(config["plausible_domain"], quote=True)}" src="{config.get("plausible_script_url", "https://plausible.io/js/script.js")}"></script>' if config.get('plausible_domain') else ''}
    
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
            color: var(--text-muted);
            line-height: 1;
            margin-bottom: 1rem;
        }}
        .error-title {{
            font-size: 2rem;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }}
        .error-description {{
            font-size: 1.1rem;
            color: var(--text-secondary);
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
            color: white;
            text-decoration: none;
            border-radius: 6px;
            transition: background-color 0.2s;
        }}
        .error-actions a:hover {{
            background: var(--primary-dark);
        }}
        .error-actions a.secondary {{
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-primary);
        }}
        .error-actions a.secondary:hover {{
            background: var(--background-secondary);
        }}
    </style>
</head>
<body>
    <header>
        <nav>
            <a href="index.html">← Home</a>
        </nav>
    </header>
    <main>
        <div class="error-page">
            <div class="error-code">404</div>
            <h1 class="error-title">Page Not Found</h1>
            <p class="error-description">
                The page you're looking for doesn't exist. It might have been moved, deleted, or you entered the wrong URL.
            </p>
            <div class="error-actions">
                <a href="index.html">← Back to Home</a>
                <a href="#" id="search-toggle" class="secondary">Search Posts</a>
            </div>
        </div>
    </main>
    <footer>
        <p>{config.get('footer_text_html', html.escape(config.get('footer_text', '')))}</p>
    </footer>
    
    <!-- Search overlay -->
    <div id="search-overlay" class="search-overlay">
        <div class="search-container">
            <div class="search-header">
                <input type="text" id="search-input" class="search-input" placeholder="Search posts..." autocomplete="off">
                <button id="search-close" class="search-close">✕</button>
            </div>
            <div id="search-results" class="search-results">
                <p class="search-hint">Type at least 2 characters to search...</p>
            </div>
        </div>
    </div>
    
    <script src="assets/js/search.js"></script>
</body>
</html>"""
