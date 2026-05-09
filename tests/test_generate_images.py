import os
import tempfile
import unittest

from generate_images import generate_overview


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
