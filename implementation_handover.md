# 月次レポートシステム実装要件書（引継ぎ用）

## プロジェクト概要

**目的**: 塾生の出席状況と学習状況を保護者に月次で報告するPDFレポート生成システム

**背景**: 
- 既存のKivy出席管理アプリ（QRコード印刷システム）に機能追加
- Google Sheetsに蓄積された出席データからレポートを自動生成
- 保護者にメールで配信（手動→自動の段階的移行）

## 現在のデータ構造

### Google スプレッドシート「生徒名簿 1.xlsx」
```
1. 生徒名簿シート
   - 利用者名前、保護者氏名、保護者連絡先、住所等

2. 塾生番号＿名前＿QRコードシート  
   - 塾生番号、名前、QRコード（既存アプリ連携済み）

3. 生徒出席情報シート ★メインデータ★
   - 入室時間: "2025/07/15 10:56:46"
   - 退出時間: "Tue Jul 15 2025 11:00:51 GMT+0900 (日本標準時)" 
   - 塾生番号: "2025070019"
   - 名前: "東城立憲"
   - 気分の天気: "快晴" | "晴れ" | "くもり"
   - 睡眠満足度: "0％" | "25％" | "50％" | "75％" | "100％"
   - 来塾の目的: "学ぶ" | "来る"
```

### 実データサンプル
```
塾生ID: 2025070019 (東城立憲)
- 出席回数: 7回
- 平均滞在時間: 29分
- 気分記録: 快晴4回、晴れ3回、くもり0回
- 睡眠記録: 平均64％
- 目的記録: 学ぶ5回、来る2回
```

## 実装要件

### 1. ディレクトリ構造
```
src/attendance_app/
├── report_system/           # 新規作成
│   ├── __init__.py
│   ├── data_analyzer.py     # データ分析・集計
│   ├── report_generator.py  # PDF生成メイン
│   ├── template_manager.py  # テンプレート管理
│   └── utils.py            # 共通ユーティリティ
├── templates/               # 新規作成
│   ├── monthly_report.html  # レポートテンプレート
│   └── styles.css          # スタイル定義
└── output/                 # 新規作成
    └── reports/            # 生成されたPDF保存先
```

### 2. 必要なライブラリ
```python
# 新規追加が必要
pip install weasyprint jinja2 pandas matplotlib

# 既存利用可能
google-api-python-client
google-auth
gspread
```

### 3. 核心機能仕様

#### 3.1 データ分析機能 (`data_analyzer.py`)
```python
def get_monthly_attendance_data(student_id: str, year: int, month: int) -> dict:
    """
    指定生徒の月次出席データを取得・分析
    
    Returns:
    {
        'student_name': str,
        'attendance_count': int,           # 出席日数
        'average_stay_minutes': float,     # 平均滞在時間（分）
        'daily_records': [                 # 日別記録
            {
                'date': 'YYYY-MM-DD',
                'entry_time': 'HH:MM',
                'exit_time': 'HH:MM', 
                'stay_minutes': int,
                'mood': str,
                'sleep_satisfaction': str,
                'purpose': str
            }
        ],
        'mood_distribution': {             # 気分の分布
            '快晴': int, '晴れ': int, 'くもり': int
        },
        'sleep_stats': {                   # 睡眠統計
            'average_percentage': float,
            'distribution': {
                '0-25%': int, '26-50%': int, 
                '51-75%': int, '76-100%': int
            }
        },
        'purpose_distribution': {          # 目的の分布
            '学ぶ': int, '来る': int
        }
    }
    """
    
def get_all_students_list() -> list:
    """登録されている全生徒のリストを取得"""
    
def calculate_stay_time(entry_time: str, exit_time: str) -> int:
    """入退室時間から滞在時間を計算（分単位）"""
```

#### 3.2 PDF生成機能 (`report_generator.py`)
```python
def generate_monthly_report(student_id: str, year: int, month: int) -> str:
    """
    月次レポートPDFを生成
    
    Args:
        student_id: 塾生番号
        year: 対象年
        month: 対象月
        
    Returns:
        str: 生成されたPDFファイルのパス
    """
    
def generate_all_reports(year: int, month: int) -> list:
    """全生徒の月次レポートを一括生成"""
```

