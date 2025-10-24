#!/usr/bin/env python3
"""Validate Staging File

Validates staging file JSON syntax and schema.

Usage:
    python3 scripts/validate_staging.py [staging_file]

Examples:
    # Validate default staging file
    python3 scripts/validate_staging.py

    # Validate custom file
    python3 scripts/validate_staging.py etc/staging/custom_staging.json
"""

import argparse
import sys
from pathlib import Path

from staging_validator import validate_staging_file


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Validate staging file JSON syntax and schema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate default staging file
  %(prog)s

  # Validate custom file
  %(prog)s etc/staging/custom_staging.json
        """
    )

    parser.add_argument(
        'file',
        nargs='?',
        default='etc/staging/tweets_staging.json',
        help='Path to staging file (default: etc/staging/tweets_staging.json)'
    )

    args = parser.parse_args()

    # Validate file
    is_valid, errors = validate_staging_file(args.file)

    if is_valid:
        print(f"✓ Staging file is valid: {args.file}")
        sys.exit(0)
    else:
        print(f"✗ Staging file validation failed: {args.file}\n", file=sys.stderr)
        print("Errors found:", file=sys.stderr)
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
