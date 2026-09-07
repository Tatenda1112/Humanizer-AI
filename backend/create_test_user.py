"""Creates a test user in Supabase and inserts their profile."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
client = create_client(url, key)

EMAIL    = "tatendatatenda1112@gmail.com"
PASSWORD = "Tatendamukono1112@"

print(f"Creating user: {EMAIL}")
print()

# 1. Create auth user
try:
    res = client.auth.admin.create_user({
        "email": EMAIL,
        "password": PASSWORD,
        "email_confirm": True,   # skip confirmation email for testing
    })
    user = res.user
    print(f"[OK] Auth user created — ID: {user.id}")
except Exception as e:
    msg = str(e)
    if "already been registered" in msg or "already exists" in msg:
        # User exists — fetch their ID instead
        users = client.auth.admin.list_users()
        user = next((u for u in users if u.email == EMAIL), None)
        if user:
            print(f"[OK] User already exists — ID: {user.id}")
        else:
            print(f"[FAIL] Could not find existing user: {e}")
            sys.exit(1)
    else:
        print(f"[FAIL] Auth error: {e}")
        sys.exit(1)

# 2. Upsert profile (in case trigger didn't fire yet)
try:
    client.table("profiles").upsert({
        "id": user.id,
        "email": EMAIL,
        "plan": "free",
        "preferred_provider": "claude",
        "words_used_today": 0,
        "words_used_month": 0,
    }).execute()
    print("[OK] Profile created in profiles table")
except Exception as e:
    msg = str(e)
    if "schema cache" in msg or "PGRST205" in msg:
        print("[MISSING] profiles table not found — run supabase/schema.sql first!")
    else:
        print(f"[WARN] Profile upsert: {e}")

print()
print("=== DONE ===")
print(f"Email   : {EMAIL}")
print(f"Password: {PASSWORD}")
print("Go to http://localhost:3000/login and sign in!")