#### 3.3 テンプレート管理 (`template_manager.py`)
```python
def render_bar_chart(value: int, max_value: int, width: int = 5) -> str:
    """
    テキストベースのバーチャートを生成
    例: render_bar_chart(3, 5) → "■■■□□"
    """
    
def load_template(template_name: str) -> str:
    """HTMLテンプレートを読み込み"""
    
def render_report_html(data: dict) -> str:
    """データをHTMLテンプレートに適用"""
```

### 4. レポートレイアウト仕様

#### 4.1 完成イメージ（A4 1ページ）
```
┌─────────────────────────────────────────┐
│          Onedrop 月次レポート             │
│    生徒名: 東城立憲   対象期間: 2025年7月   │
├─────────────────────────────────────────┤
│ 📈 出席状況                              │
│   出席日数: 7日                          │
│   平均滞在時間: 29分                      │
│                                        │
│ 📅 出席詳細                              │
│   07/15 (月) 10:56-11:00 (4分)          │
│   07/15 (月) 11:05-11:06 (1分)          │
│   07/16 (火) 10:45-10:46 (1分)          │
│   ...                                  │
│                                        │
│ 😊 気分の様子                            │
│   ■■■■□ 快晴 (4回)                    │
│   ■■■□□ 晴れ  (3回)                    │
│   ■□□□□ くもり (0回)                    │
│                                        │
│ 😴 睡眠の状況                            │
│   平均: 64％                            │
│   ■□□□□ 0-25％  (1回)                 │
│   ■■□□□ 26-50％ (1回)                 │
│   ■■■□□ 51-75％ (2回)                 │
│   ■■■■□ 76-100％(3回)                 │
│                                        │
│ 🎯 来塾の目的                            │
│   ■■■■■ 学ぶ (5回)                    │
│   ■■□□□ 来る (2回)                    │
└─────────────────────────────────────────┘
```

