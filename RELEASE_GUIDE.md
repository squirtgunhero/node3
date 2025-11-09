# Release Guide

Quick reference for creating releases using the automated build script.

## Quick Start

### Show Current Version
```bash
python release.py --current
```

### Create a Patch Release (1.0.0 → 1.0.1)
```bash
python release.py --bump patch
```

### Create a Minor Release (1.0.1 → 1.1.0)
```bash
python release.py --bump minor
```

### Create a Major Release (1.1.0 → 2.0.0)
```bash
python release.py --bump major
```

### Set Specific Version
```bash
python release.py --version 1.2.3
```

## Full Release (with GitHub Release)

```bash
python release.py --bump patch --github-release
```

This will:
1. ✅ Bump version in `main.py`
2. ✅ Commit version bump
3. ✅ Clean build artifacts
4. ✅ Build optimized executable
5. ✅ Create macOS DMG installer
6. ✅ Create git tag
7. ✅ Create GitHub release with DMG attached

## Code Signed Release (Recommended)

### First Time Setup

Run the setup assistant:
```bash
./setup_codesign.sh
```

This will:
- Check for Xcode Command Line Tools
- Find your Developer ID certificate
- Setup notarization credentials
- Create `.env` file with your settings

### Build Signed Release

```bash
# Load environment variables
source load_env.sh

# Build, sign, and notarize
python release.py --bump patch --codesign --notarize --github-release
```

This will:
1. ✅ Bump version
2. ✅ Build executable
3. ✅ **Code sign app bundle**
4. ✅ **Notarize with Apple**
5. ✅ Create DMG
6. ✅ **Code sign DMG**
7. ✅ Create GitHub release

**Result:** Users get ZERO security warnings! 🎉

## Partial Builds

### Just Update Version (no build)
```bash
python release.py --bump patch --skip-build
```

### Build Without DMG
```bash
python release.py --bump patch --skip-dmg
```

### Build Without Git Operations
```bash
python release.py --bump patch --skip-commit --skip-tag
```

## Advanced Options

```bash
python release.py --help
```

### Available Flags

**Version Control:**
- `--version X.Y.Z` - Set specific version
- `--bump [major|minor|patch]` - Auto-increment version
- `--current` - Show current version only

**Build Options:**
- `--skip-build` - Skip PyInstaller build
- `--skip-dmg` - Skip DMG creation
- `--skip-tag` - Skip git tag creation
- `--skip-commit` - Skip git commit

**Code Signing:**
- `--codesign` - Code sign app and DMG
- `--identity "Developer ID"` - Specify signing identity
- `--notarize` - Submit to Apple for notarization (requires `--codesign`)
- `--notarize-profile NAME` - Use custom keychain profile (default: `node3-notarize`)

**Distribution:**
- `--github-release` - Create GitHub release (requires `gh` CLI)

## Prerequisites

### Required
- Python 3.9+
- PyInstaller: `pip install pyinstaller`
- macOS (for DMG creation)

### Optional (but Recommended)
- **Apple Developer Account** ($99/year) - for code signing
  - Removes all security warnings
  - Professional distribution
- GitHub CLI for releases: `brew install gh`
  - Authenticated: `gh auth login`

## Typical Workflow

### 1. Bug Fix Release
```bash
# Fix bugs, test locally
python release.py --bump patch --github-release
git push origin main --tags
```

### 2. Feature Release
```bash
# Add features, test
python release.py --bump minor --github-release
git push origin main --tags
```

### 3. Breaking Changes
```bash
# Major refactor
python release.py --bump major --github-release
git push origin main --tags
```

## Manual GitHub Release

If you skip `--github-release`, you can manually create later:

```bash
# After building
gh release create v1.0.1 dist/node3agent-1.0.1-macos.dmg \
  --title "v1.0.1" \
  --notes "Bug fixes and improvements"
```

## Troubleshooting

### "gh: command not found"
Install GitHub CLI:
```bash
brew install gh
gh auth login
```

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### DMG Creation Failed
Check `create_dmg.sh` script exists and is executable:
```bash
chmod +x create_dmg.sh
```

### Version Not Updated
Check `main.py` has `VERSION = "x.x.x"` line

## Version Numbering

We use Semantic Versioning (semver):

- **Major (X.0.0)**: Breaking changes
- **Minor (1.X.0)**: New features (backwards compatible)
- **Patch (1.0.X)**: Bug fixes

### Examples
- `1.0.0` → `1.0.1`: Bug fix
- `1.0.1` → `1.1.0`: New feature
- `1.1.0` → `2.0.0`: Breaking change

## Release Checklist

- [ ] All tests pass
- [ ] Version bumped
- [ ] Changelog updated
- [ ] Built and tested locally
- [ ] Git tagged
- [ ] Pushed to GitHub
- [ ] GitHub release created
- [ ] Release notes written
- [ ] DMG tested on clean macOS

## Examples

### Quick Patch Release (Unsigned)
```bash
# Test first
./dist/node3agent

# Build and release
python release.py --bump patch --github-release
git push origin main --tags
```

### Production Release (Signed & Notarized)
```bash
# One-time setup
./setup_codesign.sh

# Load credentials
source load_env.sh

# Build, sign, notarize, and release
python release.py --bump patch --codesign --notarize --github-release

# Push to GitHub
git push origin main --tags
```

### Feature Release with Manual Testing
```bash
# Build without release
python release.py --bump minor --skip-tag

# Test the build
./dist/node3agent

# If good, tag and release
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin main --tags

# Create GitHub release
gh release create v1.1.0 dist/node3agent-1.1.0-macos.dmg \
  --title "v1.1.0 - Feature Update" \
  --notes "See CHANGELOG.md for details"
```

### Sign Existing Build
```bash
# Build first (unsigned)
python release.py --bump patch --skip-tag --skip-commit

# Test it
./dist/node3agent

# Sign and notarize
source load_env.sh
python release.py --version 1.0.1 --skip-build --codesign --notarize --github-release
```

---

**Happy Releasing! 🚀**

