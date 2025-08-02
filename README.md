# 出席管理システム v3.2 - Excel レポート生成対応

## 概要

出席管理システムが大幅にアップデートし、**Web版レポートエディタ**を搭載しました。Kivy デスクトップアプリケーションに加え、Flask を使用したWebアプリケーションによる直感的なレポート作成・カスタマイズ機能を提供します。

## 🚀 v3.2 主な新機能

### 1. Excel レポート生成機能 🆕
- **出席管理レポートのExcel出力**
- **個別生徒シート**の自動生成
- **テンプレート準拠**のレイアウト
- **プルダウンリスト**による入力支援
- **A4横向き印刷**対応

### 2. Web版レポートエディタ
- **Bootstrap 5**による現代的なWebUI
- **リアルタイムプレビュー**機能
- **ドラッグ&ドロップ**によるセクション順序変更
- **画像挿入・配置**機能（背景レイヤー対応）
- **A4レイアウト**ビジュアライザー

### 3. デスクトップ・Web連携
- **デスクトップアプリからブラウザ起動**
- **シームレスな操作体験**
- **設定の統一管理**

### 4. レポートカスタマイズ機能
- **10種類のセクション**管理
  - 出席状況、出席詳細、気分分析、睡眠分析、来塾目的
  - 月次サマリー、目標と達成度、フィードバック、改善提案、来月の計画
- **フォントサイズ**調整（タイトル、見出し、本文、統計）
- **セクションの有効/無効**切り替え
- **位置ベース**でのセクション順序管理

### 5. 画像管理システム
- **マルチ画像アップロード**（PNG、JPG、GIF対応）
- **5種類の配置モード**：
  - 背景レイヤー（文字の下）
  - カスタム位置（X・Y座標指定）
  - 透かし（中央半透明）
  - ヘッダー（上部）
  - フッター（下部）
- **画像設定**：サイズ、透明度、配置の調整

### 6. PDF生成機能
- **ReportLab**による高品質PDF生成
- **日本語フォント**対応
- **画像埋め込み**機能
- **ダウンロード**機能

## システム構成

```
attendance-management-system.3.2/
├── src/attendance_app/           # デスクトップアプリ（Kivy）
│   ├── main.py                  # メイン出席管理アプリ
│   ├── main_printer.py          # QRコード印刷システム
│   ├── report_editor_screen.py  # レポートエディタ画面
│   ├── report_system/           # レポート生成システム
│   │   ├── report_generator.py  # PDF生成エンジン
│   │   ├── excel_report_generator.py  # Excel生成エンジン 🆕
│   │   ├── preview_generator.py # プレビュー生成エンジン
│   │   ├── template_loader.py   # テンプレート管理
│   │   └── data_analyzer.py     # データ分析機能
│   └── assets/                  # アセット（フォント、画像）
│       ├── reports_template.xlsx # Excelテンプレート 🆕
│       └── images/              # 画像ファイル
├── web_app/                     # Webアプリケーション（Flask）
│   ├── app.py                   # Flask アプリケーション
│   ├── templates/               # HTMLテンプレート
│   │   ├── index.html          # トップページ
│   │   └── editor.html         # レポートエディタ
│   └── static/                  # 静的ファイル
│       ├── css/editor.css      # スタイルシート
│       └── js/editor.js        # JavaScript
└── templates/                   # レポート設定ファイル
    └── report_config.json       # レポートテンプレート設定
```

## 必要な環境

### ソフトウェア要件
- Python 3.13.3
- Brother P-touch Editor 5.4 (QRコード印刷用)
- Brother QL-800 プリンター (QRコード印刷用)
- モダンなWebブラウザ (Chrome, Firefox, Safari, Edge)

### Python依存関係
```bash
# Core frameworks
kivy==2.3.1
flask==2.3.3

# Report generation
reportlab==4.0.4
Pillow==10.0.0
openpyxl==3.1.2  # Excel生成用 🆕

# Google API (QRコード印刷機能用)
google-api-python-client
google-auth
google-auth-oauthlib
google-auth-httplib2
gspread

# Additional dependencies
webbrowser  # デスクトップ・Web連携用 🆕
```

### 設定ファイル
- `service_account.json`: Google API認証情報（QRコード印刷機能用）
- `templates/report_config.json`: レポートテンプレート設定
- `src/attendance_app/assets/reports_template.xlsx`: Excelレポートテンプレート 🆕

## インストールと設定

### 1. リポジトリクローン
```bash
git clone [repository-url]
cd attendance-management-system.3.2
```

### 2. 依存関係インストール
```bash
pip install -r requirements.txt
```

### 3. アプリケーション起動

#### デスクトップアプリ（Kivy）
```bash
python -m src.attendance_app.main
```

#### Webアプリ（Flask）
```bash
cd web_app
python app.py
```
アクセス先: http://127.0.0.1:5000

## 使用方法

### Web版レポートエディタ

