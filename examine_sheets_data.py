#!/usr/bin/env python3
"""
Script to examine Google Sheets data structure to understand July 2025 report generation issues.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from attendance_app.spreadsheet import get_client
from attendance_app.config import load_settings

def examine_sheets_structure():
    """Examine the Google Sheets data structure"""
    
    print("=== Google Sheets Data Structure Analysis ===\n")
    
    try:
        # Load settings and get spreadsheet ID
        settings = load_settings()
        spreadsheet_id = settings.get("spreadsheet_id")
        
        if not spreadsheet_id:
            print("ERROR: No spreadsheet_id found in settings.json")
            return
        
        print(f"Spreadsheet ID: {spreadsheet_id}")
        
        # Get Google Sheets client
        client = get_client()
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        print(f"Spreadsheet title: {spreadsheet.title}")
        print(f"Available worksheets: {[ws.title for ws in spreadsheet.worksheets()]}")
        
        # Get the attendance sheet
        attendance_sheet = spreadsheet.worksheet("生徒出席情報")
        
        print(f"\n=== 生徒出席情報 Sheet Analysis ===")
        print(f"Total rows: {attendance_sheet.row_count}")
        print(f"Total columns: {attendance_sheet.col_count}")
        
        # Get all data
        all_data = attendance_sheet.get_all_values()
        
        print(f"Actual data rows: {len(all_data)}")
        
        # Show headers
        if all_data:
            headers = all_data[0]
            print(f"\nColumn headers: {headers}")
            
            # Map column indices to names
            print("\nColumn mapping:")
            for i, header in enumerate(headers):
                print(f"  Column {chr(65+i)} (index {i}): {header}")
        
        # Show first 10 rows of data
        print(f"\n=== First 10 rows of data ===")
        for i, row in enumerate(all_data[:11]):  # 0 is header, 1-10 are data
            print(f"Row {i}: {row}")
        
        # Analyze date formats in Column A (entry time)
        print(f"\n=== Entry Time Analysis (Column A) ===")
        entry_times = []
        for i, row in enumerate(all_data[1:21]):  # Skip header, check first 20 data rows
            if row and len(row) > 0 and row[0]:
                entry_times.append(row[0])
        
        if entry_times:
            print(f"Sample entry times from first 20 rows:")
            for i, time_str in enumerate(entry_times):
                print(f"  {i+1}: {time_str}")
        
        # Check for July 2025 records
        print(f"\n=== July 2025 Records Check ===")
        july_2025_count = 0
        july_2025_samples = []
        
        for i, row in enumerate(all_data[1:], 1):  # Skip header
            if row and len(row) > 0 and row[0]:
                entry_time = row[0]
                # Check if it contains 2025/07 or 2025-07
                if "2025/07" in entry_time or "2025-07" in entry_time:
                    july_2025_count += 1
                    if len(july_2025_samples) < 5:  # Keep first 5 samples
                        july_2025_samples.append(f"Row {i}: {row}")
        
        print(f"Found {july_2025_count} records with July 2025 dates")
        if july_2025_samples:
            print("Sample July 2025 records:")
            for sample in july_2025_samples:
                print(f"  {sample}")
        else:
            print("No July 2025 records found")
        
        # Check date format patterns
        print(f"\n=== Date Format Analysis ===")
        format_patterns = {}
        
        for row in all_data[1:101]:  # Check first 100 data rows
            if row and len(row) > 0 and row[0]:
                entry_time = row[0]
                # Analyze the format pattern
                if "/" in entry_time and ":" in entry_time:
                    # Looks like YYYY/MM/DD HH:MM:SS format
                    pattern = "YYYY/MM/DD HH:MM:SS"
                elif "-" in entry_time and ":" in entry_time:
                    # Looks like YYYY-MM-DD HH:MM:SS format
                    pattern = "YYYY-MM-DD HH:MM:SS"
                else:
                    pattern = "Other"
                
                format_patterns[pattern] = format_patterns.get(pattern, 0) + 1
        
        print("Date format patterns found:")
        for pattern, count in format_patterns.items():
            print(f"  {pattern}: {count} occurrences")
        
        # Check for specific student data if exists
        print(f"\n=== Student Data Analysis ===")
        student_ids = set()
        for row in all_data[1:]:
            if row and len(row) > 2 and row[2]:  # Column C is student ID
                student_ids.add(row[2])
        
        print(f"Total unique student IDs found: {len(student_ids)}")
        print(f"Sample student IDs: {list(student_ids)[:10]}")
        
        # Check exit times (Column G)
        print(f"\n=== Exit Time Analysis (Column G) ===")
        exit_time_count = 0
        empty_exit_count = 0
        
        for row in all_data[1:]:
            if row and len(row) > 6:  # Column G exists
                if row[6]:  # Exit time exists
                    exit_time_count += 1
                else:
                    empty_exit_count += 1
        
        print(f"Records with exit time: {exit_time_count}")
        print(f"Records without exit time: {empty_exit_count}")
        
        # Show sample exit times
        sample_exit_times = []
        for row in all_data[1:11]:  # First 10 data rows
            if row and len(row) > 6 and row[6]:
                sample_exit_times.append(row[6])
        
        if sample_exit_times:
            print("Sample exit times:")
            for i, exit_time in enumerate(sample_exit_times):
                print(f"  {i+1}: {exit_time}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_sheets_structure()