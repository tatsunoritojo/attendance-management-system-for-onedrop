from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import gspread
import time
from ..spreadsheet import get_client, get_retrieval_sheet
from ..config import load_settings


def get_attendance_sheet() -> gspread.Worksheet:
    """出席情報シートを取得（リトライ機能付き）"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            settings = load_settings()
            ssid = settings.get("spreadsheet_id")
            if not ssid:
                raise RuntimeError("spreadsheet_id is not configured")
            client = get_client()
            sh = client.open_by_key(ssid)
            return sh.worksheet("生徒出席情報")
        except Exception as e:
            if attempt == max_retries - 1:
                # 最後の試行でも失敗した場合
                raise RuntimeError(f"Google Sheetsへの接続に失敗しました（{max_retries}回試行）: {e}")
            else:
                # 指数バックオフで待機
                wait_time = 2 ** attempt
                print(f"Google Sheets接続試行 {attempt + 1}/{max_retries} 失敗。{wait_time}秒後に再試行...")
                time.sleep(wait_time)


def get_student_name_mapping() -> Dict[str, str]:
    """塾生番号から名前へのマッピングを取得"""
    sheet = get_retrieval_sheet()
    records = sheet.get_all_values()
    mapping = {}
    for row in records[1:]:  # Skip header
        if len(row) >= 2 and row[0] and row[1]:
            mapping[row[0]] = row[1]
    return mapping


def parse_entry_time(time_str: str) -> Optional[datetime]:
    """入室時間文字列をdatetimeオブジェクトに変換"""
    if not time_str:
        return None
    
    # 複数の形式をサポート
    formats = [
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    
    print(f"Warning: Could not parse entry time: {time_str}")
    return None


def parse_exit_time(time_str: str) -> Optional[datetime]:
    """退室時間文字列をdatetimeオブジェクトに変換"""
    if not time_str:
        return None
    
    # 複数の形式をサポート
    formats = [
        # GMT形式
        "%a %b %d %Y %H:%M:%S GMT+0900 (日本標準時)",
        "%a %b %d %Y %H:%M:%S",
        # 標準形式
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    
    # GMT表記を削除して再試行
    cleaned = time_str.replace(" GMT+0900 (日本標準時)", "")
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    
    print(f"Warning: Could not parse exit time: {time_str}")
    return None


def calculate_stay_time(entry_time: str, exit_time: str) -> int:
    """入退室時間から滞在時間を計算（分単位）"""
    entry_dt = parse_entry_time(entry_time)
    exit_dt = parse_exit_time(exit_time)
    
    if not entry_dt or not exit_dt:
        return 0
    
    delta = exit_dt - entry_dt
    return max(0, int(delta.total_seconds() / 60))


def get_monthly_attendance_data(student_id: str, year: int, month: int) -> dict:
    """
    指定生徒の月次出席データを取得・分析（リトライ機能付き）
    """
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            sheet = get_attendance_sheet()
            records = sheet.get_all_values()
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"出席データの取得に失敗しました（{max_retries}回試行）: {e}")
            else:
                wait_time = 2 ** attempt
                print(f"データ取得試行 {attempt + 1}/{max_retries} 失敗。{wait_time}秒後に再試行...")
                time.sleep(wait_time)
    
    # Get student name mapping
    name_mapping = get_student_name_mapping()
    student_name = name_mapping.get(student_id, "Unknown")
    
    # Filter records for the specific student and month
    daily_records = []
    mood_count = {"快晴": 0, "晴れ": 0, "くもり": 0}
    sleep_count = {"０％": 0, "２５％": 0, "５０％": 0, "７５％": 0, "１００％": 0}
    purpose_count = {"学ぶ": 0, "来る": 0}
    sleep_values = []
    
    for i, row in enumerate(records[1:], 1):  # Skip header, start from row 1
        if len(row) < 3:  # Minimum columns needed
            continue
            
        
        # Check if this record is for our student
        if len(row) > 1 and row[1] != student_id:  # Column B: 塾生番号
            continue
            
        # Parse entry time and check if it's in our target month
        entry_time = parse_entry_time(row[0])  # Column A: 入室時間
        if not entry_time:
            continue
            
        if entry_time.year != year or entry_time.month != month:
            continue
            
        exit_time_str = row[6] if len(row) > 6 else ""  # Column G: 退出時間
        if not exit_time_str:  # Skip records without exit time
            continue
            
        stay_minutes = calculate_stay_time(row[0], exit_time_str)
        
        # Extract additional data
        mood = row[3] if len(row) > 3 else ""  # Column D: 気分の天気
        sleep_satisfaction = row[4] if len(row) > 4 else ""  # Column E: 睡眠満足度
        purpose = row[5] if len(row) > 5 else ""  # Column F: 来塾の目的
        
        # Count mood
        if mood in mood_count:
            mood_count[mood] += 1
            
        # Count sleep satisfaction
        if sleep_satisfaction:
            sleep_percent = sleep_satisfaction.replace("%", "").replace("％", "")
            try:
                sleep_val = int(sleep_percent)
                sleep_values.append(sleep_val)
                if sleep_val == 0:
                    sleep_count["０％"] += 1
                elif sleep_val == 25:
                    sleep_count["２５％"] += 1
                elif sleep_val == 50:
                    sleep_count["５０％"] += 1
                elif sleep_val == 75:
                    sleep_count["７５％"] += 1
                elif sleep_val == 100:
                    sleep_count["１００％"] += 1
            except ValueError:
                pass
                
        # Count purpose
        if purpose in purpose_count:
            purpose_count[purpose] += 1
            
        # Add to daily records
        daily_records.append({
            "date": entry_time.strftime("%Y-%m-%d"),
            "entry_time": entry_time.strftime("%H:%M"),
            "exit_time": parse_exit_time(exit_time_str).strftime("%H:%M") if parse_exit_time(exit_time_str) else "",
            "stay_minutes": stay_minutes,
            "mood": mood,
            "sleep_satisfaction": sleep_satisfaction,
            "purpose": purpose
        })
    
    # Calculate averages
    attendance_count = len(daily_records)
    average_stay_minutes = sum(r["stay_minutes"] for r in daily_records) / attendance_count if attendance_count > 0 else 0
    average_sleep_percentage = sum(sleep_values) / len(sleep_values) if sleep_values else 0
    
    return {
        "student_name": student_name,
        "attendance_count": attendance_count,
        "average_stay_minutes": round(average_stay_minutes, 1),
        "daily_records": daily_records,
        "mood_distribution": mood_count,
        "sleep_stats": {
            "average_percentage": round(average_sleep_percentage, 1),
            "distribution": sleep_count
        },
        "purpose_distribution": purpose_count
    }


def get_all_students_list() -> List[dict]:
    """登録されている全生徒のリストを取得"""
    name_mapping = get_student_name_mapping()
    return [{"id": student_id, "name": name} for student_id, name in name_mapping.items()]


def get_students_with_attendance(year: int, month: int) -> List[dict]:
    """指定月に出席記録がある生徒のリストを取得（リトライ機能付き）"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            sheet = get_attendance_sheet()
            records = sheet.get_all_values()
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"出席データの取得に失敗しました（{max_retries}回試行）: {e}")
            else:
                wait_time = 2 ** attempt
                print(f"データ取得試行 {attempt + 1}/{max_retries} 失敗。{wait_time}秒後に再試行...")
                time.sleep(wait_time)
    
    students_with_attendance = set()
    
    for row in records[1:]:  # Skip header
        if len(row) < 7:
            continue
            
        # Parse entry time and check if it's in our target month
        entry_time = parse_entry_time(row[0])
        if not entry_time or entry_time.year != year or entry_time.month != month:
            continue
            
        # Check if exit time exists
        exit_time_str = row[6] if len(row) > 6 else ""
        if not exit_time_str:
            continue
            
        student_id = row[1]  # Column B: 塾生番号
        if student_id:
            students_with_attendance.add(student_id)
    
    # Get student names
    name_mapping = get_student_name_mapping()
    result = []
    for student_id in students_with_attendance:
        if student_id in name_mapping:
            result.append({
                "id": student_id,
                "name": name_mapping[student_id]
            })
    
    return result