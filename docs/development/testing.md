# Testing Guide

This document describes the testing infrastructure and how to run tests for the Red Hat ISO Download Tool.

## Overview

The project includes multiple types of tests:
- **NixOS Integration Tests**: Automated VM-based tests of the NixOS module
- **Manual CLI Testing**: Testing the CLI tool functionality
- **Package Building**: Verifying Nix package builds correctly

## NixOS Integration Tests

### About

Comprehensive integration tests using NixOS's VM testing framework. Tests the entire NixOS module including systemd service, security hardening, and download functionality.

**Key Features:**
- Uses mock `redhat_iso` - no network or Red Hat token required
- Spins up QEMU VM with the test configuration
- Runs 10 subtests covering all aspects of the module
- Fast: ~20 seconds (cached), 2-5 minutes (first run)

### Running Tests

```bash
# Run all checks (includes integration tests)
nix flake check

# Run integration tests specifically
nix build .#checks.x86_64-linux.integration -L

# Traditional nix-build
nix-build tests/integration.nix

# Run with detailed output and keep failed builds for debugging
nix build .#checks.x86_64-linux.integration -L --keep-failed
```

### What's Tested

The integration test suite (`tests/integration.nix`) provides comprehensive testing with **10 subtests**:

#### ✅ **Package Installation**
- `redhat_iso` CLI tool is available
- Help command works correctly

#### ✅ **Systemd Service Configuration**
- Service is properly defined
- Service type is `oneshot`
- Service has `RemainAfterExit` enabled
- Service waits for network (`network-online.target`)

#### ✅ **Security Hardening**
- `PrivateTmp` is enabled
- `ProtectSystem=strict` is set
- `ProtectHome` is enabled
- `NoNewPrivileges` is enabled
- Read-write paths are restricted

#### ✅ **File System**
- Output directory is created with correct permissions (755)
- Token file exists with secure permissions (600)
- tmpfiles.d rules are applied

#### ✅ **Download Functionality (Mock)**
- Service runs successfully on boot
- Downloads complete successfully
- Files are created in output directory
- Service logs show expected behavior

#### ✅ **Service Idempotency**
- Safe to run multiple times
- No duplicate downloads
- Existing files are preserved

#### ✅ **Configuration Validation**
- Module options are properly typed
- Assertions catch configuration errors at build time

### Test Architecture

The test uses NixOS's built-in testing framework which:

1. **Creates a VM**: Spins up a QEMU VM with the test configuration
2. **Applies Configuration**: Installs the module with mock `redhat_iso`
3. **Runs Python Tests**: Executes 10 test scenarios in the VM
4. **Reports Results**: Returns success/failure

### Test Configuration

The test VM is configured with:
- Mock `redhat_iso` tool (simulates downloads without network)
- `redhat-iso-downloader` module enabled
- Fake API token for testing
- Output directory: `/var/lib/test-isos`
- Service runs on boot

### Debugging Failed Tests

If a test fails, you can inspect the VM interactively:

```bash
# Run the test and drop into a shell on failure
nix build .#checks.x86_64-linux.integration -L --keep-failed

# The failed VM will be kept in /tmp/nix-build-*
# You can examine logs there
```

To see detailed test output:
```bash
nix build .#checks.x86_64-linux.integration -L 2>&1 | tee test-output.log
```

### Adding More Tests

To add additional test scenarios, edit `tests/integration.nix` and add new subtests:

```python
with subtest("your test description"):
    machine.succeed("command that should succeed")
    result = machine.succeed("command with output")
    assert "expected" in result, "assertion message"
```

## Manual CLI Testing

### Build and Test CLI

```bash
# Build the package
nix-build shell.nix

# Test basic functionality
./result/bin/redhat_iso --help
./result/bin/redhat_iso list
./result/bin/redhat_iso --json list

# Test as module
nix-shell shell.nix --run "python -m redhat_iso list"

# Test library usage
nix-shell shell.nix --run "python example_library_usage.py"

# Test with custom token file
./result/bin/redhat_iso --token-file /path/to/token.txt list
```

