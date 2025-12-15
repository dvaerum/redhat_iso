# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python CLI tool and library to download Red Hat ISO files using the Red Hat Customer Portal API. Includes NixOS module for declarative ISO downloads. Authenticates via OAuth 2.0 using offline tokens, lists available ISOs, and downloads by checksum or filename with automatic SHA-256 verification.

## Commands

### Build & Run

```bash
# Nix (recommended)
nix-build shell.nix && ./result/bin/redhat_iso --help
nix run . -- list                           # Flakes: run without building
nix-shell shell.nix                         # Development shell

# Python
pip install -e .                            # Editable install
python -m redhat_iso list                   # Run as module
```

### Testing

```bash
# NixOS integration tests (spins up QEMU VM with mock redhat_iso)
nix flake check                             # Run all checks
nix build .#checks.x86_64-linux.integration -L  # Run integration tests

# Documentation generation
nix-build generate-doc.nix && cat result
```

### CLI Usage

```bash
# Token setup (required)
echo "YOUR_OFFLINE_TOKEN" > redhat-api-token.txt

# List ISOs
redhat_iso list                             # Auto-discover latest versions
redhat_iso list --version 9.6 --arch x86_64
redhat_iso --json list                      # JSON output for automation

# Download
redhat_iso download <SHA256_CHECKSUM>
redhat_iso download rhel-9.6-x86_64-dvd.iso --by-filename
redhat_iso download <CHECKSUM> --output ~/Downloads --force
```

## Architecture

### Separation of Concerns

**`redhat_iso/api.py`** - Pure API logic (`RedHatAPI` class)
- All API interactions, returns data structures
- Library-style methods (`version_exists()`) never print to stdout/stderr
- Exception: CLI-oriented methods (`list_downloads()`, `find_image_by_filename()`) may print progress

**`redhat_iso/cli.py`** - CLI interface
- Argument parsing with `argparse`, entry point: `main()`
- All user-facing output, handles `--json` flag

**`modules/redhat-iso-downloader.nix`** - NixOS module
- Declarative ISO downloads via systemd oneshot service
- Options: `enable`, `tokenFile`, `outputDir`, `downloads`, `runOnBoot`
- Three download modes: checksum-only (immutable), filename-only, both (with verification)
- Security hardening: PrivateTmp, ProtectSystem=strict, NoNewPrivileges

### Key Algorithms

**Version Discovery** (`discover_rhel_versions`):
- Probes API to find available versions without hardcoded lists
- Baseline: RHEL 10, 9, 8 known minors; forward discovery: majors 11-14, newer minors
- Caches results per architecture in `_discovered_versions_cache`

**Download by Filename** (`find_image_by_filename`):
- Searches x86_64 then aarch64, newest versions first
- Early exit on first match; if multiple, selects most recent by `datePublished`

### API Endpoints

- **Base**: `https://api.access.redhat.com/management/v1`
- `/images/rhel/{version}/{arch}` - List ISOs
- `/images/cset/{content_set}` - List by content set
- `/images/{checksum}/download` - Get download URL (307 redirect with JSON)
- **OAuth**: `https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token` (client_id: `rhsm-api`)

## Development Guidelines

### Modifying Code

- **api.py**: Keep CLI-agnostic, return data not formatted output. Cache expensive operations. Handle `requests.RequestException`.
- **cli.py**: All user output here. Suppress prints when `--json`, output JSON to stdout, errors to stderr.
- **NixOS module**: Add options in `options.services.redhat-iso-downloader`, add assertions for validation, add test cases to `tests/integration.nix`.

### Adding Features

1. Add method to `RedHatAPI` in `api.py`
2. If CLI needed, add subparser/argument in `cli.py`
3. Export from `__init__.py` if library-only
4. For NixOS: update module, run `nix flake check`
5. Documentation auto-updates via GitHub Actions

### Nix Packaging

- **flake.nix**: `overlays.default`, `nixosModules.default`, `packages.default`, `checks.integration`
- **default.nix**: `buildPythonApplication` with `requests` dependency
- Entry point: `redhat_iso.cli:main` via setuptools console_scripts

## Reference

**Token**: Generate at https://access.redhat.com/management/api (must be used every 30 days)

**Versions**: 10.0, 9.6, 9.5, 9.4, 8.10, 8.9, 8.8, 7.9

**Architectures**: x86_64, aarch64, ppc64le, s390x

**Content Sets**: `rhel-{10,9,8}-for-{x86_64,aarch64}-baseos-isos`
