"""Check configured database credentials; optionally create app tables."""
import argparse
from dotenv import load_dotenv
load_dotenv()
from services import postgres
import psycopg

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--initialize', action='store_true')
    args = parser.parse_args()
    try:
        with postgres.connect() as db:
            print(db.execute('SELECT current_database() AS database, current_user AS username').fetchone())
        if args.initialize:
            postgres.initialize()
            print('Application tables and development account are ready.')
    except psycopg.OperationalError:
        print('Could not connect. Check PostgreSQL service, database name, host, port, username and password in backend/.env.')
        raise SystemExit(1)
