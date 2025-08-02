# Claude Code プロジェクト情報

## 📋 プロジェクト概要

**システム名**: 出席管理システム for Onedrop  
**バージョン**: v3.2  
**開発言語**: Python 3.13.3  
**メインフレームワーク**: Kivy (デスクトップGUI), Flask (Webアプリ)  
**GitHub**: https://github.com/tatsunoritojo/attendance-management-system-for-onedrop (Private)

### システムの目的
塾生の出席管理、QRコード印刷、月次レポート生成を行うデスクトップアプリケーション

## 🏗️ アーキテクチャ概要

### プロジェクト構造
```
attendance-management-system.3.2/
├── src/attendance_app/                 # メインアプリケーション
│   ├── main.py                        # エントリーポイント
│   ├── config.py                      # 設定管理
│   ├── spreadsheet.py                 # Google Sheets連携
│   ├── report_system/                 # レポート生成システム
│   │   ├── excel_report_generator.py  # Excel生成エンジン（v3.2新機能）
│   │   ├── report_generator.py        # PDF生成エンジン
│   │   └── data_analyzer.py           # データ分析
│   ├── assets/                        # 静的ファイル
│   │   ├── fonts/                     # フォントファイル
│   │   ├── images/                    # 画像リソース
│   │   ├── reports_template.xlsx      # Excelテンプレート
│   │   └── sounds/                    # 音声ファイル
│   └── output/                        # 出力ファイル
│       └── reports/                   # 生成レポート保存先
├── manual/                            # ユーザーマニュアル
├── requirements.txt                   # Python依存関係
├── settings.json                      # アプリ設定（機密情報）
├── service_account.json               # Google API認証（機密情報）
└── print_history.json                # 印刷履歴
```

### 技術スタック
```python
# メイン依存関係
kivy==2.3.1           # デスクトップGUI
flask==3.1.1          # Webアプリ
openpyxl==3.1.5       # Excel操作
reportlab==4.0.4      # PDF生成
google-api-python-client  # Google API
gspread               # Google Sheets
pillow==10.0.0        # 画像処理
pyinstaller==6.14.2   # 実行ファイル化
```

## 🎯 主要機能

### 1. 出席管理
- **ファイル**: `src/attendance_app/main.py`
- QRコードスキャンによる入退室記録
- 手動入力による出席登録
- Google Sheetsへのリアルタイム同期

### 2. QRコード印刷システム
- **ファイル**: `src/attendance_app/printer_control.py`
- Brother P-touch Editor連携
- 生徒情報からQRコード自動生成
- 印刷履歴管理

### 3. Excel月次レポート生成（v3.2新機能）
- **ファイル**: `src/attendance_app/report_system/excel_report_generator.py`
- 生徒別月次出席レポート生成
- プルダウンリスト付き講師コメント欄
- A4横向き印刷最適化レイアウト

### 4. PDF レポート生成
- **ファイル**: `src/attendance_app/report_system/report_generator.py`
- HTML + CSS → PDF変換
- 統計グラフ付きレポート

## 🔧 よく使用するコマンド

### 開発環境セットアップ
```bash
# 依存関係インストール
pip install -r requirements.txt

# アプリケーション実行
python -m src.attendance_app.main

# 実行ファイル生成
pyinstaller attendance_app.spec --clean
```

### Git操作
```bash
# 現在の状況確認
git status
git log --oneline -10

# 開発ブランチ作成
git checkout -b feature/新機能名

# コミット作成
git add .
git commit -m "機能追加: 新機能の概要"

# GitHub にプッシュ
git push -u origin ブランチ名
```

### テスト・デバッグ
```bash
# テスト実行（設定していれば）
python -m pytest tests/

# デバッグ用データ確認
python debug_data_analyzer.py
python examine_sheets_data.py
```

## 🔗 外部連携・設定

### Google API設定
- **認証ファイル**: `service_account.json`
- **必要なAPI**: Google Sheets API, Google Drive API
- **権限**: スプレッドシート読み書き、Driveファイルアクセス

### Google Sheets構造
- **メインシート**: "生徒出席情報"
- **主要列**: 入室時間, 退出時間, 塾生番号, 名前, 気分の天気, 睡眠満足度, 来塾の目的