#### 4.2 HTMLテンプレート構造
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: "UDDigiKyokashoN-R", "Meiryo", sans-serif; 
            font-size: 12px; 
            margin: 20px;
        }
        .header { 
            text-align: center; 
            border-bottom: 2px solid #333; 
            padding: 15px; 
            margin-bottom: 20px;
        }
        .section { 
            margin: 20px 0; 
            padding: 10px;
        }
        .section h3 { 
            margin-bottom: 10px; 
            color: #333;
        }
        .stats-row { 
            display: flex; 
            justify-content: space-between; 
            margin: 5px 0;
        }
        .bar-chart { 
            font-family: monospace; 
            font-size: 14px;
            line-height: 1.5;
        }
        .bar-fill { color: #0066cc; }
        .bar-empty { color: #cccccc; }
        .attendance-record { 
            margin: 3px 0; 
            font-size: 11px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Onedrop 月次レポート</h1>
        <p>生徒名: {{ student_name }} | 対象期間: {{ year }}年{{ month }}月</p>
    </div>

    <div class="section">
        <h3>📈 出席状況</h3>
        <div class="stats-row">
            <span>出席日数: {{ attendance_count }}日</span>
            <span>平均滞在時間: {{ average_stay_minutes }}分</span>
        </div>
    </div>

    <div class="section">
        <h3>📅 出席詳細</h3>
        {% for record in daily_records %}
        <div class="attendance-record">
            {{ record.date }} {{ record.entry_time }}-{{ record.exit_time }} ({{ record.stay_minutes }}分)
        </div>
        {% endfor %}
    </div>

    <div class="section">
        <h3>😊 気分の様子</h3>
        <div class="bar-chart">
            {% for mood, count in mood_distribution.items() %}
            <div>{{ render_bar_chart(count, max_attendance) }} {{ mood }} ({{ count }}回)</div>
            {% endfor %}
        </div>
    </div>

    <div class="section">
        <h3>😴 睡眠の状況</h3>
        <div>平均: {{ sleep_average }}％</div>
        <div class="bar-chart">
            {% for range, count in sleep_distribution.items() %}
            <div>{{ render_bar_chart(count, max_attendance) }} {{ range }} ({{ count }}回)</div>
            {% endfor %}
        </div>
    </div>

    <div class="section">
        <h3>🎯 来塾の目的</h3>
        <div class="bar-chart">
            {% for purpose, count in purpose_distribution.items() %}
            <div>{{ render_bar_chart(count, max_attendance) }} {{ purpose }} ({{ count }}回)</div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
```

### 5. 技術的制約・注意点

#### 5.1 データ処理の注意点
- **時刻フォーマット**: 入室時間と退出時間の形式が異なる
  - 入室: "2025/07/15 10:56:46"
  - 退出: "Tue Jul 15 2025 11:00:51 GMT+0900 (日本標準時)"
- **名前フィールド**: 一部の記録で名前が空白の場合あり
- **滞在時間**: 短時間（平均29分）なので分単位で表示

#### 5.2 Google Sheets連携
- 既存の`spreadsheet.py`を活用
- 同一のサービスアカウント`service_account.json`使用
- エンコーディング: UTF-8で処理

#### 5.3 PDF生成の要件
- **日本語フォント**: UDDigiKyokashoN-R（既存アプリと統一）
- **ページサイズ**: A4
- **出力パス**: `output/reports/YYYY-MM_[塾生番号]_[生徒名].pdf`

### 6. 実装優先順位

#### Phase 1: コア機能（Week 1）
1. **データ分析基盤**
   - Google Sheetsからデータ取得
   - 月次統計計算
   - 日時処理ロジック

2. **PDF生成機能**
   - HTMLテンプレート作成
   - WeasyPrintでPDF変換
   - 日本語フォント対応

3. **統合テスト**
   - 実データでの動作確認
   - エラーハンドリング
   - 出力品質チェック

#### Phase 2: Kivyアプリ統合（Week 2）
1. **UI追加**
   - メイン画面に「レポート生成」ボタン
   - 対象月選択機能
   - 進捗表示

2. **メニュー統合**
   - 既存の設定画面に統合
   - 出力先フォルダ設定
   - 生成履歴表示

### 7. テストケース

#### 7.1 基本テストデータ
```python
# テスト用データ（実データベース）
test_student = {
    'id': '2025070019',
    'name': '東城立憲',
    'records': 7,
    'avg_stay': 29,
    'mood': {'快晴': 4, '晴れ': 3, 'くもり': 0},
    'sleep_avg': 64,
    'purpose': {'学ぶ': 5, '来る': 2}
}
```

#### 7.2 エッジケース
- 出席0回の生徒
- 極端に短い滞在時間（1分）
- 同日複数回出席
- データ不備（名前空白等）

### 8. 設定項目

#### 8.1 `config.py`追加項目
```python
# レポート生成設定
REPORT_CONFIG = {
    'juku_name': 'Onedrop',
    'output_directory': 'output/reports',
    'template_directory': 'templates',
    'font_family': 'UDDigiKyokashoN-R',
    'page_size': 'A4',
    'margins': {'top': 20, 'bottom': 20, 'left': 15, 'right': 15},
    'bar_chart_width': 5,
    'date_format': '%m/%d (%a)',
    'time_format': '%H:%M'
}
```

## 引継ぎ時の確認事項

1. **既存システムとの連携**
   - `spreadsheet.py`の関数仕様
   - `config.py`の設定項目
   - フォント関連の設定

2. **開発環境準備**
   - Python 3.13.3環境
   - 必要ライブラリのインストール
   - Google API認証の確認

3. **実装完了の判定基準**
   - 実データから正常にPDF生成
   - A4サイズで適切にレイアウト
   - 日本語フォントで正しく表示
   - エラーハンドリングが動作

この要件書を元に、Claude Codeでの実装を進めてください。不明な点があれば、既存のコードベースを参照するか、追加で質問してください。