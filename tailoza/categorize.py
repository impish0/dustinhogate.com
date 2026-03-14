#!/usr/bin/env python3
"""
Analyze posts and suggest categories based on content
Part of Tailoza static site generator
"""

import os
import json
from pathlib import Path

# Default category rules - can be customized in config
DEFAULT_CATEGORY_RULES = {
    "Business": ["business", "entrepreneur", "customer", "revenue", "sales", "marketing", "startup", "company", "profit", "scale", "growth"],
    "Technology": ["website", "online", "digital", "tech", "software", "app", "platform", "code", "internet", "api", "database"],
    "Marketing": ["marketing", "email", "leads", "conversion", "campaign", "audience", "content", "seo", "traffic", "brand"],
    "Development": ["code", "programming", "javascript", "python", "css", "html", "framework", "library", "git", "deploy"],
    "Design": ["design", "ui", "ux", "color", "font", "layout", "visual", "aesthetic", "style", "theme"],
    "Personal": ["personal", "life", "experience", "story", "journey", "lesson", "reflection", "growth", "mindset"],
    "Tutorial": ["how to", "guide", "tutorial", "step by step", "learn", "build", "create", "setup", "configure"],
    "News": ["announce", "release", "update", "new", "launch", "introduce", "available", "version"],
}

def load_category_rules():
    """Load custom category rules from config or use defaults"""
    config_path = Path('category_rules.json')
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_CATEGORY_RULES

def analyze_post_content(content, rules):
    """Analyze content and suggest categories"""
    content_lower = content.lower()
    
    # Count keyword matches for each category
    category_scores = {}
    for category, keywords in rules.items():
        score = sum(content_lower.count(keyword) for keyword in keywords)
        if score > 0:
            category_scores[category] = score
    
    # Sort by score and take top categories
    sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Take up to 3 categories with significant presence
    categories = []
    for cat, score in sorted_categories[:3]:
        if score >= 3:  # Require at least 3 keyword occurrences
            categories.append(cat)
    
    return categories if categories else ["General"]

def get_existing_categories(content):
    """Extract existing categories from front matter"""
    try:
        parts = content.split('---', 2)
        if len(parts) >= 3:
            front_matter = parts[1]
            for line in front_matter.split('\n'):
                if line.strip().startswith('categories:'):
                    cats = line.split(':', 1)[1].strip()
                    return [c.strip() for c in cats.split(',')]
    except:
        pass
    return []

def suggest_categories(posts_dir='posts', update=False):
    """Analyze posts and suggest categories"""
    rules = load_category_rules()
    suggestions = []
    
    for filename in os.listdir(posts_dir):
        if filename.endswith('.md') and not filename.startswith('_'):
            filepath = os.path.join(posts_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            existing = get_existing_categories(content)
            suggested = analyze_post_content(content, rules)
            
            suggestions.append({
                'file': filename,
                'existing': existing,
                'suggested': suggested,
                'needs_update': existing != suggested
            })
            
            if update and existing != suggested:
                # Update the file
                updated_content = update_front_matter(content, suggested)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
    
    return suggestions

def update_front_matter(content, categories):
    """Update categories in front matter"""
    parts = content.split('---', 2)
    if len(parts) < 3:
        return content
    
    front_matter = parts[1].strip()
    post_content = parts[2]
    
    # Update or add categories
    fm_lines = []
    has_categories = False
    
    for line in front_matter.split('\n'):
        if line.strip().startswith('categories:'):
            fm_lines.append(f"categories: {', '.join(categories)}")
            has_categories = True
        else:
            fm_lines.append(line)
    
    # Add if missing (after author line)
    if not has_categories:
        for i, line in enumerate(fm_lines):
            if line.strip().startswith('author:'):
                fm_lines.insert(i + 1, f"categories: {', '.join(categories)}")
                break
    
    return f"---\n{chr(10).join(fm_lines)}\n---{post_content}"

def main():
    """CLI interface for categorization"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze and categorize blog posts')
    parser.add_argument('--update', action='store_true', help='Update files with suggested categories')
    parser.add_argument('--posts', default='posts', help='Posts directory (default: posts)')
    parser.add_argument('--rules', help='Custom category rules JSON file')
    
    args = parser.parse_args()
    
    if args.rules:
        # Load custom rules
        global DEFAULT_CATEGORY_RULES
        with open(args.rules, 'r') as f:
            DEFAULT_CATEGORY_RULES = json.load(f)
    
    suggestions = suggest_categories(args.posts, args.update)
    
    # Display results
    print(f"Analyzed {len(suggestions)} posts\n")
    
    for s in suggestions:
        print(f"{s['file']}")
        if s['existing']:
            print(f"  Current: {', '.join(s['existing'])}")
        print(f"  Suggested: {', '.join(s['suggested'])}")
        if s['needs_update']:
            print("  ✓ Needs update" if args.update else "  → Would update")
        print()
    
    if args.update:
        updated = sum(1 for s in suggestions if s['needs_update'])
        print(f"Updated {updated} posts with new categories")
    else:
        needs_update = sum(1 for s in suggestions if s['needs_update'])
        if needs_update:
            print(f"\n{needs_update} posts need category updates. Run with --update to apply.")

if __name__ == '__main__':
    main()