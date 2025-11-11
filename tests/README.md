# NixOS Integration Tests

This directory contains the NixOS integration test suite for the redhat-iso-downloader module.

## Quick Start

```bash
# Run all tests
nix flake check

# Run integration tests with detailed output
nix build .#checks.x86_64-linux.integration -L

# Traditional nix-build
nix-build tests/integration.nix
```

## Test Suite

- **`integration.nix`** - Complete NixOS VM-based integration tests (13 subtests)
  - Tests module configuration, systemd setup, security hardening, and downloads
  - Uses mock `redhat_iso` - no network or token required
  - Performance: ~20 seconds (cached), 2-5 minutes (first run)

## Comprehensive Documentation

For detailed testing documentation including:
- Complete test coverage details
- Debugging failed tests
- Manual CLI testing procedures
- API integration testing
- Adding new tests

See: **[docs/development/testing.md](../docs/development/testing.md)**

## What's Tested

✅ Package installation and CLI functionality
✅ Systemd service configuration (oneshot, network dependencies)
✅ Security hardening (PrivateTmp, ProtectSystem, NoNewPrivileges)
✅ File system permissions (output dir, token file)
✅ Download functionality with mock data (by checksum and by filename)
✅ Service idempotency (safe to run multiple times)
✅ `--by-filename` skips existing files (no re-download)
✅ `--by-filename --force` re-downloads existing files
✅ Configuration validation and assertions
