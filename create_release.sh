#!/bin/bash
# Quick script to create a new release

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Node3 Agent Release Creator ===${NC}\n"

# Check if version provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Please provide version number${NC}"
    echo "Usage: ./create_release.sh v1.0.0"
    exit 1
fi

VERSION=$1

# Validate version format
if [[ ! $VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}Error: Version must be in format v1.0.0${NC}"
    exit 1
fi

echo -e "${YELLOW}Creating release $VERSION${NC}\n"

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo -e "${RED}Warning: You have uncommitted changes${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update version in code if file exists
if [ -f "version.py" ]; then
    echo "Updating version.py..."
    echo "__version__ = '${VERSION#v}'" > version.py
    git add version.py
fi

# Commit version bump if needed
if [[ -n $(git status -s) ]]; then
    echo "Committing version bump..."
    git commit -m "Bump version to $VERSION"
fi

# Create and push tag
echo -e "\n${YELLOW}Creating git tag...${NC}"
git tag -a "$VERSION" -m "Release $VERSION"

echo -e "${YELLOW}Pushing to GitHub...${NC}"
git push origin main
git push origin "$VERSION"

echo -e "\n${GREEN}✅ Release created!${NC}"
echo -e "\nGitHub Actions will now:"
echo "  1. Build binaries for macOS, Linux, and Windows"
echo "  2. Create a GitHub Release"
echo "  3. Upload all binaries"
echo ""
echo "Monitor progress at:"
echo "  https://github.com/YOUR_USERNAME/node3-agent/actions"
echo ""
echo "Release will be available at:"
echo "  https://github.com/YOUR_USERNAME/node3-agent/releases/tag/$VERSION"

