# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool and library to download Red Hat ISO files using the Red Hat Customer Portal API. Includes NixOS module for declarative ISO downloads. Authenticates via OAuth 2.0 using offline tokens, lists available ISOs, and downloads by checksum or filename.

**Key Features:**
- CLI tool and Python library
- NixOS overlay and module for system integration
- Automatic version discovery (no hardcoded RHEL versions)
- Download by checksum (immutable) or filename (latest)
- SHA-256 verification of all downloads
- JSON output for automation
- Comprehensive NixOS integration tests

## Project Structure

```
.
├── redhat_iso/                  # Python package
│   ├── __init__.py             # Public exports: RedHatAPI, __version__
│   ├── __main__.py             # Module runner (python -m redhat_iso)
│   ├── api.py                  # Core API logic (~520 lines)
│   └── cli.py                  # CLI interface (~125 lines)
│
├── modules/                     # NixOS integration
│   └── redhat-iso-downloader.nix  # NixOS module (~264 lines)
│
├── tests/                       # Testing infrastructure
│   ├── integration.nix         # NixOS VM tests (10 subtests)
│   └── README.md               # Test documentation pointer
│
├── docs/                        # All documentation
│   ├── README.md               # Documentation index
│   ├── features.md             # Feature list
│   │
│   ├── usage/                  # User guides
│   │   ├── cli-examples.md    # CLI usage examples
│   │   ├── library.md         # Python library API
│   │   └── json-output.md     # JSON format specs
│   │
│   ├── nixos/                  # NixOS-specific
│   │   ├── installation.md    # Integration guide
│   │   ├── module-options.md  # Auto-generated options
│   │   └── packaging.md       # Nix internals
│   │
│   └── development/            # Developer docs
│       ├── architecture.md    # Code structure
│       └── testing.md         # Testing guide
│
├── .github/workflows/           # CI/CD
│   └── update-docs.yml         # Auto-documentation workflow
│
├── examples/                    # Code examples
├── flake.nix                    # Nix flake (overlay + module)
├── default.nix                  # Package definition
├── shell.nix                    # Development shell
├── generate-doc.nix            # Documentation generator
├── setup.py                     # Python packaging
├── requirements.txt             # Python dependencies
│
├── CLAUDE.md                    # Development guide (this file)
└── README.md                    # User-facing quick start
```

## Commands

### Installation & Setup

```bash
# Nix (recommended for NixOS)
nix-build shell.nix                    # Build package
./result/bin/redhat_iso --help              # Use built package
nix run . -- list                      # Run without building (flakes)
nix-shell shell.nix                    # Development shell

# Python pip
pip install -r requirements.txt
python -m redhat_iso list                   # Run as module

# Install as package
pip install -e .                       # Editable install
redhat_iso --help                           # Use installed command
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
redhat_iso list
redhat_iso --json list                      # JSON output

# By specific version/arch
redhat_iso list --version 9.6 --arch x86_64
redhat_iso list --version 8.10 --arch aarch64

# By content set
redhat_iso list --content-set rhel-9-for-x86_64-baseos-isos
```

### Download ISOs

```bash
# By checksum (precise)
redhat_iso download <SHA256_CHECKSUM>

# By filename (automatic search)
redhat_iso download rhel-9.6-x86_64-dvd.iso --by-filename

# Custom output directory
redhat_iso download <CHECKSUM> --output ~/Downloads

# JSON output
redhat_iso --json download <CHECKSUM>
```

### Library Usage

```python
from redhat_iso import RedHatAPI

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
redhat_iso/
├── __init__.py      # Package exports: RedHatAPI, __version__
├── __main__.py      # Module runner: python -m redhat_iso
├── api.py           # Core API client (~520 lines)
└── cli.py           # CLI interface (~125 lines)

setup.py             # Package configuration
example_library_usage.py  # Library usage examples
```

### Separation of Concerns

**redhat_iso/api.py** - Pure API logic
- `RedHatAPI` class: All API interactions, no CLI dependencies
- No print statements for errors in library-style methods (like `version_exists()`)
- Returns data structures; doesn't format output

**redhat_iso/cli.py** - CLI interface
- Argument parsing with `argparse`
- Token file loading from disk
- Calls `RedHatAPI` methods and handles display
- Entry point: `main()` function

