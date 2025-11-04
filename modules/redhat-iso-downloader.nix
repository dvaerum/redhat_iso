{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.redhat-iso-downloader;

  # Combine filenames and checksums into a list of sets
  # This handles both the separate lists approach and the unified approach
  isoList = if (cfg.filenames != [] && cfg.checksums != []) then
    # Separate lists mode: zip them together
    lib.zipListsWith (filename: checksum: { inherit filename checksum; })
      cfg.filenames
      cfg.checksums
  else
    # Unified list mode
    cfg.isos;

  # Create a download script for a single ISO
  downloadIsoScript = iso: ''
    ISO_FILE="${cfg.outputDir}/${iso.filename}"
    CHECKSUM="${iso.checksum}"

    # Check if file already exists and has correct checksum
    if [ -f "$ISO_FILE" ]; then
      echo "File $ISO_FILE exists, verifying checksum..."
      ACTUAL_CHECKSUM=$(${pkgs.coreutils}/bin/sha256sum "$ISO_FILE" | ${pkgs.coreutils}/bin/awk '{print $1}')

      if [ "$ACTUAL_CHECKSUM" = "$CHECKSUM" ]; then
        echo "✓ $ISO_FILE already exists with correct checksum"
        exit 0
      else
        echo "✗ $ISO_FILE exists but checksum mismatch!"
        echo "  Expected: $CHECKSUM"
        echo "  Got:      $ACTUAL_CHECKSUM"
        if [ "${toString cfg.removeCorrupted}" = "1" ]; then
          echo "  Removing corrupted file and re-downloading..."
          rm "$ISO_FILE"
        else
          echo "  Skipping download (removeCorrupted is false)"
          exit 1
        fi
      fi
    fi

    # Download the ISO
    echo "Downloading ${iso.filename}..."
    ${pkgs.redhat_iso}/bin/redhat_iso \
      --token-file ${cfg.tokenFile} \
      download ${iso.checksum} \
      --output ${cfg.outputDir}

    if [ $? -eq 0 ]; then
      echo "✓ Successfully downloaded and verified ${iso.filename}"
    else
      echo "✗ Failed to download ${iso.filename}"
      exit 1
    fi
  '';

  # Master script that downloads all ISOs
  downloadAllScript = pkgs.writeShellScript "download-redhat-isos" ''
    set -e

    # Ensure output directory exists
    mkdir -p ${cfg.outputDir}

    # Check if token file exists
    if [ ! -f "${cfg.tokenFile}" ]; then
      echo "Error: Red Hat API token file not found at ${cfg.tokenFile}"
      exit 1
    fi

    echo "Starting Red Hat ISO downloads..."
    echo "Output directory: ${cfg.outputDir}"
    echo "ISOs to download: ${toString (length isoList)}"
    echo ""

    ${concatMapStringsSep "\n" (iso: ''
      echo "----------------------------------------"
      ${downloadIsoScript iso}
      echo ""
    '') isoList}

    echo "========================================="
    echo "All downloads completed!"
  '';

in {
  options.services.redhat-iso-downloader = {
    enable = mkEnableOption "Red Hat ISO downloader service";

    tokenFile = mkOption {
      type = types.path;
      default = "/etc/redhat-api-token.txt";
      example = "/run/secrets/redhat-api-token";
      description = ''
        Path to the Red Hat API offline token file.

        Generate your token at: https://access.redhat.com/management/api

        For security, consider using agenix or sops-nix to manage this secret.
      '';
    };

    outputDir = mkOption {
      type = types.path;
      default = "/var/lib/redhat-isos";
      example = "/srv/isos/redhat";
      description = ''
        Directory where ISO files will be downloaded.

        The directory will be created if it doesn't exist.
      '';
    };

    filenames = mkOption {
      type = types.listOf types.str;
      default = [];
      example = [ "rhel-9.6-x86_64-boot.iso" "rhel-9.6-x86_64-dvd.iso" ];
      description = ''
        List of ISO filenames to download (optional, use with checksums).

        If both filenames and checksums are provided, they will be paired by index.
        Otherwise, use the 'isos' option for a more robust configuration.
      '';
    };

    checksums = mkOption {
      type = types.listOf types.str;
      default = [];
      example = [
        "36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63"
        "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb"
      ];
      description = ''
        List of SHA-256 checksums corresponding to filenames (optional).

        Must have the same length as filenames if both are used.
        Each checksum corresponds to the filename at the same index.
      '';
    };

    isos = mkOption {
      type = types.listOf (types.submodule {
        options = {
          filename = mkOption {
            type = types.str;
            example = "rhel-9.6-x86_64-boot.iso";
            description = "ISO filename";
          };
          checksum = mkOption {
            type = types.str;
            example = "36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63";
            description = "SHA-256 checksum of the ISO";
          };
        };
      });
      default = [];
      example = literalExpression ''
        [
          {
            filename = "rhel-9.6-x86_64-boot.iso";
            checksum = "36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63";
          }
          {
            filename = "rhel-9.6-x86_64-dvd.iso";
            checksum = "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb";
          }
        ]
      '';
      description = ''
        List of ISOs to download with their checksums.

        This is the recommended way to configure ISOs as it keeps
        filenames and checksums together, reducing configuration errors.
      '';
    };

    removeCorrupted = mkOption {
      type = types.bool;
      default = true;
      description = ''
        Whether to automatically remove and re-download files with mismatched checksums.

        If false, the service will fail when encountering a corrupted file.
      '';
    };

    runOnBoot = mkOption {
      type = types.bool;
      default = true;
      description = ''
        Whether to run the download service on system boot.

        If false, you can manually trigger downloads with:
          systemctl start redhat-iso-downloader.service
      '';
    };
  };

  config = mkIf cfg.enable {
    # Validation: ensure we have ISOs to download
    assertions = [
      {
        assertion = (length isoList) > 0;
        message = ''
          services.redhat-iso-downloader: No ISOs configured!

          Either provide:
            - Both 'filenames' and 'checksums' lists (must have same length)
            - Or the 'isos' list
        '';
      }
      {
        assertion = (cfg.filenames == [] && cfg.checksums == []) ||
                    (length cfg.filenames == length cfg.checksums);
        message = ''
          services.redhat-iso-downloader: filenames and checksums must have the same length!

          Got ${toString (length cfg.filenames)} filenames and ${toString (length cfg.checksums)} checksums.

          Either:
            - Provide equal-length lists for both
            - Or use the 'isos' option instead
        '';
      }
    ];

    # Add redhat_iso to system packages
    environment.systemPackages = [ pkgs.redhat_iso ];

    # Create systemd service
    systemd.services.redhat-iso-downloader = {
      description = "Red Hat ISO Downloader";
      documentation = [ "https://github.com/YOUR_USERNAME/redhat_iso" ];

      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      wantedBy = mkIf cfg.runOnBoot [ "multi-user.target" ];

      serviceConfig = {
        Type = "oneshot";
        ExecStart = "${downloadAllScript}";
        RemainAfterExit = true;

        # Security hardening
        DynamicUser = false;  # Need to write to configured directory
        PrivateTmp = true;
        ProtectSystem = "strict";
        ReadWritePaths = [ cfg.outputDir ];
        ProtectHome = true;
        NoNewPrivileges = true;

        # Resource limits
        TimeoutStartSec = "1h";  # Large ISOs can take time
      };
    };

    # Create output directory with proper permissions
    systemd.tmpfiles.rules = [
      "d ${cfg.outputDir} 0755 root root -"
    ];
  };
}
