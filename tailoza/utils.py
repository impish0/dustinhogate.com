#!/usr/bin/env python3
"""Shared utility functions for the static site generator"""
import shutil
from pathlib import Path


def category_slug(name):
    """Convert category name to URL-safe slug"""
    return name.lower().replace(' ', '-')


def favicon_link(config, prefix=""):
    """Generate favicon link tag based on config"""
    favicon = config.get('favicon')
    if not favicon:
        return ''

    mime_types = {
        'ico': 'image/x-icon',
        'png': 'image/png',
        'svg': 'image/svg+xml'
    }
    ext = favicon.rsplit('.', 1)[-1] if '.' in favicon else ''
    mime_type = mime_types.get(ext, f'image/{ext}')

    return f'<link rel="icon" type="{mime_type}" href="{prefix}{favicon}">'


def copy_asset(src, dest, errors, label=None):
    """Copy a file if it exists, logging errors to the provided list.

    Args:
        src: Path object for source file
        dest: Destination path string or Path
        errors: List to append error messages to
        label: Optional label for logging (defaults to filename)

    Returns:
        True if file was copied successfully, False otherwise
    """
    if not src.exists():
        return False

    try:
        shutil.copy2(src, dest)
        print(f"✓ Copied {label or src.name}")
        return True
    except Exception as e:
        errors.append(f"Failed to copy {label or src.name}: {e}")
        return False
