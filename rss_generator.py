#!/usr/bin/env python3
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import html

def generate_rss(posts, blog_title, blog_url, blog_description, timezone="+0000", post_prefix="", rss_full_content=True):
    """Generate RSS feed from posts"""
    # Add content namespace for full content support
    rss = ET.Element("rss", version="2.0", attrib={
        "xmlns:content": "http://purl.org/rss/1.0/modules/content/"
    })
    channel = ET.SubElement(rss, "channel")
    
    # Channel metadata - XML escaping is handled by ElementTree
    ET.SubElement(channel, "title").text = blog_title
    ET.SubElement(channel, "link").text = blog_url
    ET.SubElement(channel, "description").text = blog_description
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now().strftime(f"%a, %d %b %Y %H:%M:%S {timezone}")
    
    # Add posts
    post_url_path = f'{post_prefix}/' if post_prefix else ''
    for post in posts[:10]:  # Latest 10 posts
        item = ET.SubElement(channel, "item")
        # ElementTree automatically escapes XML special characters
        ET.SubElement(item, "title").text = post['title']
        ET.SubElement(item, "link").text = f"{blog_url}/{post_url_path}{post['filename']}/"
        ET.SubElement(item, "description").text = post.get('description', post['title'])
        ET.SubElement(item, "pubDate").text = format_rss_date(post['date'], timezone)
        ET.SubElement(item, "guid").text = f"{blog_url}/{post_url_path}{post['filename']}/"
        
        # Add full content if enabled
        if rss_full_content and 'content' in post:
            content_encoded = ET.SubElement(item, "{http://purl.org/rss/1.0/modules/content/}encoded")
            content_encoded.text = post['content']
    
    # Pretty print XML
    rough_string = ET.tostring(rss, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def format_rss_date(date_str, timezone="+0000"):
    """Convert YYYY-MM-DD to RSS date format"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime(f"%a, %d %b %Y 00:00:00 {timezone}")
    except ValueError:
        return datetime.now().strftime(f"%a, %d %b %Y %H:%M:%S {timezone}")