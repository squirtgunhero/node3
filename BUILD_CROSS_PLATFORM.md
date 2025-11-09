# Cross-Platform Build Guide

node3 Agent runs on **Windows, macOS, and Linux**. This guide covers building installers for all platforms.

## 🎯 Quick Start

### Auto-Detect Platform
```bash
python build.py --type all
```

This detects your OS and builds the appropriate installer.

### Platform-Specific

**macOS:**
```bash
python build.py --type macos
# Creates: node3-agent-1.0.0-macos.dmg
```

**Windows:**
```bash
python build_windows.py
# Creates: node3-agent-1.0.0-windows-setup.exe
```

**Linux:**
```bash
python build_linux.py --appimage
# Creates: node3-agent-1.0.0-x86_64.AppImage
```

---

## 📦 Platform Support Matrix

| Platform | GPU Support | Build Output | Installer |
|----------|-------------|--------------|-----------|
| **macOS** | Apple M1/M2/M3, Intel | `.app` bundle | `.dmg` |
| **Windows** | NVIDIA, AMD, Intel | `.exe` | NSIS Setup |
| **Linux** | NVIDIA, AMD, Intel | Binary | AppImage/.deb |

---

## 🖥️ Windows Build

### Requirements
- Python 3.9+
- PyInstaller: `pip install pyinstaller`
- NSIS (optional): https://nsis.sourceforge.io/

### Build Steps

**1. Executable Only:**
```bash
python build_windows.py --no-installer
```
Output: `dist/node3-agent.exe` (portable)

**2. With Installer:**
```bash
python build_windows.py
```
Output: `node3-agent-1.0.0-windows-setup.exe`

### Installer Features
- ✅ Start Menu shortcuts
- ✅ Desktop shortcut
- ✅ Add/Remove Programs entry
- ✅ Uninstaller
- ✅ No admin rights needed (installs to user folder)

### GPU Detection on Windows
- **NVIDIA:** CUDA support via pynvml
- **AMD:** ROCm detection via WMI
- **Intel:** Integrated GPU detection

### Distribution
- Upload `.exe` installer to GitHub Releases
- Users download and run
- No Python required

---

## 🐧 Linux Build

### Requirements
- Python 3.9+
- PyInstaller: `pip install pyinstaller`
- appimagetool (optional): https://appimage.github.io/

### Build Steps

**1. AppImage (Universal):**
```bash
python build_linux.py --appimage
```
Output: `node3-agent-1.0.0-x86_64.AppImage`

**2. Debian Package:**
```bash
python build_linux.py --deb
```
Output: `node3-agent_1.0.0_amd64.deb`

**3. Standalone Executable:**
```bash
python build_linux.py
```
Output: `dist/node3-agent`

### Package Features

**AppImage:**
- ✅ Runs on all distributions
- ✅ No installation needed
- ✅ Portable
- ✅ Self-contained

**.deb Package:**
- ✅ Ubuntu/Debian compatible
- ✅ Installs to `/usr/bin`
- ✅ Desktop integration
- ✅ `apt` managed

### GPU Detection on Linux
- **NVIDIA:** CUDA via nvidia-smi
- **AMD:** ROCm via rocm-smi
- **Intel:** OpenCL detection

### Distribution
- **AppImage:** Upload to GitHub Releases
- **.deb:** Host on PPA or direct download
- **Flatpak/Snap:** Coming soon

---

## 🍎 macOS Build

### Requirements
- macOS 10.15+
- Python 3.9+
- PyInstaller: `pip install pyinstaller`
- Xcode Command Line Tools

### Build Steps

**1. DMG Installer:**
```bash
python build.py --type macos
```
Output: `node3-agent-1.0.0-macos.dmg`

**2. With Code Signing:**
```bash
./setup_codesign.sh
source load_env.sh
python release.py --bump patch --codesign --notarize
```

### GPU Detection on macOS
- **Apple Silicon:** Metal via system_profiler
- **Intel Macs:** Intel Iris via ioreg

### Distribution
- Upload `.dmg` to GitHub Releases
- Users drag to Applications
- Optional: Distribute via Homebrew Cask

---

## 🔄 Automated Multi-Platform Build

### Using GitHub Actions

Create `.github/workflows/build.yml`:

```yaml
name: Build All Platforms

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt pyinstaller
      - run: python build_windows.py
      - uses: actions/upload-artifact@v3
        with:
          name: windows-installer
          path: '*.exe'

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt pyinstaller
      - run: python build_linux.py --appimage --deb
      - uses: actions/upload-artifact@v3
        with:
          name: linux-packages
          path: |
            *.AppImage
            *.deb

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt pyinstaller
      - run: python build.py --type macos
      - uses: actions/upload-artifact@v3
        with:
          name: macos-installer
          path: '*.dmg'
```

### Manual Cross-Compilation

**From macOS:**
- Can build: macOS only
- Cross-compile: Not supported

**From Windows:**
- Can build: Windows only
- Cross-compile: Not supported

**From Linux:**
- Can build: Linux only
- Cross-compile: Windows (with Wine)

**Recommendation:** Use GitHub Actions for multi-platform builds

---

## 📊 Build Sizes

| Platform | Executable | Installer | Notes |
|----------|------------|-----------|-------|
| macOS | ~80MB | ~85MB DMG | Optimized |
| Windows | ~75MB | ~78MB Setup | With compression |
| Linux | ~70MB | ~73MB AppImage | Stripped |

### Size Optimization

All builds exclude:
- matplotlib
- numpy/pandas
- scipy
- Jupyter
- Qt frameworks

To reduce further:
- Use `--upx` (UPX compression)
- Split into modules
- On-demand imports

---

## 🧪 Testing Builds

### Windows
```cmd
dist\node3-agent.exe
# Should start dashboard at http://localhost:8080
```

### Linux
```bash
chmod +x node3-agent-1.0.0-x86_64.AppImage
./node3-agent-1.0.0-x86_64.AppImage
```

### macOS
```bash
open dist/node3-agent.app
# Or install DMG and test
```

### Automated Testing
```bash
# Run on CI
python test_executable.sh
```

---

## 🚀 Distribution Checklist

Before releasing:

- [ ] Build on native platform (or use CI)
- [ ] Test executable starts
- [ ] Test GPU detection works
- [ ] Test wallet creation
- [ ] Test job execution
- [ ] Sign (Windows/macOS) or verify integrity
- [ ] Upload to GitHub Releases
- [ ] Update README with download links
- [ ] Create release notes

---

## 🐛 Troubleshooting

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### "NSIS not found" (Windows)
Download from: https://nsis.sourceforge.io/
Or build without installer: `--no-installer`

### "appimagetool not found" (Linux)
Download from: https://appimage.github.io/
Or distribute standalone: `dist/node3-agent`

### "Build is too large"
- Add more `--exclude-module` flags
- Use UPX compression
- Check for duplicate dependencies

### GPU not detected
- Install GPU drivers
- Check `nvidia-smi` / `rocm-smi` / `system_profiler`
- Run with `SKIP_GPU_CHECK=true` for testing

---

## 📚 Resources

- **PyInstaller Docs:** https://pyinstaller.org/
- **NSIS:** https://nsis.sourceforge.io/
- **AppImage:** https://appimage.github.io/
- **GitHub Actions:** https://github.com/features/actions

---

**Questions?** Check the main README or open an issue on GitHub.

