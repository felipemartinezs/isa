#!/usr/bin/env python3
"""
Database Migration: Make category nullable in scan_sessions for INVENTORY mode
"""
import sqlite3
import sys

DB_PATH = "inventory_scanner.db"

def migrate():
    """Make category column nullable in scan_sessions"""
    print(f"🔍 Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # SQLite doesn't support ALTER COLUMN directly
        # We need to recreate the table
        print("🔧 Creating backup of scan_sessions...")
        
        # Create new table with nullable category
        cursor.execute("""
            CREATE TABLE scan_sessions_new (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                mode VARCHAR(50) NOT NULL,
                category VARCHAR(50),  -- ← NULLABLE AHORA
                bom_id INTEGER,
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(bom_id) REFERENCES boms(id)
            );
        """)
        
        # Copy data
        print("📋 Copying data...")
        cursor.execute("""
            INSERT INTO scan_sessions_new 
            SELECT * FROM scan_sessions;
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE scan_sessions;")
        
        # Rename new table
        cursor.execute("ALTER TABLE scan_sessions_new RENAME TO scan_sessions;")
        
        # Update INVENTORY sessions to have NULL category
        print("🔄 Setting category=NULL for INVENTORY mode sessions...")
        cursor.execute("""
            UPDATE scan_sessions 
            SET category = NULL 
            WHERE mode = 'INVENTORY';
        """)
        
        conn.commit()
        
        print("✅ Migration completed successfully!")
        print("   - scan_sessions.category is now nullable")
        print("   - INVENTORY sessions have category=NULL")
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