#!/usr/bin/env python3
"""
Database Migration: Add detected_category column
Run this once to update the database schema
"""
import sqlite3
import sys

DB_PATH = "inventory_scanner.db"

def column_exists(cursor, table, column):
    """Check if column exists in table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def migrate():
    """Add detected_category column to scan_records"""
    print(f"🔍 Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        if column_exists(cursor, "scan_records", "detected_category"):
            print("✓ Column 'detected_category' already exists. Migration not needed.")
            return True
        
        # Add the column
        print("🔧 Adding column 'detected_category' to scan_records...")
        cursor.execute("""
            ALTER TABLE scan_records 
            ADD COLUMN detected_category VARCHAR(50);
        """)
        conn.commit()
        
        print("✅ Migration completed successfully!")
        print("   Column 'detected_category' added to 'scan_records' table")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)