# PyInstaller hook to SKIP torch entirely
# This prevents PyInstaller from trying to analyze torch and its dependencies

# Return empty lists to skip torch completely
hiddenimports = []
datas = []
binaries = []

