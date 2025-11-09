# Windows Icon Fix

## Issue
The Windows build was failing with:
```
FileNotFoundError: D:\a\node3\node3\icon.ico not found
```

PyInstaller tried to use `icon.ico` for the Windows executable, but the file didn't exist in the repository.

## Solution
Made the icon optional in `build_windows.py`:

### 1. **Conditional Icon Check**
```python
# Add icon if available (optional)
icon_path = Path('icon.ico')
if icon_path.exists():
    cmd.append('--icon=icon.ico')
    print("✓ Using icon: icon.ico")
else:
    print("ℹ️  No icon.ico found - building without icon")
```

### 2. **Updated NSIS Installer Script**
```python
# Check if icon exists before adding to NSIS script
icon_line = '!define MUI_ICON "icon.ico"' if Path('icon.ico').exists() else '; No icon specified'
```

## Result
- ✅ Windows build now succeeds without icon.ico
- ✅ If icon.ico is added later, it will be automatically included
- ✅ Clear informational message when icon is not found
- ✅ NSIS installer also handles missing icon gracefully

## Future Enhancement
To add a custom icon:
1. Create or obtain a `.ico` file (256x256 or smaller)
2. Place it in the project root as `icon.ico`
3. The build script will automatically detect and use it

## Commits
- `df2f348` - Fix Windows build: Make icon.ico optional

