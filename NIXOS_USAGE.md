# NixOS Integration

This flake provides both an overlay and a NixOS module for easy integration into NixOS configurations.

## Features

1. **Overlay**: Adds `redhat_iso` package to system packages
2. **NixOS Module**: Automatically downloads Red Hat ISOs on system boot

## Usage

### Option 1: Flake-based NixOS Configuration

If you're using a flake-based NixOS configuration, add this flake as an input:

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    redhat_iso.url = "github:YOUR_USERNAME/redhat_iso";  # Update with your repo
  };

  outputs = { self, nixpkgs, redhat_iso, ... }: {
    nixosConfigurations.your-hostname = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        ./configuration.nix

        # Add the overlay
        ({ pkgs, ... }: {
          nixpkgs.overlays = [ redhat_iso.overlays.default ];
        })
      ];
    };
  };
}
```

Then in your `configuration.nix`:

```nix
{ config, pkgs, ... }:

{
  # Add the package to system packages
  environment.systemPackages = [
    pkgs.redhat_iso
  ];
}
```

### Option 2: Traditional NixOS Configuration

If you're using a traditional (non-flake) NixOS configuration, you can add the overlay manually:

```nix
# configuration.nix
{ config, pkgs, ... }:

let
  redhat_iso_overlay = import (builtins.fetchGit {
    url = "https://github.com/YOUR_USERNAME/redhat_iso";  # Update with your repo
    ref = "main";
  });
in
{
  nixpkgs.overlays = [
    redhat_iso_overlay.overlays.default
  ];

  environment.systemPackages = [
    pkgs.redhat_iso
  ];
}
```

### Option 3: Local Development

If you're developing locally and want to test the overlay:

```nix
# configuration.nix
{ config, pkgs, ... }:

{
  nixpkgs.overlays = [
    (final: prev: {
      redhat_iso = prev.callPackage /path/to/redhat_iso/default.nix {};
    })
  ];

  environment.systemPackages = [
    pkgs.redhat_iso
  ];
}
```

## Verification

After rebuilding your NixOS configuration:

```bash
# Rebuild NixOS
sudo nixos-rebuild switch

# Verify the package is available
which redhat_iso
redhat_iso --help
```

## Setup

Don't forget to set up your Red Hat API token:

```bash
# Create token file
echo "YOUR_OFFLINE_TOKEN" > ~/.config/redhat-api-token.txt

# Or system-wide (as root)
echo "YOUR_OFFLINE_TOKEN" > /etc/redhat-api-token.txt
```

Then use it:

```bash
redhat_iso --token-file ~/.config/redhat-api-token.txt list
```

## Advanced: Per-User Installation

If you want to install it per-user instead of system-wide, use Home Manager:

```nix
# home.nix
{ config, pkgs, ... }:

{
  nixpkgs.overlays = [ inputs.redhat_iso.overlays.default ];

  home.packages = [
    pkgs.redhat_iso
  ];
}
```

## Benefits of Using the Overlay

- **Declarative**: Package is managed by your NixOS configuration
- **Reproducible**: Same package version across rebuilds
- **Automatic Updates**: Update by updating the flake input
- **System Integration**: Available to all users on the system
- **Rollback Support**: Can roll back to previous configurations

---

## NixOS Module: Automatic ISO Downloads

The flake provides a NixOS module that automatically downloads Red Hat ISOs on system boot.

### Basic Configuration

Add the module to your flake-based configuration:

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    redhat_iso.url = "github:YOUR_USERNAME/redhat_iso";
  };

  outputs = { nixpkgs, redhat_iso, ... }: {
    nixosConfigurations.your-hostname = nixpkgs.lib.nixosSystem {
      modules = [
        ./configuration.nix
        redhat_iso.nixosModules.default

        # Configure the overlay so the package is available
        ({ pkgs, ... }: {
          nixpkgs.overlays = [ redhat_iso.overlays.default ];
        })
      ];
    };
  };
}
```

### Module Configuration Examples

#### Option 1: Unified List (Recommended)

Keep filename and checksum together to avoid mismatches:

```nix
# configuration.nix
{ config, pkgs, ... }:

{
  services.redhat-iso-downloader = {
    enable = true;
    tokenFile = "/etc/redhat-api-token.txt";
    outputDir = "/var/lib/redhat-isos";

    isos = [
      {
        filename = "rhel-9.6-x86_64-boot.iso";
        checksum = "36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63";
      }
      {
        filename = "rhel-9.6-x86_64-dvd.iso";
        checksum = "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb";
      }
      {
        filename = "rhel-8.10-x86_64-boot.iso";
        checksum = "6ced368628750ff3ea8a2fc52a371ba368d3377b8307caafda69070849a9e4e7";
      }
    ];
  };
}
```

#### Option 2: Separate Lists

If you prefer separate lists for filenames and checksums:

```nix
# configuration.nix
{ config, pkgs, ... }:

{
  services.redhat-iso-downloader = {
    enable = true;
    tokenFile = "/etc/redhat-api-token.txt";
    outputDir = "/var/lib/redhat-isos";

    filenames = [
      "rhel-9.6-x86_64-boot.iso"
      "rhel-9.6-x86_64-dvd.iso"
      "rhel-8.10-x86_64-boot.iso"
    ];

    checksums = [
      "36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63"
      "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb"
      "6ced368628750ff3ea8a2fc52a371ba368d3377b8307caafda69070849a9e4e7"
    ];
  };
}
```

