# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is dustinhogate.com, a static blog site built with a custom Python static site generator. The site generates clean HTML from Markdown posts with support for categories, pagination, RSS feeds, sitemaps, and client-side search.

## Core Architecture

- **Static Site Generator**: Python-based system that converts Markdown posts to HTML
- **Template System**: HTML templates with dynamic content injection (templates.py)
- **Markdown Parser**: Custom parser with support for frontmatter, code blocks, tables, TOC (parser.py)
- **Build System**: Automated build process that generates the complete site (build.py)
- **Development Server**: Local server with live reload on file changes (serve.py)

## Key Components

- `build.py` - Main build script that orchestrates the entire site generation
- `parser.py` - Markdown to HTML conversion with frontmatter parsing
- `templates.py` - HTML template functions for different page types
- `serve.py` - Development server with file watching and auto-rebuild
- `config.json` - Site configuration including title, URL, analytics, theming
- `posts/` - Markdown blog posts with frontmatter metadata
- `assets/` - CSS, JavaScript, and static assets
- `images/` - Blog post images and media files
- `output/` - Generated static site (created during build)

## Common Development Commands

### Build the site
```bash
python build.py
```

### Start development server with live reload
```bash
python serve.py
```
The server runs on http://localhost:8000 and automatically rebuilds on file changes.

### Generate RSS feed
RSS is automatically generated during the build process and saved as `output/rss.xml`

### Generate sitemap
Sitemap is automatically generated during the build process and saved as `output/sitemap.xml`

## Content Structure

### Blog Posts
- Posts are Markdown files in the `posts/` directory
- Each post supports frontmatter with metadata:
  ```yaml
  ---
  title: Post Title
  description: Brief description
  date: YYYY-MM-DD
  categories: category1, category2
  author: Author Name
  image: image-filename.jpg
  keywords: keyword1, keyword2
  toc: true
  ---
  ```
- Images should be placed in the `images/` directory
- Posts starting with `_` are treated as drafts and excluded from builds

### Categories
- Categories are automatically extracted from post frontmatter
- Category pages are generated with pagination support
- Categories use URL-friendly slugs (lowercase, spaces replaced with hyphens)

### URL Structure
- Posts: `/{post-slug}/` (clean URLs with trailing slashes)
- Categories: `/categories/{category-slug}/`
- Pagination: `/page/{number}/` for index, `/categories/{category-slug}/{number}/` for categories

## Configuration

The `config.json` file controls site-wide settings:
- `site_title`, `site_url`, `site_description` - Basic site info
- `author` - Default author name
- `footer_text` - Footer content (supports HTML links)
- `posts_per_page` - Pagination setting
- `post_url_prefix` - URL prefix for posts (currently "/")
- `plausible_domain`, `plausible_options` - Analytics configuration
- `theme` - Theme setting (currently "dark")

## Features

- **Clean URLs**: Directory-based URLs without .html extensions
- **Responsive Design**: Mobile-friendly CSS with dark theme
- **SEO Optimized**: Meta tags, structured data, sitemap generation
- **Analytics**: Plausible Analytics integration
- **Search**: Client-side search with generated JSON index
- **Code Highlighting**: Prism.js integration for syntax highlighting
- **Table of Contents**: Automatic TOC generation for posts with `toc: true`
- **Reading Time**: Automatic calculation based on word count
- **Download Detection**: Automatic download icons for file links

## File Processing

- **Markdown Processing**: Custom parser handles headers, lists, code blocks, tables, blockquotes, task lists
- **Image Handling**: Automatic path correction for local images, lazy loading
- **Asset Copying**: Automatic copying of CSS, JS, images, and favicon during build
- **HTML Processing**: Safe HTML processing in config text with link preservation

## Development Notes

- The site uses a custom static site generator rather than external frameworks
- All HTML is generated from templates in templates.py
- The parser.py handles Markdown conversion with performance optimizations
- File watching in serve.py monitors posts/, assets/, images/, and core Python files
- The build process is atomic - either succeeds completely or fails cleanly