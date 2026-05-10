import unittest

from recent_code_languages import (
    aggregate_recent_code_language_files,
    build_recent_code_language_payload,
    render_recent_code_language_svg,
)


class RecentCodeLanguageTests(unittest.TestCase):
    def test_filters_markup_and_counts_changed_code_lines(self):
        files = [
            {"filename": "app/src/main/kotlin/MainActivity.kt", "additions": 40, "deletions": 5},
            {"filename": "services/worker.py", "additions": 20, "deletions": 3},
            {"filename": "web/index.html", "additions": 900, "deletions": 100},
            {"filename": "web/styles.css", "additions": 80, "deletions": 10},
            {"filename": "README.md", "additions": 50, "deletions": 0},
            {"filename": "generated/report.py", "additions": 700, "deletions": 100},
            {"filename": "package-lock.json", "additions": 400, "deletions": 200},
            {"filename": "assets/logo.svg", "additions": 12, "deletions": 8},
        ]

        result = aggregate_recent_code_language_files(files)

        self.assertEqual(result.languages["Kotlin"].changes, 45)
        self.assertEqual(result.languages["Python"].changes, 23)
        self.assertNotIn("HTML", result.languages)
        self.assertNotIn("CSS", result.languages)
        self.assertNotIn("Markdown", result.languages)
        self.assertEqual(result.excluded_changes, 2560)

    def test_payload_and_preview_svg_exclude_markup_languages(self):
        result = aggregate_recent_code_language_files(
            [
                {"filename": "Main.kt", "additions": 10, "deletions": 2},
                {"filename": "script.py", "additions": 8, "deletions": 1},
                {"filename": "index.html", "additions": 90, "deletions": 10},
            ]
        )
        payload = build_recent_code_language_payload(
            result,
            generated_at="2026-05-10T00:00:00Z",
            window_days=365,
        )
        svg = render_recent_code_language_svg(payload)

        self.assertEqual(payload["metric"], "changed_lines")
        self.assertEqual(payload["window_days"], 365)
        self.assertEqual(payload["languages"][0]["name"], "Kotlin")
        self.assertEqual(payload["languages"][0]["changes"], 12)
        self.assertIn("Kotlin", svg)
        self.assertIn("Python", svg)
        self.assertNotIn("HTML", svg)
        self.assertNotIn("CSS", svg)
        self.assertNotIn("Markdown", svg)
