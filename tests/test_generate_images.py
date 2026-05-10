import json
import os
import tempfile
import unittest

from generate_images import generate_kpis, generate_overview, generate_recent_code_languages


class FakeStats:
    @property
    async def name(self):
        return "SHARIF"

    @property
    async def stargazers(self):
        return 8

    @property
    async def forks(self):
        return 2

    @property
    async def total_contributions(self):
        return 3018

    @property
    async def languages(self):
        return {
            "Python": {"size": 10, "prop": 50, "color": "#3572A5"},
            "Kotlin": {"size": 10, "prop": 50, "color": "#A97BFF"},
        }

    @property
    async def repos(self):
        return {"sharif-smj/stats", "sharif-smj/gemini-image-describer"}

    @property
    async def followers(self):
        return 19

    @property
    async def public_repos(self):
        return 64

    @property
    async def lines_changed(self):
        raise AssertionError("generate_overview should not query line counts")

    @property
    async def views(self):
        raise AssertionError("generate_overview should not query traffic views")


class FakeRecentCodeQueries:
    async def query_rest(self, path, params=None):
        if path == "/repos/sharif-smj/app/commits":
            if params.get("page") == 1:
                return [{"sha": "abc123"}]
            return []
        if path == "/repos/sharif-smj/app/commits/abc123":
            return {
                "files": [
                    {"filename": "Main.kt", "additions": 30, "deletions": 2},
                    {"filename": "worker.py", "additions": 15, "deletions": 1},
                    {"filename": "index.html", "additions": 300, "deletions": 50},
                ]
            }
        return []


class FakeRecentCodeStats:
    username = "sharif-smj"
    queries = FakeRecentCodeQueries()

    @property
    async def repos(self):
        return {"sharif-smj/app"}


class GenerateOverviewTests(unittest.IsolatedAsyncioTestCase):
    async def test_overview_avoids_slow_rest_stats(self):
        repo_root = os.path.dirname(os.path.dirname(__file__))
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            try:
                os.chdir(tmp)
                os.symlink(os.path.join(repo_root, "templates"), "templates")

                await generate_overview(FakeStats())

                with open("generated/overview.svg", "r") as f:
                    output = f.read()
            finally:
                os.chdir(previous)

        self.assertIn("SHARIF's GitHub Statistics", output)
        self.assertIn("Languages tracked", output)
        self.assertIn(">2<", output)
        self.assertIn("Last updated", output)
        self.assertNotIn("Lines of code changed", output)
        self.assertNotIn("Repository views", output)

    async def test_kpis_excludes_language_content(self):
        repo_root = os.path.dirname(os.path.dirname(__file__))
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            try:
                os.chdir(tmp)
                os.symlink(os.path.join(repo_root, "templates"), "templates")

                await generate_kpis(FakeStats())

                with open("generated/kpis.svg", "r") as f:
                    output = f.read()
            finally:
                os.chdir(previous)

        self.assertIn("CONTRIBUTIONS", output)
        self.assertIn(">3,018<", output)
        self.assertIn("CONTRIBUTION REPOS", output)
        self.assertIn(">2<", output)
        self.assertIn("FOLLOWERS", output)
        self.assertIn(">19<", output)
        self.assertIn("PUBLIC REPOS", output)
        self.assertIn(">64<", output)
        self.assertNotIn("Languages", output)
        self.assertNotIn("Kotlin", output)
        self.assertNotIn("Python", output)

    async def test_recent_code_language_generation_writes_json_and_preview_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            try:
                os.chdir(tmp)

                await generate_recent_code_languages(FakeRecentCodeStats())

                with open("generated/recent-code-languages.json", "r") as f:
                    payload = json.load(f)
                with open("generated/recent-code-languages.svg", "r") as f:
                    svg = f.read()
            finally:
                os.chdir(previous)

        self.assertEqual(payload["metric"], "changed_lines")
        self.assertEqual(payload["languages"][0]["name"], "Kotlin")
        self.assertEqual(payload["languages"][0]["changes"], 32)
        self.assertEqual(payload["languages"][1]["name"], "Python")
        self.assertNotIn("HTML", svg)
