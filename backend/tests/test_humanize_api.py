from types import SimpleNamespace
import os
import unittest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from middleware.auth import get_current_user
from routers.humanize import router
from services.rewrite import ProviderUnavailableError, RewriteError


class HumanizeApiTests(unittest.TestCase):
    def setUp(self):
        env_patch = patch.dict(os.environ, {'LOCAL_DEV_MODE': 'false', 'APP_STORAGE': ''})
        env_patch.start()
        self.addCleanup(env_patch.stop)
        app = FastAPI()
        app.include_router(router, prefix='/humanize')
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id='test-user')
        self.client = TestClient(app)
        self.database = MagicMock()
        self.profile = {'plan': 'free', 'words_used_today': 0, 'words_used_month': 0}
        self.database.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = SimpleNamespace(data=self.profile)
        self.db_patch = patch('routers.humanize.get_supabase', return_value=self.database)
        self.provider_patch = patch('routers.humanize.call_humanizer')
        self.db_patch.start()
        self.provider = self.provider_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.addCleanup(self.provider_patch.stop)
        self.provider.return_value = {'humanized_text': 'Clear prose.', 'provider': 'deepseek',
                                      'model_used': 'test-model', 'mode_name': 'Ghost 1',
                                      'quality': {'warnings': [], 'repair_used': False}}

    def test_invalid_requests_never_reach_database_or_provider(self):
        for request in [{'text': ' '}, {'text': 'word ' * 3001}, {'text': 'a' * 24001},
                        {'text': 'Text', 'mode': 'other'}, {'text': 'Text', 'level': 'other'},
                        {'text': 'Text', 'tone': 'other'}]:
            with self.subTest(request_keys=list(request)):
                self.assertEqual(self.client.post('/humanize', json=request).status_code, 422)
        self.database.table.assert_not_called()
        self.provider.assert_not_called()

    def test_free_users_use_free_mode_and_success_is_saved(self):
        response = self.client.post('/humanize', json={'text': ' Source prose. ', 'mode': 'ghost_2'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.provider.call_args.kwargs['mode'], 'ghost_1')
        self.assertEqual(self.provider.call_args.args[0], 'Source prose.')
        self.database.table.return_value.insert.assert_called_once()
        self.database.table.return_value.update.assert_called_once()
        self.assertEqual(response.json()['quality']['warnings'], [])

    def test_failed_generations_do_not_write_history_or_usage(self):
        for error, status in [(RewriteError('Preservation failed.'), 502),
                              (ProviderUnavailableError('Try again.'), 503)]:
            with self.subTest(status=status):
                self.provider.side_effect = error
                response = self.client.post('/humanize', json={'text': 'Source prose.'})
                self.assertEqual(response.status_code, status)
                self.database.table.return_value.insert.assert_not_called()
                self.database.table.return_value.update.assert_not_called()


if __name__ == '__main__':
    unittest.main()
