{ pkgs ? import <nixpkgs> {}, system ? builtins.currentSystem }:

let
  # Mock redhat_iso script for integration tests
  # This simulates successful downloads without needing network/token
  mockRedhatIso = pkgs.writeShellScriptBin "redhat_iso" ''
    #!/usr/bin/env bash
    set -e

    # Parse arguments
    TOKEN_FILE=""
    CHECKSUM_OR_FILENAME=""
    OUTPUT_DIR="."
    BY_FILENAME=false
    FORCE=false

    while [[ $# -gt 0 ]]; do
      case $1 in
        --token-file)
          TOKEN_FILE="$2"
          shift 2
          ;;
        --output)
          OUTPUT_DIR="$2"
          shift 2
          ;;
        --by-filename)
          BY_FILENAME=true
          shift
          ;;
        --force)
          FORCE=true
          shift
          ;;
        download)
          shift
          CHECKSUM_OR_FILENAME="$1"
          shift
          ;;
        --help)
          echo "Red Hat ISO Download Tool"
          echo "Usage: redhat_iso [--token-file FILE] download CHECKSUM [--output DIR] [--by-filename] [--force]"
          exit 0
          ;;
        *)
          shift
          ;;
      esac
    done

    # Verify token file exists
    if [ ! -f "$TOKEN_FILE" ]; then
      echo "Error: Token file not found: $TOKEN_FILE" >&2
      exit 1
    fi

    # Determine filename
    if [ "$BY_FILENAME" = true ]; then
      FILENAME="$CHECKSUM_OR_FILENAME"

      # NEW BEHAVIOR: Check if file exists when using --by-filename (unless --force)
      if [ "$FORCE" = false ] && [ -f "$OUTPUT_DIR/$FILENAME" ]; then
        echo "File already exists: $OUTPUT_DIR/$FILENAME"
        echo "Use --force to re-download."
        echo ""
        echo "Download skipped - file already exists!"
        echo "  File: $FILENAME"
        echo "  Path: $OUTPUT_DIR/$FILENAME"
        echo "  Size: $(stat -c%s "$OUTPUT_DIR/$FILENAME") bytes"
        exit 0
      fi
    else
      # Download by checksum - use generic filename
      FILENAME="test-rhel.iso"
    fi

    # Create a simple test ISO file
    echo "Mock ISO content" > "$OUTPUT_DIR/$FILENAME"
    echo "Downloaded: $FILENAME"
    exit 0
  '';