**redhat_iso/__init__.py** - Public exports
- Exports: `RedHatAPI`, `__version__`
- Package documentation

**redhat_iso/__main__.py** - Module runner
- Enables: `python -m redhat_iso`

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
- `download_file(identifier, ...)`: Download by checksum or filename with progress and automatic SHA-256 verification
- `calculate_sha256(file_path)`: Calculate SHA-256 checksum of a file (static method)

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
6. After download: Calculate SHA-256 of file and verify against expected checksum
7. If mismatch: Delete file and exit with error; If match: Report success

### JSON Output

When `--json` flag is used:
- All print statements suppressed (progress, search messages, etc.)
- Results output as JSON to stdout
- Errors output as JSON to stderr
- Used for automation and scripting

See [docs/usage/json-output.md](docs/usage/json-output.md) for format details.

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

### When Modifying API Logic (redhat_iso/api.py)

- Keep it CLI-agnostic: return data, don't print output
- Exception: methods explicitly for CLI (like `list_downloads()`, `find_image_by_filename()`)
- Quiet methods like `version_exists()` should never print to stdout/stderr
- Cache expensive operations (like version discovery)
- Handle `requests.RequestException` gracefully

### When Modifying CLI (redhat_iso/cli.py)

- All user-facing output happens here
- Argument parsing with `argparse`
- Call `RedHatAPI` methods, format results
- Handle `--json` flag: suppress prints, output JSON

### Adding New Features

**For CLI/API features:**
1. Add method to `RedHatAPI` class in `api.py`
2. If CLI command needed, add to `cli.py`:
   - Add subparser or argument
   - Call new method from `main()`
3. If library-only, just export from `__init__.py`
4. Update documentation (see below)

**For NixOS module features:**
1. Add option to `modules/redhat-iso-downloader.nix`:
   - Define option in `options.services.redhat-iso-downloader`
   - Use in `config` section (script generation or service config)
2. Update `generate-doc.nix` if needed (usually automatic)
3. Run `nix-build generate-doc.nix` to verify docs generate correctly
4. Add test case to `tests/integration.nix`
5. Run `nix flake check` to verify all tests pass
6. Documentation auto-updates via GitHub Actions on push

**Documentation files to update:**
- `CLAUDE.md`: Architecture and commands (this file)
- `README.md`: User-facing quick start
- `docs/README.md`: Documentation index if adding new docs
- `docs/usage/cli-examples.md`: CLI usage examples
- `docs/usage/library.md`: Python library API examples
- `docs/nixos/installation.md`: NixOS integration guide
- `docs/nixos/module-options.md`: Auto-generated from `generate-doc.nix`

### Nix Packaging

- **flake.nix**: Uses flake-utils, provides overlay and NixOS module
  - `overlays.default`: Adds `redhat_iso` package
  - `nixosModules.default`: Imports `modules/redhat-iso-downloader.nix`
  - `packages.default`: CLI package from `default.nix`
  - `checks.integration`: NixOS integration tests from `tests/integration.nix`
- **default.nix**: Main package definition with `buildPythonApplication`
- **shell.nix**: Development shell, imports default.nix
- **generate-doc.nix**: Documentation generator using `nixosOptionsDoc`
- Entry point: `redhat_iso.cli:main` via setuptools console_scripts
- Dependencies: Python 3.7+, requests>=2.31.0

### NixOS Module Structure

**modules/redhat-iso-downloader.nix** (~264 lines)

The NixOS module enables declarative ISO downloads:

**Key Components:**
1. **Options Definition** (lines 90-191):
   - `enable`: Toggle service
   - `tokenFile`: Path to API token (supports secrets managers)
   - `outputDir`: Download directory
   - `downloads`: List of submodules with `checksum` and `filename` fields
   - `runOnBoot`: Control automatic execution

2. **Download Script Generation** (lines 8-87):
   - `downloadIsoScript`: Generates shell script per download
   - Supports 3 modes: checksum-only, filename-only, both (with verification)
   - `downloadAllScript`: Master script that orchestrates all downloads
   - Validates token file exists and creates output directory

