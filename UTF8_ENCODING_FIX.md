# UTF-8 Encoding Fix for Windows

## Issue
Windows build was failing with:
```
UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-1: 
character maps to <undefined>
```

The build scripts use Unicode characters (✓, ℹ️, ❌, ⚠️) for better output formatting, but Windows CI runners default to `cp1252` encoding which can't display these characters.

## Root Cause
- Windows console defaults to `cp1252` encoding (not UTF-8)
- Unicode emoji/symbols used in print statements aren't in cp1252 character set
- Python tries to encode output using system default → fails

## Solution Applied

### 1. **Workflow Level - PYTHONIOENCODING** ✅
Added environment variable to Windows build job:

```yaml
build-windows:
  name: Build Windows Installer
  runs-on: windows-latest
  
  env:
    PYTHONIOENCODING: utf-8  # ← Force UTF-8 for Python I/O
```

### 2. **Script Level - sys.stdout.reconfigure** ✅
Added to all build scripts (build.py, build_linux.py, build_windows.py):

```python
# Ensure UTF-8 encoding for console output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass  # Not needed or not supported on this platform
```

For Windows-specific script (build_windows.py), added fallback for Python < 3.7:
```python
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7 fallback
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
```

### 3. **File Writing - Explicit UTF-8** ✅
Ensured NSIS script file is written with UTF-8:

```python
with open('node3-setup.nsi', 'w', encoding='utf-8') as f:
    f.write(script)
```

## Unicode Characters Used
- ✓ (U+2713) - Check mark - for success messages
- ❌ (U+274C) - Cross mark - for error messages
- ℹ️ (U+2139) - Information - for info messages
- ⚠️ (U+26A0) - Warning sign - for warning messages

## Defense in Depth Strategy

We implemented **multiple layers** of protection:

1. **Environment variable** - Most reliable, set before Python starts
2. **Script-level reconfiguration** - Catches cases where env var doesn't work
3. **Explicit file encoding** - Ensures file operations use UTF-8
4. **Graceful fallback** - Try-except blocks prevent crashes on older Python

## Benefits

- ✅ Works on all Python versions (3.6+)
- ✅ Works on all platforms (Windows, macOS, Linux)
- ✅ Preserves nice Unicode output where supported
- ✅ Fails gracefully if encoding can't be changed
- ✅ No more UnicodeEncodeError on Windows CI

## Testing

### Before Fix:
```
Error: UnicodeEncodeError: 'charmap' codec can't encode '✓'
Build failed at line 47
```

### After Fix:
```
✓ Executable built successfully!
✓ Size: 45.2 MB
ℹ️ No icon.ico found - building without icon
```

## Alternative Considered (Not Chosen)

**Replace Unicode with ASCII:**
```python
# Could have done this instead:
print("[OK] Executable built successfully!")
print("[INFO] No icon.ico found - building without icon")
print("[ERROR] Build failed!")
```

**Why we kept Unicode:**
- Better visual appearance
- Modern terminals support UTF-8
- Our fix handles it properly across all platforms

## Files Modified
- ✅ `.github/workflows/build-all-platforms.yml` - Added PYTHONIOENCODING
- ✅ `build_windows.py` - Added UTF-8 reconfiguration + fallback
- ✅ `build_linux.py` - Added UTF-8 reconfiguration
- ✅ `build.py` - Added UTF-8 reconfiguration

## Commits
- `f276d66` - Fix Windows UTF-8 encoding for Unicode characters

