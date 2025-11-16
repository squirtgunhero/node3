# Create Your First Release 🚀

Your GitHub Releases automation is now set up! Here's how to create your first release.

## Quick Start (2 Steps)

### 1. Create and Push a Tag

```bash
cd ~/Desktop/node3agent
./create_release.sh v1.0.0
```

That's it! The script will:
- Create a git tag `v1.0.0`
- Push it to GitHub
- Trigger the automated build

### 2. Watch the Magic Happen

GitHub Actions will automatically:
1. ✅ Build binaries for macOS, Linux, and Windows
2. ✅ Create a GitHub Release
3. ✅ Upload all binaries with checksums
4. ✅ Add installation instructions

Monitor progress at:
```
https://github.com/squirtgunhero/node3/actions
```

In about 10-15 minutes, your release will be live at:
```
https://github.com/squirtgunhero/node3/releases/tag/v1.0.0
```

## What Just Got Set Up

### 1. GitHub Actions Workflow
📁 `.github/workflows/release.yml`
- Automatically builds for macOS, Linux, Windows
- Creates releases when you push version tags
- Generates checksums for verification

### 2. Release Creation Script
📁 `create_release.sh`
- Helper script to create releases quickly
- Validates version format
- Handles git tagging automatically

### 3. Download Instructions
📁 `DOWNLOAD.md`
- Complete download guide for users
- Platform-specific instructions
- Troubleshooting tips

### 4. Updated README
📁 `README.md`
- Now includes one-liner install commands
- Links to latest releases
- Platform-specific examples

## Manual Method (If Needed)

If you prefer to create tags manually:

```bash
# Create tag
git tag -a v1.0.0 -m "Release v1.0.0"

# Push tag to GitHub
git push origin v1.0.0
```

The GitHub Actions workflow will still run automatically!

## After Release is Created

Users can download with one command:

**macOS:**
```bash
curl -L -o node3-agent https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-macos
chmod +x node3-agent
./node3-agent
```

**Linux:**
```bash
curl -L -o node3-agent https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-linux
chmod +x node3-agent
./node3-agent
```

**Windows:**
```powershell
Invoke-WebRequest -Uri "https://github.com/squirtgunhero/node3/releases/latest/download/node3-agent-windows.exe" -OutFile "node3-agent.exe"
.\node3-agent.exe
```

## Version Numbering

Follow [semantic versioning](https://semver.org/):

- `v1.0.0` - Major release (breaking changes)
- `v1.1.0` - Minor release (new features, backward compatible)
- `v1.0.1` - Patch release (bug fixes)

## Examples

```bash
# First release
./create_release.sh v1.0.0

# Add new feature
./create_release.sh v1.1.0

# Bug fix
./create_release.sh v1.0.1

# Major version bump
./create_release.sh v2.0.0
```

## Pre-Release Checklist

Before creating a release:

- [ ] All tests pass locally
- [ ] Code builds successfully
- [ ] Binary tested on your platform
- [ ] CHANGELOG updated (if you have one)
- [ ] Version number decided

## Troubleshooting

### "GitHub Actions not running"
1. Go to: https://github.com/squirtgunhero/node3/actions
2. Check the "Actions" tab is enabled
3. Look for "Build and Release" workflow

### "Build failed"
1. Check the Actions logs
2. Common issues:
   - Missing dependencies in `requirements.txt`
   - PyInstaller compatibility
   - Platform-specific issues

### "Can't find GITHUB_TOKEN"
The workflow uses the automatic `GITHUB_TOKEN` provided by GitHub Actions. No setup needed!

## Next Steps

1. **Create your first release:**
   ```bash
   ./create_release.sh v1.0.0
   ```

2. **Share the download link:**
   ```
   https://github.com/squirtgunhero/node3/releases/latest
   ```

3. **Monitor downloads:**
   GitHub shows download counts on each release

4. **Update regularly:**
   Users trust actively maintained projects!

## Tips

- 📊 Release often (every 2-4 weeks is good)
- 📝 Write clear release notes
- 🐛 Fix critical bugs with patch releases
- 🎉 Celebrate milestones (v1.0.0, v2.0.0)
- 📢 Announce releases on social media

## Need Help?

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [GitHub Releases Docs](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Semantic Versioning](https://semver.org/)

---

Ready? Create your first release now:

```bash
./create_release.sh v1.0.0
```

🚀 Your users will be able to download the agent in minutes!

