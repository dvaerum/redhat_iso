"""
CLI interface for Red Hat ISO Download Tool.
"""

import argparse
import sys
from pathlib import Path

from .api import RedHatAPI


def load_token(token_file: str = "redhat-api-token.txt") -> str:
    """Load offline token from file."""
    token_path = Path(token_file)

    if not token_path.exists():
        print(f"Error: Token file not found: {token_file}", file=sys.stderr)
        print()
        print("Please create a file named 'redhat-api-token.txt' with your Red Hat API offline token.")
        print("You can generate a token at: https://access.redhat.com/management/api")
        sys.exit(1)

    token = token_path.read_text().strip()

    if not token:
        print(f"Error: Token file is empty: {token_file}", file=sys.stderr)
        sys.exit(1)

    return token


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Red Hat ISO Download Tool - List and download Red Hat ISO files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list
  %(prog)s list --version 9.6 --arch x86_64
  %(prog)s --json list
  %(prog)s --json list --version 9.6 --arch x86_64
  %(prog)s download <checksum>
  %(prog)s download rhel-9.6-x86_64-dvd.iso --by-filename
  %(prog)s --json download <checksum>

Getting Started:
  1. Generate an offline token at: https://access.redhat.com/management/api
  2. Save the token to redhat-api-token.txt
  3. List available ISOs: %(prog)s list
  4. Download by checksum: %(prog)s download <checksum>
     Or by filename: %(prog)s download rhel-9.6-x86_64-dvd.iso --by-filename
        """
    )

    parser.add_argument(
        '--token-file',
        default='redhat-api-token.txt',
        help='Path to file containing Red Hat API offline token (default: redhat-api-token.txt)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List command
    list_parser = subparsers.add_parser('list', help='List available ISO downloads')
    list_parser.add_argument(
        '--version',
        help='RHEL version (e.g., 9.6, 8.10, 7.9)'
    )
    list_parser.add_argument(
        '--arch',
        help='Architecture (e.g., x86_64, aarch64, ppc64le, s390x)'
    )
    list_parser.add_argument(
        '--content-set',
        help='Content set name (e.g., rhel-9-for-x86_64-baseos-isos)'
    )

    # Download command
    download_parser = subparsers.add_parser('download', help='Download an ISO by checksum or filename')
    download_parser.add_argument(
        'identifier',
        help='SHA-256 checksum or filename of the file to download'
    )
    download_parser.add_argument(
        '--output',
        default='.',
        help='Output directory for downloaded file (default: current directory)'
    )
    download_parser.add_argument(
        '--by-filename',
        action='store_true',
        help='Treat the identifier as a filename instead of checksum'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load token and initialize API client
    token = load_token(args.token_file)
    api = RedHatAPI(token)

    # Execute command
    if args.command == 'list':
        api.list_downloads(
            version=args.version,
            arch=args.arch,
            content_set=args.content_set,
            json_output=args.json
        )

    elif args.command == 'download':
        api.download_file(args.identifier, args.output, args.by_filename, args.json)


if __name__ == '__main__':
    main()
