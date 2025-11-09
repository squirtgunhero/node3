# PyInstaller hook to SKIP torch entirely
# This prevents PyInstaller from trying to analyze torch and its dependencies

# Tell PyInstaller to exclude torch and all its submodules
excludedimports = [
    'torch',
    'torch.utils',
    'torch.utils.tensorboard',
    'tensorboard',
    'numpy',  # Often imported by torch
]

# Return empty lists - nothing to import
hiddenimports = []
datas = []
binaries = []

