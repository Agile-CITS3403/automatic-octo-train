from .migrate_users import migrate as migrate_users
from .migrate_pictures import migrate as migrate_pictures
from .migrate_interests import migrate as migrate_interests
from .migrate_tags import migrate as migrate_tags

def run_all_migrations():
    print("Running database migrations...")
    migrate_users()
    migrate_pictures()
    migrate_interests()
    migrate_tags()
    print("All migrations checked.")
