#!/usr/bin/env python3
"""
Linux Build Script for node3 Agent
===================================

Creates a Linux AppImage for universal distribution.

Requirements:
- PyInstaller: pip install pyinstaller
- AppImage tools (optional)

Usage:
    python build_linux.py
    python build_linux.py --deb      # Create .deb package
    python build_linux.py --rpm      # Create .rpm package
    python build_linux.py --appimage # Create AppImage
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")

def get_version():
    """Extract version from main.py"""
    try:
        with open('main.py', 'r') as f:
            content = f.read()
            import re
            match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
            return match.group(1) if match else '1.0.0'
    except:
        return '1.0.0'

def clean_build():
    """Remove previous build artifacts"""
    print_step("Cleaning previous builds")
    
    dirs_to_remove = ['build', 'dist', 'node3-agent.AppDir']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Removed {dir_name}/")
    
    # Remove spec and package files
    for pattern in ['*.spec', '*.deb', '*.rpm', '*.AppImage']:
        for file in Path('.').glob(pattern):
            file.unlink()
            print(f"✓ Removed {file}")

def build_executable():
    """Build Linux executable with PyInstaller"""
    print_step("Building Linux executable")
    
    # Check PyInstaller
    try:
        subprocess.run(['pyinstaller', '--version'], 
                      capture_output=True, check=True)
    except:
        print("❌ PyInstaller not found!")
        print("Install with: pip install pyinstaller")
        return False
    
    # Build command
    cmd = [
        'pyinstaller',
        '--name=node3-agent',
        '--onefile',
        '--add-data=templates:templates',
        
        # Hidden imports
        '--hidden-import=uvicorn.logging',
        '--hidden-import=uvicorn.loops',
        '--hidden-import=uvicorn.loops.auto',
        '--hidden-import=uvicorn.protocols',
        '--hidden-import=uvicorn.protocols.http',
        '--hidden-import=uvicorn.protocols.http.auto',
        '--hidden-import=uvicorn.protocols.websockets',
        '--hidden-import=uvicorn.protocols.websockets.auto',
        '--hidden-import=uvicorn.lifespan',
        '--hidden-import=uvicorn.lifespan.on',
        '--collect-all=fastapi',
        '--collect-all=pydantic',
        
        # Exclude unused modules
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        '--exclude-module=notebook',
        '--exclude-module=tkinter',
        '--exclude-module=PyQt5',
        '--exclude-module=PyQt6',
        '--exclude-module=PySide2',
        '--exclude-module=PySide6',
        
        '--strip',
        '--clean',
        'main.py'
    ]
    
    print("Building with PyInstaller...")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✓ Executable built successfully!")
        
        # Get file size
        exe_path = Path('dist') / 'node3-agent'
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"✓ Size: {size_mb:.1f} MB")
            print(f"✓ Location: {exe_path}")
            
            # Make executable
            exe_path.chmod(0o755)
        return True
    else:
        print("\n❌ Build failed!")
        return False

def create_desktop_file(version):
    """Create .desktop file for Linux"""
    desktop_content = f'''[Desktop Entry]
Version={version}
Type=Application
Name=node3 Agent
Comment=Decentralized compute agent - Earn SOL for GPU/CPU tasks
Exec=node3-agent
Icon=node3-agent
Terminal=false
Categories=Utility;Network;
Keywords=blockchain;solana;compute;earnings;
'''
    
    with open('node3-agent.desktop', 'w') as f:
        f.write(desktop_content)
    
    print("✓ Created desktop file: node3-agent.desktop")

def create_appimage(version):
    """Create AppImage package"""
    print_step("Creating AppImage")
    
    # Create AppDir structure
    appdir = Path('node3-agent.AppDir')
    appdir.mkdir(exist_ok=True)
    
    usr_bin = appdir / 'usr' / 'bin'
    usr_share = appdir / 'usr' / 'share' / 'applications'
    usr_bin.mkdir(parents=True, exist_ok=True)
    usr_share.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    shutil.copy('dist/node3-agent', usr_bin / 'node3-agent')
    
    # Create desktop file
    create_desktop_file(version)
    shutil.copy('node3-agent.desktop', usr_share / 'node3-agent.desktop')
    shutil.copy('node3-agent.desktop', appdir / 'node3-agent.desktop')
    
    # Create AppRun script
    apprun = appdir / 'AppRun'
    apprun.write_text('''#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/usr/bin/node3-agent" "$@"
''')
    apprun.chmod(0o755)
    
    # Check for appimagetool
    try:
        subprocess.run(['appimagetool', '--version'], 
                      capture_output=True, check=True)
        
        # Build AppImage
        print("Building AppImage...")
        appimage_name = f'node3-agent-{version}-x86_64.AppImage'
        result = subprocess.run([
            'appimagetool',
            str(appdir),
            appimage_name
        ])
        
        if result.returncode == 0:
            if Path(appimage_name).exists():
                size_mb = Path(appimage_name).stat().st_size / (1024 * 1024)
                print(f"\n✓ AppImage created: {appimage_name}")
                print(f"✓ Size: {size_mb:.1f} MB")
                return True
        
    except:
        print("⚠️  appimagetool not found - skipping AppImage")
        print("   Install from: https://appimage.github.io/")
        print("   Or distribute: dist/node3-agent (standalone)")
        return False
    
    return False

def create_deb_package(version):
    """Create .deb package"""
    print_step("Creating .deb package")
    
    # Create package structure
    pkg_dir = Path(f'node3-agent_{version}_amd64')
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    
    (pkg_dir / 'DEBIAN').mkdir(parents=True)
    (pkg_dir / 'usr' / 'bin').mkdir(parents=True)
    (pkg_dir / 'usr' / 'share' / 'applications').mkdir(parents=True)
    
    # Copy files
    shutil.copy('dist/node3-agent', pkg_dir / 'usr' / 'bin' / 'node3-agent')
    create_desktop_file(version)
    shutil.copy('node3-agent.desktop', 
                pkg_dir / 'usr' / 'share' / 'applications' / 'node3-agent.desktop')
    
    # Create control file
    control = f'''Package: node3-agent
Version: {version}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: node3 <support@node3.com>
Description: Decentralized compute agent
 Earn SOL for completing GPU/CPU compute tasks.
 Connects to the node3 marketplace and executes jobs.
'''
    
    (pkg_dir / 'DEBIAN' / 'control').write_text(control)
    
    # Build package
    try:
        subprocess.run(['dpkg-deb', '--version'], 
                      capture_output=True, check=True)
        
        print("Building .deb package...")
        deb_name = f'node3-agent_{version}_amd64.deb'
        result = subprocess.run([
            'dpkg-deb',
            '--build',
            str(pkg_dir)
        ])
        
        if result.returncode == 0:
            if Path(deb_name).exists():
                size_mb = Path(deb_name).stat().st_size / (1024 * 1024)
                print(f"\n✓ .deb package created: {deb_name}")
                print(f"✓ Size: {size_mb:.1f} MB")
                return True
        
    except:
        print("⚠️  dpkg-deb not found - skipping .deb creation")
        return False
    
    return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Build node3 Agent for Linux')
    parser.add_argument('--deb', action='store_true',
                       help='Create .deb package')
    parser.add_argument('--rpm', action='store_true',
                       help='Create .rpm package')
    parser.add_argument('--appimage', action='store_true',
                       help='Create AppImage')
    args = parser.parse_args()
    
    version = get_version()
    
    print(f'''
{'='*60}
    Building node3 Agent for Linux v{version}
{'='*60}
''')
    
    # Step 1: Clean
    clean_build()
    
    # Step 2: Build executable
    if not build_executable():
        print("\n❌ Build failed!")
        sys.exit(1)
    
    # Step 3: Create packages
    if args.appimage:
        create_appimage(version)
    
    if args.deb:
        create_deb_package(version)
    
    if args.rpm:
        print("⚠️  RPM packaging not yet implemented")
        print("   Use: alien to convert .deb to .rpm")
    
    # If no package specified, try AppImage by default
    if not (args.appimage or args.deb or args.rpm):
        create_appimage(version)
    
    # Summary
    print_step("Build Complete!")
    print(f"Version: {version}")
    print(f"Executable: dist/node3-agent")
    print("\nTest the build:")
    print("  ./dist/node3-agent")
    print("\nDistribute:")
    print("  Standalone: dist/node3-agent")
    
    for pattern in ['*.AppImage', '*.deb', '*.rpm']:
        for file in Path('.').glob(pattern):
            print(f"  Package: {file}")

if __name__ == '__main__':
    main()

