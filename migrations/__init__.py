from .migrate_users import migrate as migrate_users
from .migrate_pictures import migrate as migrate_pictures

def run_all_migrations():
    print("Running database migrations...")
    migrate_users()
    migrate_pictures()
    print("All migrations checked.")
