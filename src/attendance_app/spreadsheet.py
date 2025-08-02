from pathlib import Path
from datetime import datetime
from functools import lru_cache
from typing import Optional, Tuple

import gspread
import csv
import os
from google.oauth2.service_account import Credentials

from .config import load_settings

RETRIEVAL_SHEET_NAME = "塾生番号＿名前＿QRコード"
INPUT_SHEET_NAME = "生徒出席情報"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


@lru_cache()
def get_client() -> gspread.Client:
    """Return an authorized gspread client using service_account.json."""
    try:
        service_account_file = Path(__file__).resolve().parents[2] / 'service_account.json'
        return gspread.service_account(filename=str(service_account_file))
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Google Sheets client: {e}")


def get_retrieval_sheet() -> gspread.Worksheet:
    settings = load_settings()
    ssid = settings.get("spreadsheet_id")
    if not ssid:
        raise RuntimeError("spreadsheet_id is not configured")
    client = get_client()
    sh = client.open_by_key(ssid)
    return sh.worksheet(RETRIEVAL_SHEET_NAME)

def get_input_sheet() -> gspread.Worksheet:
    settings = load_settings()
    ssid = settings.get("spreadsheet_id")
    if not ssid:
        raise RuntimeError("spreadsheet_id is not configured")
    client = get_client()
    sh = client.open_by_key(ssid)
    return sh.worksheet(INPUT_SHEET_NAME)


@lru_cache()
def get_all_students() -> dict[str, str]:
    """Retrieves all students from the retrieval sheet and caches the result."""
    print("Fetching and caching student list...")
    sheet = get_retrieval_sheet()
    records = sheet.get_all_values()
    # Skip header row and create a dictionary of {id: name}
    return {row[0]: row[1] for row in records[1:] if len(row) >= 2}

def get_student_name(student_id: str) -> str:
    students = get_all_students()
    return students.get(str(student_id), "Unknown")


# import requests  # GAS連携無効化により不要

