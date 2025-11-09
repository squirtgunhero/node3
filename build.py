# build.py
"""
Build script for creating distributable packages
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_executable():
    """Build executable using PyInstaller"""
    print("Building executable with PyInstaller...")
    
    # Clean up old build artifacts
    dist_dir = Path('dist')
    build_dir = Path('build')
    spec_file = Path('node3-agent.spec')
    
    if dist_dir.exists():
        print("  Cleaning old dist directory...")
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        print("  Cleaning old build directory...")
        shutil.rmtree(build_dir)
    
    # PyInstaller command - optimized for size
    cmd = [
        'pyinstaller',
        '--name=node3-agent',
        '--onefile',
        '--console',  # Show console for logging (change to --windowed for release)
        '--add-data=templates:templates',
        # Essential hidden imports only
        '--hidden-import=uvicorn',
        '--hidden-import=fastapi',
        '--hidden-import=jinja2',
        '--hidden-import=pynvml',
        '--hidden-import=solana',
        '--hidden-import=solders',
        '--hidden-import=native_executor',
        '--hidden-import=psutil',
        # Exclude unnecessary modules to reduce size
        '--exclude-module=torch',
        '--exclude-module=tensorflow',
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',  # Only include if needed
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        '--exclude-module=notebook',
        '--exclude-module=tkinter',  # GUI not needed
        '--exclude-module=PyQt5',
        '--exclude-module=PyQt6',
        '--exclude-module=PySide2',
        '--exclude-module=PySide6',
        '--exclude-module=pytest',
        '--exclude-module=tensorboard',
        # Optimize collections - only collect what's needed
        '--collect-all=fastapi',
        '--collect-all=uvicorn',
        '--collect-submodules=fastapi',
        '--collect-submodules=uvicorn',
        '--clean',  # Clean PyInstaller cache
        '--noconfirm',  # Replace output directory without asking
        '--strip',  # Strip debug symbols (reduces size)
        '--noupx',  # Disable UPX compression (can cause issues, but smaller)
        'main.py'
    ]
    
    # Platform-specific adjustments
    if sys.platform == 'linux':
        # Linux already uses --console
        pass
    elif sys.platform == 'darwin':
        # macOS: use console for development, windowed for release
        # Change '--console' to '--windowed' for release builds
        pass
    
    subprocess.run(cmd, check=True)
    
    # Get executable size
    exe_path = Path(f"dist/node3-agent{'.exe' if sys.platform == 'win32' else ''}")
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / 1024 / 1024
        print("✓ Executable built successfully!")
        print(f"  Location: {exe_path}")
        print(f"  Size: {size_mb:.1f} MB")
        
        # Show optimization tips if size is large
        if size_mb > 100:
            print(f"  ⚠️  Size is large ({size_mb:.1f} MB). Consider:")
            print("     - Using --exclude-module for unused libraries")
            print("     - Using UPX compression (--upx-dir)")
            print("     - Splitting into separate modules")
    else:
        print("⚠️  Executable not found - check build output for errors")

def build_docker_image():
    """Build Docker image"""
    print("Building Docker image...")
    subprocess.run(['docker', 'build', '-t', 'node3-agent:latest', '.'], check=True)
    print("✓ Docker image built successfully!")

def create_app_bundle():
    """Create macOS .app bundle with Lima bundled"""
    print("Creating macOS .app bundle...")
    
    app_path = Path('dist/node3-agent.app')
    app_path.mkdir(parents=True, exist_ok=True)
    
    # Create Contents structure
    contents = app_path / 'Contents'
    macos = contents / 'MacOS'
    resources = contents / 'Resources'
    
    macos.mkdir(parents=True, exist_ok=True)
    resources.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    exe_source = Path('dist/node3-agent')
    if exe_source.exists():
        shutil.copy(exe_source, macos / 'node3-agent')
        os.chmod(macos / 'node3-agent', 0o755)
        print("  ✓ Executable copied")
    else:
        print("  ⚠️  Executable not found - run build_executable() first")
        return False
    
    # Copy Lima binaries (lima wrapper + limactl)
    lima_source_dir = Path('lima/bin')
    if lima_source_dir.exists():
        lima_dest = resources / 'lima' / 'bin'
        lima_dest.mkdir(parents=True, exist_ok=True)
        
        # Copy all Lima binaries
        copied_files = []
        for binary in lima_source_dir.glob('*'):
            if binary.is_file():
                shutil.copy(binary, lima_dest / binary.name)
                os.chmod(lima_dest / binary.name, 0o755)
                copied_files.append(binary.name)
        
        print(f"  ✓ Lima binaries bundled ({len(copied_files)} files: {', '.join(copied_files[:3])}{'...' if len(copied_files) > 3 else ''})")
    else:
        print("  ⚠️  Lima binaries not found at lima/bin/")
        print("     Download from: https://github.com/lima-vm/lima/releases")
    
    # Copy templates
    if Path('templates').exists():
        shutil.copytree('templates', resources / 'templates', dirs_exist_ok=True)
        print("  ✓ Templates copied")
    
    # Read version from main.py or use default
    version = "1.0.0"
    try:
        import re
        main_py = Path('main.py').read_text()
        version_match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', main_py)
        if version_match:
            version = version_match.group(1)
    except:
        pass
    
    # Create Info.plist with version info
    info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>node3-agent</string>
    <key>CFBundleIdentifier</key>
    <string>com.node3.agent</string>
    <key>CFBundleName</key>
    <string>node³ Agent</string>
    <key>CFBundleVersion</key>
    <string>{version}</string>
    <key>CFBundleShortVersionString</key>
    <string>{version}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.utilities</string>
</dict>
</plist>"""
    
    (contents / 'Info.plist').write_text(info_plist)
    print("  ✓ Info.plist created")
    
    print(f"✓ .app bundle created: {app_path}")
    return True

