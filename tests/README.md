# NixOS Integration Tests

This directory contains NixOS integration tests for the redhat-iso-downloader module.

## Running Tests

### Using Nix Flakes (Recommended)

Run all checks (includes integration tests):
```bash
nix flake check
```

Run only the integration test:
```bash
nix build .#checks.x86_64-linux.integration
```

Run the integration test with verbose output:
```bash
nix build .#checks.x86_64-linux.integration -L
```

### Using nix-build (Traditional Nix)

```bash
nix-build tests/integration.nix
```

## What the Tests Cover

The integration test suite (`integration.nix`) verifies:

### ✅ Package Installation
- `redhat_iso` CLI tool is available
- Help command works correctly

### ✅ Systemd Service
- Service is properly defined
- Service type is `oneshot`
- Service has `RemainAfterExit` enabled
- Service waits for network (`network-online.target`)

### ✅ Security Hardening
- `PrivateTmp` is enabled
- `ProtectSystem=strict` is set
- `ProtectHome` is enabled
- `NoNewPrivileges` is enabled
- Read-write paths are restricted

### ✅ File System
- Output directory is created with correct permissions (755)
- Token file exists with secure permissions (600)
- tmpfiles.d rules are applied

### ✅ Service Operation
- Service can be triggered manually
- Service logs are accessible via journalctl
- Service attempts to download ISOs (fails gracefully without real token)

### ✅ Configuration Validation
- Module options are properly typed
- Assertions catch configuration errors at build time

## Test Architecture

The test uses NixOS's built-in testing framework which:

1. **Creates a VM**: Spins up a QEMU VM with the test configuration
2. **Applies Configuration**: Installs the module and test config
3. **Runs Python Tests**: Executes test scenarios in the VM
4. **Reports Results**: Returns success/failure

## Test Configuration

The test VM is configured with:
- The `redhat-iso-downloader` module enabled
- A fake API token (for testing service startup)
- Test ISO configuration (doesn't download real files)
- Output directory: `/var/lib/test-isos`

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
- **Subsequent runs**: 30-60 seconds (cached)

## Known Limitations

1. **No Real Downloads**: Tests don't download actual RHEL ISOs (would be too large)
2. **Mocked Token**: Uses a fake API token (real downloads would fail)
3. **Network Isolation**: VM has limited network access by design

These limitations are intentional to keep tests:
- Fast
- Reliable
- Reproducible
- Independent of external services

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