def get_last_record(student_id: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Google Sheets APIを使用して、指定した学生IDの今日の最新記録を取得する。
    退室時刻が記録されていない場合は、その行番号を返す。
    """
    print(f"DEBUG: get_last_record called for student_id={student_id}")
    
    try:
        sheet = get_input_sheet()
        records = sheet.get_all_values()
        
        from datetime import datetime
        today = datetime.now().strftime("%Y/%m/%d")
        
        # 逆順で検索（最新の記録を優先）
        for i in range(len(records) - 1, 0, -1):  # ヘッダー行をスキップ
            row = records[i]
            if len(row) < 2:  # 必要な列数が足りない場合はスキップ
                continue
                
            # B列（インデックス1）が学生ID
            row_student_id = str(row[1]) if len(row) > 1 else ""
            
            if row_student_id == str(student_id):
                # A列（インデックス0）が入室時刻
                entry_timestamp = row[0] if len(row) > 0 else ""
                
                # 今日の日付かチェック
                if entry_timestamp.startswith(today):
                    # G列（インデックス6）が退室時刻
                    exit_time = row[6] if len(row) > 6 else ""
                    
                    if not exit_time:  # 退室時刻が空の場合
                        print(f"DEBUG: Found entry without exit time at row {i + 1}")
                        return i + 1, None  # 1から始まる行番号を返す
                    else:
                        print(f"DEBUG: Found entry with exit time: {exit_time}")
                        # 退室時刻がある場合は次の記録を探す
                        continue
        
        print(f"DEBUG: No entry without exit time found for student_id={student_id}")
        return None, None
        
    except Exception as e:
        print(f"ERROR: Failed to get last record: {e}")
        return None, None


def append_entry(student_id: str, student_name: str) -> Optional[int]:
    sheet = get_input_sheet()
    entry_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    sheet.append_row([entry_time, student_id, student_name, "", "", "", ""])
    # 追加された行のインデックスを返す
    # gspreadのappend_rowは追加された行の情報を直接返さないため、
    # 全てのデータを再取得して最終行のインデックスを特定する
    all_data = sheet.get_all_values()
    return len(all_data)


def write_response(row: int, col: int, value: str) -> bool:
    sheet = get_input_sheet()
    print(f"DEBUG: Writing to sheet: row={row}, col={col}, value='{value}'")
    try:
        cell_range = gspread.utils.rowcol_to_a1(row, col)
        sheet.update(cell_range, [[value]], value_input_option='USER_ENTERED')
        print(f"DEBUG: Successfully wrote to sheet.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to write to sheet: {e}")
        raise # Re-raise the exception to be caught by main.py


def write_exit(row: int) -> bool:
    sheet = get_input_sheet()
    exit_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    try:
        sheet.update_cell(row, 7, exit_time) # Column G is 7th column (1-based)
        return True
    except Exception as e:
        print(f"ERROR: Failed to write exit time: {e}")
        return False

def get_student_list_for_printing() -> list[dict]:
    """印刷用に、塾生名簿シートから全塾生のIDと名前のリストを取得する"""
    try:
        sheet = get_retrieval_sheet()
        records = sheet.get_all_values()
        student_list = []
        # ヘッダー行 (1行目) をスキップして処理
        for row in records[1:]:
            # 少なくともIDと名前の列が存在することを確認
            if len(row) >= 2 and row[0] and row[1]:
                student_list.append({"id": row[0], "name": row[1]})
        return student_list
    except Exception as e:
        print(f"塾生名簿の取得中にエラーが発生しました: {e}")
        return []

def update_sample_csv() -> bool:
    """スプレッドシートからデータを取得してsample_data.csvを更新する"""
    try:
        # スプレッドシートから塾生リストを取得
        student_list = get_student_list_for_printing()
        
        if not student_list:
            print("塾生リストが空のため、CSVファイルの更新をスキップします")
            return False
        
        # CSVファイルのパスを設定
        csv_file_path = os.path.join(os.path.dirname(__file__), 'assets', 'sample_data.csv')
        
        # UTF-8 BOM付きでCSVファイルを作成
        with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            # ヘッダー行を書き込み
            writer.writerow(['StudentID', 'StudentName'])
            # データ行を書き込み
            for student in student_list:
                writer.writerow([student['id'], student['name']])
        
        print(f"sample_data.csvを更新しました。塾生数: {len(student_list)}")
        print(f"ファイルパス: {csv_file_path}")
        return True
        
    except Exception as e:
        print(f"sample_data.csvの更新中にエラーが発生しました: {e}")
        return False

def update_selected_student_csv(student_id: str, student_name: str) -> bool:
    """選択された塾生のデータでsample_data.csvを更新する（ワンクリック印刷用）"""
    try:
        # CSVファイルのパスを設定
        csv_file_path = os.path.join(os.path.dirname(__file__), 'assets', 'sample_data.csv')
        
        # 複数のエンコーディングを試行してP-touch Editorに最適な形式で保存
        encodings_to_try = ['shift_jis', 'cp932', 'utf-8-sig', 'utf-8']
        
        for encoding in encodings_to_try:
            try:
                with open(csv_file_path, 'w', newline='', encoding=encoding) as csvfile:
                    writer = csv.writer(csvfile)
                    # ヘッダー行を書き込み
                    writer.writerow(['StudentID', 'StudentName'])
                    # 選択された塾生のデータ行を書き込み
                    writer.writerow([f"#{student_id}", student_name]) # ここを修正
                
                print(f"選択された塾生でsample_data.csvを更新: {student_name} (ID: {student_id})")
                print(f"使用エンコーディング: {encoding}")
                print(f"ファイルパス: {csv_file_path}")
                return True
                
            except UnicodeEncodeError:
                print(f"エンコーディング {encoding} でエラー、次を試行...")
                continue
        
        # 全てのエンコーディングで失敗した場合のフォールバック
        print(f"全エンコーディングで失敗、UTF-8でフォールバック")
        return False
        
    except Exception as e:
        print(f"選択塾生用CSVの更新中にエラーが発生しました: {e}")
        return False