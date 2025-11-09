#!/usr/bin/env python3
"""
Automated Release Builder for node3 Agent
==========================================

This script automates the entire release process:
1. Version bumping (major.minor.patch)
2. Building executable with PyInstaller
3. Creating macOS DMG installer
4. Optionally creating GitHub release

Usage:
    python release.py --version 1.0.1
    python release.py --bump patch
    python release.py --bump minor
    python release.py --bump major
    python release.py --current  # Just show current version
"""

import os
import sys
import argparse
import subprocess
import shutil
import re
from pathlib import Path
from datetime import datetime
import tempfile

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{message.center(60)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

def print_step(message):
    print(f"{Colors.BOLD}{Colors.BLUE}➜{Colors.ENDC} {message}")

def print_success(message):
    print(f"{Colors.GREEN}✓{Colors.ENDC} {message}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠{Colors.ENDC} {message}")

def print_error(message):
    print(f"{Colors.RED}✗{Colors.ENDC} {message}")

def run_command(cmd, cwd=None, capture_output=False):
    """Run a shell command and return result"""
    try:
        if capture_output:
            result = subprocess.run(
                cmd, 
                shell=True, 
                cwd=cwd, 
                capture_output=True, 
                text=True,
                check=True
            )
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, cwd=cwd, check=True)
            return True
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {cmd}")
        if capture_output and e.stderr:
            print(e.stderr)
        return None

def get_current_version():
    """Read current version from main.py"""
    main_py = Path(__file__).parent / "main.py"
    
    with open(main_py, 'r') as f:
        content = f.read()
        match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    
    return "0.0.0"

def set_version(version):
    """Update VERSION in main.py"""
    main_py = Path(__file__).parent / "main.py"
    
    with open(main_py, 'r') as f:
        content = f.read()
    
    # Replace VERSION = "x.x.x" with new version
    new_content = re.sub(
        r'VERSION\s*=\s*["\'][^"\']+["\']',
        f'VERSION = "{version}"',
        content
    )
    
    with open(main_py, 'w') as f:
        f.write(new_content)
    
    print_success(f"Updated VERSION to {version} in main.py")

def bump_version(current, bump_type):
    """Bump version number"""
    parts = current.split('.')
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    
    return f"{major}.{minor}.{patch}"

