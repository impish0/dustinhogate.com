#!/usr/bin/env python3
"""Generate sitemap.xml for better SEO"""
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_sitemap(posts, config):
    """Generate sitemap.xml from posts"""
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Get post URL configuration
    post_prefix = config.get('post_url_prefix', '/posts').strip('/')
    post_url_path = f'{post_prefix}/' if post_prefix else ''
    
    # Add homepage - ElementTree automatically escapes XML special characters
    url = ET.SubElement(urlset, "url")
    ET.SubElement(url, "loc").text = config['site_url']
    ET.SubElement(url, "lastmod").text = datetime.now().strftime("%Y-%m-%d")
    ET.SubElement(url, "changefreq").text = "daily"
    ET.SubElement(url, "priority").text = "1.0"
    
    # Add posts
    for post in posts:
        url = ET.SubElement(urlset, "url")
        # ElementTree automatically escapes XML special characters
        ET.SubElement(url, "loc").text = f"{config['site_url']}/{post_url_path}{post['filename']}"
        ET.SubElement(url, "lastmod").text = post['date']
        ET.SubElement(url, "changefreq").text = "monthly"
        ET.SubElement(url, "priority").text = "0.8"
    
    # Add category pages
    categories = {}
    for post in posts:
        for category in post.get('categories', []):
            categories[category] = True
    
    for category in categories:
        url = ET.SubElement(urlset, "url")
        category_slug = category.lower().replace(' ', '-')
        ET.SubElement(url, "loc").text = f"{config['site_url']}/categories/{category_slug}.html"
        ET.SubElement(url, "lastmod").text = datetime.now().strftime("%Y-%m-%d")
        ET.SubElement(url, "changefreq").text = "weekly"
        ET.SubElement(url, "priority").text = "0.6"
    
    # Pretty print XML
    rough_string = ET.tostring(urlset, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")