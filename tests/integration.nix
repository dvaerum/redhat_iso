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
        download)
          shift
          CHECKSUM_OR_FILENAME="$1"
          shift
          ;;
        --help)
          echo "Red Hat ISO Download Tool"
          echo "Usage: redhat_iso [--token-file FILE] download CHECKSUM [--output DIR]"
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

    # Create a simple test ISO file
    FILENAME="test-rhel.iso"
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

    print("All tests passed!")
  '';
}
