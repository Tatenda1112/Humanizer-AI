import os
import unittest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers import humanize, user, stripe_router
from services.rewrite import RewriteError


class LocalDevTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {'LOCAL_DEV_MODE': 'true', 'APP_STORAGE': '', 'SUPABASE_URL': '', 'SUPABASE_SERVICE_KEY': ''})
        env.start()
        self.addCleanup(env.stop)
        for target in ['middleware.auth.get_supabase', 'routers.humanize.get_supabase', 'routers.user.get_supabase', 'routers.stripe_router.get_supabase']:
            mock = patch(target, side_effect=AssertionError('Local mode must not access Supabase'))
            mock.start()
            self.addCleanup(mock.stop)
        app = FastAPI()
        app.include_router(humanize.router, prefix='/humanize')
        app.include_router(user.router, prefix='/user')
        app.include_router(stripe_router.router, prefix='/stripe')
        self.client = TestClient(app)

    def test_no_account_editor_flow_for_both_modes(self):
        self.assertEqual(self.client.get('/user/me').json()['plan'], 'premium')
        before = self.client.get('/user/me').json()['words_used_today']
        for mode in ['ghost_1', 'ghost_2']:
            result = dict(humanized_text='Clear prose.', provider='test', mode_name=mode,
                          quality={'warnings': [], 'repair_used': False})
            with patch('routers.humanize.call_humanizer', return_value=result) as generate:
                response = self.client.post('/humanize', json={'text': 'Source text.', 'mode': mode})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(generate.call_args.kwargs['mode'], mode)
                self.assertTrue(generate.call_args.args[3])
        self.assertEqual(self.client.get('/user/me').json()['words_used_today'], before + 4)
        self.assertEqual(self.client.get('/user/history').json()[0]['original_text'], 'Source text.')

    def test_failed_rewrite_does_not_change_local_usage(self):
        before = self.client.get('/user/me').json()['words_used_today']
        with patch('routers.humanize.call_humanizer', side_effect=RewriteError('Invalid rewrite')):
            self.assertEqual(self.client.post('/humanize', json={'text': 'Source text.'}).status_code, 502)
        self.assertEqual(self.client.get('/user/me').json()['words_used_today'], before)

    def test_billing_disabled_and_normal_mode_still_requires_auth(self):
        self.assertEqual(self.client.post('/stripe/checkout', json={'plan': 'premium'}).status_code, 503)
        with patch.dict(os.environ, {'LOCAL_DEV_MODE': 'false'}):
            self.assertEqual(self.client.get('/user/me').status_code, 401)


if __name__ == '__main__':
    unittest.main()
