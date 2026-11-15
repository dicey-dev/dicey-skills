"""Structural checks, not a substitute for behavioral model evaluations."""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/offload-task'


class SkillContractTests(unittest.TestCase):
    def test_snapshot_is_unchanged_and_complete(self):
        inventory = json.loads((ROOT / 'inventory.json').read_text())['skills']
        self.assertEqual(len(inventory), 29)
        for name, entry in inventory.items():
            folder = ROOT / 'skills' / name
            actual = {str(p.relative_to(folder)) for p in folder.rglob('*')
                      if p.is_file() and '__pycache__' not in p.parts
                      and p.suffix != '.pyc'}
            self.assertEqual(actual, set(entry['files']), name)
            for relative, digest in entry['files'].items():
                self.assertEqual(hashlib.sha256((folder / relative).read_bytes()).hexdigest(),
                                 digest, f'{name}/{relative}')

    def test_frontmatter_and_reference(self):
        text = (SKILL / 'SKILL.md').read_text()
        self.assertTrue(text.startswith('---\nname: offload-task\n'))
        self.assertIn('\ndescription: >-\n', text)
        self.assertIn('(references/performance.md)', text)
        self.assertTrue((SKILL / 'references/performance.md').is_file())
        self.assertLess(len(text.splitlines()), 500)

    def test_initial_history_is_empty(self):
        text = (SKILL / 'SKILL.md').read_text()
        self.assertEqual(text.count('## Historical performance'), 1)
        self.assertEqual(text.split('## Historical performance', 1)[1].strip(), '')

    def test_eval_folders_have_prompts_and_graders(self):
        cases = sorted((SKILL / 'evals').iterdir())
        self.assertEqual(len(cases), 2)
        for case in cases:
            self.assertIn('Dry-run only:', (case / 'prompt.md').read_text())
            self.assertIn('schema_version: "1.1"', (case / 'case.yaml').read_text())
            self.assertIn(f'name: {case.name}\n', (case / 'case.yaml').read_text())
            graders = list((case / 'graders').glob('*.md'))
            self.assertEqual(len(graders), 2)
            for grader in graders:
                self.assertTrue(grader.read_text().startswith('---\ntype: llm\nfocus: trace\nweight: 1\n---\n'))


if __name__ == '__main__':
    unittest.main()