**Note**: Lists must have the same length! The first filename corresponds to the first checksum, etc.

### Module Options

```nix
services.redhat-iso-downloader = {
  # Enable the service
  enable = true;

  # Path to Red Hat API offline token file
  # Generate at: https://access.redhat.com/management/api
  tokenFile = "/etc/redhat-api-token.txt";

  # Directory where ISOs will be downloaded
  outputDir = "/var/lib/redhat-isos";

  # Option 1: Unified list (recommended)
  isos = [
    { filename = "..."; checksum = "..."; }
  ];

  # Option 2: Separate lists (must have same length)
  filenames = [ "file1.iso" "file2.iso" ];
  checksums = [ "hash1" "hash2" ];

  # Automatically remove corrupted files and re-download
  removeCorrupted = true;  # default: true

  # Run downloads on system boot
  runOnBoot = true;  # default: true
};
```

### How It Works

1. **On System Boot**: Service runs after network is online
2. **Check Existing**: For each ISO, checks if file exists in `outputDir`
3. **Verify Checksum**: If file exists, verifies SHA-256 checksum
4. **Download**: If missing or corrupted, downloads using `redhat_iso` tool
5. **Idempotent**: Safe to run multiple times - skips files with correct checksums

### Manual Triggering

If you set `runOnBoot = false`, you can manually trigger downloads:

```bash
# Trigger download service
sudo systemctl start redhat-iso-downloader.service

# Check status
sudo systemctl status redhat-iso-downloader.service

# View logs
sudo journalctl -u redhat-iso-downloader.service
```

### Security Considerations

#### Token Management

**Option 1: Using agenix (recommended for secrets)**

```nix
{
  age.secrets.redhat-api-token = {
    file = ./secrets/redhat-api-token.age;
    path = "/run/secrets/redhat-api-token";
    mode = "0400";
  };

  services.redhat-iso-downloader = {
    enable = true;
    tokenFile = config.age.secrets.redhat-api-token.path;
    # ... rest of config
  };
}
```

**Option 2: Using sops-nix**

```nix
{
  sops.secrets.redhat-api-token = {
    sopsFile = ./secrets.yaml;
    path = "/run/secrets/redhat-api-token";
  };

  services.redhat-iso-downloader = {
    enable = true;
    tokenFile = config.sops.secrets.redhat-api-token.path;
    # ... rest of config
  };
}
```

**Option 3: Plain file (less secure)**

```bash
# As root
echo "YOUR_OFFLINE_TOKEN" > /etc/redhat-api-token.txt
chmod 600 /etc/redhat-api-token.txt
```

### Real-World Example

Complete configuration for a PXE boot server:

```nix
# configuration.nix
{ config, pkgs, ... }:

{
  # Import the module
  imports = [ inputs.redhat_iso.nixosModules.default ];

  # Add overlay
  nixpkgs.overlays = [ inputs.redhat_iso.overlays.default ];

  # Configure automatic downloads
  services.redhat-iso-downloader = {
    enable = true;
    tokenFile = "/run/secrets/redhat-api-token";
    outputDir = "/srv/tftp/isos";

    isos = [
      # RHEL 9.6
      {
        filename = "rhel-9.6-x86_64-boot.iso";
        checksum = "36a06d4c36605550c2626d5af9ee84fc2badce9e71010b7e94a9a469a0335d63";
      }
      {
        filename = "rhel-9.6-x86_64-dvd.iso";
        checksum = "febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb";
      }

      # RHEL 8.10
      {
        filename = "rhel-8.10-x86_64-boot.iso";
        checksum = "6ced368628750ff3ea8a2fc52a371ba368d3377b8307caafda69070849a9e4e7";
      }
      {
        filename = "rhel-8.10-x86_64-dvd.iso";
        checksum = "9b3c8e31bc2cdd2de9cf96abb3726347f5840ff3b176270647b3e66639af291b";
      }
    ];

    removeCorrupted = true;
    runOnBoot = true;
  };

  # Serve ISOs over HTTP
  services.nginx = {
    enable = true;
    virtualHosts."isos.example.com" = {
      locations."/rhel/" = {
        alias = "/srv/tftp/isos/";
        extraConfig = "autoindex on;";
      };
    };
  };
}
```

### Troubleshooting

**Check service status:**
```bash
sudo systemctl status redhat-iso-downloader.service
```

**View download logs:**
```bash
sudo journalctl -u redhat-iso-downloader.service -f
```

**Manually test download:**
```bash
sudo systemctl start redhat-iso-downloader.service
```

**Check output directory:**
```bash
ls -lh /var/lib/redhat-isos/
```

**Verify checksums:**
```bash
cd /var/lib/redhat-isos
sha256sum -c <(echo "36a06d4c... rhel-9.6-x86_64-boot.iso")
```

### Module Benefits

- **Declarative**: ISOs defined in NixOS configuration
- **Automatic**: Downloads on boot if missing
- **Idempotent**: Safe to run multiple times
- **Verified**: Always checks SHA-256 checksums
- **Resilient**: Auto-removes corrupted files
- **Integrated**: Uses system's redhat_iso package
- **Logged**: Full systemd journal integration
