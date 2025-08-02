#!/usr/bin/env python3
"""
Debug script to understand the column mapping issue in the Google Sheets.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from attendance_app.report_system.data_analyzer import get_attendance_sheet

def debug_column_mapping():
    """Debug the column mapping issue"""
    
    print("=== Column Mapping Debug ===\n")
    
    try:
        # Get the attendance sheet
        sheet = get_attendance_sheet()
        records = sheet.get_all_values()
        
        print("Headers and column mapping:")
        headers = records[0]
        for i, header in enumerate(headers):
            print(f"  Column {chr(65+i)} (index {i}): '{header}'")
        
        print("\nFirst few data rows:")
        for i, row in enumerate(records[1:5], 1):
            print(f"Row {i}:")
            for j, cell in enumerate(row):
                if j < len(headers):
                    print(f"  {headers[j]}: '{cell}'")
        
        # Check what the actual student ID column is
        print("\nAnalyzing student ID column:")
        for i, row in enumerate(records[1:5], 1):
            print(f"Row {i}:")
            print(f"  Column A (index 0): '{row[0]}'")  # Entry time
            print(f"  Column B (index 1): '{row[1]}'")  # Should be student ID
            print(f"  Column C (index 2): '{row[2]}'")  # Student name
            print(f"  Column D (index 3): '{row[3]}'")  # Purpose
            print(f"  Column E (index 4): '{row[4]}'")  # Mood
            print(f"  Column F (index 5): '{row[5]}'")  # Sleep satisfaction
            print(f"  Column G (index 6): '{row[6]}'")  # Exit time
            print()
        
        # The issue is that the code is checking row[2] for student ID, but it should be row[1]
        print("=== Issue Analysis ===")
        print("The data structure shows:")
        print("  Column A: Entry time")
        print("  Column B: Student ID (but code is checking Column C)")
        print("  Column C: Student name")
        print("  Column D: Purpose")
        print("  Column E: Mood")
        print("  Column F: Sleep satisfaction")
        print("  Column G: Exit time")
        print()
        print("The data_analyzer.py is checking row[2] for student ID, but it should be row[1]")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_column_mapping()