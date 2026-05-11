import sqlite3
import os

def migrate():
    db_path = 'instance/users.db'
    if not os.path.exists(db_path):
        # Check if it's in the root directory
        db_path = 'users.db'
        if not os.path.exists(db_path):
            print("Database not found.")
            return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    columns_to_add = [
        ('owned_pictures_ids', "TEXT DEFAULT '[]'"),
        ('profile_description', "TEXT DEFAULT ''"),
        ('likes', "TEXT DEFAULT '[]'")
    ]

    for col_name, col_def in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_def}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding column {col_name}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
