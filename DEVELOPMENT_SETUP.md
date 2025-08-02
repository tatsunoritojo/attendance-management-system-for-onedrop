# 開発環境セットアップガイド

## 📋 概要

出席管理システムの開発環境を新規セットアップする手順書です。  
新しい開発者や別PCでの開発開始時に使用してください。

## 🔧 必要な環境

### システム要件
- **OS**: Windows 10/11 (推奨)
- **Python**: 3.13.3
- **メモリ**: 8GB以上推奨
- **ストレージ**: 5GB以上の空き容量

### 必要なソフトウェア
- Python 3.13.3
- Git
- Brother P-touch Editor（QRコード印刷用）
- テキストエディタ（VS Code推奨）

## 🚀 セットアップ手順

### 1. Python環境の準備

#### Python 3.13.3 インストール
```bash
# Python バージョン確認
python --version
# 出力例: Python 3.13.3

# pipアップグレード
python -m pip install --upgrade pip
```

#### 仮想環境作成（推奨）
```bash
# プロジェクトディレクトリに移動
cd attendance-management-system.3.2

# 仮想環境作成
python -m venv venv

# 仮想環境アクティベート（Windows）
venv\Scripts\activate

# （仮想環境内で）依存関係インストール
pip install -r requirements.txt
```

### 2. Git設定

#### 基本設定
```bash
# ユーザー情報設定
git config --global user.name "your-username"
git config --global user.email "your-email@example.com"

# デフォルトブランチ設定
git config --global init.defaultBranch main

# 改行コード設定（Windows）
git config --global core.autocrlf true
```

#### エイリアス設定（任意）
```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.cm commit
git config --global alias.lg "log --oneline --graph --decorate"
```

### 3. プロジェクトクローン・初期設定

#### GitHub からクローン
```bash
# HTTPSでクローン（認証が必要）
git clone https://github.com/tatsunoritojo/attendance-management-system-for-onedrop.git
cd attendance-management-system-for-onedrop

# SSH設定済みの場合
git clone git@github.com:tatsunoritojo/attendance-management-system-for-onedrop.git
```

#### 必要な設定ファイル作成
```bash
# settings.json テンプレート作成
copy settings.json.template settings.json
# 実際の値を設定（後述）

# service_account.json の配置
# Google Cloud Consoleから取得したファイルを配置
```

### 4. Google API設定

#### service_account.json の取得
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクト選択（または新規作成）
3. APIとサービス > 認証情報
4. サービスアカウント作成
5. キーを生成（JSON形式）
6. ダウンロードしたファイルを `service_account.json` として保存

#### API の有効化
```bash
# 必要なAPI
- Google Sheets API
- Google Drive API
```

#### settings.json の設定
```json
{
  "spreadsheet_id": "1ABCD..._Google_Sheets_ID",
  "drive_qr_folder_id": "1EFGH..._Google_Drive_Folder_ID",
  "qr_code_folder": "C:\\path\\to\\qr_codes",
  "ptouch_editor_path": "C:\\Program Files (x86)\\Brother\\Ptedit54\\ptedit54.exe"
}
```

### 5. プリンター設定（開発環境では任意）

#### Brother QL-800 設定
1. Brother P-touch Editor をインストール
2. プリンタードライバーインストール
3. USB接続確認
4. 設定ファイルでパス指定

```bash
# プリンター接続確認
# P-touch Editor で印刷テスト実行
```

### 6. 開発用ツール設定

#### VS Code 推奨拡張機能
- Python
- Python Debugger  
- GitLens
- Pylint
- Japanese Language Pack

#### VS Code settings.json
```json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "files.encoding": "utf8",
    "files.eol": "\r\n"
}
```

## ✅ 動作確認

### 1. Python依存関係確認
```bash
# 必要なパッケージが正しくインストールされているか確認
pip list | findstr "kivy flask openpyxl"

# 出力例:
# Flask          3.1.1
# Kivy           2.3.1  
# openpyxl       3.1.5
```

### 2. アプリケーション起動テスト
```bash
# メインアプリケーション起動
python -m src.attendance_app.main

# 正常起動すれば Kivy ウィンドウが表示される
```

### 3. Google API接続テスト
```bash
# 認証テスト用スクリプト実行
python test_auth.py

# 成功例の出力:
# Google Sheets API connection: OK
# Google Drive API connection: OK
```

### 4. 各機能の動作確認
```bash
# QRコード印刷テスト（プリンター接続時のみ）
# Alt+P でプリンター画面に移動
# 「テスト印刷」実行

# レポート生成テスト
# Alt+R でレポート画面に移動  
# サンプルデータでレポート生成実行
```

## 🐛 よくある問題と解決法

