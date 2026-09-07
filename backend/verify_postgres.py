"""Opt-in real database integration check using an isolated, temporary test account."""
import os
import secrets
from uuid import uuid4
from unittest.mock import patch
from dotenv import load_dotenv
load_dotenv()
from fastapi.testclient import TestClient
from main import app
from services import postgres


def main():
    test_id = str(uuid4())
    credentials = {'email': 'integration-test@localhost', 'password': secrets.token_urlsafe(24)}
    try:
        with patch.object(postgres, 'USER_ID', test_id), patch.dict(os.environ, {
            'APP_STORAGE': 'postgres', 'APP_LOGIN_EMAIL': credentials['email'],
            'APP_LOGIN_PASSWORD': credentials['password']}), TestClient(app) as client:
            assert client.get('/user/me').status_code == 401
            assert client.post('/auth/login', json={**credentials, 'password': 'incorrect'}).status_code == 401
            assert client.post('/auth/login', json=credentials).status_code == 200
            assert client.get('/user/me').json()['id'] == test_id
            result = dict(humanized_text='Database storage works.', provider='test', model_used='test',
                          mode_name='Ghost 2', quality={'warnings': [], 'repair_used': False})
            with patch('routers.humanize.call_humanizer', return_value=result):
                response = client.post('/humanize', json={'text': 'Test database persistence.', 'mode': 'ghost_2'})
                assert response.status_code == 200, response.status_code
            assert client.get('/user/me').json()['words_used_today'] == 3
            assert client.get('/user/history').json()[0]['humanized_text'] == result['humanized_text']
            # Read committed data through a separate connection.
            with postgres.connect() as db:
                row = db.execute('SELECT count(*) AS count FROM humanizer_app_history WHERE user_id=%s', (test_id,)).fetchone()
                assert row['count'] == 1
            assert client.post('/auth/logout').status_code == 200
            assert client.get('/user/me').status_code == 401
            print('PASS: login, rejected password, authenticated rewrite, persistent history, usage and logout.')
    finally:
        # Only remove rows owned by the UUID created for this test.
        with postgres.connect() as db:
            db.execute('DELETE FROM humanizer_app_sessions WHERE user_id=%s', (test_id,))
            db.execute('DELETE FROM humanizer_app_history WHERE user_id=%s', (test_id,))
            db.execute('DELETE FROM humanizer_app_users WHERE id=%s', (test_id,))


if __name__ == '__main__':
    main()
