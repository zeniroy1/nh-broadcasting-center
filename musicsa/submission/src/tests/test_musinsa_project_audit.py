import unittest

from scripts.musinsa_project_audit import build_project_audit, validate_project_audit


class MusinsaProjectAuditTest(unittest.TestCase):
    def test_project_audit_is_valid(self):
        self.assertEqual(validate_project_audit(), [])

    def test_audit_reports_all_required_check_groups(self):
        audit = build_project_audit()
        keys = {check["key"] for check in audit["checks"]}

        self.assertEqual(audit["status"], "pass")
        self.assertIn("plugin_structure", keys)
        self.assertIn("step_documents", keys)
        self.assertIn("step_reports", keys)
        self.assertIn("boundary_language", keys)
        self.assertIn("visual_decisions", keys)

    def test_audit_keeps_roadmap_step_counts(self):
        audit = build_project_audit()

        self.assertEqual(audit["completed_implementation_steps"], 9)
        self.assertEqual(audit["total_roadmap_steps"], 10)

    def test_audit_blocks_automatic_next_step(self):
        audit = build_project_audit()

        self.assertIn("사용자 승인 전", audit["next_step_policy"])


if __name__ == "__main__":
    unittest.main()