### Python関連
```bash
# 問題: "python is not recognized"
# 解決: Python インストールパスを環境変数PATHに追加

# 問題: "pip install" でエラー
# 解決: pip アップグレード実行
python -m pip install --upgrade pip

# 問題: 仮想環境でのパッケージが見つからない
# 解決: 仮想環境が正しくアクティベートされているか確認
where python  # venv内のpythonを指しているか確認
```

### Git関連
```bash
# 問題: "fatal: repository not found"
# 解決: プライベートリポジトリへのアクセス権限確認

# 問題: プッシュ時に認証エラー
# 解決: GitHub Personal Access Token使用
# Settings > Developer settings > Personal access tokens

# 問題: line ending warning
# 解決: core.autocrlf 設定済み、無視して可
```

### Google API関連
```bash
# 問題: "quota exceeded"
# 解決: Google Cloud Console でAPI制限確認

# 問題: "unauthorized"  
# 解決: service_account.json ファイル内容確認
# Google Sheets での共有設定確認

# 問題: "permission denied"
# 解決: サービスアカウントにシート編集権限付与
```

### アプリケーション関連
```bash
# 問題: Kivy ウィンドウが表示されない
# 解決: 
python -c "import kivy; print('Kivy version:', kivy.__version__)"

# 問題: フォントが表示されない
# 解決: assets/fonts/ フォルダの存在確認

# 問題: プリンター接続エラー
# 解決: P-touch Editor 手動起動確認
# USB接続・プリンター電源確認
```

## 🔄 開発ワークフロー

### 日常的な開発フロー
```bash
# 1. 開発開始前
git checkout main
git pull origin main
git checkout -b feature/新機能名

# 2. 開発中
# コード編集...
python -m src.attendance_app.main  # 動作確認

# 3. コミット前確認
git status
git diff

# 4. コミット・プッシュ
git add .
git commit -m "feat: 新機能の説明"
git push -u origin feature/新機能名

# 5. プルリクエスト作成（GitHub UI）
```

### デバッグ用コマンド
```bash
# データ分析デバッグ
python debug_data_analyzer.py

# Google Sheets データ確認
python examine_sheets_data.py

# 設定ファイル検証
python -c "from src.attendance_app.config import load_settings; print(load_settings())"
```

### 実行ファイル生成
```bash
# 本番用実行ファイル作成
pyinstaller attendance_app.spec --clean

# 出力確認
ls dist/AttendanceManagementSystem/

# 動作テスト
cd dist/AttendanceManagementSystem
./AttendanceManagementSystem.exe
```

## 📚 参考資料

### 公式ドキュメント
- [Python 3.13 Documentation](https://docs.python.org/3.13/)
- [Kivy Documentation](https://kivy.org/doc/stable/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Google Sheets API](https://developers.google.com/sheets/api/guides/concepts)

### プロジェクト内資料
- `CLAUDE.md`: プロジェクト概要・Claude Code向け情報
- `GIT_WORKFLOW.md`: Git運用ルール
- `引継ぎ資料_v3.2.md`: 技術詳細・実装情報
- `manual/index.html`: エンドユーザー向けマニュアル

### トラブルシューティング
- `README.md`: 基本的な使用方法
- `requirements.txt`: 依存関係一覧
- GitHub Issues: 既知の問題と解決策

## 🎯 開発環境別の注意事項

### Windows 開発環境
- パス区切り文字: `\` (バックスラッシュ)
- 改行コード: CRLF
- 権限: 通常ユーザーで実行可能

### 他OS での開発（参考）
```bash
# macOS/Linux の場合
pip3 install -r requirements.txt
python3 -m src.attendance_app.main

# パス区切り文字の違いに注意
# 設定ファイルでのパス指定を適切に変更
```

## ✅ セットアップ完了チェックリスト

### 必須項目
- [ ] Python 3.13.3 インストール完了
- [ ] Git設定完了
- [ ] プロジェクトクローン完了
- [ ] 依存関係インストール完了
- [ ] settings.json 設定完了
- [ ] service_account.json 配置完了
- [ ] Google API認証テスト通過
- [ ] アプリケーション起動確認

### 推奨項目
- [ ] 仮想環境セットアップ
- [ ] VS Code拡張機能インストール
- [ ] Brother P-touch Editor インストール（印刷機能使用時）
- [ ] Git エイリアス設定
- [ ] デバッグ用スクリプト動作確認

### 開発準備完了
- [ ] サンプルデータでの動作確認
- [ ] Git ワークフロー理解
- [ ] プロジェクト構造把握
- [ ] 開発タスク明確化

---

**作成日**: 2025-08-02  
**対象**: 新規開発者・開発環境移行時  
**更新頻度**: 依存関係・手順変更時