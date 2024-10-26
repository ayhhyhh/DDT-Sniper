# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
                 ('ddtcv/static/model/angle_1_rec_en_number_lite/angle_1_rec_en_number_lite.onnx', 'ddtcv/static/model/angle_1_rec_en_number_lite'),
                 ('ddtcv/static/model/angle_1_rec_en_number_lite/angle_dict.txt', 'ddtcv/static/model/angle_1_rec_en_number_lite'),
                 ('ddtcv/static/model/wind_1_rec_en_number_lite/wind_1_rec_en_number_lite.onnx', 'ddtcv/static/model/wind_1_rec_en_number_lite'),
                 ('ddtcv/static/model/wind_1_rec_en_number_lite/wind_dict.txt', 'ddtcv/static/model/wind_1_rec_en_number_lite')
             ],
    hiddenimports=['onnxruntime', 'onnxruntime.capi._pybind_state'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='sniper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
