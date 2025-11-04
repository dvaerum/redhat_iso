# Just run this nix program with: nix-build generate-doc.nix

{ pkgs ? import <nixpkgs>{}, modulesPath ? null, ... }@args: let
    inherit (pkgs)
      lib
      nixosOptionsDoc
      runCommand
    ;

    modulesPath =
        if builtins.hasAttr "modulesPath" args && args.modulesPath != null
        then args.modulesPath
        else "${pkgs.path}/nixos/modules";

    # evaluate our options with minimal NixOS module infrastructure
    eval = lib.evalModules {
        modules = [
            { _module.check = false; }
            # Provide minimal NixOS infrastructure for module evaluation
            {
                options = {
                    assertions = lib.mkOption {
                        type = lib.types.listOf lib.types.unspecified;
                        default = [];
                    };
                    environment.systemPackages = lib.mkOption {
                        type = lib.types.listOf lib.types.package;
                        default = [];
                    };
                    systemd.services = lib.mkOption {
                        type = lib.types.attrsOf lib.types.unspecified;
                        default = {};
                    };
                    systemd.tmpfiles.rules = lib.mkOption {
                        type = lib.types.listOf lib.types.str;
                        default = [];
                    };
                };
            }
            ./modules/redhat-iso-downloader.nix
        ];
    };
    # generate our docs - only include our module's options with proper structure
    optionsDoc = nixosOptionsDoc {
        options = {
            services.redhat-iso-downloader = eval.options.services.redhat-iso-downloader;
        };
    };
in
    # create a derivation for capturing the markdown output
    runCommand "options-doc.md" {} ''
        cat ${optionsDoc.optionsCommonMark} >> $out
    ''
