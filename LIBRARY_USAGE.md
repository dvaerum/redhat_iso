# Using rhiso as a Python Library

The `rhiso` package can be used both as a command-line tool and as a Python library in your own scripts.

## Installation

```bash
# Using pip
pip install rhiso

# Using Nix
nix-shell shell.nix
```

## Library Usage

### Basic Example

```python
from rhiso import RedHatAPI

# Initialize with offline token
token = open("redhat-api-token.txt").read().strip()
api = RedHatAPI(token)

# List RHEL images
images = api.list_rhel_images("9.6", "x86_64")
for img in images:
    print(f"{img['filename']}: {img['checksum']}")
```

### Available Methods

#### `RedHatAPI(offline_token: str)`
Initialize the API client with your Red Hat offline token.

```python
api = RedHatAPI("your_offline_token_here")
```

#### `list_rhel_images(version: str, arch: str) -> List[Dict]`
List all images for a specific RHEL version and architecture.

```python
images = api.list_rhel_images("9.6", "x86_64")
# Returns: [{"imageName": "...", "filename": "...", "checksum": "...", ...}, ...]
```

#### `list_images_by_content_set(content_set: str) -> List[Dict]`
List images in a specific content set.

```python
images = api.list_images_by_content_set("rhel-9-for-x86_64-baseos-isos")
```

#### `discover_rhel_versions(arch: str = "x86_64") -> List[tuple]`
Automatically discover available RHEL versions.

```python
versions = api.discover_rhel_versions("x86_64")
# Returns: [("10.0", "x86_64"), ("9.6", "x86_64"), ...]
```

#### `version_exists(version: str, arch: str) -> bool`
Check if a specific RHEL version exists.

```python
if api.version_exists("11.0", "x86_64"):
    print("RHEL 11.0 is available!")
```

#### `find_image_by_filename(filename: str) -> Optional[Dict]`
Find an image by filename across all versions.

```python
image = api.find_image_by_filename("rhel-9.6-x86_64-boot.iso")
if image:
    print(f"Found: {image['checksum']}")
```

#### `download_file(identifier: str, output_dir: str = ".", by_filename: bool = False, json_output: bool = False)`
Download a file by checksum or filename.

```python
# Download by checksum
api.download_file(
    "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb",
    output_dir="./downloads"
)

# Download by filename
api.download_file(
    "rhel-9.6-x86_64-boot.iso",
    output_dir="./downloads",
    by_filename=True
)
```

## Complete Example

```python
#!/usr/bin/env python3
from rhiso import RedHatAPI

# Initialize
token = open("redhat-api-token.txt").read().strip()
api = RedHatAPI(token)

# Discover versions
print("Discovering RHEL versions...")
versions = api.discover_rhel_versions("x86_64")
print(f"Found {len(versions)} versions")

# Get images for latest version
latest_version, arch = versions[0]
print(f"\nGetting images for RHEL {latest_version}...")
images = api.list_rhel_images(latest_version, arch)

# Filter for ISO files only
iso_images = [img for img in images if img['filename'].endswith('.iso')]

# Display
for img in iso_images:
    print(f"  {img['imageName']}")
    print(f"    File: {img['filename']}")
    print(f"    SHA256: {img['checksum']}")
    print()

# Download the Boot ISO
boot_iso = next((img for img in iso_images if 'boot' in img['filename'].lower()), None)
if boot_iso:
    print(f"Downloading {boot_iso['filename']}...")
    api.download_file(
        boot_iso['checksum'],
        output_dir="./downloads"
    )
    print("Download complete!")
```

## CLI Usage

The same functionality is available via the command line:

```bash
# List images
rhiso list
rhiso list --version 9.6 --arch x86_64

# Download by checksum
rhiso download <checksum>

# Download by filename
rhiso download rhel-9.6-x86_64-boot.iso --by-filename

# JSON output
rhiso --json list
rhiso --json download <checksum>
```

## Running as a Module

You can also run rhiso as a Python module:

```bash
python -m rhiso list
python -m rhiso download <checksum>
```

## Use Cases

### Automation Script
```python
from rhiso import RedHatAPI

def download_latest_rhel_boot_iso(output_dir="./iso"):
    """Download the latest RHEL boot ISO."""
    token = open("redhat-api-token.txt").read().strip()
    api = RedHatAPI(token)

    # Get latest version
    versions = api.discover_rhel_versions("x86_64")
    latest_version, arch = versions[0]

    # Find boot ISO
    images = api.list_rhel_images(latest_version, arch)
    boot_iso = next(
        (img for img in images if 'boot' in img['filename'].lower() and img['filename'].endswith('.iso')),
        None
    )

    if boot_iso:
        api.download_file(boot_iso['checksum'], output_dir)
        return boot_iso['filename']
    return None

# Use it
filename = download_latest_rhel_boot_iso()
print(f"Downloaded: {filename}")
```

### Version Checker
```python
from rhiso import RedHatAPI

def check_rhel_versions():
    """Check which RHEL versions are available."""
    token = open("redhat-api-token.txt").read().strip()
    api = RedHatAPI(token)

    versions_to_check = ["10.0", "10.1", "9.7", "9.6", "8.11", "8.10"]

    for version in versions_to_check:
        exists = api.version_exists(version, "x86_64")
        status = "✓ Available" if exists else "✗ Not available"
        print(f"RHEL {version}: {status}")

check_rhel_versions()
```

### Bulk Download
```python
from rhiso import RedHatAPI

def download_all_boot_isos(versions=["10.0", "9.6", "8.10"]):
    """Download boot ISOs for multiple versions."""
    token = open("redhat-api-token.txt").read().strip()
    api = RedHatAPI(token)

    for version in versions:
        print(f"Processing RHEL {version}...")
        images = api.list_rhel_images(version, "x86_64")

        boot_iso = next(
            (img for img in images if 'boot' in img['filename'].lower() and img['filename'].endswith('.iso')),
            None
        )

        if boot_iso:
            print(f"  Downloading {boot_iso['filename']}...")
            api.download_file(
                boot_iso['checksum'],
                output_dir=f"./rhel-{version}"
            )
        else:
            print(f"  No boot ISO found")

download_all_boot_isos()
```

## Error Handling

```python
from rhiso import RedHatAPI
import sys

try:
    token = open("redhat-api-token.txt").read().strip()
    api = RedHatAPI(token)

    images = api.list_rhel_images("9.6", "x86_64")
    if not images:
        print("No images found", file=sys.stderr)
        sys.exit(1)

    # Process images...

except FileNotFoundError:
    print("Token file not found", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

## API Response Format

Each image dictionary contains:

```python
{
    "imageName": "Red Hat Enterprise Linux 9.6 Binary DVD",
    "filename": "rhel-9.6-x86_64-dvd.iso",
    "arch": "x86_64",
    "checksum": "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb",
    "datePublished": "2025-04-22T09:34:36.000Z",
    "downloadHref": "https://api.access.redhat.com/management/v1/images/.../download"
}
```

## See Also

- [README.md](README.md) - General usage and installation
- [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - CLI usage examples
- [example_library_usage.py](example_library_usage.py) - Runnable example
