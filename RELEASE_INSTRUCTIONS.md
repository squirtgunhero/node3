# Release Instructions

## Automated Release (Recommended)

The easiest way to create a release is using GitHub Actions:

### 1. Create a Git Tag

```bash
# Update version in your code if needed
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

This will automatically:
- Build binaries for macOS, Linux, and Windows
- Create a GitHub Release
- Upload all binaries
- Generate checksums

### 2. Users Can Download

Once the release is created, users can download binaries directly from:
```
https://github.com/YOUR_USERNAME/node3-agent/releases/latest
```

## Manual Release (If Needed)

If you need to create a manual release:

### Build Binaries

**macOS:**
```bash
python build.py
# Binary at: dist/node3-agent
```

**Linux:**
```bash
# On a Linux machine or using Docker
python build_linux.py
# Binary at: dist/node3-agent
```

**Windows:**
```bash
# On a Windows machine
python build_windows.py
# Binary at: dist/node3-agent.exe
```

### Create Release Manually

1. Go to: `https://github.com/YOUR_USERNAME/node3-agent/releases/new`
2. Create a new tag (e.g., `v1.0.0`)
3. Upload the binaries:
   - `node3-agent-macos` (macOS binary)
   - `node3-agent-linux` (Linux binary)
   - `node3-agent-windows.exe` (Windows binary)
4. Add release notes
5. Click "Publish release"

## Version Numbering

Follow semantic versioning:
- `v1.0.0` - Major release
- `v1.1.0` - Minor release (new features)
- `v1.0.1` - Patch release (bug fixes)

## Testing Before Release

Always test the binaries before releasing:

```bash
# Test the binary
./dist/node3-agent --help
./dist/node3-agent --version

# Test basic functionality
./dist/node3-agent
# Check if it starts correctly
```

## Checklist

Before creating a release:

- [ ] All tests pass
- [ ] Version number updated
- [ ] CHANGELOG.md updated
- [ ] README.md updated (if needed)
- [ ] Binaries tested on target platforms
- [ ] Git tag created
- [ ] Release notes prepared

## Post-Release

After release:

1. Announce on social media / community channels
2. Update documentation site (if any)
3. Monitor for issues
4. Respond to user feedback

## Rollback

If you need to rollback:

1. Delete the git tag:
   ```bash
   git tag -d v1.0.0
   git push origin :refs/tags/v1.0.0
   ```

2. Delete the GitHub release from the web interface

3. Fix the issue and create a new release

