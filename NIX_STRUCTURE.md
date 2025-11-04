# Nix Package Structure

## Overview

The project supports both traditional Nix and modern Nix flakes, using a **DRY (Don't Repeat Yourself)** approach.

## File Structure

```
├── default.nix    # Package definition (30 lines)
├── flake.nix      # Flake wrapper (31 lines)
└── shell.nix      # Development shell (3 lines)
```

## Design: Single Source of Truth

### `default.nix` - The Package Definition
```nix
{ lib, python3 }:

python3.pkgs.buildPythonApplication {
  pname = "redhat_iso";
  version = "1.0.0";
  pyproject = true;
  src = ./.;

  build-system = with python3.pkgs; [ setuptools ];
  propagatedBuildInputs = with python3.pkgs; [ requests ];

  # ... rest of configuration
}
```

**Purpose**: Contains the actual package build configuration.

### `flake.nix` - The Flake Wrapper
```nix
{
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        # Use default.nix (no duplication!)
        packages.default = pkgs.callPackage ./default.nix {};

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/redhat_iso";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [ python3 python3.pkgs.requests ];
        };
      }
    );
}
```

**Purpose**: Wraps `default.nix` for flake users, adds apps and devShells.

### `shell.nix` - The Development Shell Wrapper
```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.callPackage ./default.nix {}
```

**Purpose**: Wraps `default.nix` for `nix-build` and `nix-shell` users.

## Benefits of This Approach

### ✅ No Duplication
- Package configuration exists in **one place only** (`default.nix`)
- `flake.nix` and `shell.nix` simply reference it
- Changes to package definition only need to be made once

### ✅ Consistency
- All build methods use **identical configuration**
- `nix-build`, `nix build`, and `nix run` produce the same result
- Impossible for configurations to drift apart

### ✅ Maintainability
- Update version? Edit one file (`default.nix`)
- Add dependency? Edit one file (`default.nix`)
- Change build process? Edit one file (`default.nix`)

### ✅ Best Practices
- Follows standard Nix patterns
- `pkgs.callPackage` is the recommended approach
- Works with both traditional Nix and flakes

## Usage

### Traditional Nix

```bash
# Build
nix-build shell.nix
./result/bin/redhat_iso --help

# Development shell
nix-shell shell.nix
python -c "from redhat_iso import RedHatAPI"
```

### Nix Flakes

```bash
# Build
nix build
./result/bin/redhat_iso --help

# Run directly
nix run . -- list

# Development shell
nix develop
python -c "from redhat_iso import RedHatAPI"
```

## How It Works

### `pkgs.callPackage`

When you call `pkgs.callPackage ./default.nix {}`:

1. Nix reads `default.nix`
2. Sees it's a function: `{ lib, python3 }: ...`
3. Automatically provides `lib` and `python3` from `pkgs`
4. Returns the built package

This is the standard Nix pattern for modular package definitions.

### Build Flow

```
flake.nix  ────┐
               ├──> pkgs.callPackage ──> default.nix ──> Built Package
shell.nix  ────┘
```

All paths lead to the same `default.nix`, ensuring consistency.

## Before vs After

### Before (Duplicated - 55 lines in flake.nix)

```nix
# flake.nix had full build configuration
packages.default = python.pkgs.buildPythonApplication {
  pname = "redhat_iso";
  version = "1.0.0";
  pyproject = true;
  src = ./.;
  build-system = with python.pkgs; [ setuptools ];
  propagatedBuildInputs = with python.pkgs; [ requests ];
  doCheck = false;
  meta = with pkgs.lib { ... };
};
```

**Problems**:
- Same configuration in two files
- Easy to update one and forget the other
- More code to maintain

### After (DRY - 31 lines in flake.nix)

```nix
# flake.nix simply references default.nix
packages.default = pkgs.callPackage ./default.nix {};
```

**Benefits**:
- Single source of truth
- Impossible to have drift
- Less code overall

## Testing

All methods tested and working:

```bash
✓ nix-build shell.nix
✓ nix build
✓ nix run . -- --help
✓ nix-shell shell.nix
✓ nix develop
```

## Comparison to Other Projects

This structure matches common Nix patterns:

- **nixpkgs**: Uses `callPackage` extensively
- **flake-utils**: Standard for flake wrappers
- **Most Nix projects**: Define package in `default.nix`, wrap with `flake.nix`

## Summary

The Nix structure follows the **DRY principle**:
- ✅ Single source of truth (`default.nix`)
- ✅ Minimal wrappers (`flake.nix`, `shell.nix`)
- ✅ No duplication
- ✅ Easy to maintain
- ✅ Consistent across all build methods
