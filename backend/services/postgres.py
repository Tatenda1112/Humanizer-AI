"""PostgreSQL storage and sessions for the single configured development account."""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import psycopg
from psycopg.rows import dict_row

USER_ID = '00000000-0000-4000-8000-000000000001'
COOKIE = 'humanizer_session'


def enabled():
    return os.getenv('APP_STORAGE') == 'postgres'


def connect():
    return psycopg.connect(host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5432')), dbname=os.getenv('POSTGRES_DB', 'humanizer'),
        user=os.getenv('POSTGRES_USER', 'postgres'), password=os.getenv('POSTGRES_PASSWORD'),
        connect_timeout=5, row_factory=dict_row)


def initialize():
    if not os.getenv('APP_LOGIN_EMAIL') or not os.getenv('APP_LOGIN_PASSWORD'):
        raise RuntimeError('APP_LOGIN_EMAIL and APP_LOGIN_PASSWORD must be configured')
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS humanizer_app_users (
            id UUID PRIMARY KEY, email TEXT NOT NULL, words_used BIGINT NOT NULL DEFAULT 0)''')
        db.execute('''CREATE TABLE IF NOT EXISTS humanizer_app_history (
            id UUID PRIMARY KEY, user_id UUID NOT NULL REFERENCES humanizer_app_users(id),
            original_text TEXT NOT NULL, humanized_text TEXT NOT NULL, provider TEXT NOT NULL,
            model_used TEXT, word_count INTEGER NOT NULL, level TEXT NOT NULL, tone TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now())''')
        db.execute('''CREATE TABLE IF NOT EXISTS humanizer_app_sessions (
            token_hash TEXT PRIMARY KEY, user_id UUID NOT NULL REFERENCES humanizer_app_users(id),
            expires_at TIMESTAMPTZ NOT NULL)''')
        db.execute('CREATE INDEX IF NOT EXISTS humanizer_history_user_date ON humanizer_app_history(user_id, created_at DESC)')
        db.execute('''INSERT INTO humanizer_app_users(id,email) VALUES (%s,%s)
            ON CONFLICT(id) DO UPDATE SET email=excluded.email''', (USER_ID, os.environ['APP_LOGIN_EMAIL']))


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def login(email, password):
    email_ok = hmac.compare_digest(email.strip().lower().encode(), os.environ['APP_LOGIN_EMAIL'].lower().encode())
    password_ok = hmac.compare_digest(password.encode(), os.environ['APP_LOGIN_PASSWORD'].encode())
    if not (email_ok and password_ok):
        return None
    token = secrets.token_urlsafe(32)
    with connect() as db:
        db.execute('DELETE FROM humanizer_app_sessions WHERE expires_at <= now()')
        db.execute('INSERT INTO humanizer_app_sessions VALUES (%s,%s,%s)',
                   (digest(token), USER_ID, datetime.now(timezone.utc) + timedelta(hours=12)))
    return token


def authenticate(token):
    if not token:
        return None
    with connect() as db:
        row = db.execute('''SELECT u.id,u.email FROM humanizer_app_users u
            JOIN humanizer_app_sessions s ON s.user_id=u.id
            WHERE s.token_hash=%s AND s.expires_at>now()''', (digest(token),)).fetchone()
    return SimpleNamespace(id=str(row['id']), email=row['email']) if row else None


def logout(token):
    if token:
        with connect() as db:
            db.execute('DELETE FROM humanizer_app_sessions WHERE token_hash=%s', (digest(token),))


def profile(user_id):
    with connect() as db:
        row = db.execute('SELECT * FROM humanizer_app_users WHERE id=%s', (user_id,)).fetchone()
    return dict(id=str(row['id']), email=row['email'], plan='premium', preferred_provider='claude',
        words_used_today=row['words_used'], words_used_month=row['words_used'], daily_limit=None,
        monthly_limit=None, words_remaining_today=None, words_remaining_month=None, subscription_end_date=None)


def record(user_id, text, result, level, tone):
    from uuid import uuid4
    words = len(text.split())
    with connect() as db:
        db.execute('''INSERT INTO humanizer_app_history
            (id,user_id,original_text,humanized_text,provider,model_used,word_count,level,tone)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)''', (uuid4(),user_id,text,result['humanized_text'],
            result['provider'],result.get('model_used'),words,level,tone))
        db.execute('UPDATE humanizer_app_users SET words_used=words_used+%s WHERE id=%s', (words,user_id))


def history(user_id):
    with connect() as db:
        rows = db.execute('SELECT * FROM humanizer_app_history WHERE user_id=%s ORDER BY created_at DESC LIMIT 20', (user_id,)).fetchall()
    return [dict(**row, original_preview=row['original_text'][:50],
                 humanized_preview=row['humanized_text'][:50], ai_score_before=None, ai_score_after=None) for row in rows]


def reset(user_id):
    with connect() as db:
        db.execute('UPDATE humanizer_app_users SET words_used=0 WHERE id=%s', (user_id,))
