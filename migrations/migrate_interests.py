import sqlite3
import os

def migrate():
    db_path = 'instance/users.db'
    if not os.path.exists(db_path):
        db_path = 'users.db'
        if not os.path.exists(db_path):
            print('Database not found.')
            return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS interest (id INTEGER PRIMARY KEY, name VARCHAR(80) UNIQUE NOT NULL)"
        )
        print('Ensured interest table exists.')
    except sqlite3.OperationalError as e:
        print(f"Error creating interest table: {e}")

    try:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS user_interest (user_id INTEGER NOT NULL, interest_id INTEGER NOT NULL, PRIMARY KEY (user_id, interest_id), FOREIGN KEY(user_id) REFERENCES user(id), FOREIGN KEY(interest_id) REFERENCES interest(id))"
        )
        print('Ensured user_interest table exists.')
    except sqlite3.OperationalError as e:
        print(f"Error creating user_interest table: {e}")

    conn.commit()
    conn.close()
    print('Migration complete.')

if __name__ == '__main__':
    migrate()
