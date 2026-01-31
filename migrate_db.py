
import sqlite3

DB_PATH = "app.db"

def migrate():
    print(f"Migrating {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if is_admin column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "is_admin" not in columns:
            print("Adding 'is_admin' column to 'users' table...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            print("Column added.")
        else:
            print("'is_admin' column already exists.")
            
        # Update 'admin' user to be admin if exists
        cursor.execute("UPDATE users SET is_admin = 1 WHERE username = 'admin'")
        if cursor.rowcount > 0:
            print("Updated 'admin' user to admin status.")
            
        conn.commit()
        print("Migration complete.")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