### プリンター設定
- **対応機種**: Brother QL-800
- **連携ソフト**: P-touch Editor
- **ラベルサイズ**: 62mm x 29mm

## 🐛 よくある問題と解決法

### 1. Google API接続エラー
```
エラー: "quota exceeded" または "unauthorized"
解決法:
1. service_account.json の存在確認
2. Google Cloud Console でAPI有効化確認
3. 認証情報の再生成
```

### 2. プリンター接続エラー
```
エラー: P-touch Editor が応答しない
解決法:
1. USB接続確認
2. プリンター電源確認
3. P-touch Editor 手動起動
4. プリンタードライバー再インストール
```

### 3. Excel生成エラー
```
エラー: "テンプレートファイルが見つからない"
解決法:
1. reports_template.xlsx の存在確認
2. ファイルパーミッション確認
3. PyInstaller の datas 設定確認
```

### 4. 相対インポートエラー
```
エラー: "attempted relative import with no known parent package"
解決法:
既存のコードでは try-except でフォールバック実装済み
```

## 🚀 v3.2の主要変更点

### 新機能
1. **Excel月次レポート生成**
   - openpyxl による Excel ファイル作成
   - テンプレート準拠のレイアウト
   - プルダウンリスト自動挿入

2. **デスクトップ-Web連携**
   - webbrowser モジュールによるブラウザ起動
   - Flask Web アプリとの統合

3. **実行ファイル化**
   - PyInstaller による .exe 生成
   - リソースファイルの適切な包含

### アップグレード時の注意点
- 新しい依存関係: openpyxl
- 新しいアセット: reports_template.xlsx
- 設定ファイルの変更はなし

## 💡 開発のベストプラクティス

### コード品質
- 既存のコード規約に従う（特にKivyアプリ部分）
- try-except による適切なエラーハンドリング
- 日本語コメントで可読性向上

### ファイル管理
- 機密情報（settings.json, service_account.json）は .gitignore に含める
- バイナリファイル（画像、音声）は必要最小限に
- ログファイルは定期的にクリーンアップ

### テスト戦略
- 実データでの動作確認が重要
- Google API の制限に注意（1日あたりのリクエスト数）
- プリンター動作は物理デバイスでのテストが必須

## 🔐 セキュリティ考慮事項

### 機密情報の管理
- `service_account.json`: Google API 認証キー
- `settings.json`: Google Sheets ID などの設定
- 生成された Excel ファイル: 個人情報含有

### 配布時の注意
- 機密ファイルを配布パッケージから除外
- 実行ファイル化時は適切な除外設定
- エンドユーザーによる個別設定が必要

## 📞 引継ぎ・サポート情報

### 主要な引継ぎ資料
- `引継ぎ資料_v3.2.md`: 技術詳細・開発引継ぎ
- `implementation_handover.md`: 機能実装要件
- `manual/handover_guide.md`: 運用引継ぎ

### 緊急時対応
1. システム停止時: 紙ベースでの出席記録継続
2. データ同期失敗時: Google Sheets で手動データ確認
3. レポート生成失敗時: 手動 Excel 作成でのフォールバック

### 将来の拡張計画
- データベース統合（Google Sheets からの移行）
- モバイルアプリ版の開発
- AI機能の統合（出席パターン分析など）

---

## 🚀 Claude Code 向けクイックスタート

### 初回セットアップ（新しいClaude Codeセッション用）
```bash
# 1. プロジェクト概要把握
cat CLAUDE.md

# 2. 現在の状況確認  
git status
git log --oneline -5

# 3. 主要ファイル確認
ls -la src/attendance_app/
cat requirements.txt

# 4. 実行確認
python -m src.attendance_app.main --help
```

### よくある作業パターン
1. **機能追加**: feature ブランチ作成 → 実装 → テスト → PR
2. **バグ修正**: hotfix ブランチ作成 → 修正 → テスト → PR  
3. **レポート改善**: Excel テンプレート更新 → 生成ロジック調整
4. **設定変更**: config.py 更新 → 全機能での動作確認

### デバッグ時の確認ポイント
1. Google API 認証状態
2. プリンター接続状態  
3. ファイルパス・権限
4. 依存関係のバージョン整合性

---

**最終更新**: 2025-08-02  
**作成者**: Claude Code Assistant  
**次回更新予定**: システム機能追加時