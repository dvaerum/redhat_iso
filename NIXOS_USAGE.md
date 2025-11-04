# NixOS Integration

This flake provides an overlay for easy integration into NixOS configurations.

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
