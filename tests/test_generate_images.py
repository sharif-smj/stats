import os
import tempfile
import unittest

from generate_images import generate_contributions, generate_kpis, generate_overview


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
    async def contribution_calendar(self):
        return {
            "totalContributions": 3044,
            "weeks": [
                {
                    "firstDay": "2026-05-03",
                    "contributionDays": [
                        {
                            "date": "2026-05-03",
                            "weekday": 0,
                            "contributionCount": 0,
                            "contributionLevel": "NONE",
                        },
                        {
                            "date": "2026-05-04",
                            "weekday": 1,
                            "contributionCount": 2,
                            "contributionLevel": "FIRST_QUARTILE",
                        },
                        {
                            "date": "2026-05-05",
                            "weekday": 2,
                            "contributionCount": 9,
                            "contributionLevel": "THIRD_QUARTILE",
                        },
                    ],
                }
            ],
        }

    @property
    async def lines_changed(self):
        raise AssertionError("generate_overview should not query line counts")

    @property
    async def views(self):
        raise AssertionError("generate_overview should not query traffic views")


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

    async def test_contribution_calendar_renders_dark_heatmap(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            try:
                os.chdir(tmp)

                await generate_contributions(FakeStats())

                with open("generated/contributions.svg", "r") as f:
                    output = f.read()
            finally:
                os.chdir(previous)

        self.assertIn('aria-label="3,044 contributions in the last year"', output)
        self.assertIn(">May<", output)
        self.assertNotIn(">Less<", output)
        self.assertNotIn(">More<", output)
        self.assertNotIn("3,044 contributions in the last year</text>", output)
        self.assertIn("#0d1117", output)
        self.assertIn("2026-05-04: 2 contributions", output)
