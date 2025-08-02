

import io
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Kivyアプリ内の他モジュールから設定を読み込む
from .config import load_settings

# スコープの定義 (読み取り専用)
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def get_drive_service():
    """Google Drive APIのサービスオブジェクトを生成して返す"""
    # service_account.jsonへのパスを解決
    # このファイル(drive_handler.py)から見て2階層上のservice_account.jsonを指す
    creds_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "service_account.json"))

    if not os.path.exists(creds_path):
        print(f"エラー: service_account.json が見つかりません: {creds_path}")
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        service = build("drive", "v3", credentials=creds)
        return service
    except Exception as e:
        print(f"Google Driveサービスへの接続中にエラー: {e}")
        return None

def get_qr_download_path():
    """設定ファイルからQRコードのローカル保存パスを取得し、整形する"""
    settings = load_settings()
    path = settings.get("qr_code_folder", "").strip()

    # パスが引用符で囲まれていたら除去する
    if path.startswith(('"', "'")) and path.endswith(('"', "'")):
        path = path[1:-1]

    # パスが設定されていない場合、ユーザー指定のデフォルトパスを使用
    if not path:
        path = r"C:\Users\tatsu\Github\attendance-management-system.2.7\src\attendance_app\assets\images\塾生QRコード"
        print(f"ローカル保存パスが未設定のため、デフォルトパスを使用: {path}")

    # フォルダが存在しない場合は作成
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except OSError as e:
        print(f"[ERROR] ダウンロード先のフォルダ作成に失敗しました: {e}")
        # エラーが発生した場合は、安全なフォールバックパスを返す
        fallback_path = os.path.join(os.path.expanduser("~"), "Downloads", "QR_Codes")
        os.makedirs(fallback_path, exist_ok=True)
        print(f"[INFO] 代替フォルダを使用します: {fallback_path}")
        return fallback_path


def list_qr_files_from_drive():
    """設定されたGoogle DriveフォルダからPNGファイルの一覧を返す"""
    settings = load_settings()
    folder_id = settings.get("drive_qr_folder_id")
    if not folder_id:
        print("Google DriveのQRコード用フォルダIDが設定されていません")
        return []

    service = get_drive_service()
    if not service:
        return []

    try:
        query = f"'{folder_id}' in parents and mimeType='image/png' and trashed=false"
        results = service.files().list(
            q=query,
            pageSize=100,  # 最大100件まで取得
            fields="nextPageToken, files(id, name)"
        ).execute()
        
        return results.get("files", [])
    except Exception as e:
        print(f"Google Driveからのファイル一覧取得エラー: {e}")
        return []

def download_file_from_drive(file_id, file_name):
    """指定されたファイルをGoogle Driveからローカルパスにダウンロードする"""
    service = get_drive_service()
    if not service:
        return None

    download_path = get_qr_download_path()
    file_path = os.path.join(download_path, file_name)

    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            # print(f"ダウンロード中 {file_name}: {int(status.progress() * 100)}%")
        
        print(f"ダウンロード完了: {file_path}")
        return file_path
    except Exception as e:
        print(f"ダウンロードエラー ({file_name}): {e}")
        return None

