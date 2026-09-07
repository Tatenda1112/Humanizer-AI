"""Quick Supabase connection test — run with: python test_supabase.py"""
import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

print(f"URL  : {url}")
print(f"KEY  : {key[:20]}..." if key else "KEY  : NOT SET")
print()

try:
    from supabase import create_client
    client = create_client(url, key)
    print("[OK] Supabase client created — credentials valid")
except Exception as e:
    print(f"[FAIL] Could not create client: {e}")
    sys.exit(1)

# Test auth admin
try:
    users = client.auth.admin.list_users()
    print(f"[OK] Auth endpoint reachable — total users: {len(users)}")
except Exception as e:
    print(f"[FAIL] Auth endpoint: {e}")

# Test DB tables
for table in ("profiles", "humanizations", "subscriptions"):
    try:
        res = client.table(table).select("id").limit(1).execute()
        print(f"[OK] Table '{table}' exists — rows: {len(res.data)}")
    except Exception as e:
        msg = str(e)
        if "schema cache" in msg or "PGRST205" in msg:
            print(f"[MISSING] Table '{table}' not found — run supabase/schema.sql first")
        else:
            print(f"[FAIL] Table '{table}': {e}")

print()
print("=== CONNECTION TEST DONE ===")
print("If any tables are [MISSING]: open Supabase dashboard -> SQL Editor -> paste supabase/schema.sql -> Run")
