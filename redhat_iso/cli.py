"""
CLI interface for Red Hat ISO Download Tool.
"""

import argparse
import json
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


def format_list_output(result: dict, json_output: bool = False) -> None:
    """Format and print list command output."""
    if json_output:
        # JSON output
        if result["type"] == "content_set":
            output = {
                "content_set": result["content_set"],
                "images": result["images"]
            }
        elif result["type"] == "version_arch":
            output = {
                "version": result["version"],
                "architecture": result["architecture"],
                "images": result["images"]
            }
        else:  # default
            output = {
                "releases": result["releases"]
            }
        print(json.dumps(output, indent=2))
        return

    # Text output
    if result["type"] == "content_set":
        print("Fetching available downloads from Red Hat Customer Portal...")
        print()

        images = result["images"]
        content_set = result["content_set"]

        if not images:
            print(f"No images found for content set: {content_set}")
            return

        print(f"Available images in content set '{content_set}':")
        print()
        for img in images:
            filename = img.get('filename', 'N/A')
            checksum = img.get('checksum', 'N/A')
            date = img.get('datePublished', 'N/A')
            arch_info = img.get('arch', 'N/A')

            print(f"  {filename}")
            print(f"    Architecture: {arch_info}")
            print(f"    Checksum: {checksum}")
            print(f"    Published: {date}")
            print()

    elif result["type"] == "version_arch":
        print("Fetching available downloads from Red Hat Customer Portal...")
        print()

        images = result["images"]
        version = result["version"]
        arch = result["architecture"]

        if not images:
            print(f"No images found for RHEL {version} ({arch})")
            print()
            print("Try different version/arch combinations. Examples:")
            print("  redhat_iso list --version 9.6 --arch x86_64")
            print("  redhat_iso list --version 8.10 --arch aarch64")
            return

        print(f"Available images for RHEL {version} ({arch}):")
        print()
        for img in images:
            filename = img.get('filename', 'N/A')
            checksum = img.get('checksum', 'N/A')
            date = img.get('datePublished', 'N/A')
            image_name = img.get('imageName', 'N/A')

            print(f"  {image_name}")
            print(f"    Filename: {filename}")
            print(f"    Checksum: {checksum}")
            print(f"    Published: {date}")
            print()

    else:  # default
        print("Fetching currently supported RHEL releases for x86_64...")
        print()

        for release in result["releases"]:
            ver = release["version"]
            arch = release["architecture"]
            images = release["images"]

            print(f"═══ RHEL {ver} ({arch}) ═══")
            print()
            for img in images:
                filename = img.get('filename', 'N/A')
                checksum = img.get('checksum', 'N/A')
                image_name = img.get('imageName', 'N/A')

                print(f"  {image_name}")
                print(f"    Filename: {filename}")
                print(f"    Checksum: {checksum}")
                print()
            print()

        print("For other versions or architectures, use:")
        print("  redhat_iso list --version <version> --arch <arch>")
        print()
        print("Common versions: 9.6, 9.5, 9.4, 8.10, 8.9, 7.9")
        print("Common architectures: x86_64, aarch64, ppc64le, s390x")


def format_download_output(result: dict, json_output: bool = False) -> None:
    """Format and print download command success output."""
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print()
        print("Download complete!")
        print(f"  File: {result['filename']}")
        print(f"  Path: {result['path']}")
        print(f"  Size: {result['size']:,} bytes")
        print(f"  Checksum: {result['checksum']}")
        print(f"  Verified: {result['verified']}")


def create_progress_callback(json_output: bool):
    """Create a progress callback for downloads."""
    if json_output:
        # No progress output in JSON mode
        return None

    # Only show progress bar when output is to a TTY
    # (prevents garbled output when redirecting to files or pipes)
    if not sys.stdout.isatty():
        return None

    def show_progress(downloaded: int, total: int) -> None:
        """Display download progress."""
        if total > 0:
            percent = (downloaded / total) * 100
            bar_length = 50
            filled = int(bar_length * downloaded / total)
            bar = '=' * filled + '-' * (bar_length - filled)

            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)

            print(f"\r  Progress: [{bar}] {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)",
                  end='', flush=True)

    return show_progress


def create_message_callback(json_output: bool):
    """Create a message callback."""
    if json_output:
        # No message output in JSON mode
        return None

    def show_message(message: str) -> None:
        """Display a message."""
        print(message, flush=True)

    return show_message


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
    try:
        token = load_token(args.token_file)
        api = RedHatAPI(token)
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Execute command
    try:
        if args.command == 'list':
            result = api.list_downloads(
                version=args.version,
                arch=args.arch,
                content_set=args.content_set
            )
            format_list_output(result, args.json)

        elif args.command == 'download':
            progress_cb = create_progress_callback(args.json)
            message_cb = create_message_callback(args.json)

            result = api.download_file(
                identifier=args.identifier,
                output_dir=args.output,
                by_filename=args.by_filename,
                progress_callback=progress_cb,
                message_callback=message_cb
            )
            format_download_output(result, args.json)

    except RuntimeError as e:
        if args.json:
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.json:
            print(json.dumps({"error": f"Unexpected error: {e}"}, indent=2))
        else:
            print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