### Test Different Scenarios

#### 1. List RHEL 9.6 x86_64 Images ✅
```bash
./result/bin/redhat_iso list --version 9.6 --arch x86_64
```
**Expected:** Successfully retrieves images including Boot ISO and Binary DVD

#### 2. List by Content Set ✅
```bash
./result/bin/redhat_iso list --content-set rhel-9-for-x86_64-baseos-isos
```
**Expected:** Retrieves multiple RHEL 9.x images from the content set

#### 3. Download by Checksum ✅
```bash
./result/bin/redhat_iso download <SHA256_CHECKSUM>
```
**Expected:** Downloads ISO, shows progress, verifies checksum

#### 4. Download by Filename ✅
```bash
./result/bin/redhat_iso download rhel-9.6-x86_64-dvd.iso --by-filename
```
**Expected:** Searches for filename, downloads when found

#### 5. JSON Output ✅
```bash
./result/bin/redhat_iso --json list --version 9.6 --arch x86_64
```
**Expected:** Returns valid JSON, no progress/status messages

### Verified Test Checksums

Real checksums from Red Hat that can be used for testing downloads:

| Product | Checksum |
|---------|----------|
| RHEL 9.6 Binary DVD | `febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb` |
| RHEL 9.6 Boot ISO | `36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63` |
| RHEL 8.10 Binary DVD | `9b3c8e31bc2cdd2de9cf96abb3726347f5840ff3b176270647b3e66639af291b` |
| RHEL 8.10 Boot ISO | `6ced368628750ff3ea8a2fc52a371ba368d3377b8307caafda69070849a9e4e7` |

## API Integration Testing

### Authentication ✅
- OAuth 2.0 token exchange working correctly
- Offline token → Access token conversion functional
- API calls authenticated successfully with Bearer token
- Token endpoint: `https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token`

### API Endpoints ✅
1. `/management/v1/images/rhel/{version}/{arch}` - List RHEL images by version/architecture
2. `/management/v1/images/cset/{content_set}` - List images from content set
3. `/management/v1/images/{checksum}/download` - Get download URL for checksum

## CI/CD Integration

These tests can be run in CI/CD pipelines:

### GitHub Actions
```yaml
- name: Run NixOS tests
  run: nix flake check
```

### GitLab CI
```yaml
test:
  script:
    - nix flake check
```

## Performance

The integration test typically takes:
- **First run**: 2-5 minutes (builds VM image)
- **Subsequent runs**: ~20 seconds (cached)
- **10 subtests**: Completes in under 20 seconds

## Testing Philosophy

**Mock-Based Testing**: Uses mock `redhat_iso` instead of real downloads because:
- ✅ **Fast**: No large ISO downloads
- ✅ **Reliable**: No network dependencies
- ✅ **Reproducible**: Same results every time
- ✅ **Pure**: Can run in isolated environments (CI/CD)

**For Real Downloads**: Test the CLI directly on your system:
```bash
# Test real download functionality
nix run .#packages.x86_64-linux.default -- \
  --token-file redhat-api-token.txt \
  download <checksum>
```

## Test Maintenance

When updating the module, ensure tests are updated to cover:
- New configuration options
- Changed behavior
- Security improvements
- Error handling

Run tests before committing changes:
```bash
nix flake check && git commit
```

## System Requirements

✅ Python 3.7+ (tested with Python 3.13)
✅ Active Red Hat subscription (for manual testing)
✅ Red Hat API offline token (for manual testing)
✅ requests library (only dependency)
✅ Nix package system

## Related Documentation

- [Integration Test Source](../../tests/integration.nix) - The actual test code
- [Architecture Guide](architecture.md) - Understanding the codebase structure
- [CLI Examples](../usage/cli-examples.md) - More usage examples
