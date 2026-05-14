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
            "CREATE TABLE IF NOT EXISTS picture_interest (picture_id INTEGER NOT NULL, interest_id INTEGER NOT NULL, PRIMARY KEY (picture_id, interest_id), FOREIGN KEY(picture_id) REFERENCES picture(id), FOREIGN KEY(interest_id) REFERENCES interest(id))"
        )
        print('Ensured picture_interest table exists.')
    except sqlite3.OperationalError as e:
        print(f"Error creating picture_interest table: {e}")

    conn.commit()
    conn.close()
    print('Migration for picture tags complete.')

if __name__ == '__main__':
    migrate()