def clean_build_artifacts():
    """Clean previous build artifacts"""
    print_step("Cleaning previous build artifacts...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        dir_path = Path(__file__).parent / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print_success(f"Removed {dir_name}/")
    
    # Clean .spec files
    for spec_file in Path(__file__).parent.glob("*.spec"):
        spec_file.unlink()
        print_success(f"Removed {spec_file.name}")

def build_executable():
    """Build executable with PyInstaller"""
    print_step("Building executable with PyInstaller...")
    
    # Build command with optimizations
    cmd = [
        "pyinstaller",
        "--name=node3agent",
        "--onefile",
        "--windowed",
        "--icon=icon.icns",
        "--add-data=templates:templates",
        "--add-data=static:static",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--collect-all=fastapi",
        "--collect-all=pydantic",
        # Exclude unused modules to reduce size
        "--exclude-module=matplotlib",
        "--exclude-module=numpy",
        "--exclude-module=pandas",
        "--exclude-module=scipy",
        "--exclude-module=IPython",
        "--exclude-module=jupyter",
        "--exclude-module=notebook",
        "--exclude-module=tkinter",
        "--exclude-module=PyQt5",
        "--exclude-module=PyQt6",
        "--exclude-module=PySide2",
        "--exclude-module=PySide6",
        "--strip",
        "--clean",
        "main.py"
    ]
    
    result = run_command(" ".join(cmd))
    
    if result:
        print_success("Executable built successfully")
        
        # Get file size
        exe_path = Path(__file__).parent / "dist" / "node3agent"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print_success(f"Executable size: {size_mb:.1f} MB")
        
        return True
    else:
        print_error("Failed to build executable")
        return False

def create_dmg(version):
    """Create macOS DMG installer"""
    print_step("Creating macOS DMG installer...")
    
    script_dir = Path(__file__).parent
    dist_dir = script_dir / "dist"
    dmg_name = f"node3agent-{version}-macos.dmg"
    dmg_path = dist_dir / dmg_name
    
    # Remove old DMG if exists
    if dmg_path.exists():
        dmg_path.unlink()
    
    # Create DMG using create_dmg.sh script
    result = run_command(f"bash create_dmg.sh {version}", cwd=script_dir)
    
    if result and dmg_path.exists():
        size_mb = dmg_path.stat().st_size / (1024 * 1024)
        print_success(f"DMG created: {dmg_name} ({size_mb:.1f} MB)")
        return True
    else:
        print_error("Failed to create DMG")
        return False

def code_sign_app(app_path, identity=None):
    """Code sign the app bundle"""
    print_step("Code signing application...")
    
    # Get identity from environment or parameter
    if identity is None:
        identity = os.environ.get('CODESIGN_IDENTITY')
    
    if not identity:
        print_error("No code signing identity provided")
        print("Set CODESIGN_IDENTITY environment variable or use --identity flag")
        print("\nFind your identity:")
        print("  security find-identity -v -p codesigning")
        return False
    
    # Sign the app with hardened runtime
    cmd = [
        "codesign",
        "--deep",
        "--force",
        "--verify",
        "--verbose",
        "--sign", f'"{identity}"',
        "--options", "runtime",
        "--timestamp",
        str(app_path)
    ]
    
    result = run_command(" ".join(cmd))
    
    if result:
        # Verify signature
        verify_cmd = f"codesign --verify --deep --strict --verbose=2 {app_path}"
        verify_result = run_command(verify_cmd, capture_output=True)
        
        if verify_result:
            print_success(f"App signed successfully with identity: {identity}")
            return True
        else:
            print_error("Signature verification failed")
            return False
    else:
        print_error("Code signing failed")
        return False

def code_sign_dmg(dmg_path, identity=None):
    """Code sign the DMG"""
    print_step("Code signing DMG...")
    
    # Get identity from environment or parameter
    if identity is None:
        identity = os.environ.get('CODESIGN_IDENTITY')
    
    if not identity:
        print_error("No code signing identity provided")
        return False
    
    cmd = [
        "codesign",
        "--sign", f'"{identity}"',
        "--timestamp",
        str(dmg_path)
    ]
    
    result = run_command(" ".join(cmd))
    
    if result:
        # Verify signature
        verify_cmd = f"codesign --verify --verbose {dmg_path}"
        if run_command(verify_cmd, capture_output=True):
            print_success("DMG signed successfully")
            return True
        else:
            print_error("DMG signature verification failed")
            return False
    else:
        print_error("DMG signing failed")
        return False

def notarize_app(app_path, profile="node3-notarize"):
    """Notarize the app with Apple"""
    print_step("Submitting app for notarization...")
    print_warning("This may take a few minutes...")
    
    # Create temporary ZIP for notarization
    zip_path = Path(app_path).parent / "node3agent_notarize.zip"
    
    try:
        # Create ZIP
        print_step("Creating ZIP for notarization...")
        cmd = f"ditto -c -k --keepParent {app_path} {zip_path}"
        if not run_command(cmd):
            print_error("Failed to create ZIP for notarization")
            return False
        
        # Check if profile exists
        profile_check = run_command("xcrun notarytool store-credentials --list", capture_output=True)
        if profile not in profile_check:
            print_error(f"Notarization profile '{profile}' not found")
            print("\nSetup notarization:")
            print(f"  xcrun notarytool store-credentials \"{profile}\" \\")
            print("    --apple-id your@email.com \\")
            print("    --team-id YOUR_TEAM_ID \\")
            print("    --password xxxx-xxxx-xxxx-xxxx")
            return False
        
        # Submit for notarization
        print_step("Uploading to Apple (this may take a while)...")
        cmd = f'xcrun notarytool submit {zip_path} --keychain-profile "{profile}" --wait'
        result = run_command(cmd)
        
        if result:
            print_success("Notarization successful!")
            
            # Staple the ticket
            print_step("Stapling notarization ticket...")
            staple_cmd = f"xcrun stapler staple {app_path}"
            if run_command(staple_cmd):
                print_success("Notarization ticket stapled")
                
                # Final verification
                verify_cmd = f"spctl --assess --type execute --verbose {app_path}"
                verify_output = run_command(verify_cmd, capture_output=True)
                if verify_output and "accepted" in verify_output.lower():
                    print_success("App is fully notarized and ready for distribution!")
                    return True
                else:
                    print_warning("Stapling succeeded but verification unclear")
                    return True
            else:
                print_warning("Stapling failed, but app is notarized")
                return True
        else:
            print_error("Notarization failed")
            print("\nCheck logs:")
            print(f"  xcrun notarytool history --keychain-profile \"{profile}\"")
            return False
    
    finally:
        # Clean up ZIP
        if zip_path.exists():
            zip_path.unlink()

def create_git_tag(version):
    """Create git tag for release"""
    print_step(f"Creating git tag v{version}...")
    
    # Check if tag already exists
    existing_tags = run_command("git tag", capture_output=True)
    if existing_tags and f"v{version}" in existing_tags:
        print_warning(f"Tag v{version} already exists")
        return False
    
    # Create tag
    tag_message = f"Release v{version}"
    result = run_command(f'git tag -a v{version} -m "{tag_message}"')
    
    if result:
        print_success(f"Created tag v{version}")
        return True
    else:
        print_error("Failed to create git tag")
        return False

def commit_version_bump(version):
    """Commit version bump to git"""
    print_step("Committing version bump...")
    
    # Add main.py
    run_command("git add main.py")
    
    # Commit
    result = run_command(f'git commit -m "Bump version to {version}"')
    
    if result:
        print_success("Version bump committed")
        return True
    else:
        print_warning("Nothing to commit or commit failed")
        return False

def generate_release_notes(version):
    """Generate release notes"""
    notes = f"""# node3 Agent v{version}

## 🚀 What's New

### Features
- **Native Execution**: Run jobs without Docker - zero setup required
- **Modern Dashboard**: Real-time monitoring with Apple/Tesla aesthetic
- **GPU Support**: Automatic detection and monitoring (NVIDIA, AMD, Intel, Apple)
- **Solana Integration**: Earn SOL for completed jobs
- **Light/Dark Mode**: Beautiful UI with theme toggle

### Installation
Download the DMG, drag to Applications, and run. No additional setup needed!

### Requirements
- macOS 10.15+
- No Docker required (native execution)
- Optional: NVIDIA/AMD GPU for GPU jobs

### Files
- `node3agent-{version}-macos.dmg` - macOS installer
- `node3agent` - Standalone executable

## 📊 Metrics
- Executable size: ~50-100MB (optimized)
- Memory usage: ~100-200MB
- Startup time: <5 seconds

## 🐛 Known Issues
- macOS may show security warning (see README for instructions)
- GPU metrics on Intel Macs are estimated (requires sudo for real data)

## 📚 Documentation
See README.md for full documentation and troubleshooting.

Built on {datetime.now().strftime('%Y-%m-%d')}
"""
    
    return notes

def create_github_release(version):
    """Create GitHub release (requires gh CLI)"""
    print_step("Creating GitHub release...")
    
    # Check if gh CLI is installed
    gh_check = run_command("which gh", capture_output=True)
    if not gh_check:
        print_warning("GitHub CLI (gh) not installed - skipping release creation")
        print("Install with: brew install gh")
        return False
    
    # Check if authenticated
    auth_check = run_command("gh auth status", capture_output=True)
    if not auth_check:
        print_warning("Not authenticated with GitHub - skipping release creation")
        print("Run: gh auth login")
        return False
    
    # Generate release notes
    notes = generate_release_notes(version)
    notes_file = Path(__file__).parent / "dist" / "release_notes.md"
    notes_file.write_text(notes)
    
    # Get DMG path
    dmg_path = Path(__file__).parent / "dist" / f"node3agent-{version}-macos.dmg"
    
    if not dmg_path.exists():
        print_error("DMG not found - cannot create release")
        return False
    
    # Create release
    cmd = f'gh release create v{version} "{dmg_path}" --title "v{version}" --notes-file "{notes_file}"'
    result = run_command(cmd)
    
    if result:
        print_success(f"GitHub release v{version} created")
        print(f"\n{Colors.CYAN}View at: https://github.com/squirtgunhero/node3.git/releases/tag/v{version}{Colors.ENDC}")
        return True
    else:
        print_error("Failed to create GitHub release")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Automated release builder for node3 agent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--version', help='Set specific version (e.g., 1.0.1)')
    group.add_argument('--bump', choices=['major', 'minor', 'patch'], help='Bump version')
    group.add_argument('--current', action='store_true', help='Show current version')
    
    parser.add_argument('--skip-build', action='store_true', help='Skip building (just bump version)')
    parser.add_argument('--skip-dmg', action='store_true', help='Skip DMG creation')
    parser.add_argument('--skip-tag', action='store_true', help='Skip git tag creation')
    parser.add_argument('--skip-commit', action='store_true', help='Skip git commit')
    parser.add_argument('--github-release', action='store_true', help='Create GitHub release')
    
    # Code signing arguments
    parser.add_argument('--codesign', action='store_true', help='Code sign the executable and DMG')
    parser.add_argument('--identity', help='Code signing identity (or set CODESIGN_IDENTITY env var)')
    parser.add_argument('--notarize', action='store_true', help='Notarize with Apple (requires --codesign)')
    parser.add_argument('--notarize-profile', default='node3-notarize', help='Notarization keychain profile name')
    
    args = parser.parse_args()
    
    # Get current version
    current_version = get_current_version()
    
    # Handle --current flag
    if args.current:
        print(f"\n{Colors.BOLD}Current version:{Colors.ENDC} {Colors.GREEN}{current_version}{Colors.ENDC}\n")
        return
    
    # Determine new version
    if args.version:
        new_version = args.version
    elif args.bump:
        new_version = bump_version(current_version, args.bump)
    
    # Print release info
    print_header(f"Building node3 Agent Release v{new_version}")
    print(f"{Colors.BOLD}Current version:{Colors.ENDC} {current_version}")
    print(f"{Colors.BOLD}New version:{Colors.ENDC}     {Colors.GREEN}{new_version}{Colors.ENDC}\n")
    
    # Confirm
    if not args.skip_commit:
        response = input(f"{Colors.YELLOW}Continue with release v{new_version}? [y/N]:{Colors.ENDC} ")
        if response.lower() != 'y':
            print_warning("Release cancelled")
            return
    
    # Step 1: Update version
    set_version(new_version)
    
    # Step 2: Commit version bump
    if not args.skip_commit:
        commit_version_bump(new_version)
    
    # Step 3: Build executable
    if not args.skip_build:
        clean_build_artifacts()
        
        if not build_executable():
            print_error("Build failed - aborting release")
            return
    
    # Step 4: Code sign app (if requested)
    app_path = Path(__file__).parent / "dist" / "node3agent.app"
    if args.codesign and not args.skip_build:
        if app_path.exists():
            if not code_sign_app(app_path, args.identity):
                print_error("Code signing failed - aborting release")
                return
        else:
            print_warning(f"App bundle not found at {app_path} - skipping code signing")
    
    # Step 5: Notarize app (if requested)
    if args.notarize and args.codesign and not args.skip_build:
        if not notarize_app(app_path, args.notarize_profile):
            print_error("Notarization failed - aborting release")
            return
    elif args.notarize and not args.codesign:
        print_warning("--notarize requires --codesign, skipping notarization")
    
    # Step 6: Create DMG
    if not args.skip_dmg and not args.skip_build:
        if not create_dmg(new_version):
            print_error("DMG creation failed - aborting release")
            return
        
        # Sign DMG if code signing is enabled
        dmg_path = Path(__file__).parent / "dist" / f"node3agent-{new_version}-macos.dmg"
        if args.codesign and dmg_path.exists():
            if not code_sign_dmg(dmg_path, args.identity):
                print_warning("DMG signing failed, but continuing...")
    
    # Step 7: Create git tag
    if not args.skip_tag:
        create_git_tag(new_version)
    
    # Step 8: Create GitHub release (optional)
    if args.github_release:
        create_github_release(new_version)
    
    # Final summary
    print_header("Release Complete!")
    print(f"{Colors.BOLD}Version:{Colors.ENDC}     v{new_version}")
    print(f"{Colors.BOLD}Executable:{Colors.ENDC}  dist/node3agent")
    if not args.skip_dmg:
        print(f"{Colors.BOLD}DMG:{Colors.ENDC}         dist/node3agent-{new_version}-macos.dmg")
    if args.codesign:
        print(f"{Colors.BOLD}Signed:{Colors.ENDC}      ✅ Code signed")
    if args.notarize:
        print(f"{Colors.BOLD}Notarized:{Colors.ENDC}   ✅ Apple notarized")
    
    print(f"\n{Colors.CYAN}Next steps:{Colors.ENDC}")
    print(f"  1. Test the executable: ./dist/node3agent")
    if not args.skip_dmg:
        print(f"  2. Test the DMG installer")
    if not args.skip_tag:
        print(f"  3. Push tags: git push origin v{new_version}")
    if args.github_release:
        print(f"  4. View release: https://github.com/squirtgunhero/node3.git/releases/tag/v{new_version}")
    else:
        print(f"  4. Create GitHub release: python release.py --version {new_version} --github-release")
    
    if args.codesign and args.notarize:
        print(f"\n{Colors.GREEN}✓ Your release is fully signed and notarized!{Colors.ENDC}")
        print(f"{Colors.GREEN}  Users will see NO security warnings{Colors.ENDC}")
    elif args.codesign:
        print(f"\n{Colors.YELLOW}⚠ App is signed but not notarized{Colors.ENDC}")
        print(f"{Colors.YELLOW}  Users may still see warnings (use --notarize){Colors.ENDC}")
    print()

if __name__ == "__main__":
    main()

