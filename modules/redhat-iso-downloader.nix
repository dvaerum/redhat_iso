{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.redhat-iso-downloader;

  # Create a download script for a single ISO download
  # Handles three modes:
  # 1. Only checksum: download by checksum (immutable)
  # 2. Only filename: download by filename (may change over time!)
  # 3. Both: download by checksum and verify filename matches
  downloadIsoScript = download:
    let
      hasChecksum = download.checksum != null;
      hasFilename = download.filename != null;

      # Determine download mode
      downloadByChecksum = hasChecksum;
      downloadByFilename = !hasChecksum && hasFilename;
      verifyFilename = hasChecksum && hasFilename;

      # Build the appropriate redhat_iso command
      downloadCmd = if downloadByChecksum then
        # Download by checksum (recommended)
        "${pkgs.redhat_iso}/bin/redhat_iso --token-file ${cfg.tokenFile} download ${download.checksum} --output ${cfg.outputDir}"
      else
        # Download by filename (--by-filename flag)
        "${pkgs.redhat_iso}/bin/redhat_iso --token-file ${cfg.tokenFile} download ${download.filename} --by-filename --output ${cfg.outputDir}";

      identifier = if hasChecksum then download.checksum else download.filename;
    in ''
      echo "----------------------------------------"
      ${if downloadByChecksum then ''
        echo "Downloading ISO by checksum: ${download.checksum}"
      '' else ''
        echo "Downloading ISO by filename: ${download.filename}"
        echo "⚠️  Note: Filename-based downloads may have different checksums if Red Hat updates the file"
      ''}

      # Run the download command
      if ${downloadCmd}; then
        echo "✓ Successfully downloaded: ${identifier}"

        ${if verifyFilename then ''
          # Verify the filename matches expected
          if [ -f "${cfg.outputDir}/${download.filename}" ]; then
            echo "✓ Filename verification passed: ${download.filename}"
          else
            echo "⚠️  Warning: Downloaded file has different filename than expected (${download.filename})"
            echo "    This may happen if Red Hat renamed the file"
            ls -lh ${cfg.outputDir}/
          fi
        '' else ""}
      else
        echo "✗ Failed to download: ${identifier}"
        exit 1
      fi
      echo ""
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

    echo "========================================="
    echo "Red Hat ISO Downloader"
    echo "========================================="
    echo "Output directory: ${cfg.outputDir}"
    echo "Downloads to process: ${toString (length cfg.downloads)}"
    echo ""

    ${concatMapStringsSep "\n" downloadIsoScript cfg.downloads}

    echo "========================================="
    echo "All downloads completed successfully!"
    echo "========================================="
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

    downloads = mkOption {
      type = types.listOf (types.submodule {
        options = {
          checksum = mkOption {
            type = types.nullOr types.str;
            default = null;
            example = "36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63";
            description = ''
              SHA-256 checksum of the ISO to download.

              Download by checksum is the recommended approach as checksums
              are immutable identifiers.

              At least one of 'checksum' or 'filename' must be provided.
            '';
          };
          filename = mkOption {
            type = types.nullOr types.str;
            default = null;
            example = "rhel-9.6-x86_64-boot.iso";
            description = ''
              Filename of the ISO to download.

              WARNING: Downloading by filename may result in different checksums
              over time if Red Hat updates the file. For immutable downloads,
              use checksum instead.

              At least one of 'checksum' or 'filename' must be provided.
            '';
          };
        };
      });
      default = [];
      example = literalExpression ''
        [
          # Download by checksum (recommended - immutable)
          {
            checksum = "36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63";
          }

          # Download by filename (may change over time)
          {
            filename = "rhel-9.6-x86_64-boot.iso";
          }

          # Download by checksum and verify filename matches
          {
            checksum = "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb";
            filename = "rhel-9.6-x86_64-dvd.iso";
          }
        ]
      '';
      description = ''
        List of ISOs to download.

        Each download can specify:
        - Only checksum: Downloads by SHA-256 checksum (immutable)
        - Only filename: Downloads by filename (may change over time)
        - Both: Downloads by checksum and verifies filename matches

        The checksum-based approach is recommended for reproducibility.
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
    # Validation: ensure downloads are properly configured
    assertions = [
      {
        assertion = (length cfg.downloads) > 0;
        message = ''
          services.redhat-iso-downloader: No downloads configured!

          Please provide at least one download in the 'downloads' option.

          Example:
            services.redhat-iso-downloader.downloads = [
              { checksum = "36a06d4c..."; }
            ];
        '';
      }
    ] ++ (map (download:
      let
        hasChecksum = download.checksum != null;
        hasFilename = download.filename != null;
        idx = elemAt (splitString "\n" (concatMapStringsSep "\n" (d: "${d.checksum or "null"}-${d.filename or "null"}") cfg.downloads)) 0;
      in {
        assertion = hasChecksum || hasFilename;
        message = ''
          services.redhat-iso-downloader: Invalid download configuration!

          Each download must specify at least one of:
            - checksum: SHA-256 hash (recommended)
            - filename: ISO filename (may change over time)

          Found entry with neither checksum nor filename.
        '';
      }
    ) cfg.downloads);

    # Add redhat_iso to system packages
    environment.systemPackages = [ pkgs.redhat_iso ];

    # Create systemd service
    systemd.services.redhat-iso-downloader = {
      description = "Red Hat ISO Downloader";
      documentation = [ "https://github.com/dvaerum/redhat_iso" ];

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
