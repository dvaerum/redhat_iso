# Documentation Index

Complete documentation for the Red Hat ISO Download Tool.

## 📚 Quick Links

- **[Main README](../README.md)** - Project overview and quick start
- **[Feature List](features.md)** - Complete list of features
- **[CLAUDE.md](../CLAUDE.md)** - Developer guide for Claude Code

## 📖 User Guides

### CLI Usage
- **[CLI Examples](usage/cli-examples.md)** - Command-line usage examples
  - List available ISOs
  - Download by checksum or filename
  - JSON output for automation
  - Custom token files and output directories

### Python Library
- **[Library API](usage/library.md)** - Using redhat_iso as a Python library
  - `RedHatAPI` class documentation
  - Programmatic access to Red Hat API
  - Integration into Python applications

### JSON Output
- **[JSON Format](usage/json-output.md)** - JSON output format specification
  - List operations format
  - Download response format
  - Error handling in JSON mode

## 🔧 NixOS Integration

### Installation & Configuration
- **[NixOS Installation Guide](nixos/installation.md)** - Complete NixOS integration
  - Overlay setup (adding `redhat_iso` package)
  - Module configuration (automatic downloads)
  - Real-world examples (PXE boot server)
  - Security best practices (agenix, sops-nix)

### Reference
- **[Module Options](nixos/module-options.md)** - Auto-generated module options reference
  - All configuration options documented
  - Types, defaults, and examples
  - **Auto-updated by CI/CD on every push**

### Internals
- **[Nix Packaging](nixos/packaging.md)** - Nix package structure
  - `flake.nix`, `default.nix`, `shell.nix`
  - Overlay and module exports
  - Development environment

## 👨‍💻 Developer Documentation

### Architecture
- **[Code Architecture](development/architecture.md)** - Module structure and design
  - Python package organization
  - Separation of concerns (API vs CLI)
  - Public exports and entry points

### Testing
- **[Testing Guide](development/testing.md)** - Comprehensive testing documentation
  - NixOS integration tests (10 subtests)
  - Manual CLI testing procedures
  - API integration testing
  - CI/CD integration

## 📋 Documentation by Task

### I want to...

#### ...use the CLI tool
1. Start with [Main README](../README.md) for installation
2. See [CLI Examples](usage/cli-examples.md) for usage
3. Check [JSON Format](usage/json-output.md) for automation

#### ...use it as a Python library
1. Read [Library API](usage/library.md)
2. See `example_library_usage.py` in the repository
3. Check [Code Architecture](development/architecture.md) for internals

#### ...integrate with NixOS
1. Follow [NixOS Installation Guide](nixos/installation.md)
2. Reference [Module Options](nixos/module-options.md) for configuration
3. See real-world examples in the installation guide

#### ...contribute to development
1. Read [CLAUDE.md](../CLAUDE.md) for development setup
2. Review [Code Architecture](development/architecture.md)
3. Follow [Testing Guide](development/testing.md) before commits
4. Run `nix flake check` to verify all tests pass

#### ...understand the features
1. Browse [Feature List](features.md)
2. Try [CLI Examples](usage/cli-examples.md)
3. Explore [NixOS Integration](nixos/installation.md) for advanced use

## 🔄 Documentation Maintenance

### Auto-Generated Documentation

Some documentation is auto-generated from source code:

- **[nixos/module-options.md](nixos/module-options.md)** - Generated from `modules/redhat-iso-downloader.nix`
  - Build locally: `nix-build generate-doc.nix`
  - Auto-updated by GitHub Actions on every push
  - Reflects actual module options

### Manual Documentation

All other documentation is manually maintained. When updating:

1. Keep examples up-to-date with actual code
2. Update CLAUDE.md when architecture changes
3. Cross-reference related documentation
4. Run tests to verify examples work

## 📂 Documentation Structure

```
docs/
├── README.md (this file)          # Documentation index
├── features.md                     # Feature list
│
├── usage/                          # User guides
│   ├── cli-examples.md            # CLI usage examples
│   ├── library.md                 # Python library API
│   └── json-output.md             # JSON format specs
│
├── nixos/                          # NixOS-specific
│   ├── installation.md            # Integration guide
│   ├── module-options.md          # Auto-generated options
│   └── packaging.md               # Nix internals
│
└── development/                    # Developer docs
    ├── architecture.md            # Code structure
    └── testing.md                 # Testing guide
```

## 🔗 External Resources

- **Red Hat Customer Portal**: https://access.redhat.com
- **API Token Generation**: https://access.redhat.com/management/api
- **Red Hat API Documentation**: https://access.redhat.com/documentation/
- **GitHub Repository**: https://github.com/dvaerum/redhat_iso (update with actual URL)

## 📝 Contributing to Documentation

Found an issue or want to improve the documentation?

1. Documentation files use GitHub Flavored Markdown
2. Keep line length reasonable (~100 characters)
3. Use code blocks with language syntax highlighting
4. Add cross-references to related documentation
5. Test code examples before documenting them

---

**Last Updated**: Auto-maintained by Git
**Documentation Version**: Synchronized with code version