def create_installer_macos():
    """Create macOS installer (.dmg) with Lima bundled"""
    if sys.platform != 'darwin':
        print("macOS installer can only be created on macOS")
        return
    
    print("Creating macOS installer...")
    
    # Clean up old .app bundle if exists
    app_path = Path('dist/node3-agent.app')
    if app_path.exists():
        print("  Removing old .app bundle...")
        shutil.rmtree(app_path)
    
    # Create .app bundle first
    if not create_app_bundle():
        print("Failed to create .app bundle")
        return
    
    # Create DMG using hdiutil
    dmg_name = 'node3-agent-installer.dmg'
    dmg_source = Path('dist')
    
    # Clean up old DMG if exists
    if Path(dmg_name).exists():
        print(f"  Removing old DMG: {dmg_name}")
        Path(dmg_name).unlink()
    
    print("Creating DMG...")
    subprocess.run([
        'hdiutil', 'create',
        '-volname', 'node³ Agent',
        '-srcfolder', str(dmg_source / 'node3-agent.app'),
        '-ov',
        '-format', 'UDZO',
        dmg_name
    ], check=True)
    
    print(f"✓ macOS installer created: {dmg_name}")
    print(f"  Size: {Path(dmg_name).stat().st_size / 1024 / 1024:.1f} MB")

def create_windows_installer():
    """Create Windows installer (.exe)"""
    if sys.platform != 'win32':
        print("Windows installer can only be created on Windows")
        return
    
    print("Creating Windows installer...")
    # Would use Inno Setup or NSIS here
    print("Note: Installer creation requires Inno Setup or NSIS")

def create_deb_package():
    """Create Debian package (.deb)"""
    if sys.platform != 'linux':
        print("Debian package can only be created on Linux")
        return
    
    print("Creating Debian package...")
    # Create package structure
    pkg_dir = Path('dist/deb')
    pkg_dir.mkdir(parents=True, exist_ok=True)
    
    # Create DEBIAN control file
    control_dir = pkg_dir / 'DEBIAN'
    control_dir.mkdir(exist_ok=True)
    
    control_content = """Package: node3-agent
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Depends: python3, docker.io
Maintainer: node3 Team <support@node3.com>
Description: node3 Agent - Monetize your GPU compute capacity
"""
    
    (control_dir / 'control').write_text(control_content)
    
    # Copy files
    usr_bin = pkg_dir / 'usr' / 'bin'
    usr_bin.mkdir(parents=True, exist_ok=True)
    shutil.copy('dist/node3-agent', usr_bin / 'node3-agent')
    
    # Build package
    subprocess.run(['dpkg-deb', '--build', str(pkg_dir), 'dist/node3-agent.deb'], check=True)
    print("✓ Debian package created: dist/node3-agent.deb")

def create_pip_package():
    """Create pip-installable package"""
    print("Creating pip package...")
    
    # Ensure setup.py exists
    if not Path('setup.py').exists():
        print("Creating setup.py...")
        create_setup_py()
    
    # Build package
    subprocess.run([sys.executable, 'setup.py', 'sdist', 'bdist_wheel'], check=True)
    print("✓ Pip package created in dist/")

def create_setup_py():
    """Create setup.py for pip package"""
    setup_content = '''from setuptools import setup, find_packages

setup(
    name="node3-agent",
    version="1.0.0",
    description="node3 Agent - Monetize your GPU compute capacity",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="node3 Team",
    author_email="support@node3.com",
    url="https://github.com/node3/agent",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["templates/*.html"],
    },
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
    entry_points={
        "console_scripts": [
            "node3-agent=main:main_entry",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
'''
    Path('setup.py').write_text(setup_content)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Build node3 agent distributions')
    parser.add_argument('--type', choices=['exe', 'docker', 'macos', 'windows', 'deb', 'pip', 'all'],
                       default='exe', help='Type of distribution to build')
    
    args = parser.parse_args()
    
    # Create dist directory
    Path('dist').mkdir(exist_ok=True)
    
    if args.type == 'exe' or args.type == 'all':
        build_executable()
    
    if args.type == 'docker' or args.type == 'all':
        build_docker_image()
    
    if args.type == 'macos' or args.type == 'all':
        if sys.platform == 'darwin':
            build_executable()
            create_installer_macos()
    
    if args.type == 'windows' or args.type == 'all':
        if sys.platform == 'win32':
            build_executable()
            create_windows_installer()
    
    if args.type == 'deb' or args.type == 'all':
        if sys.platform == 'linux':
            build_executable()
            create_deb_package()
    
    if args.type == 'pip' or args.type == 'all':
        create_pip_package()

