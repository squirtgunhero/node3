# Code Signing Guide for macOS

This guide walks you through code signing your node3 agent to remove macOS security warnings.

## Prerequisites

- ✅ Apple Developer Account ($99/year)
- ✅ macOS computer
- ✅ Xcode Command Line Tools installed

## Step 1: Install Xcode Command Line Tools

If not already installed:

```bash
xcode-select --install
```

## Step 2: Get Your Developer ID Certificate

### Option A: Through Xcode (Recommended)

1. Open **Xcode**
2. Go to **Xcode** → **Settings** → **Accounts**
3. Click **+** and sign in with your Apple ID
4. Select your account → Click **Manage Certificates**
5. Click **+** → **Developer ID Application**
6. Certificate will be downloaded and installed in Keychain

### Option B: Through Apple Developer Portal

1. Go to [developer.apple.com/account/resources/certificates/list](https://developer.apple.com/account/resources/certificates/list)
2. Click **+** to create new certificate
3. Select **Developer ID Application**
4. Follow the wizard to create a Certificate Signing Request (CSR)
5. Download and double-click to install in Keychain

## Step 3: Verify Certificate Installation

```bash
security find-identity -v -p codesigning
```

You should see output like:
```
1) ABC123DEF456 "Developer ID Application: Your Name (TEAM_ID)"
```

**Copy your identity string** (e.g., "Developer ID Application: Your Name (TEAM_ID)")

## Step 4: Update release.py with Your Identity

Open `release.py` and update the code signing section with your identity:

```python
# In release.py, find CODESIGN_IDENTITY and update:
CODESIGN_IDENTITY = "Developer ID Application: Your Name (TEAM_ID)"
```

Or set as environment variable:

```bash
export CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
```

## Step 5: Generate App-Specific Password (for Notarization)

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign in
3. **Security** → **App-Specific Passwords**
4. Click **+** → Name it "node3 agent notarization"
5. Copy the generated password (xxxx-xxxx-xxxx-xxxx)

**Save this password** - you'll need it for notarization.

## Step 6: Get Your Team ID

```bash
# List your team IDs
xcrun notarytool store-credentials --list

# Or find in developer portal
open https://developer.apple.com/account
# Click on "Membership" in sidebar, copy Team ID
```

## Step 7: Build and Sign

### Automated (Recommended)

```bash
# Build with code signing
python release.py --bump patch --codesign

# Build, sign, and notarize
python release.py --bump patch --codesign --notarize
```

### Manual

```bash
# Build first
python build.py --type macos

# Sign the app bundle
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  --options runtime \
  --timestamp \
  dist/node3agent.app

# Verify signature
codesign --verify --deep --strict --verbose=2 dist/node3agent.app
spctl --assess --type execute --verbose dist/node3agent.app
```

## Step 8: Notarization (Required for macOS 10.15+)

### Setup Credentials (One-Time)

```bash
xcrun notarytool store-credentials "node3-notarize" \
  --apple-id "your@email.com" \
  --team-id "YOUR_TEAM_ID" \
  --password "xxxx-xxxx-xxxx-xxxx"
```

This securely saves your credentials in Keychain.

### Notarize the App

```bash
# Create ZIP for notarization
ditto -c -k --keepParent dist/node3agent.app node3agent.zip

# Submit for notarization
xcrun notarytool submit node3agent.zip \
  --keychain-profile "node3-notarize" \
  --wait

# If successful, staple the ticket
xcrun stapler staple dist/node3agent.app

# Verify notarization
spctl --assess --type execute --verbose dist/node3agent.app
```

**Expected output:**
```
dist/node3agent.app: accepted
source=Notarized Developer ID
```

## Step 9: Sign the DMG

After creating the DMG:

```bash
# Sign DMG
codesign --sign "Developer ID Application: Your Name (TEAM_ID)" \
  --timestamp \
  dist/node3agent-1.0.0-macos.dmg

# Verify
codesign --verify --verbose dist/node3agent-1.0.0-macos.dmg
```

## Automated Workflow

Update `release.py` configuration:

```bash
# Set environment variables
export CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
export NOTARIZE_PROFILE="node3-notarize"

# Run automated release with signing
python release.py --bump patch --codesign --notarize --github-release
```

This will:
1. ✅ Bump version
2. ✅ Build executable
3. ✅ Sign app bundle
4. ✅ Create DMG
5. ✅ Sign DMG
6. ✅ Submit for notarization
7. ✅ Staple notarization ticket
8. ✅ Create GitHub release

## Troubleshooting

### "No identity found"

**Problem:** `security find-identity` returns nothing

**Solution:**
1. Open Keychain Access
2. Look for "Developer ID Application" certificate
3. If not there, create new certificate in Xcode (Step 2)

### "rejected (malformed or invalid)"

**Problem:** App is rejected during notarization

**Solution:**
```bash
# Get detailed log
xcrun notarytool log <submission-id> --keychain-profile "node3-notarize"
```

Common issues:
- Missing `--options runtime` flag
- Unsigned nested binaries
- Invalid bundle structure

### "developer cannot be verified"

**Problem:** App shows security warning despite signing

**Solution:**
1. Ensure you signed with **Developer ID Application** (not "Mac App Distribution")
2. Must be notarized for macOS 10.15+
3. Check signature: `codesign --verify --deep --strict dist/node3agent.app`

### Notarization takes too long

**Problem:** `--wait` flag hangs

**Solution:**
```bash
# Submit without waiting
xcrun notarytool submit node3agent.zip \
  --keychain-profile "node3-notarize"

# Check status later
xcrun notarytool history --keychain-profile "node3-notarize"

# Get logs
xcrun notarytool log <submission-id> --keychain-profile "node3-notarize"
```

## Quick Reference

### Check Certificate
```bash
security find-identity -v -p codesigning
```

### Sign App
```bash
codesign --sign "$CODESIGN_IDENTITY" --options runtime --timestamp dist/node3agent.app
```

### Verify Signature
```bash
codesign --verify --deep --strict --verbose=2 dist/node3agent.app
```

### Notarize
```bash
ditto -c -k --keepParent dist/node3agent.app app.zip
xcrun notarytool submit app.zip --keychain-profile "node3-notarize" --wait
xcrun stapler staple dist/node3agent.app
```

### Check Notarization Status
```bash
spctl --assess --type execute --verbose dist/node3agent.app
```

## Cost Breakdown

- **Apple Developer Program:** $99/year
- **Code Signing:** Free (included)
- **Notarization:** Free (included)

## Security Benefits

✅ **No security warnings** when users download  
✅ **Verified developer** badge  
✅ **Malware protection** validation  
✅ **Professional distribution**  

## Next Steps

After signing and notarizing:

1. ✅ Test on a clean Mac
2. ✅ Upload to GitHub Releases
3. ✅ Users can download and run immediately
4. ✅ No "unidentified developer" warnings

---

**Need help?** Check the [Apple notarization guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)

