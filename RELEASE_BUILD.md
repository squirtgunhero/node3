# Release Build Guide

## Quick Build Commands

### Build Executable Only
```bash
python build.py --type exe
```

### Build macOS DMG Installer
```bash
python build.py --type macos
# Or use the script:
./create_dmg.sh
```

### Build Everything
```bash
python build.py --type all
```

## Optimization Steps

### 1. Optimize Executable Size

The build script now includes optimizations:
- Excludes unused modules (matplotlib, pandas, etc.)
- Strips debug symbols
- Only collects necessary FastAPI/uvicorn modules

**Current size:** ~586MB (can be optimized further)

**To reduce further:**
1. Review `requirements.txt` - remove unused dependencies
2. Use UPX compression (add `--upx-dir` to PyInstaller)
3. Split into separate modules
4. Use virtual environment with minimal packages

### 2. Code Signing (macOS)

To code sign the executable:

```bash
# Sign the executable
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/node3-agent.app

# Verify signature
codesign --verify --verbose dist/node3-agent.app
spctl --assess --verbose dist/node3-agent.app
```

**Requirements:**
- Apple Developer account ($99/year)
- Developer ID certificate installed in Keychain

### 3. Notarization (macOS)

For distribution outside App Store:

```bash
# Create notarization package
ditto -c -k --keepParent dist/node3-agent.app node3-agent.zip

# Submit for notarization
xcrun notarytool submit node3-agent.zip \
    --apple-id your@email.com \
    --team-id YOUR_TEAM_ID \
    --password YOUR_APP_SPECIFIC_PASSWORD \
    --wait

# Staple the notarization ticket
xcrun stapler staple dist/node3-agent.app
```

### 4. DMG Optimization

The `create_dmg.sh` script creates a DMG with:
- Proper Applications symlink
- Clean layout
- Compressed format (UDZO)

**To customize:**
- Add background image: `dmg_background.png`
- Customize icon positions with `osascript`
- Add README file in DMG

## Version Management

Version is read from `main.py`:
```python
VERSION = "1.0.0"
```

Update this before each release.

## Build Checklist

Before releasing:

- [ ] Update version in `main.py`
- [ ] Update version in `build.py` (Info.plist)
- [ ] Test executable on clean system
- [ ] Verify all features work
- [ ] Code sign (if distributing)
- [ ] Notarize (if distributing publicly)
- [ ] Create DMG
- [ ] Test DMG installation
- [ ] Upload to GitHub Releases
- [ ] Update README with download links

## GitHub Releases

To create a release:

1. **Tag the release:**
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

2. **Create release on GitHub:**
   - Go to Releases → Draft new release
   - Select tag v1.0.0
   - Upload DMG file
   - Add release notes

3. **Automate with GitHub Actions** (optional):
   - Create `.github/workflows/release.yml`
   - Auto-build on tag push
   - Auto-upload to releases

## Distribution Options

### Option 1: Direct Download
- Upload DMG to GitHub Releases
- Users download and install manually

### Option 2: Homebrew Cask
```ruby
# Formula: node3-agent.rb
cask 'node3-agent' do
  version '1.0.0'
  sha256 '...'
  url "https://github.com/node3/agent/releases/download/v#{version}/node3-agent-installer-#{version}.dmg"
  name 'node³ Agent'
  homepage 'https://node3.com'
  app 'node3-agent.app'
end
```

### Option 3: Auto-Updates
- Implement update checker in agent
- Download updates automatically
- Prompt user to install

## Size Optimization Tips

**Current:** ~586MB

**Target:** <200MB

**Strategies:**
1. **Remove unnecessary dependencies:**
   - Review imports in each file
   - Remove unused libraries from requirements.txt

2. **Use PyInstaller excludes:**
   - Already added: matplotlib, pandas, scipy, jupyter
   - Add more as needed

3. **Split into modules:**
   - Separate core from optional features
   - Load modules on demand

4. **Use UPX compression:**
   - Add `--upx-dir=/path/to/upx` to PyInstaller
   - Can reduce size by 30-50%

5. **Consider alternatives:**
   - Use `--onedir` instead of `--onefile` (faster startup)
   - Use Docker image for deployment
   - Provide pip package instead

## Testing the Build

After building:

```bash
# Test executable
./dist/node3-agent --help

# Test DMG (on macOS)
hdiutil attach node3-agent-installer-1.0.0.dmg
# Drag to Applications, test
hdiutil detach /Volumes/node3-agent
```

## Troubleshooting

### "Executable too large"
- Use `--exclude-module` for unused libs
- Consider `--onedir` instead of `--onefile`
- Use UPX compression

### "Code signing failed"
- Check certificate is installed: `security find-identity -v -p codesigning`
- Ensure certificate is valid and not expired
- Use `--deep` flag for nested bundles

### "Notarization failed"
- Check logs: `xcrun notarytool log <submission-id>`
- Ensure all binaries are signed
- Fix any errors and resubmit

### "DMG won't mount"
- Check file integrity: `hdiutil verify node3-agent-installer.dmg`
- Rebuild DMG with `create_dmg.sh`
- Ensure .app bundle is valid

## Next Steps

1. ✅ Optimize build script (done)
2. ⏳ Build and test executable
3. ⏳ Create DMG
4. ⏳ Code sign (if distributing)
5. ⏳ Upload to GitHub Releases