3. **Configuration** (lines 193-262):
   - **Assertions**: Validates downloads list and each entry has checksum or filename
   - **Package Installation**: Adds `pkgs.redhat_iso` to system packages
   - **Systemd Service**: oneshot service with network dependencies
   - **Security Hardening**: PrivateTmp, ProtectSystem=strict, NoNewPrivileges
   - **Tmpfiles Rules**: Creates output directory with 0755 permissions

**Module Design Principles:**
- Declarative: All config in NixOS configuration.nix
- Flexible: Supports immutable (checksum) or dynamic (filename) downloads
- Secure: Integrates with agenix/sops-nix for token management
- Idempotent: Safe to run multiple times (redhat_iso handles deduplication)
- Validated: Build-time assertions catch configuration errors

## Testing

### CLI and Package Testing

```bash
# Build and test CLI
nix-build shell.nix
./result/bin/redhat_iso list
./result/bin/redhat_iso --json list

# Test as module
nix-shell shell.nix --run "python -m redhat_iso list"

# Test library usage
nix-shell shell.nix --run "python example_library_usage.py"

# Test with custom token file
./result/bin/redhat_iso --token-file /path/to/token.txt list
```

### NixOS Integration Tests

The project includes comprehensive NixOS integration tests using NixOS's VM testing framework:

```bash
# Run all tests (includes integration tests)
nix flake check

# Run integration tests specifically
nix build .#checks.x86_64-linux.integration -L

# Traditional nix-build
nix-build tests/integration.nix

# Run with detailed output and keep failed builds
nix build .#checks.x86_64-linux.integration -L --keep-failed
```

**Test Architecture:**
- Located in `tests/integration.nix`
- Uses mock `redhat_iso` (no network/token required)
- Spins up QEMU VM with the NixOS module
- Tests: 10 subtests covering module config, systemd, security, and downloads
- Performance: ~20 seconds (cached), 2-5 minutes (first run)
- See `tests/README.md` for comprehensive test documentation

**What's Tested:**
- Package installation and CLI functionality
- Systemd service configuration (oneshot, network dependencies)
- Security hardening (PrivateTmp, ProtectSystem, NoNewPrivileges)
- File system permissions (output dir, token file)
- Download functionality with mock data
- Service idempotency (safe to run multiple times)
- Configuration validation and assertions

### Documentation Generation

```bash
# Generate module options documentation
nix-build generate-doc.nix

# View generated docs
cat result

# Documentation is auto-generated to docs/options.md by GitHub Actions
```

**How it works:**
- `generate-doc.nix` uses `nixosOptionsDoc` to extract options programmatically
- Provides minimal NixOS infrastructure for module evaluation
- Filters to only document `services.redhat-iso-downloader` options
- GitHub Actions workflow (`.github/workflows/update-docs.yml`) runs on every push
- Auto-commits updated docs to `docs/nixos/module-options.md` if changes detected

## CI/CD

### GitHub Actions Workflows

**.github/workflows/update-docs.yml** - Auto-Documentation

Runs on every push to any branch:

1. **Setup**: Checks out code, configures git user, installs Nix
2. **Build**: Runs `nix-build generate-doc.nix` to generate docs
3. **Update**: Copies result to `docs/nixos/module-options.md`
4. **Commit**: Commits and pushes if changes detected

**Requirements:**
- SSH deploy key configured as `SSH_PRIVATE_KEY` secret
- Deploy key must have write access
- See workflow comments for setup instructions

**Setup SSH Deploy Key:**
```bash
# 1. Generate key pair
ssh-keygen -t ed25519 -N "" -f /tmp/github

# 2. Add private key as Actions secret:
#    Settings → Secrets → Actions → New secret
#    Name: SSH_PRIVATE_KEY
#    Value: Contents of /tmp/github

# 3. Add public key as Deploy Key:
#    Settings → Deploy keys → Add deploy key
#    Title: Github Action Key
#    Key: Contents of /tmp/github.pub
#    ☑ Allow write access
```

## Security Considerations

- API token file excluded from git via .gitignore
- Access tokens expire after 15 minutes
- Never log or print token values
- Requires valid Red Hat subscription with download permissions
- **Automatic SHA-256 verification**: All downloads are verified against expected checksums
  - Corrupted or tampered files are detected and deleted
  - Ensures data integrity and authenticity
