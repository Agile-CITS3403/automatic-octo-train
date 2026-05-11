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

    # This migration covers the changes in commit 9f4441c (adding description to Picture table)
    columns_to_add = [
        ('picture', 'description', 'TEXT')
    ]

    for table_name, col_name, col_def in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}")
            print(f"Added column {col_name} to table {table_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {col_name} already exists in table {table_name}.")
            elif "no such table" in str(e):
                print(f"Table {table_name} does not exist yet. It will be created by the app.")
            else:
                print(f"Error adding column {col_name} to {table_name}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