#### 基本操作
1. **ブラウザで http://127.0.0.1:5000/editor にアクセス**
2. **基本設定**タブでレポートタイトルを設定
3. **セクション**タブで表示するセクションを選択
4. **レイアウト**タブでセクション順序をドラッグ&ドロップで調整
5. **画像**タブで画像をアップロード・配置設定
6. **デザイン**タブでフォントサイズを調整
7. **プレビュー**でリアルタイム確認
8. **「PDF生成」**ボタンでレポート作成

#### 画像機能の使用方法

**画像アップロード**:
- 「画像アップロード」でPNG、JPG、GIFファイルを選択
- 複数画像の同時アップロード対応
- アップロード済み画像の一覧表示・削除機能

**画像配置設定**:
- **背景レイヤー**: 文字の下に薄く表示（推奨）
- **カスタム位置**: X・Y座標を0-100%で指定
- **透かし**: 中央に半透明で表示
- **ヘッダー**: レポート上部に表示
- **フッター**: レポート下部に表示

**画像調整**:
- 画像幅: 10-100%
- 透明度: 10-100%
- 配置: 左寄せ、中央寄せ、右寄せ

### デスクトップアプリ

#### QRコード印刷機能
1. **メイン画面で「印刷」ボタンクリック**
2. **「リスト更新」ボタンでGoogle Sheetsから塾生リスト取得**
3. **印刷したい塾生をクリック**
4. **「このQRコードを印刷」ボタンでP-touch Editorで印刷**

#### レポートエディタ
1. **メイン画面で「レポート」ボタンクリック**
2. **デスクトップ版レポートエディタで設定調整**
3. **プレビュー確認後、PDF生成**

## 技術仕様

### Webアプリケーション
- **フレームワーク**: Flask 2.3.3
- **フロントエンド**: Bootstrap 5, SortableJS
- **画像処理**: Pillow (PIL)
- **PDF生成**: ReportLab
- **API**: RESTful設計

### プレビュー生成エンジン
- **リアルタイム生成**: 設定変更時に自動更新
- **画像合成**: 背景レイヤーと文字レイヤーの合成
- **フォント処理**: 日本語フォント対応
- **レイアウト**: A4サイズ対応

### 画像処理システム
- **フォーマット**: PNG, JPG, GIF対応
- **Base64エンコーディング**: ブラウザ-サーバー間データ転送
- **画像変換**: リサイズ、透明度、配置調整
- **メモリ効率**: 一時ファイルによる効率的な処理

### PDF生成エンジン
- **ReportLab統合**: 高品質PDF出力
- **日本語対応**: MS Gothicフォント使用
- **画像埋め込み**: 背景画像、ヘッダー、フッター対応
- **レイアウト**: A4サイズ、カスタマイズ可能

## API仕様

### RESTful API エンドポイント

```
GET  /                          # トップページ
GET  /editor                    # レポートエディタ
GET  /api/template              # テンプレート取得
POST /api/template              # テンプレート保存
POST /api/preview               # プレビュー生成
POST /api/layout-preview        # レイアウトプレビュー生成
POST /api/generate-report       # PDF生成
POST /api/reset-template        # テンプレートリセット
```

### データ形式

```json
{
  "report_title": "Onedrop 月次レポート",
  "sections": {
    "attendance_status": {
      "title": "■ 出席状況",
      "enabled": true,
      "position": 1
    }
  },
  "formatting": {
    "fonts": {
      "title_size": 18,
      "heading_size": 13,
      "normal_size": 10,
      "stats_size": 11
    }
  },
  "images": {
    "uploaded": [],
    "settings": {
      "position": "background",
      "width": 50,
      "opacity": 30,
      "alignment": "center",
      "x": 10,
      "y": 10
    }
  }
}
```

## トラブルシューティング

### よくある問題

#### 1. Webアプリケーションが起動しない
```bash
# 依存関係を確認
pip install flask pillow reportlab

# ポートが使用中の場合
python app.py --port 5001
```

#### 2. プレビューが表示されない
- ブラウザの開発者ツール（F12）でエラーを確認
- JavaScript のUTF-8エンコーディングエラーは修正済み
- 画像サイズが大きすぎる場合は縮小して再アップロード

#### 3. PDF生成エラー
- ReportLabがインストールされているか確認
- 一時ディレクトリの書き込み権限を確認
- 画像ファイルの形式がサポートされているか確認

#### 4. 画像が反映されない
- アップロード完了後に「保存」ボタンを押す
- ブラウザキャッシュをクリア（Ctrl+F5）
- 画像ファイルサイズを5MB以下に調整

## 開発情報

### v3.2.0 - Excel レポート生成対応 📊

**リリース日**: 2025年7月18日

**主要な新機能**:
- ✅ **Excel レポート生成**: openpyxlによる高品質Excel出力
- ✅ **テンプレート準拠**: 既存Excelテンプレートの完全再現
- ✅ **個別生徒シート**: 1つのExcelファイルに複数シート生成
- ✅ **プルダウンリスト**: プランニング・カウンセリング・個別対応列
- ✅ **画像統合**: 透明背景ロゴの自動配置
- ✅ **デスクトップ-Web連携**: アプリからブラウザ起動
- ✅ **A4横向き印刷**: 印刷設定の自動調整
- ✅ **データ検証**: 入力ミス防止機能

