import json
from pathlib import Path
import unittest
from services.rewrite import Completion, RewriteError, assess, clean_output, rewrite, source_overlap


SOURCE = ('Institutions increasingly use digital systems to improve their daily operations. '
          'The value of these systems depends on technical capacity and staff training '
          '(Moyo, 2023). Limited resources may prevent smaller institutions from adopting them.')
GOOD = ('Digital systems are becoming part of everyday institutional work. Whether they help '
        'depends on the available technical capacity and the training staff receive '
        '(Moyo, 2023). Smaller institutions may lack the resources needed to adopt them.')


class RewriteTests(unittest.TestCase):
    def test_permission_cannot_become_new_obligation(self):
        source = 'The method allowed the researcher to remain detached and use numerical data.'
        for replacement in ['required', 'requires']:
            self.assertTrue(assess(source, source.replace('allowed', replacement), 'medium')[0])
        self.assertFalse(assess(source, source.replace('allowed', 'enabled'), 'medium')[0])

    def test_repeated_acronym_can_become_pronoun(self):
        errors, _ = assess('AI helps analysts. AI can also help attackers.', 'AI helps analysts. It can also help attackers.', 'medium')
        self.assertFalse(errors)

    def test_reviewed_near_copy_is_returned_with_explicit_warning(self):
        replies = iter([Completion(SOURCE), Completion('{"issues": []}')] * 2)
        result = rewrite(SOURCE, 'aggressive', 'academic', lambda *args: next(replies), review=True)
        self.assertEqual(result['humanized_text'], SOURCE)
        self.assertTrue(any('requested level of rewriting was not achieved' in w for w in result['quality']['warnings']))
        self.assertEqual(result['usage']['generation_calls'], 4)

    def test_plan_drives_writer_but_review_keeps_original(self):
        source = ' '.join([SOURCE] * 3)
        output = ' '.join([GOOD] * 3)
        plan = {'paragraphs': [{'claims': [SOURCE] * 3}], 'terms': ['technical capacity']}
        replies = iter([Completion(json.dumps(plan)), Completion(output), Completion('{"issues": []}')])
        calls = []
        def generate(prompt, budget):
            calls.append(json.loads(prompt))
            return next(replies)
        result = rewrite(source, 'medium', 'academic', generate, review=True, planning=True)
        self.assertEqual([c['task'] for c in calls], ['plan', 'rewrite', 'review'])
        self.assertNotIn('source', calls[1])
        self.assertEqual(calls[1]['content_plan'], plan)
        self.assertEqual(calls[2]['source'], source)
        self.assertEqual(result['humanized_text'], output)

    def test_plan_cannot_invent_protected_terms(self):
        plan = {'paragraphs': [{'claims': [SOURCE] * 3}], 'terms': ['invented technical term', 'technical capacity']}
        calls = []
        def generate(prompt, budget):
            payload = json.loads(prompt)
            calls.append(payload)
            return Completion(json.dumps(plan) if payload['task'] == 'plan' else ' '.join([GOOD] * 3))
        rewrite(' '.join([SOURCE] * 3), 'medium', 'academic', generate, planning=True)
        self.assertEqual(calls[1]['content_plan']['terms'], ['technical capacity'])

    def test_meaning_review_detects_and_repairs_changed_claim(self):
        source = SOURCE + ' The method allowed researchers to work independently, but independent work was not required.'
        good = GOOD + ' The method made independent work possible for researchers, but it was not mandatory.'
        bad = good.replace('made independent work possible for researchers, but it was not mandatory', 'required researchers to work independently')
        replies = iter([Completion(bad), Completion('{"issues": ["Preserve permission rather than imposing an obligation."]}'),
                        Completion(good), Completion('{"issues": []}')])
        calls = []
        def generate(prompt, budget):
            calls.append(json.loads(prompt))
            return next(replies)
        result = rewrite(source, 'light', 'academic', generate, review=True)
        self.assertEqual([c['task'] for c in calls], ['rewrite', 'review', 'rewrite', 'review'])
        self.assertEqual(result['humanized_text'], good)
        self.assertTrue(result['quality']['meaning_reviewed'])
        self.assertEqual(result['usage']['generation_calls'], 4)

    def test_malformed_review_does_not_silently_pass(self):
        source = SOURCE + ' The research also considered practical constraints on access to equipment and training.'
        output = GOOD + ' Access to equipment and training was also considered in terms of practical constraints.'
        replies = iter([Completion(output), Completion('Everything looks fine.')])
        with self.assertRaises(RewriteError):
            rewrite(source, 'light', 'academic', lambda *args: next(replies), review=True)

    def test_repeated_meaning_failure_rejects_output(self):
        source = SOURCE + ' The research also considered practical constraints on access to equipment and training.'
        output = GOOD + ' Access to equipment and training was also considered in terms of practical constraints.'
        replies = iter([Completion(output), Completion('{"issues": ["A claim was altered."]}')] * 3)
        with self.assertRaises(RewriteError):
            rewrite(source, 'light', 'academic', lambda *args: next(replies), review=True)

    def test_definition_keeps_its_opening_concept(self):
        original = 'A research philosophy refers to beliefs about knowledge and research.'
        moved = 'Beliefs about knowledge and research constitute a research philosophy.'
        kept = 'A research philosophy concerns beliefs about knowledge and research.'
        self.assertTrue(any('opening term' in error for error in assess(original, moved, 'aggressive')[0]))
        self.assertFalse(assess(original, kept, 'aggressive')[0])

    def test_reported_superficial_rewrite_is_flagged(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures/research_philosophy.json').read_text(encoding='utf-8'))
        errors, warnings = assess(fixture['source'], fixture['previous_output'], 'medium')
        self.assertFalse(errors)
        self.assertTrue(any('closely follows' in warning for warning in warnings))
        self.assertFalse(assess(fixture['source'], fixture['previous_output'], 'light')[1])

    def test_moving_copied_sentences_still_counts_as_resemblance(self):
        sentences = ['Researchers collected information through a questionnaire that was distributed to participants',
                     'The study examined how transport choices differed between residents of several districts',
                     'All participants answered the same questions to support consistent comparisons between groups']
        source = '. '.join(sentences) + '.'
        output = '. '.join(reversed(sentences)) + '.'
        self.assertEqual(source_overlap(source, output)['sentence_resemblance'], 1.0)
        self.assertTrue(assess(source, output, 'medium')[1])

    def test_citation_text_does_not_inflate_overlap(self):
        source = 'Weather changes rapidly (Saunders, Lewis, & Thornhill, 2019).'
        output = 'Rain arrived yesterday (Saunders, Lewis, & Thornhill, 2019).'
        self.assertEqual(source_overlap(source, output)['word_sequence'], 0.0)

    def test_cleanup_does_not_corrupt_citations_decimals_or_names(self):
        text = '  (Smith, Jones and Brown, 2024); USD 4.2 million, Zimbabwe; 5–10%…  '
        self.assertEqual(clean_output(text), text.strip())

    def test_valid_first_pass_costs_one_generation(self):
        calls = []
        def generate(prompt, budget):
            calls.append((json.loads(prompt), budget))
            return Completion(GOOD, input_tokens=100, output_tokens=50)
        result = rewrite(SOURCE, 'medium', 'academic', generate)
        self.assertEqual(result['humanized_text'], GOOD)
        self.assertEqual(result['usage'], {'input_tokens': 100, 'output_tokens': 50, 'generation_calls': 1})
        self.assertEqual(calls[0][0]['source'], SOURCE)

    def test_superficial_rewrite_retry_starts_again_without_old_draft(self):
        calls = []
        def generate(prompt, budget):
            calls.append(json.loads(prompt))
            return Completion(SOURCE if len(calls) == 1 else GOOD)
        rewrite(SOURCE, 'medium', 'academic', generate)
        self.assertEqual(len(calls), 2)
        self.assertNotIn('draft', calls[1])
        self.assertEqual(calls[1]['source'], SOURCE)
        self.assertIn('revision_strategy', calls[1])

    def test_repairs_changed_citation_against_original(self):
        calls = []
        def generate(prompt, budget):
            calls.append(json.loads(prompt))
            return Completion(GOOD.replace('2023', '2024') if len(calls) == 1 else GOOD)
        result = rewrite(SOURCE, 'medium', 'academic', generate)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1]['source'], SOURCE)
        self.assertIn('Preserve all citations', ' '.join(calls[1]['repair_instructions']))
        self.assertTrue(result['quality']['repair_used'])

    def test_repeated_invalid_result_is_not_returned(self):
        for completion in [Completion(''), Completion(GOOD, complete=False), Completion(GOOD.replace('2023', '2024'))]:
            with self.subTest(completion=completion):
                with self.assertRaises(RewriteError):
                    rewrite(SOURCE, 'medium', 'academic', lambda *args: completion)

    def test_truncation_retry_increases_budget(self):
        budgets = []
        def generate(prompt, budget):
            budgets.append(budget)
            return Completion(GOOD, complete=len(budgets) == 2)
        rewrite(SOURCE, 'medium', 'academic', generate)
        self.assertGreater(budgets[1], budgets[0])

    def test_never_replace_valid_draft_with_invalid_repair(self):
        responses = iter([Completion(SOURCE), Completion(GOOD.replace('2023', '2024'))])
        result = rewrite(SOURCE, 'aggressive', 'academic', lambda *args: next(responses))
        self.assertEqual(result['humanized_text'], SOURCE)
        self.assertTrue(result['quality']['warnings'])

    def test_preservation_checks_detect_number_citation_acronym_changes(self):
        text = 'AI increased by 5.3% (Smith, 2024) [1–3]. AI did not reach 10%.'
        for changed in [text.replace('5.3%', '5.4%'), text.replace('Smith', 'Jones'),
                        text.replace('AI', 'ML', 1), text.replace('[1–3]', '[1]'), text + ' 10%']:
            with self.subTest(changed=changed):
                self.assertTrue(assess(text, changed, 'medium')[0])

    def test_paragraph_loss_and_near_copy_are_flagged(self):
        self.assertTrue(assess(SOURCE, SOURCE, 'aggressive')[1])
        self.assertIn('Preserve the source paragraph structure.', assess('First.\n\nSecond.', 'First. Second.', 'light')[1])

    def test_invalid_input_does_not_call_provider(self):
        def generate(*args):
            self.fail('Provider must not be called')
        for text, level, tone in [('', 'medium', 'academic'), ('word ' * 3001, 'medium', 'academic'),
                                  ('a' * 24001, 'light', 'academic'), (SOURCE, 'bad', 'academic'),
                                  (SOURCE, 'medium', 'bad')]:
            with self.subTest(level=level, tone=tone):
                with self.assertRaises(ValueError):
                    rewrite(text, level, tone, generate)

    def test_supplied_dissertation_fixture_rejects_citation_damage(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures/academic_cybersecurity.json').read_text(encoding='utf-8'))
        source = fixture['source']
        changed = source.replace('(Achuthan et al., 2024; Ofusori et al., 2024)', '(Achuthan, 2024)')
        self.assertTrue(assess(source, changed, fixture['level'])[0])
        self.assertFalse(assess(source, source, 'light')[0])


if __name__ == '__main__':
    unittest.main()
