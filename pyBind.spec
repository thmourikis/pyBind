# -*- mode: python -*-

block_cipher = None


a = Analysis(['pyBind.py'],
             pathex=['/Users/athanasiosmourikis/pyBind'],
             binaries=[],
             datas=[('/Users/athanasiosmourikis/pyBind/data/*', 'data')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='pyBind',
          debug=False,
          strip=False,
          upx=True,
          console=False )
app = BUNDLE(exe,
             name='pyBind.app',
             icon=None,
             bundle_identifier='pyBind')
