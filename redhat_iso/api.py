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
            print(f"Error getting access token: {e}", file=sys.stderr)
            sys.exit(1)

    def list_rhel_images(self, version: str, arch: str) -> List[Dict]:
        """List RHEL images for a specific version and architecture."""
        access_token = self.get_access_token()
        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            url = f"{self.API_BASE}/images/rhel/{version}/{arch}"
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('body', [])
        except requests.RequestException as e:
            print(f"Error listing RHEL images: {e}", file=sys.stderr)
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status: {e.response.status_code}", file=sys.stderr)
                if e.response.status_code == 404:
                    print(f"Version {version} or architecture {arch} not found.", file=sys.stderr)
            return []

    def list_images_by_content_set(self, content_set: str) -> List[Dict]:
        """List images in a specific content set."""
        access_token = self.get_access_token()
        headers = {'Authorization': f'Bearer {access_token}'}

        try:
            url = f"{self.API_BASE}/images/cset/{content_set}"
            response = requests.get(url, headers=headers, timeout=30, params={'limit': 100})
            response.raise_for_status()
            data = response.json()
            return data.get('body', [])
        except requests.RequestException as e:
            print(f"Error listing images for content set: {e}", file=sys.stderr)
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status: {e.response.status_code}", file=sys.stderr)
            return []

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

    def find_image_by_filename(self, filename: str) -> Optional[Dict]:
        """
        Find an image by filename across multiple versions.
        If multiple matches found, returns the most recent one.
        """
        print(f"Searching for filename: {filename}", flush=True)
        print("This may take a moment as we search across multiple RHEL versions...", flush=True)
        print(flush=True)

        # Discover available versions dynamically for both x86_64 and aarch64
        # This automatically finds the latest versions
        x86_64_versions = self.discover_rhel_versions("x86_64")
        aarch64_versions = self.discover_rhel_versions("aarch64")

        # Search x86_64 first (most common), then aarch64
        search_versions = x86_64_versions + aarch64_versions

        matches = []

        for version, arch in search_versions:
            print(f"  Searching RHEL {version} ({arch})...", end='', flush=True)
            images = self.list_rhel_images(version, arch)
            for img in images:
                if img.get('filename') == filename:
                    matches.append(img)
                    print(f" ✓ Found!", flush=True)
                    # If we found one in the most recent version, we can stop early
                    if not matches or len(matches) == 1:
                        break
            if not any(img.get('filename') == filename for img in images):
                print(" -", flush=True)

            # Early exit if we found a match in a recent version
            if matches:
                break

        if not matches:
            print(f"\nNo image found with filename: {filename}", flush=True)
            return None

        if len(matches) == 1:
            print(flush=True)
            print("Found 1 match.", flush=True)
            return matches[0]

        # Multiple matches - return the most recent
        print(flush=True)
        print(f"Found {len(matches)} matches. Selecting the most recent...", flush=True)

        # Sort by datePublished in descending order
        matches_sorted = sorted(
            matches,
            key=lambda x: x.get('datePublished', ''),
            reverse=True
        )

        latest = matches_sorted[0]
        print(f"Selected: {latest.get('imageName')} (published {latest.get('datePublished')})", flush=True)
        print(flush=True)

        return latest

    def list_downloads(self, version: Optional[str] = None, arch: Optional[str] = None,
                      content_set: Optional[str] = None, json_output: bool = False) -> None:
        """List available downloads from Red Hat Customer Portal API."""

        if content_set:
            if not json_output:
                print("Fetching available downloads from Red Hat Customer Portal...")
                print()
            # List images from a specific content set
            images = self.list_images_by_content_set(content_set)

            if json_output:
                output = {
                    "content_set": content_set,
                    "images": images
                }
                print(json.dumps(output, indent=2))
                return

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

        elif version and arch:
            if not json_output:
                print("Fetching available downloads from Red Hat Customer Portal...")
                print()
            # List RHEL images by version and architecture
            images = self.list_rhel_images(version, arch)

            if json_output:
                output = {
                    "version": version,
                    "architecture": arch,
                    "images": images
                }
                print(json.dumps(output, indent=2))
                return

            if not images:
                print(f"No images found for RHEL {version} ({arch})")
                print()
                print("Try different version/arch combinations. Examples:")
                print("  rhiso list --version 9.6 --arch x86_64")
                print("  rhiso list --version 8.10 --arch aarch64")
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

        else:
            # Default: List currently supported RHEL versions for x86_64
            if not json_output:
                print("Fetching currently supported RHEL releases for x86_64...")
                print()

            # Discover available RHEL versions dynamically
            # This will find the latest versions plus check for newer releases
            default_versions = self.discover_rhel_versions("x86_64")

            # Limit to top 3 most recent versions for default display
            default_versions = default_versions[:3]

            all_releases = []
            for ver, arch in default_versions:
                images = self.list_rhel_images(ver, arch)
                if images:
                    if json_output:
                        # Filter to ISO files only for JSON output too
                        iso_images = [img for img in images if img.get('filename', '').endswith('.iso')]
                        all_releases.append({
                            "version": ver,
                            "architecture": arch,
                            "images": iso_images
                        })
                    else:
                        print(f"═══ RHEL {ver} ({arch}) ═══")
                        print()
                        for img in images:
                            filename = img.get('filename', 'N/A')
                            checksum = img.get('checksum', 'N/A')
                            image_name = img.get('imageName', 'N/A')

                            # Only show ISO files by default
                            if filename.endswith('.iso'):
                                print(f"  {image_name}")
                                print(f"    Filename: {filename}")
                                print(f"    Checksum: {checksum}")
                                print()
                        print()

            if json_output:
                output = {
                    "releases": all_releases
                }
                print(json.dumps(output, indent=2))
            else:
                print("For other versions or architectures, use:")
                print("  rhiso list --version <version> --arch <arch>")
                print()
                print("Common versions: 9.6, 9.5, 9.4, 8.10, 8.9, 7.9")
                print("Common architectures: x86_64, aarch64, ppc64le, s390x")

    def get_download_info(self, checksum: str) -> Dict:
        """Get download information for a file by checksum."""
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
            print(f"Error getting download info: {e}", file=sys.stderr)
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}", file=sys.stderr)
                print(f"Response text: {e.response.text[:500]}", file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def calculate_sha256(file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(8192), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def download_file(self, identifier: str, output_dir: str = ".", by_filename: bool = False, json_output: bool = False) -> None:
        """
        Download a file by checksum or filename.

        Args:
            identifier: Either a checksum or filename
            output_dir: Directory to save the downloaded file
            by_filename: If True, treat identifier as filename; otherwise as checksum
            json_output: If True, output results in JSON format
        """
        if by_filename:
            # Search for the file by filename
            if not json_output:
                print(f"Searching for filename: {identifier}", flush=True)
                print("This may take a moment as we search across multiple RHEL versions...", flush=True)
                print(flush=True)

            # We need to temporarily suppress the print statements in find_image_by_filename for JSON
            if json_output:
                # Search quietly for JSON mode using discovered versions
                x86_64_versions = self.discover_rhel_versions("x86_64")
                aarch64_versions = self.discover_rhel_versions("aarch64")
                search_versions = x86_64_versions + aarch64_versions

                image = None
                for version, arch in search_versions:
                    images = self.list_rhel_images(version, arch)
                    for img in images:
                        if img.get('filename') == identifier:
                            image = img
                            break
                    if image:
                        break
            else:
                image = self.find_image_by_filename(identifier)

            if not image:
                if json_output:
                    print(json.dumps({"error": f"File not found: {identifier}"}, indent=2))
                else:
                    print(f"Error: Could not find file with name: {identifier}", file=sys.stderr)
                sys.exit(1)

            checksum = image.get('checksum')
            if not checksum:
                if json_output:
                    print(json.dumps({"error": "No checksum found for image"}, indent=2))
                else:
                    print(f"Error: No checksum found for image", file=sys.stderr)
                sys.exit(1)

            if not json_output:
                print(f"Using checksum: {checksum}")
                print()
        else:
            checksum = identifier

        if not json_output:
            print(f"Fetching download information for checksum: {checksum}", flush=True)

        download_info = self.get_download_info(checksum)

        if 'body' not in download_info:
            print(f"Error: Unexpected response format: {download_info}", file=sys.stderr)
            sys.exit(1)

        body = download_info['body']
        filename = body.get('filename')
        download_url = body.get('href')

        if not filename or not download_url:
            print(f"Error: Missing filename or download URL in response", file=sys.stderr)
            print(f"Response: {download_info}", file=sys.stderr)
            sys.exit(1)

        output_path = Path(output_dir) / filename

        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if not json_output:
            print(f"Downloading: {filename}", flush=True)
            print(f"Destination: {output_path}", flush=True)

        try:
            # Download with progress indication (suppressed in JSON mode)
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
                        if total_size > 0 and not json_output:
                            progress = (downloaded / total_size) * 100
                            print(f"\rProgress: {progress:.1f}% ({downloaded}/{total_size} bytes)", end='', flush=True)

            # Verify checksum
            if not json_output:
                print(flush=True)  # New line after progress
                print(f"Verifying checksum...", flush=True)

            calculated_checksum = self.calculate_sha256(str(output_path))

            if calculated_checksum != checksum:
                # Checksum mismatch - delete the file
                output_path.unlink()
                error_msg = f"Checksum verification failed!\n  Expected: {checksum}\n  Got:      {calculated_checksum}"

                if json_output:
                    error_result = {
                        "error": "Checksum verification failed",
                        "expected_checksum": checksum,
                        "calculated_checksum": calculated_checksum,
                        "filename": filename,
                        "status": "failed"
                    }
                    print(json.dumps(error_result, indent=2), file=sys.stderr)
                else:
                    print(f"Error: {error_msg}", file=sys.stderr)
                sys.exit(1)

            if not json_output:
                print(f"Checksum verified successfully!", flush=True)

            if json_output:
                # Output JSON result after successful download and verification
                result = {
                    "filename": filename,
                    "checksum": checksum,
                    "destination": str(output_path),
                    "size": downloaded,
                    "verified": True,
                    "status": "completed"
                }
                print(json.dumps(result, indent=2))
            else:
                print(f"Successfully downloaded: {output_path}", flush=True)

        except requests.RequestException as e:
            if json_output:
                error_result = {
                    "error": f"Download failed: {str(e)}",
                    "filename": filename,
                    "checksum": checksum,
                    "status": "failed"
                }
                print(json.dumps(error_result, indent=2), file=sys.stderr)
            else:
                print(f"\nError downloading file: {e}", file=sys.stderr)
            sys.exit(1)
