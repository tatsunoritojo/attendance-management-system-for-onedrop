import sys
import os
from pathlib import Path

# プロジェクトルートをPythonのパスに追加
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from src.attendance_app.spreadsheet import get_client, load_settings

def test_google_auth():
    print("--- Google認証テスト開始 ---")
    try:
        # settings.jsonからspreadsheet_idを読み込む
        settings = load_settings()
        spreadsheet_id = settings.get("spreadsheet_id")

        if not spreadsheet_id:
            print("エラー: settings.jsonにspreadsheet_idが設定されていません。")
            print("設定画面でスプレッドシートIDを設定してください。")
            return False

        client = get_client()
        print("Google Sheetsクライアントの初期化に成功しました。")
        
        # スプレッドシートにアクセスできるかテスト
        try:
            sh = client.open_by_key(spreadsheet_id)
            print(f"スプレッドシート '{sh.title}' へのアクセスに成功しました。")
            print("--- Google認証テスト成功 ---")
            return True
        except Exception as e:
            print(f"エラー: スプレッドシートへのアクセスに失敗しました。")
            print(f"詳細: {e}")
            print("考えられる原因:")
            print("  1. service_account.jsonが正しくない、または存在しない。")
            print("  2. スプレッドシートIDが間違っている。")
            print("  3. サービスアカウントにスプレッドシートへのアクセス権限がない。")
            print("  4. サービスアカウントのメールアドレスがスプレッドシートと共有されていない。")
            print("--- Google認証テスト失敗 ---")
            return False

    except Exception as e:
        print(f"エラー: Google認証クライアントの初期化に失敗しました。")
        print(f"詳細: {e}")
        print("考えられる原因:")
        print("  1. service_account.jsonファイルが見つからない、または破損している。")
        print("  2. 必要なライブラリがインストールされていない（gspread, google-auth）。")
        print("--- Google認証テスト失敗 ---")
        return False

if __name__ == "__main__":
    test_google_auth()