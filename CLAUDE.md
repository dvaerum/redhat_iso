# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool and library to download Red Hat ISO files using the Red Hat Customer Portal API. Authenticates via OAuth 2.0 using offline tokens, lists available ISOs, and downloads by checksum or filename.

## Commands

### Installation & Setup

```bash
# Nix (recommended for NixOS)
nix-build shell.nix                    # Build package
./result/bin/rhiso --help              # Use built package
nix run . -- list                      # Run without building (flakes)
nix-shell shell.nix                    # Development shell

# Python pip
pip install -r requirements.txt
python -m rhiso list                   # Run as module

# Install as package
pip install -e .                       # Editable install
rhiso --help                           # Use installed command
```

### Token Setup

```bash
# Create token file (required for all operations)
echo "YOUR_OFFLINE_TOKEN" > redhat-api-token.txt
# Generate token at: https://access.redhat.com/management/api
```

### List Available ISOs

```bash
# Default: Auto-discover latest RHEL versions
rhiso list
rhiso --json list                      # JSON output

# By specific version/arch
rhiso list --version 9.6 --arch x86_64
rhiso list --version 8.10 --arch aarch64

# By content set
rhiso list --content-set rhel-9-for-x86_64-baseos-isos
```

### Download ISOs

```bash
# By checksum (precise)
rhiso download <SHA256_CHECKSUM>

# By filename (automatic search)
rhiso download rhel-9.6-x86_64-dvd.iso --by-filename

# Custom output directory
rhiso download <CHECKSUM> --output ~/Downloads

# JSON output
rhiso --json download <CHECKSUM>
```

### Library Usage

```python
from rhiso import RedHatAPI

token = open("redhat-api-token.txt").read().strip()
api = RedHatAPI(token)

# List images
images = api.list_rhel_images("9.6", "x86_64")

# Discover available versions
versions = api.discover_rhel_versions("x86_64")

# Download
api.download_file("checksum_or_filename", output_dir="./downloads")
```

## Architecture

### Module Structure

```
rhiso/
├── __init__.py      # Package exports: RedHatAPI, __version__
├── __main__.py      # Module runner: python -m rhiso
├── api.py           # Core API client (~520 lines)
└── cli.py           # CLI interface (~125 lines)

setup.py             # Package configuration
example_library_usage.py  # Library usage examples
```

### Separation of Concerns

**rhiso/api.py** - Pure API logic
- `RedHatAPI` class: All API interactions, no CLI dependencies
- No print statements for errors in library-style methods (like `version_exists()`)
- Returns data structures; doesn't format output

**rhiso/cli.py** - CLI interface
- Argument parsing with `argparse`
- Token file loading from disk
- Calls `RedHatAPI` methods and handles display
- Entry point: `main()` function

**rhiso/__init__.py** - Public exports
- Exports: `RedHatAPI`, `__version__`
- Package documentation

**rhiso/__main__.py** - Module runner
- Enables: `python -m rhiso`

### RedHatAPI Class Methods

**Authentication:**
- `get_access_token()`: Exchange offline token for 15-minute access token via OAuth 2.0

**Listing:**
- `list_rhel_images(version, arch)`: List ISOs for specific RHEL version/arch
- `list_images_by_content_set(content_set)`: List ISOs from content set
- `list_downloads(...)`: Main CLI listing function with formatted output

**Version Discovery:**
- `version_exists(version, arch)`: Quietly check if version has ISOs (no error prints)
- `discover_rhel_versions(arch)`: Auto-discover available RHEL versions by API probing
  - Caches results per architecture for session
  - Baseline: RHEL 10, 9, 8 series with known minors
  - Forward discovery: Probes for RHEL 11+, newer minors
  - Returns sorted list: newest first

**Search & Download:**
- `find_image_by_filename(filename)`: Search across versions for filename (with progress prints)
- `get_download_info(checksum)`: Get download URL for checksum
- `download_file(identifier, ...)`: Download by checksum or filename with progress

### Authentication Flow

1. Read offline token from `redhat-api-token.txt` (or custom path via `--token-file`)
2. POST to `https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token`
   - Client ID: `rhsm-api`
   - Grant type: `refresh_token`
   - Offline token in `refresh_token` field
3. Receive access token (valid 15 minutes)
4. Use in `Authorization: Bearer` header for all API calls

### Version Discovery Algorithm

