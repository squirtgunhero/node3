#!/bin/bash
# Setup script for code signing and notarization

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        node3 Agent Code Signing Setup Assistant           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check for Xcode Command Line Tools
echo -e "${BLUE}➜${NC} Checking for Xcode Command Line Tools..."
if ! xcode-select -p &> /dev/null; then
    echo -e "${RED}✗${NC} Xcode Command Line Tools not installed"
    echo ""
    echo "Installing Xcode Command Line Tools..."
    xcode-select --install
    echo ""
    echo -e "${YELLOW}Please complete the installation and run this script again.${NC}"
    exit 1
else
    echo -e "${GREEN}✓${NC} Xcode Command Line Tools installed"
fi

# Step 2: Check for code signing certificate
echo ""
echo -e "${BLUE}➜${NC} Checking for Developer ID certificate..."
IDENTITY=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | sed 's/^[^"]*"\([^"]*\)".*/\1/')

if [ -z "$IDENTITY" ]; then
    echo -e "${RED}✗${NC} No Developer ID Application certificate found"
    echo ""
    echo "You need to create a Developer ID certificate:"
    echo ""
    echo "Option 1: Through Xcode (Recommended)"
    echo "  1. Open Xcode"
    echo "  2. Xcode → Settings → Accounts"
    echo "  3. Click + and sign in with your Apple ID"
    echo "  4. Select your account → Manage Certificates"
    echo "  5. Click + → Developer ID Application"
    echo ""
    echo "Option 2: Through Apple Developer Portal"
    echo "  1. Go to: https://developer.apple.com/account/resources/certificates/list"
    echo "  2. Click + → Developer ID Application"
    echo "  3. Follow the wizard"
    echo ""
    echo -e "${YELLOW}After creating the certificate, run this script again.${NC}"
    exit 1
else
    echo -e "${GREEN}✓${NC} Found: $IDENTITY"
    
    # Save to .env file
    ENV_FILE=".env"
    if [ -f "$ENV_FILE" ]; then
        # Remove old CODESIGN_IDENTITY if exists
        sed -i '' '/CODESIGN_IDENTITY/d' "$ENV_FILE"
    fi
    echo "CODESIGN_IDENTITY=\"$IDENTITY\"" >> "$ENV_FILE"
    echo -e "${GREEN}✓${NC} Saved to $ENV_FILE"
fi

# Step 3: Get Apple ID for notarization
echo ""
echo -e "${BLUE}➜${NC} Setting up notarization credentials..."
echo ""
read -p "Enter your Apple ID email: " APPLE_ID

if [ -z "$APPLE_ID" ]; then
    echo -e "${YELLOW}⚠${NC} Skipping notarization setup"
else
    # Get Team ID
    echo ""
    echo "Finding your Team ID..."
    echo "(You can find this at: https://developer.apple.com/account → Membership)"
    echo ""
    read -p "Enter your Team ID (10 characters, e.g., ABC123DEF4): " TEAM_ID
    
    if [ -z "$TEAM_ID" ]; then
        echo -e "${YELLOW}⚠${NC} No Team ID provided, skipping notarization setup"
    else
        echo ""
        echo "You need an App-Specific Password for notarization:"
        echo "  1. Go to: https://appleid.apple.com"
        echo "  2. Sign in → Security → App-Specific Passwords"
        echo "  3. Click + → Name it 'node3 agent notarization'"
        echo "  4. Copy the password (xxxx-xxxx-xxxx-xxxx)"
        echo ""
        read -s -p "Enter your App-Specific Password: " APP_PASSWORD
        echo ""
        
        if [ -z "$APP_PASSWORD" ]; then
            echo -e "${YELLOW}⚠${NC} No password provided, skipping notarization setup"
        else
            echo ""
            echo -e "${BLUE}➜${NC} Storing notarization credentials..."
            
            # Store credentials in keychain
            xcrun notarytool store-credentials "node3-notarize" \
                --apple-id "$APPLE_ID" \
                --team-id "$TEAM_ID" \
                --password "$APP_PASSWORD"
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓${NC} Notarization credentials saved to keychain"
                
                # Save profile name to .env
                if [ -f "$ENV_FILE" ]; then
                    sed -i '' '/NOTARIZE_PROFILE/d' "$ENV_FILE"
                fi
                echo "NOTARIZE_PROFILE=\"node3-notarize\"" >> "$ENV_FILE"
            else
                echo -e "${RED}✗${NC} Failed to store credentials"
                exit 1
            fi
        fi
    fi
fi

# Step 4: Summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   Setup Complete! ✓                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Your configuration:"
echo "  • Code Signing Identity: $IDENTITY"
if [ ! -z "$APPLE_ID" ]; then
    echo "  • Apple ID: $APPLE_ID"
    echo "  • Team ID: $TEAM_ID"
    echo "  • Notarization Profile: node3-notarize"
fi
echo ""
echo "Environment variables saved to: $ENV_FILE"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Load environment variables:"
echo "     source .env"
echo ""
echo "  2. Build and sign a release:"
echo "     python release.py --bump patch --codesign --notarize"
echo ""
echo "  3. Or set them permanently in your shell profile:"
echo "     echo 'export CODESIGN_IDENTITY=\"$IDENTITY\"' >> ~/.zshrc"
echo "     echo 'export NOTARIZE_PROFILE=\"node3-notarize\"' >> ~/.zshrc"
echo ""

# Create helper script to load env vars
cat > load_env.sh << 'EOF'
#!/bin/bash
# Source this file to load code signing environment variables
# Usage: source load_env.sh

if [ -f .env ]; then
    export $(cat .env | xargs)
    echo "✓ Environment variables loaded"
    echo "  CODESIGN_IDENTITY: $CODESIGN_IDENTITY"
    echo "  NOTARIZE_PROFILE: $NOTARIZE_PROFILE"
else
    echo "✗ .env file not found"
    echo "Run: ./setup_codesign.sh"
fi
EOF

chmod +x load_env.sh

echo -e "${GREEN}✓${NC} Created load_env.sh helper script"
echo ""

