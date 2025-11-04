{ pkgs ? import <nixpkgs> {}, system ? builtins.currentSystem }:

let
  # Import nixpkgs with our overlay
  nixpkgs = import <nixpkgs> { inherit system; };

  # Create a test ISO file and its checksum for testing
  testIsoContent = "This is a test RHEL ISO file for testing purposes";
  testIsoChecksum = builtins.hashString "sha256" testIsoContent;

in pkgs.testers.nixosTest {
  name = "redhat-iso-downloader";

  nodes.machine = { config, pkgs, lib, ... }: {
    imports = [
      ../modules/redhat-iso-downloader.nix
    ];

    # Add our overlay to get redhat_iso package
    nixpkgs.overlays = [
      (final: prev: {
        redhat_iso = prev.callPackage ../default.nix {};
      })
    ];

    # Configure the downloader service
    services.redhat-iso-downloader = {
      enable = true;
      tokenFile = "/etc/redhat-api-token.txt";
      outputDir = "/var/lib/test-isos";
      runOnBoot = true;

      # Use test data - in a real scenario, these would be actual RHEL ISOs
      isos = [
        {
          filename = "test-rhel-9.6-x86_64-boot.iso";
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

    # Test 8: Service logs contain expected information
    with subtest("service logs show expected behavior"):
        # The service runs on boot and will fail (expected - no network)
        # Check the service logs contain expected patterns
        result = machine.succeed("journalctl -u redhat-iso-downloader.service --no-pager")
        # Service should have attempted to start
        assert "redhat-iso-downloader" in result.lower() or "Starting Red Hat ISO Downloader" in result, \
               "Service didn't appear in logs"

    print("All tests passed!")
  '';
}
