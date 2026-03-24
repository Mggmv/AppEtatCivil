# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[('mon_projet', 'mon_projet'), ('registre', 'registre'), ('templates', 'templates'), ('db.sqlite3', '.')],
    hiddenimports=['mon_projet.settings', 'mon_projet.urls', 'django.template.defaulttags', 'django.template.loader_tags', 'django.templatetags.tz', 'django.templatetags.static', 'html.parser', 'math', 'django.contrib.messages.middleware', 'django.contrib.auth.middleware', 'django.contrib.sessions.middleware', 'django.middleware.security', 'django.middleware.common', 'django.middleware.csrf', 'django.middleware.clickjacking', 'django.contrib.admin.apps', 'django.contrib.auth.apps', 'django.contrib.contenttypes.apps', 'django.contrib.sessions.apps', 'django.contrib.messages.apps', 'django.contrib.staticfiles.apps', 'registre.urls', 'whitenoise.middleware', 'qrcode', 'PIL'],
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
    [],
    exclude_binaries=True,
    name='run',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='run',
)
