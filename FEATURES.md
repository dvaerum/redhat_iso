# Red Hat ISO Download Tool - Feature List

## Complete Feature Set

### 🔍 List Available ISOs

1. **Default List** - Automatically discovers and shows latest RHEL releases
   ```bash
   rhiso list
   ```
   - Auto-detects newest RHEL versions (10.x, 9.x, 8.x)
   - Discovers minor version updates automatically
   - No manual updates needed when new RHEL versions are released

2. **By Version and Architecture**
   ```bash
   rhiso list --version 9.6 --arch x86_64
   rhiso list --version 8.10 --arch aarch64
   ```

3. **By Content Set**
   ```bash
   rhiso list --content-set rhel-9-for-x86_64-baseos-isos
   ```

4. **JSON Output** - For automation and scripting
   ```bash
   rhiso --json list
   rhiso --json list --version 9.6 --arch x86_64
   ```

### 📥 Download ISOs

1. **By Checksum** (Precise version control)
   ```bash
   rhiso download febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb
   ```

2. **By Filename** (Automatic search, latest version) ⭐ NEW
   ```bash
   rhiso download rhel-9.6-x86_64-dvd.iso --by-filename
   ```
   - Searches across RHEL versions automatically
   - Selects most recent if multiple matches
   - Early termination for faster results

3. **Custom Output Directory**
   ```bash
   rhiso download <checksum> --output ~/Downloads
   rhiso download rhel-9.6-x86_64-dvd.iso --by-filename --output /var/isos
   ```

### 🔐 Authentication

- OAuth 2.0 token exchange
- Offline token support (valid for 30 days with usage)
- Custom token file location support

### 📦 Installation Methods

1. **nix run** - No build required
   ```bash
   nix run . -- list
   nix run . -- download rhel-9.6-x86_64-dvd.iso --by-filename
   ```

2. **nix-build** - Build once, use many times
   ```bash
   nix-build shell.nix
   ./result/bin/rhiso list
   ```

3. **Direct Python**
   ```bash
   pip install -r requirements.txt
   ./rhiso.py list
   ```

### 🎯 Key Features

| Feature | Status | Description |
|---------|--------|-------------|
| List by version/arch | ✅ | Query specific RHEL versions |
| List by content set | ✅ | Browse historical releases |
| JSON output | ✅ | Automation-friendly format |
| Download by checksum | ✅ | Precise version control |
| Download by filename | ⭐ NEW | Automatic search & latest version |
| Progress indication | ✅ | Real-time download progress |
| Custom token file | ✅ | Flexible authentication |
| Nix package | ✅ | NixOS integration |
| Early search termination | ✅ | Fast filename lookups |

### 🚀 Usage Examples

**Quick Start:**
```bash
# 1. List all supported ISOs
nix run . -- list

# 2. Download by filename (easiest!)
nix run . -- download rhel-9.6-x86_64-dvd.iso --by-filename
```

**Advanced Usage:**
```bash
# JSON automation
rhiso --json list --version 9.6 --arch x86_64 | jq -r '.images[].checksum'

# Batch download all ISOs
rhiso --json list --version 9.6 --arch x86_64 | \
  jq -r '.images[].checksum' | \
  xargs -I {} rhiso download {} --output /var/isos
```

**Filename Search:**
```bash
# Automatically finds latest version
rhiso download rhel-9.6-x86_64-dvd.iso --by-filename

# Search output:
# Searching for filename: rhel-9.6-x86_64-dvd.iso
# This may take a moment as we search across multiple RHEL versions...
#
#   Searching RHEL 9.6 (x86_64)... ✓ Found!
#
# Found 1 match.
# Using checksum: febcc1359fd68faceff82d7eed8d21016e022a17e9c74e0e3f9dc3a78816b2bb
```

### 📊 Performance Optimizations

- **Early termination**: Stops searching once filename is found
- **Newest first**: Searches most recent versions first
- **Parallel listing**: Multiple API calls can run concurrently
- **Streaming downloads**: Memory-efficient file transfer

### 🔧 Technical Details

**RHEL Version Discovery:**
- Automatically discovers available RHEL versions via API probing
- Baseline: RHEL 10, 9, and 8 series (x86_64, aarch64)
- Auto-detects newer major versions (e.g., RHEL 11 when released)
- Auto-detects newer minor versions (e.g., 10.1, 9.7, etc.)
- Results cached per session for performance

**API Endpoints Used:**
- `/management/v1/images/rhel/{version}/{arch}` - List by version
- `/management/v1/images/cset/{content_set}` - List by content set
- `/management/v1/images/{checksum}/download` - Get download URL

**Output Formats:**
- Human-readable text (default)
- JSON (with `--json` flag)

### 📚 Documentation

- **README.md** - User guide and installation
- **USAGE_EXAMPLES.md** - Comprehensive examples
- **CLAUDE.md** - Technical architecture
- **JSON_OUTPUT.md** - JSON format reference
- **FEATURES.md** - This file
- **TESTING.md** - Test results
