# GitHub Release Guide

## Creating a Release

### Step 1: Commit and Push Code

```bash
# Add all changes
git add .

# Commit with release message
git commit -m "Release v1.0.0 - Distribution build ready"

# Push to GitHub
git push origin main
```

### Step 2: Create Release Tag

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0 - First distribution build"

# Push tag to GitHub
git push origin v1.0.0
```

### Step 3: Create GitHub Release

1. Go to GitHub repository
2. Click "Releases" → "Draft a new release"
3. Select tag: `v1.0.0`
4. Title: `v1.0.0 - First Distribution Build`
5. Description:

```markdown
## 🎉 First Distribution Release

### What's New
- ✅ Optimized executable (403MB - 31% smaller)
- ✅ macOS DMG installer ready
- ✅ Zero Docker dependency
- ✅ Native job execution
- ✅ Real-time dashboard
- ✅ GPU monitoring

### Installation

**macOS:**
1. Download `node3-agent-installer.dmg`
2. Double-click to mount
3. Drag `node3-agent.app` to Applications
4. Open from Applications folder

**Note:** First run may show security warning. Go to System Preferences → Security & Privacy → Click "Open Anyway"

### Requirements
- macOS 10.15 or later
- 8GB+ RAM
- 50GB+ disk space
- GPU (optional - CPU jobs also supported)

### Features
- 🚀 Native execution (no Docker needed)
- 📊 Real-time dashboard
- 💰 Solana wallet integration
- 🔧 GPU detection and monitoring
- 💼 Job marketplace integration

### Links
- Documentation: See README.md
- Issues: Report bugs on GitHub Issues
```

6. Upload `node3-agent-installer.dmg` to assets
7. Click "Publish release"

### Step 4: Update README Download Link

After release is published, update README.md with actual release URL:

```markdown
Download: [Latest Release](https://github.com/YOUR_USERNAME/node3agent/releases/latest)
```

## Automated Release (Optional)

Create `.github/workflows/release.yml` for automated releases:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-and-release:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Build executable
        run: python build.py --type macos
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: node3-agent-installer.dmg
          draft: false
          prerelease: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Release Checklist

- [ ] All code committed
- [ ] Version updated in main.py
- [ ] README updated
- [ ] DMG built and tested
- [ ] Tag created
- [ ] Tag pushed to GitHub
- [ ] GitHub Release created
- [ ] DMG uploaded to release
- [ ] Release notes written
- [ ] Download link verified

