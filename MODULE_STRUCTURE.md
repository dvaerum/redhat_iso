# rhiso - Python Module Structure

## Overview

The `rhiso` package is now a proper Python module that works both as:
1. **Command-line tool** - `rhiso list`, `rhiso download`, etc.
2. **Python library** - `from rhiso import RedHatAPI`

## Directory Structure

```
rhiso/
├── __init__.py      # Package exports: RedHatAPI, __version__
├── __main__.py      # Enables: python -m rhiso
├── api.py           # Core API client (RedHatAPI class)
└── cli.py           # CLI interface (argument parsing, main())
```

## Module Components

### `rhiso/__init__.py`
- Exports `RedHatAPI` class for library usage
- Defines `__version__`
- Package-level documentation

### `rhiso/api.py`
- `RedHatAPI` class with all API methods:
  - `list_rhel_images()` - List images by version/arch
  - `list_images_by_content_set()` - List images by content set
  - `discover_rhel_versions()` - Auto-discover available versions
  - `version_exists()` - Check if version exists
  - `find_image_by_filename()` - Search for image by filename
  - `download_file()` - Download ISO by checksum or filename
  - `get_download_info()` - Get download URL
  - `get_access_token()` - OAuth token exchange

### `rhiso/cli.py`
- `load_token()` - Load offline token from file
- `main()` - CLI entry point with argparse
- Command-line argument parsing
- Calls RedHatAPI methods based on arguments

### `rhiso/__main__.py`
- Enables `python -m rhiso` usage
- Simply calls `cli.main()`

## Usage Modes

### 1. Command-Line Tool (Standalone Binary)

```bash
# Installed via Nix or pip
rhiso list
rhiso download <checksum>

# Via nix-build
./result/bin/rhiso list

# Via nix run
nix run . -- list

# As Python module
python -m rhiso list
```

### 2. Python Library

```python
from rhiso import RedHatAPI

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
./result/bin/rhiso --help

# Using pip (after publishing)
pip install rhiso
rhiso --help
```

### As a Library

```bash
# Using Nix
nix-shell shell.nix
python -c "from rhiso import RedHatAPI; print('Success!')"

# Using pip
pip install rhiso
python -c "from rhiso import RedHatAPI; print('Success!')"
```

## Package Configuration

### `setup.py`
```python
setup(
    name='rhiso',
    version='1.0.0',
    packages=find_packages(),  # Finds rhiso/ package
    entry_points={
        'console_scripts': [
            'rhiso=rhiso.cli:main',  # CLI entry point
        ],
    },
)
```

### `default.nix` / `flake.nix`
- Both use `buildPythonApplication`
- Package includes all of `rhiso/` directory
- Entry point: `rhiso.cli:main`

## Benefits of Module Structure

1. **Separation of Concerns**
   - `api.py` - Pure API logic
   - `cli.py` - CLI-specific code
   - Clear boundaries between library and CLI

2. **Reusability**
   - Other Python projects can `import rhiso`
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

## Migration from rhiso.py

The old monolithic `rhiso.py` file has been split into:
- `rhiso/api.py` - RedHatAPI class (510 lines)
- `rhiso/cli.py` - CLI interface (120 lines)
- `rhiso/__init__.py` - Package exports (30 lines)
- `rhiso/__main__.py` - Module runner (7 lines)

**Total**: Same functionality, better organized

The old `rhiso.py` file can be kept for reference or removed as it's fully replaced by the module structure.

## Examples

See documentation:
- **LIBRARY_USAGE.md** - Comprehensive library examples
- **example_library_usage.py** - Runnable example script
- **USAGE_EXAMPLES.md** - CLI usage examples
- **README.md** - Installation and quick start

## Testing

```bash
# Test CLI
./result/bin/rhiso --help
./result/bin/rhiso list

# Test library
nix-shell shell.nix --run "python example_library_usage.py"

# Test as module
nix-shell shell.nix --run "python -m rhiso --help"
```

## Future Enhancements

Potential improvements:
1. Add unit tests (`rhiso/tests/`)
2. Add type hints throughout
3. Add async support (`rhiso/async_api.py`)
4. Add caching layer
5. Add configuration file support
6. Publish to PyPI

## Summary

The `rhiso` package now follows Python best practices:
- ✅ Proper package structure
- ✅ Works as CLI and library
- ✅ Clean separation of concerns
- ✅ Standard entry points
- ✅ Comprehensive documentation
- ✅ Nix packaging updated
- ✅ Tested and working
