"""
PyInstaller build configuration for Attendance Management System v3.2
"""
import os
from pathlib import Path

# アプリケーションのルートディレクトリ
app_root = Path(__file__).parent

# アセットファイルのパス
assets_dir = app_root / "src" / "attendance_app" / "assets"

# データファイルのリスト
datas = [
    # フォントファイル
    (str(assets_dir / "fonts"), "assets/fonts"),
    # 画像ファイル
    (str(assets_dir / "images"), "assets/images"),
    # サンプルデータ
    (str(assets_dir / "sample_data.csv"), "assets/"),
    # Excelテンプレート
    (str(assets_dir / "reports_template.xlsx"), "assets/"),
    # Webアプリケーション
    (str(app_root / "web_app" / "templates"), "web_app/templates"),
    (str(app_root / "web_app" / "static"), "web_app/static"),
    # レポート設定
    (str(app_root / "templates"), "templates"),
]

# 隠しインポート
hiddenimports = [
    'kivy',
    'kivy.core.window',
    'kivy.core.audio',
    'kivy.core.camera',
    'kivy.core.image',
    'kivy.core.spelling',
    'kivy.core.text',
    'kivy.core.video',
    'kivy.uix.boxlayout',
    'kivy.uix.button',
    'kivy.uix.label',
    'kivy.uix.popup',
    'kivy.uix.screenmanager',
    'kivy.uix.scrollview',
    'kivy.uix.textinput',
    'kivy.uix.spinner',
    'kivy.uix.gridlayout',
    'kivy.uix.image',
    'kivy.clock',
    'kivy.graphics',
    'kivy.core.text',
    'flask',
    'reportlab',
    'openpyxl',
    'PIL',
    'google.auth',
    'google.auth.transport.requests',
    'google.oauth2.credentials',
    'google.oauth2.service_account',
    'googleapiclient',
    'gspread',
    'webbrowser',
    'threading',
    'pathlib',
    'datetime',
    'csv',
    'json',
    'tempfile',
    'base64',
    'io',
    'os',
    'sys',
    'subprocess',
    'jinja2'
]

# 除外するモジュール
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'IPython',
    'jupyter',
    'notebook'
]

print("PyInstaller build configuration loaded successfully!")
print(f"Assets directory: {assets_dir}")
print(f"Number of data files: {len(datas)}")
print(f"Number of hidden imports: {len(hiddenimports)}")