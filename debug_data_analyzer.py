#!/usr/bin/env python3
"""
Debug script to understand why data_analyzer.py is not finding July 2025 records.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from attendance_app.report_system.data_analyzer import (
    get_attendance_sheet, 
    get_student_name_mapping, 
    parse_entry_time,
    get_monthly_attendance_data,
    get_students_with_attendance
)

def debug_data_analyzer():
    """Debug the data analyzer to understand why July 2025 records are not found"""
    
    print("=== Data Analyzer Debug ===\n")
    
    try:
        # Get the attendance sheet
        sheet = get_attendance_sheet()
        records = sheet.get_all_values()
        
        print(f"Total records: {len(records)}")
        print(f"First few records:")
        for i, record in enumerate(records[:5]):
            print(f"  {i}: {record}")
        
        # Get student name mapping
        name_mapping = get_student_name_mapping()
        print(f"\nStudent name mapping: {name_mapping}")
        
        # Test parsing entry times
        print(f"\n=== Testing Entry Time Parsing ===")
        test_times = [
            "2025/07/15 10:56:46",
            "2025/07/16 10:45:56",
            "2025-07-15 10:56:46",
            "07/15/2025 10:56:46"
        ]
        
        for time_str in test_times:
            parsed = parse_entry_time(time_str)
            print(f"  '{time_str}' -> {parsed}")
        
        # Test get_students_with_attendance for July 2025
        print(f"\n=== Testing get_students_with_attendance for July 2025 ===")
        students_july_2025 = get_students_with_attendance(2025, 7)
        print(f"Students with attendance in July 2025: {students_july_2025}")
        
        # Test manually looking for July 2025 records
        print(f"\n=== Manual Search for July 2025 Records ===")
        july_2025_records = []
        
        for i, row in enumerate(records[1:], 1):  # Skip header
            if len(row) < 3:
                continue
                
            entry_time_str = row[0]  # Column A
            student_id = row[2]      # Column C
            
            print(f"Row {i}: entry_time='{entry_time_str}', student_id='{student_id}'")
            
            # Parse entry time
            entry_time = parse_entry_time(entry_time_str)
            if entry_time:
                print(f"  Parsed time: {entry_time}, year={entry_time.year}, month={entry_time.month}")
                if entry_time.year == 2025 and entry_time.month == 7:
                    july_2025_records.append({
                        'row': i,
                        'entry_time': entry_time,
                        'student_id': student_id,
                        'exit_time': row[6] if len(row) > 6 else ""
                    })
                    print(f"  *** FOUND JULY 2025 RECORD ***")
            else:
                print(f"  Failed to parse entry time")
        
        print(f"\nFound {len(july_2025_records)} July 2025 records:")
        for record in july_2025_records:
            print(f"  Row {record['row']}: {record}")
        
        # Test get_monthly_attendance_data for a specific student
        if july_2025_records:
            test_student_id = july_2025_records[0]['student_id']
            print(f"\n=== Testing get_monthly_attendance_data for student {test_student_id} ===")
            
            # Let's trace through the function step by step
            print("Starting get_monthly_attendance_data debug...")
            
            # Get all records again for debugging
            records = sheet.get_all_values()
            print(f"Total records in sheet: {len(records)}")
            
            # Get student name mapping
            name_mapping = get_student_name_mapping()
            student_name = name_mapping.get(test_student_id, "Unknown")
            print(f"Student ID: {test_student_id}, Name: {student_name}")
            
            # Filter records manually
            matching_records = []
            for i, row in enumerate(records[1:], 1):
                if len(row) < 3:
                    continue
                    
                # Check student ID match
                if row[2] != test_student_id:
                    continue
                
                print(f"Row {i} matches student ID: {row}")
                
                # Parse entry time
                entry_time = parse_entry_time(row[0])
                if not entry_time:
                    print(f"  Failed to parse entry time: {row[0]}")
                    continue
                
                print(f"  Entry time: {entry_time}")
                
                # Check year/month
                if entry_time.year == 2025 and entry_time.month == 7:
                    print(f"  Matches July 2025!")
                    
                    # Check exit time
                    exit_time_str = row[6] if len(row) > 6 else ""
                    if exit_time_str:
                        print(f"  Has exit time: {exit_time_str}")
                        matching_records.append(row)
                    else:
                        print(f"  No exit time, skipping")
                else:
                    print(f"  Not July 2025: {entry_time.year}-{entry_time.month}")
            
            print(f"\nMatching records for July 2025: {len(matching_records)}")
            
            # Now call the actual function
            result = get_monthly_attendance_data(test_student_id, 2025, 7)
            print(f"\nFunction result: {result}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_data_analyzer()