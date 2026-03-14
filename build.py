#!/usr/bin/env python3
"""Build script for Tailoza static site generator"""
import sys

try:
    from tailoza.builder import build_site
except ImportError as e:
    print(f"Error: Could not import tailoza package: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

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
