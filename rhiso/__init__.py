"""
Red Hat ISO Download Tool

A Python library and CLI tool for listing and downloading Red Hat ISO files
using the Red Hat Customer Portal API.

Library Usage:
    from rhiso import RedHatAPI

    # Initialize with offline token
    api = RedHatAPI(offline_token="your_token_here")

    # List RHEL images
    images = api.list_rhel_images("9.6", "x86_64")

    # Download ISO
    api.download_file("checksum_or_filename", output_dir="./downloads")

CLI Usage:
    rhiso list
    rhiso list --version 9.6 --arch x86_64
    rhiso download <checksum>
    rhiso download rhel-9.6-x86_64-dvd.iso --by-filename
"""

__version__ = "1.0.0"

from .api import RedHatAPI

__all__ = ["RedHatAPI", "__version__"]
