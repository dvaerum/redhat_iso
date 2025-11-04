# Usage Examples - Red Hat ISO Download Tool

## Installation Methods

### 1. Using nix run (No Installation Required)
```bash
# Direct execution with flakes
nix run . -- --help
nix run . -- list --version 9.6 --arch x86_64
nix run . -- download febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb
```

### 2. Using nix-build
```bash
# Build once, use many times
nix-build shell.nix
./result/bin/rhiso list --version 9.6 --arch x86_64
```

### 3. Using Direct Python Script
```bash
pip install -r requirements.txt
./rhiso.py list --version 9.6 --arch x86_64
```

---

## Common Usage Patterns

### List Currently Supported RHEL Releases

```bash
# Automatically discovers and shows latest RHEL ISOs for x86_64
rhiso list

# Or with nix run
nix run . -- list
```

This automatically discovers and displays ISO files for the latest RHEL versions. The tool probes the Red Hat API to find the newest releases, so it will automatically show RHEL 11 when it's released, or newer minor versions like 10.1 or 9.7.

### List RHEL Images by Version and Architecture

```bash
# RHEL 9.6 for x86_64
rhiso list --version 9.6 --arch x86_64

# RHEL 8.10 for x86_64
rhiso list --version 8.10 --arch x86_64

# RHEL 9.6 for aarch64 (ARM64)
rhiso list --version 9.6 --arch aarch64

# RHEL 8.9 for ppc64le (IBM Power)
rhiso list --version 8.9 --arch ppc64le
```

### List Images from Content Sets

```bash
# RHEL 9 for x86_64 base OS ISOs
rhiso list --content-set rhel-9-for-x86_64-baseos-isos

# RHEL 8 for aarch64 base OS ISOs
rhiso list --content-set rhel-8-for-aarch64-baseos-isos

# RHEL 9 for x86_64 AppStream ISOs
rhiso list --content-set rhel-9-for-x86_64-appstream-isos
```

### Download ISOs

**By Checksum:**
```bash
# Download RHEL 9.6 Binary DVD
rhiso download febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb

# Download to specific directory
rhiso download 36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63 \
  --output ~/iso-downloads

# Download RHEL 8.10 Binary DVD to /tmp
rhiso download 9b3c8e31bc2cdd2de9cf96abb3726347f5840ff3b176270647b3e66639af291b \
  --output /tmp
```

**By Filename (Automatic Search):**
```bash
# Download by filename - tool searches for latest version
rhiso download rhel-9.6-x86_64-dvd.iso --by-filename

# Download Boot ISO by filename
rhiso download rhel-9.6-x86_64-boot.iso --by-filename

# Download to specific directory
rhiso download rhel-8.10-x86_64-dvd.iso --by-filename --output ~/Downloads

# If multiple versions have the same filename, downloads the most recent
rhiso download rhel-baseos-9-latest-x86_64.iso --by-filename
```

### Using Custom Token File

```bash
# Specify alternative token file location
rhiso --token-file ~/.config/redhat-token.txt list --version 9.6 --arch x86_64

rhiso --token-file /path/to/token.txt download <checksum>
```

---

## Complete Workflow Examples

### Example 1: Download Latest RHEL 9.6 x86_64 DVD

```bash
# Step 1: List currently supported RHEL releases
nix run . -- list

# Output shows:
# ═══ RHEL 9.6 (x86_64) ═══
# Red Hat Enterprise Linux 9.6 Binary DVD
#   Filename: rhel-9.6-x86_64-dvd.iso
#   Checksum: febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb

# Step 2: Download using the checksum from output
nix run . -- download febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb \
  --output ~/Downloads
```

### Example 2: Download Boot ISO for Quick Install

```bash
# List RHEL 9.6 images
./result/bin/rhiso list --version 9.6 --arch x86_64

# Download the smaller Boot ISO instead of full DVD
./result/bin/rhiso download 36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63
```

### Example 3: Browse Historical RHEL Versions

```bash
# List RHEL 9.2 images (older version)
rhiso list --content-set rhel-9-for-x86_64-baseos-isos

# This will show all RHEL 9.x versions available in the content set:
# - rhel-9.0-x86_64-dvd.iso
# - rhel-9.2-x86_64-dvd.iso
# - rhel-9.4-x86_64-dvd.iso
# - etc.
```

### Example 4: Download for Different Architectures

```bash
# List ARM64 (aarch64) images
rhiso list --version 9.6 --arch aarch64

# List IBM Power (ppc64le) images
rhiso list --version 9.6 --arch ppc64le

# List IBM Z (s390x) images
rhiso list --version 9.6 --arch s390x
```

---

## Verified Checksums

Use these real checksums for testing:

```bash
# RHEL 9.6 Binary DVD (x86_64) - 10.5 GB
rhiso download febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb

# RHEL 9.6 Boot ISO (x86_64) - 950 MB
rhiso download 36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63

# RHEL 8.10 Binary DVD (x86_64)
rhiso download 9b3c8e31bc2cdd2de9cf96abb3726347f5840ff3b176270647b3e66639af291b

# RHEL 8.10 Boot ISO (x86_64)
rhiso download 6ced368628750ff3ea8a2fc52a371ba368d3377b8307caafda69070849a9e4e7
```

