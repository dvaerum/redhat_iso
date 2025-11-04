# NixOS Integration Tests

This directory contains NixOS integration tests for the redhat-iso-downloader module.

## Test Suite

### **Integration Tests** (`integration.nix`)
Comprehensive tests covering module configuration, systemd setup, security hardening, and download functionality.

**Uses mock `redhat_iso` - no network or Red Hat token required.**

## Running Tests

### Using Nix Flakes (Recommended)

**Run all checks:**
```bash
nix flake check
```

**Run integration tests:**
```bash
nix build .#checks.x86_64-linux.integration -L
```

### Using nix-build (Traditional Nix)

```bash
nix-build tests/integration.nix
```

## What the Tests Cover

The integration test suite (`integration.nix`) provides comprehensive testing with **10 subtests**:

### ✅ **Package Installation**
- `redhat_iso` CLI tool is available
- Help command works correctly

### ✅ **Systemd Service Configuration**
- Service is properly defined
- Service type is `oneshot`
- Service has `RemainAfterExit` enabled
- Service waits for network (`network-online.target`)

### ✅ **Security Hardening**
- `PrivateTmp` is enabled
- `ProtectSystem=strict` is set
- `ProtectHome` is enabled
- `NoNewPrivileges` is enabled
- Read-write paths are restricted

### ✅ **File System**
- Output directory is created with correct permissions (755)
- Token file exists with secure permissions (600)
- tmpfiles.d rules are applied

### ✅ **Download Functionality (Mock)**
- Service runs successfully on boot
- Downloads complete successfully
- Files are created in output directory
- Service logs show expected behavior

### ✅ **Service Idempotency**
- Safe to run multiple times
- No duplicate downloads
- Existing files are preserved

### ✅ **Configuration Validation**
- Module options are properly typed
- Assertions catch configuration errors at build time

## Test Architecture

The test uses NixOS's built-in testing framework which:

1. **Creates a VM**: Spins up a QEMU VM with the test configuration
2. **Applies Configuration**: Installs the module with mock `redhat_iso`
3. **Runs Python Tests**: Executes 10 test scenarios in the VM
4. **Reports Results**: Returns success/failure

## Test Configuration

The test VM is configured with:
- Mock `redhat_iso` tool (simulates downloads without network)
- `redhat-iso-downloader` module enabled
- Fake API token for testing
- Output directory: `/var/lib/test-isos`
- Service runs on boot

## Debugging Failed Tests

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

## Adding More Tests

To add additional test scenarios, edit `integration.nix` and add new subtests:

```python
with subtest("your test description"):
    machine.succeed("command that should succeed")
    result = machine.succeed("command with output")
    assert "expected" in result, "assertion message"
```

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
