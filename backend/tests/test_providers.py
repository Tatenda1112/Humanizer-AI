import os
from types import SimpleNamespace as Obj
import unittest
from unittest.mock import patch
from services.ai_provider import call_humanizer
from services.claude import call_claude_humanizer
from services.deepseek_service import call_deepseek_humanizer
from services.rewrite import ProviderUnavailableError


class ProviderTests(unittest.TestCase):
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-only'})
    @patch('anthropic.resources.messages.Messages.create', autospec=True)
    def test_claude_request_matches_installed_sdk_signature(self, create):
        create.return_value = Obj(content=[Obj(type='text', text='Clear prose.')],
                                  stop_reason='end_turn', usage=Obj(input_tokens=20, output_tokens=5))
        result = call_claude_humanizer('Readable writing.', 'medium', 'academic', True)
        self.assertEqual(result['humanized_text'], 'Clear prose.')
        create.assert_called_once()

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-only'}, clear=True)
    @patch('services.claude.anthropic.Anthropic')
    def test_claude_collects_text_blocks_and_uses_one_good_pass(self, factory):
        client = factory.return_value.__enter__.return_value
        client.messages.create.return_value = Obj(
            content=[Obj(type='text', text='Clear '), Obj(type='text', text='prose.')],
            stop_reason='end_turn', usage=Obj(input_tokens=20, output_tokens=5))
        result = call_claude_humanizer('Readable writing.', 'medium', 'academic', True)
        self.assertEqual(result['humanized_text'], 'Clear prose.')
        client.messages.create.assert_called_once()
        self.assertEqual(result['usage']['output_tokens'], 5)

    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-only'}, clear=True)
    @patch('services.deepseek_service.OpenAI')
    def test_deepseek_disables_thinking_and_reports_usage(self, factory):
        client = factory.return_value.__enter__.return_value
        client.chat.completions.create.return_value = Obj(
            choices=[Obj(message=Obj(content='Clear prose.'), finish_reason='stop')],
            usage=Obj(prompt_tokens=20, completion_tokens=5))
        result = call_deepseek_humanizer('Readable writing.', 'medium', 'academic', False)
        kwargs = client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs['extra_body']['thinking']['type'], 'disabled')
        self.assertEqual(kwargs['model'], 'deepseek-v4-flash')
        self.assertEqual(result['usage']['generation_calls'], 1)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_free_provider_never_silently_calls_paid_provider(self):
        with patch('services.claude.call_claude_humanizer') as claude:
            with self.assertRaises(ProviderUnavailableError):
                call_humanizer('Text', 'medium', 'academic', False, 'auto')
            claude.assert_not_called()


if __name__ == '__main__':
    unittest.main()
