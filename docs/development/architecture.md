# redhat_iso - Python Module Structure

## Overview

The `redhat_iso` package is now a proper Python module that works both as:
1. **Command-line tool** - `redhat_iso list`, `redhat_iso download`, etc.
2. **Python library** - `from redhat_iso import RedHatAPI`

## Directory Structure

```
redhat_iso/
├── __init__.py      # Package exports: RedHatAPI, __version__
├── __main__.py      # Enables: python -m redhat_iso
├── api.py           # Core API client (RedHatAPI class)
└── cli.py           # CLI interface (argument parsing, main())
```

## Module Components

### `redhat_iso/__init__.py`
- Exports `RedHatAPI` class for library usage
- Defines `__version__`
- Package-level documentation

### `redhat_iso/api.py`
- `RedHatAPI` class with all API methods:
  - `list_rhel_images()` - List images by version/arch
  - `list_images_by_content_set()` - List images by content set
  - `discover_rhel_versions()` - Auto-discover available versions
  - `version_exists()` - Check if version exists
  - `find_image_by_filename()` - Search for image by filename
  - `download_file()` - Download ISO by checksum or filename
  - `get_download_info()` - Get download URL
  - `get_access_token()` - OAuth token exchange

### `redhat_iso/cli.py`
- `load_token()` - Load offline token from file
- `main()` - CLI entry point with argparse
- Command-line argument parsing
- Calls RedHatAPI methods based on arguments

### `redhat_iso/__main__.py`
- Enables `python -m redhat_iso` usage
- Simply calls `cli.main()`

## Usage Modes

### 1. Command-Line Tool (Standalone Binary)

```bash
# Installed via Nix or pip
redhat_iso list
redhat_iso download <checksum>

# Via nix-build
./result/bin/redhat_iso list

# Via nix run
nix run . -- list

# As Python module
python -m redhat_iso list
```

### 2. Python Library

```python
from redhat_iso import RedHatAPI

token = open("redhat-api-token.txt").read().strip()
api = RedHatAPI(token)

# List images
images = api.list_rhel_images("9.6", "x86_64")

# Discover versions
versions = api.discover_rhel_versions("x86_64")

# Download
api.download_file("checksum", output_dir="./downloads")
```

## Installation

### As a CLI Tool

```bash
# Using Nix
nix-build shell.nix
./result/bin/redhat_iso --help

# Using pip (after publishing)
pip install redhat_iso
redhat_iso --help
```

### As a Library

```bash
# Using Nix
nix-shell shell.nix
python -c "from redhat_iso import RedHatAPI; print('Success!')"

# Using pip
pip install redhat_iso
python -c "from redhat_iso import RedHatAPI; print('Success!')"
```

## Package Configuration

### `setup.py`
```python
setup(
    name='redhat_iso',
    version='1.0.0',
    packages=find_packages(),  # Finds redhat_iso/ package
    entry_points={
        'console_scripts': [
            'redhat_iso=redhat_iso.cli:main',  # CLI entry point
        ],
    },
)
```

### `default.nix` / `flake.nix`
- Both use `buildPythonApplication`
- Package includes all of `redhat_iso/` directory
- Entry point: `redhat_iso.cli:main`

## Benefits of Module Structure

1. **Separation of Concerns**
   - `api.py` - Pure API logic
   - `cli.py` - CLI-specific code
   - Clear boundaries between library and CLI

2. **Reusability**
   - Other Python projects can `import redhat_iso`
   - No need to shell out to CLI
   - Type-safe, Pythonic API

3. **Testability**
   - Can unit test `RedHatAPI` independently
   - Can test CLI parsing separately
   - Mock API calls in tests

4. **Maintainability**
   - Smaller, focused files
   - Easier to navigate and understand
   - Clear module responsibilities

5. **Flexibility**
   - Users choose: CLI or library
   - Can use both in same project
   - Standard Python package structure

## Migration from redhat_iso.py

The old monolithic `redhat_iso.py` file has been split into:
- `redhat_iso/api.py` - RedHatAPI class (510 lines)
- `redhat_iso/cli.py` - CLI interface (120 lines)
- `redhat_iso/__init__.py` - Package exports (30 lines)
- `redhat_iso/__main__.py` - Module runner (7 lines)

**Total**: Same functionality, better organized

The old `redhat_iso.py` file can be kept for reference or removed as it's fully replaced by the module structure.

## Examples

See documentation:
- **[docs/usage/library.md](../usage/library.md)** - Comprehensive library examples
- **example_library_usage.py** - Runnable example script in repository root
- **[docs/usage/cli-examples.md](../usage/cli-examples.md)** - CLI usage examples
- **[README.md](../../README.md)** - Installation and quick start

## Testing

```bash
# Test CLI
./result/bin/redhat_iso --help
./result/bin/redhat_iso list

# Test library
nix-shell shell.nix --run "python example_library_usage.py"

# Test as module
nix-shell shell.nix --run "python -m redhat_iso --help"
```

## Future Enhancements

Potential improvements:
1. Add unit tests (`redhat_iso/tests/`)
2. Add type hints throughout
3. Add async support (`redhat_iso/async_api.py`)
4. Add caching layer
5. Add configuration file support
6. Publish to PyPI

## Summary

The `redhat_iso` package now follows Python best practices:
- ✅ Proper package structure
- ✅ Works as CLI and library
- ✅ Clean separation of concerns
- ✅ Standard entry points
- ✅ Comprehensive documentation
- ✅ Nix packaging updated
- ✅ Tested and working
