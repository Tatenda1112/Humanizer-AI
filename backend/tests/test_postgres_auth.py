import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers import auth, humanize, user
from services import postgres


class PostgresTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {'APP_STORAGE': 'postgres', 'LOCAL_DEV_MODE': 'false',
                                     'APP_LOGIN_EMAIL': 'test@example.com', 'APP_LOGIN_PASSWORD': 'test-secret'})
        env.start()
        self.addCleanup(env.stop)
        app = FastAPI()
        app.include_router(auth.router, prefix='/auth')
        app.include_router(humanize.router, prefix='/humanize')
        app.include_router(user.router, prefix='/user')
        self.client = TestClient(app)

    def test_bad_password_does_not_connect(self):
        with patch('services.postgres.connect') as connect:
            response = self.client.post('/auth/login', json={'email': 'test@example.com', 'password': 'incorrect'})
            self.assertEqual(response.status_code, 401)
            connect.assert_not_called()

    def test_login_sets_http_only_cookie_and_hashes_stored_token(self):
        with patch('services.postgres.connect') as connect:
            response = self.client.post('/auth/login', json={'email': 'test@example.com', 'password': 'test-secret'})
            self.assertEqual(response.status_code, 200)
            self.assertIn('HttpOnly', response.headers['set-cookie'])
            token = response.cookies[postgres.COOKIE]
            db = connect.return_value.__enter__.return_value
            stored = db.execute.call_args.args[1][0]
            self.assertEqual(stored, postgres.digest(token))
            self.assertNotEqual(stored, token)

    def test_unauthenticated_requests_are_denied(self):
        self.assertEqual(self.client.get('/user/me').status_code, 401)
        self.assertEqual(self.client.post('/humanize', json={'text':'Sample text'}).status_code, 401)

    def test_logout_removes_session_and_cookie(self):
        self.client.cookies.set(postgres.COOKIE, 'test-session')
        with patch('services.postgres.logout') as logout:
            response = self.client.post('/auth/logout')
            logout.assert_called_once_with('test-session')
            self.assertEqual(response.status_code, 200)
            self.assertIn('Max-Age=0', response.headers['set-cookie'])

    def test_authenticated_rewrite_uses_database_not_supabase(self):
        account = SimpleNamespace(id=postgres.USER_ID, email='test@example.com')
        result = dict(humanized_text='Clear prose.', provider='claude', mode_name='Ghost 2', quality={})
        with patch('services.postgres.authenticate', return_value=account), \
             patch('routers.humanize.call_humanizer', return_value=result), \
             patch('services.postgres.record') as record, \
             patch('routers.humanize.get_supabase') as supabase:
            response = self.client.post('/humanize', json={'text':'Original text'})
            self.assertEqual(response.status_code, 200)
            record.assert_called_once_with(postgres.USER_ID, 'Original text', result, 'medium', 'professional')
            supabase.assert_not_called()

    def test_history_and_usage_write_share_transaction(self):
        result = dict(humanized_text='New text', provider='test', model_used='test-model')
        with patch('services.postgres.connect') as connect:
            postgres.record(postgres.USER_ID, 'Original text', result, 'medium', 'academic')
            connect.assert_called_once()
            db = connect.return_value.__enter__.return_value
            self.assertEqual(db.execute.call_count, 2)
            self.assertIn('INSERT INTO humanizer_app_history', db.execute.call_args_list[0].args[0])
            self.assertIn('words_used=words_used+', db.execute.call_args_list[1].args[0])
            connect.return_value.__exit__.assert_called_once_with(None, None, None)


if __name__ == '__main__':
    unittest.main()