---

## Tips

1. **Use Boot ISO for network installs**: Boot ISOs are much smaller (~1 GB) and install packages from network repositories
2. **Use Binary DVD for offline installs**: Full DVD includes all packages (~10 GB) for offline installation
3. **Check available versions**: Common versions include 9.6, 9.5, 9.4, 8.10, 8.9, 8.8, 7.9
4. **List by content set for historical versions**: Content sets contain all versions for a major release

---

## Troubleshooting

### Flakes Not Enabled
If `nix run` doesn't work, you may need to enable flakes:

Add to `~/.config/nix/nix.conf`:
```
experimental-features = nix-command flakes
```

Or use the traditional method:
```bash
nix-build shell.nix
./result/bin/rhiso --help
```

### Token Expired
If you get authentication errors:
1. Regenerate token at https://access.redhat.com/management/api
2. Update `redhat-api-token.txt` with new token
3. Try again

## Quick Start

The fastest way to get started:

```bash
# 1. List currently supported RHEL ISOs
nix run . -- list

# 2. Copy the checksum for the ISO you want
# 3. Download it
nix run . -- download <checksum>
```

That's it! No build required with `nix run`.

---

## JSON Output for Automation

All list commands support JSON output for programmatic use:

### Default List with JSON

```bash
rhiso --json list
```

**Output:**
```json
{
  "releases": [
    {
      "version": "9.6",
      "architecture": "x86_64",
      "images": [
        {
          "imageName": "Red Hat Enterprise Linux 9.6 Binary DVD",
          "filename": "rhel-9.6-x86_64-dvd.iso",
          "arch": "x86_64",
          "checksum": "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb",
          "datePublished": "2025-04-22T09:34:36.000Z",
          "downloadHref": "https://api.access.redhat.com/management/v1/images/..."
        }
      ]
    }
  ]
}
```

### Specific Version with JSON

```bash
rhiso --json list --version 9.6 --arch x86_64
```

**Output:**
```json
{
  "version": "9.6",
  "architecture": "x86_64",
  "images": [
    {
      "imageName": "Red Hat Enterprise Linux 9.6 Binary DVD",
      "filename": "rhel-9.6-x86_64-dvd.iso",
      "checksum": "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb",
      ...
    }
  ]
}
```

### Content Set with JSON

```bash
rhiso --json list --content-set rhel-9-for-x86_64-baseos-isos
```

### Using JSON Output in Scripts

```bash
# Extract checksums for all RHEL 9.6 ISOs
rhiso --json list --version 9.6 --arch x86_64 | jq -r '.images[].checksum'

# Get just the Binary DVD checksum
rhiso --json list --version 9.6 --arch x86_64 | \
  jq -r '.images[] | select(.filename | contains("dvd.iso")) | .checksum'

# Download all ISOs automatically
rhiso --json list --version 9.6 --arch x86_64 | \
  jq -r '.images[].checksum' | \
  xargs -I {} rhiso download {}
```

### Parsing JSON in Python

```python
import subprocess
import json

# Get list of ISOs
result = subprocess.run(
    ["rhiso", "--json", "list", "--version", "9.6", "--arch", "x86_64"],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)

# Process each image
for image in data["images"]:
    print(f"Name: {image['imageName']}")
    print(f"Checksum: {image['checksum']}")
    print(f"Filename: {image['filename']}")
    print()
```

---

## Download by Filename Feature

The tool can automatically search for and download ISOs by filename, selecting the most recent version if multiple matches exist.

### How It Works

1. Searches across RHEL 9.6, 9.5, 9.4, 8.10, 8.9, 8.8 for x86_64 and aarch64
2. Stops as soon as it finds a match (searches newest first)
3. If multiple versions match, selects the most recently published
4. Automatically retrieves the checksum and downloads

### Examples

**Simple filename download:**
```bash
rhiso download rhel-9.6-x86_64-dvd.iso --by-filename
```

**Output:**
```
Searching for filename: rhel-9.6-x86_64-dvd.iso
This may take a moment as we search across multiple RHEL versions...

  Searching RHEL 9.6 (x86_64)... ✓ Found!

Found 1 match.
Using checksum: febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb

Downloading: rhel-9.6-x86_64-dvd.iso
Destination: ./rhel-9.6-x86_64-dvd.iso
```

### When To Use Filename vs Checksum

| Method | Use Case |
|--------|----------|
| **By Filename** | Quick downloads when you know the filename but not the checksum |
| **By Checksum** | Precise downloads when you need a specific version/build |
| **By Filename** | Automation scripts that always want the latest version |
| **By Checksum** | Production deployments requiring exact version verification |

### Automation Example

```bash
#!/bin/bash
# Always download the latest RHEL 9.6 DVD

rhiso download rhel-9.6-x86_64-dvd.iso --by-filename --output /var/isos

# The tool automatically finds and downloads the most recent version
```
