from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/create-prd'


class CreatePrdRevisionContractTests(unittest.TestCase):
    def test_entry_routes_revisions_without_restarting_interview(self):
        text = (SKILL / 'SKILL.md').read_text()
        self.assertIn('references/prd-revision-rules.md', text)
        self.assertIn('do not restart the creation interview', text)

    def test_revision_rules_cover_evidence_format_and_readback(self):
        path = SKILL / 'references/prd-revision-rules.md'
        self.assertTrue(path.is_file())
        text = path.read_text()
        for marker in ('确认事实', '建议方案', '待决策', 'fix all',
                       '&&', '||', '同一输入', '回读', '版本', '原有格式'):
            self.assertIn(marker, text)

    def test_lark_format_is_delegated_not_hardcoded(self):
        text = (SKILL / 'SKILL.md').read_text()
        for obsolete in ('<lark-table>', '<grid cols=',
                         '<whiteboard type="blank">', '--markdown "'):
            self.assertNotIn(obsolete, text)

    def test_validation_checks_policy_preservation(self):
        text = (SKILL / 'references/prd-validation-checklist.md').read_text()
        self.assertIn('prd-revision-rules.md', text)
        self.assertIn('新增业务规则', text)


if __name__ == '__main__':
    unittest.main()
