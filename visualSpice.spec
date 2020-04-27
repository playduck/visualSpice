# -*- mode: python -*-

from pathlib import Path
import os
import sys
import importlib

# add qtmodern qss files
package_imports = [["qtmodern", ["resources/frameless.qss", "resources/style.qss"]]]
added_files = []
for package, files in package_imports:
    proot = Path(importlib.import_module(package).__file__).parent
    added_files.extend((proot / f, package) for f in files)

# add asset_dir
asset_dirs = ["assets", "ui"]
for asset_dir in asset_dirs:
    asset_files = [f for f in os.listdir(asset_dir) if os.path.isfile(os.path.join(asset_dir, f))]
    for asset in asset_files:
        added_files.extend([(
            Path(os.path.abspath(os.path.join(asset_dir, asset) )),
            asset_dir
        )])

block_cipher = None

a = Analysis(["visualSpice.py"],
            pathex=["/Users/robin/PycharmProjects/visualSpice"],
            binaries=[],
            datas=added_files,
            hiddenimports=[],
            hookspath=[],
            runtime_hooks=[],
            excludes=[],
            win_no_prefer_redirects=False,
            win_private_assemblies=False,
            cipher=block_cipher,
            noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
            cipher=block_cipher)

exe = {}
if sys.platform == "darwin":
    exe = EXE(pyz,
            a.scripts,
            a.binaries,
            a.zipfiles,
            a.datas,
            name="visualSpice",
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            runtime_tmpdir=None,
            console=False
            # icon=os.path.abspath(os.path.join(asset_dir, "icon-512.icns"))
    )
elif sys.platform == "win32" or sys.platform == "win64" or sys.platform == "linux":
    exe = EXE(pyz,
            a.scripts,
            a.binaries,
            a.zipfiles,
            a.datas,
            name="visualSpice",
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            runtime_tmpdir=None,
            console=False
            # icon=os.path.abspath(os.path.join(asset_dir, "icon-512.ico"))
)

if sys.platform == "darwin":
    app = BUNDLE(exe,
                    name="visualSpice.app",
                    info_plist={
                        "NSHighResolutionCapable": "True",
                        "LSBackgroundOnly": "False",
                        "NSRequiresAquaSystemAppearance": "True"
                        # should be false to support dark mode
                        # known bug: https://github.com/pyinstaller/pyinstaller/issues/4615 with pyinstaller
                        # need to recompile pyinstaller with SDK >= 10.13
                    }
                    # icon=os.path.abspath(os.path.join(asset_dir, "icon-512.icns"))
                    )
