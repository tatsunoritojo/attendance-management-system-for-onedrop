import subprocess
from pathlib import Path
import os
import csv
import tempfile
import time
from .config import load_settings

# P-touch Editorのデフォルトパス
DEFAULT_PTOUCH_EDITOR = r"C:\Program Files (x86)\Brother\Ptedit54\ptedit54.exe"

def get_ptouch_editor_path():
    """設定からP-touch Editorのパスを取得する"""
    settings = load_settings()
    return settings.get('ptouch_editor_path', DEFAULT_PTOUCH_EDITOR)

# ラベルテンプレートファイルのパスをassetsフォルダからの相対パスで解決
# このファイルの場所から assets/label_template.lbx を指す
LABEL_TEMPLATE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets', 'qr_text_template.lbx'))

def print_label(student_id: str, student_name: str) -> None:
    """Brother P-touch EditorでQRコード（テキストベース）ラベルを印刷する（ワンクリック印刷対応）"""
    
    if not Path(LABEL_TEMPLATE).exists():
        raise FileNotFoundError(f"ラベルテンプレートが見つかりません: {LABEL_TEMPLATE}")

    # 設定からP-touch Editorパスを取得
    ptouch_editor = get_ptouch_editor_path()
    
    # P-touch Editorの存在確認
    if not os.path.exists(ptouch_editor):
        raise FileNotFoundError(f"P-touch Editorが見つかりません: {ptouch_editor}\n"
                              f"Brother P-touch Editorをインストールするか、\n"
                              f"設定画面で正しいパスを設定してください。")

    # sample_data.csvのパスを取得（塾生選択時に既に更新済み）
    csv_file = os.path.join(os.path.dirname(__file__), 'assets', 'sample_data.csv')
    
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSVデータベースファイルが見つかりません: {csv_file}")

    try:
        print(f"=== ワンクリック印刷処理開始 ===")
        print(f"選択された塾生: {student_name}")
        print(f"塾生ID（QRコード用）: {student_id}")
        print(f"CSVデータベースファイル: {csv_file}")
        print(f"テンプレートファイル: {LABEL_TEMPLATE}")
        print(f"P-touch Editorパス: {ptouch_editor}")
        
        # P-touch Editorに渡すコマンドを作成
        # /D: データベースファイル（CSV）を指定
        # /R: レコード番号（1行目のデータ）を指定
        # /P: 印刷実行
        # /FIT: 自動フィット
        # /S: 印刷設定ダイアログを表示しない
        cmd = [
            ptouch_editor,
            str(LABEL_TEMPLATE),
            f'/D:{csv_file}',  # 事前に更新されたCSVファイルを指定
            '/R:1',  # 1行目のデータレコードを使用
            '/FIT',  # 自動フィット
            '/S',  # 印刷設定ダイアログを表示しない
            '/P',  # 印刷実行
        ]
        
        print(f"実行コマンド: {' '.join(cmd)}") # デバッグ用にコマンドを出力
        
        # P-touch Editorを実行
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("ワンクリック印刷が正常に完了しました。")
        print(f"標準出力: {result.stdout}")
        
    except subprocess.CalledProcessError as e:
        print(f"P-touch Editorの実行に失敗しました。")
        print(f"コマンド: {e.cmd}")
        print(f"リターンコード: {e.returncode}")
        print(f"標準出力: {e.stdout}")
        print(f"標準エラー: {e.stderr}")
        raise
    except FileNotFoundError as e:
        print(f"ファイルが見つかりません: {e}")
        raise