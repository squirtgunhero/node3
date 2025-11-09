# PyInstaller hook to SKIP torch entirely
# This stub hook overrides PyInstaller's built-in torch hooks
# Actual exclusion is handled by --exclude-module flags in build scripts

# Return empty lists - no imports, data, or binaries for torch
hiddenimports = []
datas = []
binaries = []

