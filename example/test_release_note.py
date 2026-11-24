import unittest

from release_note import render_release_note


class ReleaseNoteTest(unittest.TestCase):
    def test_writes_heading_and_preserves_bullet_order(self):
        self.assertEqual(render_release_note("v0.2.0", ["新增导出", "修正标题"]),
                         "# v0.2.0\n\n- 新增导出\n- 修正标题\n")

    def test_trims_inputs_and_ignores_empty_changes(self):
        self.assertEqual(render_release_note(" v0.2.0 ", ["  ", " 修正标题 "]),
                         "# v0.2.0\n\n- 修正标题\n")

    def test_requires_at_least_one_nonempty_change(self):
        for changes in ([], [" ", "\t"]):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                render_release_note("v0.2.0", changes)

    def test_requires_nonempty_version(self):
        with self.assertRaises(ValueError):
            render_release_note("  ", ["新增导出"])


if __name__ == "__main__":
    unittest.main()