in pkgs.testers.nixosTest {
  name = "redhat-iso-downloader";

  nodes.machine = { config, pkgs, lib, ... }: {
    imports = [
      ../modules/redhat-iso-downloader.nix
    ];

    # Add our overlay with mock redhat_iso for testing
    nixpkgs.overlays = [
      (final: prev: {
        redhat_iso = mockRedhatIso;
      })
    ];

    # Configure the downloader service
    services.redhat-iso-downloader = {
      enable = true;
      tokenFile = "/etc/redhat-api-token.txt";
      outputDir = "/var/lib/test-isos";
      runOnBoot = true;

      # Use test data - in a real scenario, these would be actual RHEL ISOs
      downloads = [
        {
          # Test download by checksum
          checksum = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";  # sha256 of empty file
        }
        {
          # Test download by filename
          filename = "test-rhel-by-filename.iso";
        }
      ];
    };

    # Create a fake token file for testing
    # In production, this would contain a real Red Hat API token
    environment.etc."redhat-api-token.txt" = {
      text = "fake-token-for-testing";
      mode = "0600";
    };

    # Add some useful debugging tools
    environment.systemPackages = with pkgs; [
      coreutils
      gnugrep
    ];
  };

  # Test script
  testScript = ''
    machine.start()
    machine.wait_for_unit("multi-user.target")

    # Test 1: Check that redhat_iso package is installed
    with subtest("redhat_iso package is available"):
        machine.succeed("which redhat_iso")
        result = machine.succeed("redhat_iso --help")
        assert "Red Hat ISO Download Tool" in result, "redhat_iso help text not found"

    # Test 2: Check that the service is defined
    with subtest("systemd service is defined"):
        # Just check that the service exists (it may be failed/inactive)
        machine.succeed("systemctl list-unit-files | grep redhat-iso-downloader.service")

    # Test 3: Check that output directory was created
    with subtest("output directory exists"):
        machine.succeed("test -d /var/lib/test-isos")
        result = machine.succeed("stat -c '%a' /var/lib/test-isos")
        assert "755" in result, f"Directory permissions are not 755: {result}"

    # Test 4: Check token file exists and has correct permissions
    with subtest("token file exists with correct permissions"):
        machine.succeed("test -f /etc/redhat-api-token.txt")
        result = machine.succeed("stat -c '%a' /etc/redhat-api-token.txt")
        assert "600" in result, f"Token file permissions are not 600: {result}"

    # Test 5: Check service configuration
    with subtest("service has correct configuration"):
        result = machine.succeed("systemctl show redhat-iso-downloader.service")
        assert "Type=oneshot" in result, "Service type is not oneshot"
        assert "RemainAfterExit=yes" in result, "RemainAfterExit not set"

    # Test 6: Verify service dependencies
    with subtest("service has correct dependencies"):
        result = machine.succeed("systemctl show redhat-iso-downloader.service -p After")
        assert "network-online.target" in result, "Service doesn't wait for network"
        result = machine.succeed("systemctl show redhat-iso-downloader.service -p Wants")
        assert "network-online.target" in result, "Service doesn't want network"

    # Test 7: Check systemd security hardening
    with subtest("service has security hardening enabled"):
        result = machine.succeed("systemctl show redhat-iso-downloader.service")
        assert "PrivateTmp=yes" in result, "PrivateTmp not enabled"
        assert "ProtectSystem=strict" in result, "ProtectSystem not strict"
        assert "ProtectHome=yes" in result, "ProtectHome not enabled"
        assert "NoNewPrivileges=yes" in result, "NoNewPrivileges not enabled"

    # Test 8: Service runs successfully on boot
    with subtest("service runs successfully on boot"):
        # Service should have completed successfully
        machine.succeed("systemctl is-active redhat-iso-downloader.service")

        # Check the service logs show successful execution
        result = machine.succeed("journalctl -u redhat-iso-downloader.service --no-pager")
        assert "Downloaded: test-rhel.iso" in result, \
               "Service didn't complete download successfully"
        assert "All downloads completed successfully" in result, \
               "Service didn't show success message"

    # Test 9: Downloaded file exists
    with subtest("downloaded file exists"):
        machine.succeed("test -f /var/lib/test-isos/test-rhel.iso")
        result = machine.succeed("cat /var/lib/test-isos/test-rhel.iso")
        assert "Mock ISO content" in result, "Downloaded file has incorrect content"

    # Test 10: Service is idempotent (safe to run multiple times)
    with subtest("service is idempotent"):
        # Get current file count
        file_count_before = machine.succeed("ls -1 /var/lib/test-isos/ | wc -l").strip()

        # Restart service
        machine.succeed("systemctl restart redhat-iso-downloader.service")
        machine.succeed("systemctl is-active redhat-iso-downloader.service")

        # File count should remain the same
        file_count_after = machine.succeed("ls -1 /var/lib/test-isos/ | wc -l").strip()
        assert file_count_before == file_count_after, \
               "File count changed after re-run: " + file_count_before + " -> " + file_count_after

    # Test 11: Verify --by-filename download created file
    with subtest("by-filename download created file"):
        machine.succeed("test -f /var/lib/test-isos/test-rhel-by-filename.iso")
        result = machine.succeed("cat /var/lib/test-isos/test-rhel-by-filename.iso")
        assert "Mock ISO content" in result, "Downloaded file has incorrect content"

    # Test 12: Test --by-filename skips existing files
    with subtest("by-filename skips existing files"):
        # Try to download the same file again directly
        result = machine.succeed(
            "redhat_iso --token-file /etc/redhat-api-token.txt download test-rhel-by-filename.iso --by-filename --output /var/lib/test-isos"
        )
        assert "File already exists" in result, "Should detect existing file"
        assert "Download skipped" in result, "Should skip download"

    # Test 13: Test --force with --by-filename re-downloads
    with subtest("by-filename with --force re-downloads"):
        # Modify the existing file to verify it gets replaced
        machine.succeed("echo 'Modified content' > /var/lib/test-isos/test-rhel-by-filename.iso")
        result = machine.succeed("cat /var/lib/test-isos/test-rhel-by-filename.iso")
        assert "Modified content" in result, "File wasn't modified"

        # Download with --force should replace it
        result = machine.succeed(
            "redhat_iso --token-file /etc/redhat-api-token.txt download test-rhel-by-filename.iso --by-filename --force --output /var/lib/test-isos"
        )
        assert "Downloaded: test-rhel-by-filename.iso" in result, "Should download with --force"

        # Verify file was replaced with original content
        result = machine.succeed("cat /var/lib/test-isos/test-rhel-by-filename.iso")
        assert "Mock ISO content" in result, "File should be restored to original content"
        assert "Modified content" not in result, "Modified content should be gone"

    print("All tests passed!")
  '';
}
