"""
Manually add remaining_numbers column to games table.
Run this ONCE before starting the backend.
"""
import sqlite3
import os

# Path to your database
DB_PATH = "bingo.db"

def add_column():
    """Add remaining_numbers column to games table"""
    print("="*60)
    print("Adding remaining_numbers column to games table")
    print("="*60)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        print("Please run the backend first to create the database")
        return
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(games)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'remaining_numbers' in columns:
            print("✅ Column 'remaining_numbers' already exists!")
            return
        
        print("📝 Adding column 'remaining_numbers' to games table...")
        
        # Add the column (SQLite doesn't support JSON type, use TEXT)
        cursor.execute("ALTER TABLE games ADD COLUMN remaining_numbers TEXT DEFAULT '[]'")
        
        conn.commit()
        print("✅ Column added successfully!")
        
        # Verify
        cursor.execute("PRAGMA table_info(games)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'remaining_numbers' in columns:
            print("✅ Verified: Column exists in database")
        else:
            print("❌ Error: Column not found after adding")
        
    except sqlite3.OperationalError as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()
    
    print("\n" + "="*60)
    print("✅ DONE! Now you can:")
    print("1. Run: python migrate_add_remaining_numbers.py")
    print("2. Start backend: python -m uvicorn app.main:app --reload")
    print("="*60)

if __name__ == "__main__":
    add_column()
