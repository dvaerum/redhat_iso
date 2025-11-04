{
  description = "Red Hat ISO Download Tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    {
      # Overlay for NixOS configurations
      # Usage in configuration.nix:
      #   nixpkgs.overlays = [ inputs.redhat_iso.overlays.default ];
      #   environment.systemPackages = [ pkgs.redhat_iso ];
      overlays.default = final: prev: {
        redhat_iso = prev.callPackage ./default.nix {};
      };

      # NixOS module for automatic ISO downloads
      # Usage in configuration.nix:
      #   imports = [ inputs.redhat_iso.nixosModules.default ];
      #   services.redhat-iso-downloader.enable = true;
      nixosModules.default = import ./modules/redhat-iso-downloader.nix;
    } //
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        # Use default.nix for package definition (DRY principle - Don't Repeat Yourself)
        packages.default = pkgs.callPackage ./default.nix {};

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/redhat_iso";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python3
            python3.pkgs.requests
          ];
        };
      }
    );
}
