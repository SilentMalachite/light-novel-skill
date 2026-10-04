import importlib.util
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "light-novel" / "scripts" / "check_style.py"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"

spec = importlib.util.spec_from_file_location("check_style", SCRIPT)
assert spec is not None and spec.loader is not None
check_style = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_style)


def kinds(text):
    return [f.kind for f in check_style.check(text)]


def lines_of(text, kind):
    return [f.line for f in check_style.check(text) if f.kind == kind]


class FixtureTest(unittest.TestCase):
    def test_natural_text_passes(self):
        text = (FIXTURES / "natural.md").read_text(encoding="utf-8")
        self.assertEqual(check_style.check(text), [])

    def test_ai_like_text_hits_every_kind(self):
        text = (FIXTURES / "ai_like.md").read_text(encoding="utf-8")
        self.assertEqual(
            set(kinds(text)),
            {
                "冒頭", "比喩", "句点", "AI定型", "感情ラベル", "文末",
                "長文", "説明", "の連続", "記号", "章末",
            },
        )


class RuleTest(unittest.TestCase):
    def test_period_before_closing_bracket(self):
        self.assertEqual(lines_of("前置き。\n\n「行くよ。」\n", "句点"), [3])
        self.assertEqual(lines_of("前置き。\n\n「行くよ！」\n", "句点"), [])

    def test_ai_phrase_flagged_from_second_use(self):
        once = "俺は息を呑んだ。\n"
        self.assertEqual(lines_of(once, "AI定型"), [])
        twice = "俺は息を呑んだ。\n\n彼女も息をのんだ。\n"
        self.assertEqual(lines_of(twice, "AI定型"), [3])

    def test_emotion_label_at_paragraph_end(self):
        self.assertEqual(lines_of("前置き。\n\n俺は悲しかった。\n", "感情ラベル"), [3])
        self.assertEqual(lines_of("前置き。\n\n俺は緊張していた。\n", "感情ラベル"), [3])
        self.assertEqual(lines_of("前置き。\n\n悲しかった。だから走った。\n", "感情ラベル"), [])

    def test_same_ending_three_times(self):
        three = "前置き。\n\n待っていた。見ていた。\n\n座っていた。\n"
        self.assertEqual(lines_of(three, "文末"), [5])
        two = "前置き。\n\n待っていた。見ていた。走った。\n"
        self.assertEqual(lines_of(two, "文末"), [])

    def test_dialogue_resets_ending_run(self):
        text = "前置き。\n\n待っていた。見ていた。\n\n「おい」\n\n座っていた。\n"
        self.assertEqual(lines_of(text, "文末"), [])

    def test_long_sentence_in_narration_only(self):
        long_sentence = "あ" * 61 + "。"
        self.assertEqual(lines_of("前置き。\n\n" + long_sentence + "\n", "長文"), [3])
        self.assertEqual(lines_of("前置き。\n\n" + "あ" * 60 + "。\n", "長文"), [])
        self.assertEqual(lines_of("前置き。\n\n「" + "あ" * 70 + "」\n", "長文"), [])

    def test_long_paragraph(self):
        para = "短い文だ。" * 25
        self.assertEqual(lines_of("前置き。\n\n" + para + "\n", "説明"), [3])

    def test_no_chain(self):
        self.assertEqual(lines_of("前置き。\n\n王都の学園の中庭の前だ。\n", "の連続"), [3])
        self.assertEqual(lines_of("前置き。\n\n学園の中庭の前だ。\n", "の連続"), [])

    def test_simile_count_per_scene(self):
        text = "前置き。\n\nまるで猫だ。\n\n石のような顔だ。\n"
        self.assertEqual(lines_of(text, "比喩"), [5])
        reset = "前置き。\n\nまるで猫だ。\n\n※ ※ ※\n\n石のような顔だ。\n"
        self.assertEqual(lines_of(reset, "比喩"), [])
        self.assertEqual(lines_of("前置き。\n\nそのような話だ。\n\nまるで猫だ。\n", "比喩"), [])

    def test_simile_closing_paragraph(self):
        self.assertEqual(lines_of("前置き。\n\n空は燃えているかのようだった。\n", "比喩"), [3])

    def test_opening_skips_heading(self):
        self.assertEqual(lines_of("# 第1話\n\n目覚まし時計が鳴った。\n", "冒頭"), [3])
        self.assertEqual(lines_of("# 第1話\n\n「逃げるぞ」\n\n雨が降っていた。\n", "冒頭"), [])

    def test_opening_judges_main_clause(self):
        self.assertEqual(lines_of("窓の外は、雨が降っていた。\n", "冒頭"), [1])
        self.assertEqual(lines_of("雨が降る前に、俺は走り出した。\n", "冒頭"), [])
        self.assertEqual(lines_of("朝の光が差し込む前に、俺は部室を出た。\n", "冒頭"), [])

    def test_summary_ending(self):
        self.assertEqual(lines_of("前置き。\n\nこうして一日が終わった。\n", "章末"), [3])
        self.assertEqual(lines_of("こうして始まった。\n\n扉が開いた。\n", "章末"), [])

    def test_markup_in_prose(self):
        self.assertEqual(lines_of("前置き。\n\n**運命**だった。\n", "記号"), [3])
        self.assertEqual(lines_of("前置き。\n\n星が出た✨\n", "記号"), [3])

    def test_stats(self):
        stats = check_style.stats("前置きの文。\n\n「はい」\n")
        self.assertEqual(stats["dialogue_ratio"], 4 / 10)
        self.assertEqual(stats["avg_sentence_len"], 5)


class CliTest(unittest.TestCase):
    def run_cli(self, name):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(FIXTURES / name)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_natural_exits_zero(self):
        result = self.run_cli("natural.md")
        self.assertEqual(result.returncode, 0)
        self.assertIn("違反 0件", result.stdout)

    def test_ai_like_exits_one_with_review_format(self):
        result = self.run_cli("ai_like.md")
        self.assertEqual(result.returncode, 1)
        findings = [l for l in result.stdout.splitlines() if l.startswith("- ")]
        self.assertTrue(findings)
        for line in findings:
            self.assertRegex(line, r"^- \[[^\]]+\] \d+行目: .+")

    def test_reads_stdin(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="前置き。\n\n「行くよ。」\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("[句点] 3行目", result.stdout)


if __name__ == "__main__":
    unittest.main()
