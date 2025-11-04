"""
Red Hat Customer Portal API client.
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import Optional, Dict, List
import requests


class RedHatAPI:
    """Red Hat Customer Portal API client."""

    TOKEN_URL = "https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token"
    API_BASE = "https://api.access.redhat.com/management/v1"
    DOWNLOADS_URL = "https://access.redhat.com/downloads"

    def __init__(self, offline_token: str):
        """Initialize API client with offline token."""
        self.offline_token = offline_token
        self.access_token: Optional[str] = None
        self.session = requests.Session()
        self._discovered_versions_cache: Dict[str, List[tuple]] = {}  # Cache for discovered versions

    def get_access_token(self) -> str:
        """Exchange offline token for access token."""
        if self.access_token:
            return self.access_token

        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    'grant_type': 'refresh_token',
                    'client_id': 'rhsm-api',
                    'refresh_token': self.offline_token
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data['access_token']
            return self.access_token
        except requests.RequestException as e:
            raise RuntimeError(f"Error getting access token: {e}") from e

    def list_rhel_images(self, version: str, arch: str) -> List[Dict]:
        """
        List RHEL images for a specific version and architecture.
        Returns empty list if version/arch not found (404).
        Raises exception for other errors.
        """
        access_token = self.get_access_token()
        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            url = f"{self.API_BASE}/images/rhel/{version}/{arch}"
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('body', [])
        except requests.RequestException as e:
            # Return empty list for 404 (not found)
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                return []
            # Raise exception for other errors
            raise RuntimeError(f"Error listing RHEL images: {e}") from e

    def list_images_by_content_set(self, content_set: str) -> List[Dict]:
        """
        List images in a specific content set.
        Returns empty list if content set not found (404).
        Raises exception for other errors.
        """
        access_token = self.get_access_token()
        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            url = f"{self.API_BASE}/images/cset/{content_set}"
            response = requests.get(url, headers=headers, timeout=30, params={'limit': 100})
            response.raise_for_status()
            data = response.json()
            return data.get('body', [])
        except requests.RequestException as e:
            # Return empty list for 404 (not found)
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                return []
            # Raise exception for other errors
            raise RuntimeError(f"Error listing images for content set: {e}") from e

    def version_exists(self, version: str, arch: str) -> bool:
        """Check if a RHEL version exists (quietly, without printing errors)."""
        access_token = self.get_access_token()
        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            url = f"{self.API_BASE}/images/rhel/{version}/{arch}"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                images = data.get('body', [])
                # Check if there are any ISO files available
                return any(img.get('filename', '').endswith('.iso') for img in images)
            return False
        except:
            return False

    def discover_rhel_versions(self, arch: str = "x86_64") -> List[tuple]:
        """
        Discover available RHEL versions by probing the API.
        Uses a baseline of known versions and tries to find newer ones.
        Results are cached per architecture to avoid redundant API calls.
        """
        # Return cached results if available
        if arch in self._discovered_versions_cache:
            return self._discovered_versions_cache[arch]

        discovered = []

        # Baseline: Known stable versions to always try
        baseline_majors = [10, 9, 8]
        baseline_versions = {
            10: [0],  # RHEL 10.0
            9: [6, 5, 4],  # RHEL 9.6, 9.5, 9.4
            8: [10, 9, 8],  # RHEL 8.10, 8.9, 8.8
        }

        # First, add all baseline versions that exist
        for major in baseline_majors:
            for minor in baseline_versions.get(major, []):
                version = f"{major}.{minor}"
                if self.version_exists(version, arch):
                    discovered.append((version, arch))

        # Try to discover newer major versions (e.g., RHEL 11, 12)
        for major in range(11, 15):  # Check up to RHEL 14
            # Try .0 first (initial release)
            version = f"{major}.0"
            if self.version_exists(version, arch):
                discovered.append((version, arch))
                # If .0 exists, try finding minor versions
                for minor in range(1, 10):
                    version = f"{major}.{minor}"
                    if self.version_exists(version, arch):
                        discovered.append((version, arch))
                    else:
                        break  # Stop when we hit a non-existent version
            else:
                break  # Stop checking higher major versions

        # Try to discover newer minor versions for existing majors
        for major in baseline_majors:
            max_known_minor = max(baseline_versions.get(major, [0]))
            # Try a few versions ahead
            for minor in range(max_known_minor + 1, max_known_minor + 5):
                version = f"{major}.{minor}"
                if self.version_exists(version, arch):
                    discovered.append((version, arch))
                else:
                    break  # Stop when we hit a non-existent version

        # Sort by version (newest first)
        discovered.sort(key=lambda x: tuple(map(int, x[0].split('.'))), reverse=True)

        # Cache the results
        self._discovered_versions_cache[arch] = discovered

        return discovered

    def find_image_by_filename(self, filename: str,
                               message_callback: Optional[callable] = None) -> Optional[Dict]:
        """
        Find an image by filename across multiple versions.
        If multiple matches found, returns the most recent one.

        Args:
            filename: Filename to search for
            message_callback: Optional callback for progress messages (str) -> None

        Returns:
            Image dict if found, None otherwise
        """
        def msg(text: str) -> None:
            """Helper to call message_callback if provided."""
            if message_callback:
                message_callback(text)

        msg(f"Searching for filename: {filename}")
        msg("This may take a moment as we search across multiple RHEL versions...")
        msg("")

        # Discover available versions dynamically for both x86_64 and aarch64
        x86_64_versions = self.discover_rhel_versions("x86_64")
        aarch64_versions = self.discover_rhel_versions("aarch64")

        # Search x86_64 first (most common), then aarch64
        search_versions = x86_64_versions + aarch64_versions

        matches = []

        for version, arch in search_versions:
            msg(f"  Searching RHEL {version} ({arch})...")
            images = self.list_rhel_images(version, arch)
            for img in images:
                if img.get('filename') == filename:
                    matches.append(img)
                    msg(f"  Searching RHEL {version} ({arch})... ✓ Found!")
                    # If we found one in the most recent version, we can stop early
                    if not matches or len(matches) == 1:
                        break
            if not any(img.get('filename') == filename for img in images):
                msg(f"  Searching RHEL {version} ({arch})... -")

            # Early exit if we found a match in a recent version
            if matches:
                break

        if not matches:
            msg(f"\nNo image found with filename: {filename}")
            return None

        if len(matches) == 1:
            msg("")
            msg("Found 1 match.")
            return matches[0]

        # Multiple matches - return the most recent
        msg("")
        msg(f"Found {len(matches)} matches. Selecting the most recent...")

        # Sort by datePublished in descending order
        matches_sorted = sorted(
            matches,
            key=lambda x: x.get('datePublished', ''),
            reverse=True
        )

        latest = matches_sorted[0]
        msg(f"Selected: {latest.get('imageName')} (published {latest.get('datePublished')})")
        msg("")

        return latest

    def list_downloads(self, version: Optional[str] = None, arch: Optional[str] = None,
                      content_set: Optional[str] = None) -> Dict:
        """
        List available downloads from Red Hat Customer Portal API.

        Returns:
            Dict with structure depending on input:
            - content_set: {"type": "content_set", "content_set": str, "images": List[Dict]}
            - version+arch: {"type": "version_arch", "version": str, "arch": str, "images": List[Dict]}
            - default: {"type": "default", "releases": List[{"version": str, "architecture": str, "images": List[Dict]}]}
        """
        if content_set:
            # List images from a specific content set
            images = self.list_images_by_content_set(content_set)
            return {
                "type": "content_set",
                "content_set": content_set,
                "images": images
            }

        elif version and arch:
            # List RHEL images by version and architecture
            images = self.list_rhel_images(version, arch)
            return {
                "type": "version_arch",
                "version": version,
                "architecture": arch,
                "images": images
            }

        else:
            # Default: List currently supported RHEL versions for x86_64
            # Discover available RHEL versions dynamically
            default_versions = self.discover_rhel_versions("x86_64")

            # Limit to top 3 most recent versions for default display
            default_versions = default_versions[:3]

            all_releases = []
            for ver, arch_info in default_versions:
                images = self.list_rhel_images(ver, arch_info)
                if images:
                    # Filter to ISO files only
                    iso_images = [img for img in images if img.get('filename', '').endswith('.iso')]
                    all_releases.append({
                        "version": ver,
                        "architecture": arch_info,
                        "images": iso_images
                    })

            return {
                "type": "default",
                "releases": all_releases
            }

    def get_download_info(self, checksum: str) -> Dict:
        """
        Get download information for a file by checksum.

        Returns:
            Dict with download info including 'body' with 'filename' and 'href'

        Raises:
            RuntimeError: If API call fails or response is invalid
        """
        access_token = self.get_access_token()

        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        try:
            url = f"{self.API_BASE}/images/{checksum}/download"
            response = requests.get(url, headers=headers, timeout=60, allow_redirects=False)
            response.raise_for_status()

            # API returns 307 redirect with JSON body containing download link
            if response.status_code == 307:
                try:
                    return response.json()
                except ValueError:
                    # If JSON parsing fails, extract from redirect location
                    location = response.headers.get('Location', '')
                    if location:
                        # Extract filename from URL
                        filename = location.split('/')[-1].split('?')[0]
                        return {
                            'body': {
                                'href': location,
                                'filename': filename
                            }
                        }
                    raise

            return response.json()
        except requests.RequestException as e:
            error_msg = f"Error getting download info: {e}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"\nResponse status: {e.response.status_code}"
                error_msg += f"\nResponse text: {e.response.text[:500]}"
            raise RuntimeError(error_msg) from e

    @staticmethod
    def calculate_sha256(file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(8192), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def download_file(self, identifier: str, output_dir: str = ".", by_filename: bool = False,
                     progress_callback: Optional[callable] = None,
                     message_callback: Optional[callable] = None) -> Dict:
        """
        Download a file by checksum or filename.

        Args:
            identifier: Either a checksum or filename
            output_dir: Directory to save the downloaded file
            by_filename: If True, treat identifier as filename; otherwise as checksum
            progress_callback: Optional callback for download progress (downloaded: int, total: int) -> None
            message_callback: Optional callback for status messages (str) -> None

        Returns:
            Dict with download result:
            {
                "status": "success" | "error",
                "filename": str,
                "checksum": str,
                "path": str,
                "size": int,
                "verified": bool,
                "error": str (only if status=="error")
            }

        Raises:
            RuntimeError: If download fails, file not found, or checksum mismatch
        """
        def msg(text: str) -> None:
            """Helper to call message_callback if provided."""
            if message_callback:
                message_callback(text)

        def progress(downloaded: int, total: int) -> None:
            """Helper to call progress_callback if provided."""
            if progress_callback:
                progress_callback(downloaded, total)

        # Resolve filename to checksum if needed
        if by_filename:
            image = self.find_image_by_filename(identifier, message_callback=message_callback)

            if not image:
                raise RuntimeError(f"File not found: {identifier}")

            checksum = image.get('checksum')
            if not checksum:
                raise RuntimeError("No checksum found for image")

            msg(f"Using checksum: {checksum}")
            msg("")
        else:
            checksum = identifier

        msg(f"Fetching download information for checksum: {checksum}")

        download_info = self.get_download_info(checksum)

        if 'body' not in download_info:
            raise RuntimeError(f"Unexpected response format: {download_info}")

        body = download_info['body']
        filename = body.get('filename')
        download_url = body.get('href')

        if not filename or not download_url:
            raise RuntimeError(f"Missing filename or download URL in response: {download_info}")

        output_path = Path(output_dir) / filename

        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        msg(f"Downloading: {filename}")
        msg(f"Destination: {output_path}")

        try:
            # Download with progress indication
            response = requests.get(download_url, stream=True, timeout=120)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress(downloaded, total_size)

            # Verify checksum
            msg("")  # New line after progress
            msg("Verifying checksum...")

            calculated_checksum = self.calculate_sha256(str(output_path))

            if calculated_checksum != checksum:
                # Checksum mismatch - delete the file
                output_path.unlink()
                raise RuntimeError(
                    f"Checksum mismatch!\n"
                    f"Expected: {checksum}\n"
                    f"Got:      {calculated_checksum}\n"
                    f"File deleted for security."
                )

            msg("Checksum verified successfully!")

            return {
                "status": "success",
                "filename": filename,
                "checksum": checksum,
                "path": str(output_path),
                "size": downloaded,
                "verified": True
            }

        except requests.RequestException as e:
            raise RuntimeError(f"Download failed: {e}") from e