The tool automatically discovers available RHEL versions without hardcoded lists:

1. **Baseline Probing**: Check known stable versions (10.0, 9.6, 9.5, 9.4, 8.10, 8.9, 8.8)
2. **Forward Discovery**:
   - Try major versions 11-14 (.0 release first)
   - If major.0 exists, probe minor versions 1-9
   - Try 4 minor versions ahead of known minors for existing majors
3. **API Probing**: Call `/images/rhel/{version}/{arch}` and check for ISO files
4. **Caching**: Results cached in `_discovered_versions_cache[arch]` for session
5. **Sorting**: Returns versions newest-first

This ensures the tool always shows latest RHEL releases without code updates.

### Download by Filename Flow

When `--by-filename` flag is used:

1. Call `discover_rhel_versions()` for x86_64 and aarch64
2. Search x86_64 first (most common), then aarch64
3. For each version (newest first):
   - Call `list_rhel_images(version, arch)`
   - Check if any image has matching filename
   - Print progress: "Searching RHEL X.Y (arch)... ✓ Found!" or " -"
   - Early exit on first match (searches newest first)
4. If multiple matches, select most recent by `datePublished`
5. Extract checksum and download via `get_download_info()`

### JSON Output

When `--json` flag is used:
- All print statements suppressed (progress, search messages, etc.)
- Results output as JSON to stdout
- Errors output as JSON to stderr
- Used for automation and scripting

See JSON_OUTPUT.md for format details.

## API Endpoints

**Red Hat RHSM API Base:** `https://api.access.redhat.com/management/v1`

- `/images/rhel/{version}/{arch}` - List ISOs by RHEL version/architecture
- `/images/cset/{content_set}` - List ISOs by content set
- `/images/{checksum}/download` - Get download URL (returns 307 redirect with JSON body)

**OAuth 2.0:** `https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token`

## Configuration

**redhat-api-token.txt** - Red Hat API offline token
- Generate at: https://access.redhat.com/management/api
- Must be used at least once every 30 days
- In .gitignore (never commit)

## Common RHEL Metadata

**Versions**: 10.0, 9.6, 9.5, 9.4, 8.10, 8.9, 8.8, 7.9

**Architectures**: x86_64, aarch64, ppc64le, s390x

**Content Sets**:
- `rhel-10-for-x86_64-baseos-isos`
- `rhel-9-for-x86_64-baseos-isos`
- `rhel-8-for-x86_64-baseos-isos`
- `rhel-9-for-aarch64-baseos-isos`

## Development Guidelines

### When Modifying API Logic (rhiso/api.py)

- Keep it CLI-agnostic: return data, don't print output
- Exception: methods explicitly for CLI (like `list_downloads()`, `find_image_by_filename()`)
- Quiet methods like `version_exists()` should never print to stdout/stderr
- Cache expensive operations (like version discovery)
- Handle `requests.RequestException` gracefully

### When Modifying CLI (rhiso/cli.py)

- All user-facing output happens here
- Argument parsing with `argparse`
- Call `RedHatAPI` methods, format results
- Handle `--json` flag: suppress prints, output JSON

### Adding New Features

1. Add method to `RedHatAPI` class in `api.py`
2. If CLI command needed, add to `cli.py`:
   - Add subparser or argument
   - Call new method from `main()`
3. If library-only, just export from `__init__.py`
4. Update documentation (README.md, USAGE_EXAMPLES.md, LIBRARY_USAGE.md)

### Nix Packaging

- **flake.nix**: Uses flake-utils, imports default.nix
- **default.nix**: Main package definition with `buildPythonApplication`
- **shell.nix**: Development shell, imports default.nix
- Entry point: `rhiso.cli:main` via setuptools console_scripts
- Dependencies: Python 3.7+, requests>=2.31.0

## Testing

```bash
# Build and test CLI
nix-build shell.nix
./result/bin/rhiso list
./result/bin/rhiso --json list

# Test as module
nix-shell shell.nix --run "python -m rhiso list"

# Test library usage
nix-shell shell.nix --run "python example_library_usage.py"

# Test with custom token file
./result/bin/rhiso --token-file /path/to/token.txt list
```

## Security Considerations

- API token file excluded from git via .gitignore
- Access tokens expire after 15 minutes
- Never log or print token values
- Requires valid Red Hat subscription with download permissions
