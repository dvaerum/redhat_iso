# Red Hat ISO Download Tool

A command-line tool to download Red Hat ISO files using the Red Hat Customer Portal API.

## Prerequisites

- Python 3.7 or higher
- Active Red Hat subscription with download access
- Red Hat API offline token

## Installation

### Option 1: Nix (Recommended for NixOS)

**Using nix-build:**
```bash
# Build the package
nix-build shell.nix

# The executable will be available at ./result/bin/rhiso
./result/bin/rhiso --help
./result/bin/rhiso list --version 9.6 --arch x86_64
```

**Using nix run (with flakes):**
```bash
# Run directly without building
nix run . -- --help
nix run . -- list --version 9.6 --arch x86_64
nix run . -- download <checksum>
```

**Using nix-shell for development:**
```bash
nix-shell shell.nix
```

**Using nix build (with flakes):**
```bash
nix build
./result/bin/rhiso --help
```

### Option 2: Python pip

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make the script executable:
```bash
chmod +x rhiso.py
```

### Setup

1. Generate your Red Hat API offline token:
   - Visit https://access.redhat.com/management/api
   - Click "Generate Token"
   - Copy the token

2. Save your token to a file:
```bash
echo "YOUR_OFFLINE_TOKEN_HERE" > redhat-api-token.txt
```

## Usage

### List Available Downloads

The tool can list available ISO files directly from the Red Hat API:

**List currently supported RHEL releases (default):**
```bash
# Automatically discovers and shows latest RHEL versions for x86_64
rhiso list

# Or with nix run:
nix run . -- list

# JSON output for programmatic use:
rhiso --json list
```

**List RHEL images by version and architecture:**
```bash
rhiso list --version 9.6 --arch x86_64
rhiso list --version 8.10 --arch aarch64

# JSON output:
rhiso --json list --version 9.6 --arch x86_64

# Or with direct script:
./rhiso.py list --version 9.6 --arch x86_64
```

**List images from a content set:**
```bash
rhiso list --content-set rhel-9-for-x86_64-baseos-isos
rhiso list --content-set rhel-8-for-aarch64-baseos-isos
```

The list command will display available ISOs with their:
- Filename
- SHA-256 checksum (use this to download)
- Architecture
- Publication date

**Common RHEL versions**: 9.6, 9.5, 9.4, 8.10, 8.9, 8.8, 7.9
**Common architectures**: x86_64, aarch64, ppc64le, s390x

### Download an ISO

**Download by checksum:**
```bash
rhiso download <SHA256_CHECKSUM>

# Example with real checksum from RHEL 9.6:
rhiso download febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb
```

**Download by filename (searches automatically):**
```bash
# The tool will search across RHEL versions and download the latest match
rhiso download rhel-9.6-x86_64-dvd.iso --by-filename
rhiso download rhel-8.10-x86_64-boot.iso --by-filename

# If multiple versions exist with same filename, downloads the most recent
```

Download to a specific directory:
```bash
rhiso download <SHA256_CHECKSUM> --output /path/to/downloads
rhiso download rhel-9.6-x86_64-dvd.iso --by-filename --output ~/Downloads
```

### Custom Token File

If your token is stored in a different file:

```bash
rhiso --token-file /path/to/token.txt download <CHECKSUM>
```

## How It Works

1. **Authentication**: The tool exchanges your offline token for a short-lived access token (valid for 15 minutes)
2. **List**: Queries the Red Hat Subscription Management API to retrieve available images
   - By RHEL version/architecture: `/management/v1/images/rhel/{version}/{arch}`
   - By content set: `/management/v1/images/cset/{content_set}`
3. **Download**: Uses the API endpoint to get the download URL for a specific checksum
   - Endpoint: `/management/v1/images/{checksum}/download`
4. **Progress**: Shows download progress as the file is retrieved

## Example Workflow

```bash
# 1. List available RHEL 9.6 x86_64 ISOs
rhiso list --version 9.6 --arch x86_64

# 2. Copy the checksum from the output (e.g., the Binary DVD)
# 3. Download the ISO using the checksum
rhiso download febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb

# Alternative: Download to specific directory
rhiso download febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb --output ~/downloads
```

## Troubleshooting

### "Token file not found"
Create the `redhat-api-token.txt` file with your offline token from https://access.redhat.com/management/api

### "Error getting access token"
Your offline token may be expired or invalid. Generate a new token at https://access.redhat.com/management/api

### "Error getting download info"
- Verify the checksum is correct (copy from the download page)
- Ensure you have an active subscription with access to the product
- Check that your account has download permissions

## Security Notes

- Keep your `redhat-api-token.txt` file secure
- Add it to `.gitignore` if using version control
- The offline token never expires as long as it's used at least once every 30 days

## License

This tool is provided as-is for use with valid Red Hat subscriptions.