**技術的成果**:
- **openpyxl統合**: Excel操作の完全自動化
- **テンプレート解析**: 既存ファイルの詳細情報取得
- **画像処理**: 縦横比固定、スケーリング対応
- **webbrowser連携**: デスクトップアプリからWeb画面起動
- **レイアウト最適化**: A4印刷に最適化された設定

### v3.0.0 - Web版レポートエディタ搭載 🌐

**リリース日**: 2025年7月17日

**主要な新機能**:
- ✅ **Flask Webアプリケーション**: Bootstrap 5による現代的なUI
- ✅ **リアルタイムプレビュー**: 設定変更の即座反映
- ✅ **画像管理システム**: アップロード、配置、透明度調整
- ✅ **セクション管理**: 10種類のセクション、ドラッグ&ドロップ順序変更
- ✅ **PDF生成エンジン**: ReportLabによる高品質出力
- ✅ **A4レイアウト**: プレビューとPDF生成の完全対応
- ✅ **日本語フォント**: MS Gothic、フォールバック対応
- ✅ **RESTful API**: 設定保存、テンプレート管理

**技術的成果**:
- **Kivy + Flask**: デスクトップとWebのハイブリッド構成
- **PIL画像処理**: 背景レイヤー、カスタム位置、透明度対応
- **Base64エンコーディング**: ブラウザ-サーバー間の画像転送
- **SortableJS**: 直感的なドラッグ&ドロップ機能
- **UTF-8対応**: 日本語文字のエンコーディング問題解決

### 過去バージョン

#### v2.8.0 - UI/UX大幅改善 🎨
- カラースキーム統一
- 設定画面改善
- 印刷システムUI改善

#### v2.7.0 - QRコード印刷自動化 🎯
- P-touch Editor統合
- ワンクリック印刷システム
- エンコーディング最適化

#### v2.6.x - Google API統合
- Google Sheets連携
- Google Drive連携
- OAuth 2.0認証

## アーキテクチャ

### システム設計思想
- **モジュラー設計**: 機能別の明確な分離
- **ハイブリッド構成**: デスクトップとWebの最適活用
- **リアルタイム処理**: 即座のフィードバック
- **レスポンシブデザイン**: 様々な画面サイズに対応

### セキュリティ対策
- **Base64エンコーディング**: 安全な画像データ転送
- **サーバーサイド処理**: 画像処理の信頼性確保
- **一時ファイル管理**: 適切なファイル管理
- **エラーハンドリング**: 包括的なエラー処理

## 📚 ドキュメント・引継ぎ資料

### 🚀 開発者向けドキュメント
- **[CLAUDE.md](CLAUDE.md)**: Claude Code向けプロジェクト情報・クイックスタート
- **[GIT_WORKFLOW.md](GIT_WORKFLOW.md)**: Git運用ルール・ブランチ戦略・コミット規約
- **[DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md)**: 開発環境セットアップガイド

### 📋 引継ぎ・運用資料
- **[引継ぎ資料_v3.2.md](引継ぎ資料_v3.2.md)**: 技術詳細・開発引継ぎ資料
- **[implementation_handover.md](implementation_handover.md)**: 機能実装要件書
- **[manual/handover_guide.md](manual/handover_guide.md)**: 運用引継ぎガイド

### 🔧 ユーザー向け資料
- **[manual/index.html](manual/index.html)**: エンドユーザーマニュアル

## サポート

### 動作確認済み環境
- **OS**: Windows 11, Windows 10
- **Python**: 3.13.3
- **ブラウザ**: Chrome 119+, Firefox 119+, Safari 17+, Edge 119+
- **テスト日**: 2025年7月17日

### 推奨システム要件
- **CPU**: Intel i5 以上
- **メモリ**: 8GB以上
- **ストレージ**: 1GB以上の空き容量
- **ネットワーク**: インターネット接続（Google API用）

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照

---

## 📋 クイックスタート

### 1分でWeb版レポートエディタを試す

```bash
# 1. リポジトリクローン
git clone [repository-url]
cd attendance-management-system.3.2

# 2. 依存関係インストール
pip install flask pillow reportlab openpyxl

# 3. Webアプリ起動
cd web_app
python app.py

# 4. ブラウザでアクセス
# http://127.0.0.1:5000/editor
```

### 5分でレポート作成

1. **画像タブ**: ロゴ画像をアップロード
2. **セクションタブ**: 必要なセクションを選択
3. **レイアウトタブ**: セクション順序を調整
4. **デザインタブ**: フォントサイズを調整
5. **PDF生成**: 完成したレポートをダウンロード

---

**注意**: このシステムは教育機関での使用を想定して設計されています。商用利用の際は適切な検証とライセンス確認を行ってください。