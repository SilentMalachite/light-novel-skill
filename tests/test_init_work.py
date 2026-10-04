import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "light-novel"
SCRIPT = SKILL / "scripts" / "init_work.py"
ASSETS = SKILL / "assets"
NAMES = ["plot.md", "characters.md"]


def run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
    )


class InitWorkTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_copies_both_into_empty_dir(self):
        result = run(str(self.dir))
        self.assertEqual(result.returncode, 0)
        for name in NAMES:
            self.assertEqual(
                (self.dir / name).read_bytes(), (ASSETS / name).read_bytes()
            )
            self.assertIn(f"作成: {self.dir / name}", result.stdout)

    def test_keeps_existing_file(self):
        (self.dir / "plot.md").write_text("既存のプロット\n", encoding="utf-8")
        result = run(str(self.dir))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            (self.dir / "plot.md").read_text(encoding="utf-8"), "既存のプロット\n"
        )
        self.assertIn(f"既存: {self.dir / 'plot.md'}", result.stdout)
        self.assertEqual(
            (self.dir / "characters.md").read_bytes(),
            (ASSETS / "characters.md").read_bytes(),
        )
        self.assertIn(f"作成: {self.dir / 'characters.md'}", result.stdout)

    def test_defaults_to_current_dir(self):
        result = run(cwd=self.dir)
        self.assertEqual(result.returncode, 0)
        for name in NAMES:
            self.assertTrue((self.dir / name).is_file())

    def test_creates_missing_work_dir(self):
        target = self.dir / "作品" / "魔王"
        result = run(str(target))
        self.assertEqual(result.returncode, 0)
        for name in NAMES:
            self.assertTrue((target / name).is_file())


class TemplatesDocTest(unittest.TestCase):
    def test_templates_md_links_assets(self):
        doc = (SKILL / "references" / "templates.md").read_text(encoding="utf-8")
        for name in NAMES:
            self.assertIn(f"../assets/{name}", doc)


if __name__ == "__main__":
    unittest.main()
