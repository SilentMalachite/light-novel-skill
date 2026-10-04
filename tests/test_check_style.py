import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
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

    def test_finding_keeps_matched_text(self):
        finding = check_style.check("前置き。\n\n「行くよ。」\n")[0]
        self.assertEqual(finding.match, "。」")
        finding = check_style.check("前置き。\n\n" + "あ" * 61 + "。\n")[0]
        self.assertEqual(finding.match, "あ" * 61 + "。")

    def test_stats(self):
        stats = check_style.stats("前置きの文。\n\n「はい」\n")
        self.assertEqual(stats["dialogue_ratio"], 4 / 10)
        self.assertEqual(stats["avg_sentence_len"], 5)


class FixTest(unittest.TestCase):
    def test_removes_period_before_closing_bracket(self):
        self.assertEqual(check_style.fix("前置き。\n\n「行くよ。」\n"), "前置き。\n\n「行くよ」\n")
        self.assertEqual(check_style.fix("前置き。\n\n『題。』だ。\n"), "前置き。\n\n『題』だ。\n")

    def test_removes_markup_and_closes_sentence(self):
        self.assertEqual(check_style.fix("前置き。\n\n**運命**だった✨\n"), "前置き。\n\n運命だった。\n")
        self.assertEqual(check_style.fix("前置き。\n\n星が出た✨。\n"), "前置き。\n\n星が出た。\n")

    def test_keeps_headings_and_line_endings(self):
        self.assertEqual(check_style.fix("# **題**\r\n\r\n「行くよ。」\r\n"), "# **題**\r\n\r\n「行くよ」\r\n")

    def test_removes_zwj_emoji_whole(self):
        self.assertEqual(check_style.fix("前置き。\n\n家族だ👨\u200d👩\u200d👧\n"), "前置き。\n\n家族だ。\n")
        self.assertEqual(check_style.fix("前置き。\n\n走った🏃\u200d♀\ufe0f\n"), "前置き。\n\n走った。\n")

    def test_closes_narration_after_dialogue(self):
        self.assertEqual(
            check_style.fix("前置き。\n\n「行くよ」と彼は言った✨\n"), "前置き。\n\n「行くよ」と彼は言った。\n"
        )
        self.assertEqual(check_style.fix("前置き。\n\n「行くよ✨」\n"), "前置き。\n\n「行くよ」\n")

    def test_broken_zwj_keeps_following_text(self):
        self.assertEqual(check_style.fix("前置き。\n\n走🏃\u200dった。\n"), "前置き。\n\n走\u200dった。\n")

    def test_keeps_other_trailing_characters(self):
        self.assertEqual(check_style.fix("前置き。\n\n**運命**だ。  \n"), "前置き。\n\n運命だ。  \n")
        self.assertEqual(check_style.fix("「行くよ。」\u2028次。\n"), "「行くよ」\u2028次。\n")

    def test_bom_is_ignored(self):
        self.assertEqual(check_style.fix("\ufeff# **題**\n\n「行くよ。」\n"), "\ufeff# **題**\n\n「行くよ」\n")
        self.assertEqual(lines_of("\ufeff# 第1話\n\n目覚まし時計が鳴った。\n", "冒頭"), [3])

    def test_leaves_judgment_kinds(self):
        text = (FIXTURES / "ai_like.md").read_text(encoding="utf-8")
        before = set(kinds(text))
        after = set(kinds(check_style.fix(text)))
        self.assertEqual(before - after, {"句点", "記号"})


class CompareTest(unittest.TestCase):
    def test_counts_resolved_remaining_new(self):
        before = "前置き。\n\n「行くよ。」\n\n俺は悲しかった。\n"
        after = "前置き。\n\n「行くよ」\n\n俺は悲しかった。\n\n王都の学園の中庭の前だ。\n"
        result = check_style.compare(before, after)
        self.assertEqual(result["resolved"], {"句点": 1})
        self.assertEqual(result["remaining"], {"感情ラベル": 1})
        self.assertEqual(result["new"], {"の連続": 1})

    def test_dialogue_punctuation_is_ignored(self):
        result = check_style.compare("前置き。\n\n「行くよ。」\n", "前置き。\n\n「行くよ！」\n")
        self.assertEqual(result["dialogue_changes"], [])

    def test_dialogue_commas_and_dots_count(self):
        result = check_style.compare("前置き。\n\n「だめ」\n", "前置き。\n\n「だ、め」\n")
        self.assertEqual(len(result["dialogue_changes"]), 1)
        result = check_style.compare("前置き。\n\n「田中・太郎」\n", "前置き。\n\n「田中太郎」\n")
        self.assertEqual(len(result["dialogue_changes"]), 1)

    def test_same_kind_elsewhere_is_new(self):
        before = "前置き。\n\n" + "あ" * 61 + "。\n"
        after = "前置き。\n\n" + "あ" * 30 + "。" + "あ" * 31 + "。\n\n" + "い" * 61 + "。\n"
        result = check_style.compare(before, after)
        self.assertEqual(result["resolved"], {"長文": 1})
        self.assertEqual(result["remaining"], {})
        self.assertEqual(result["new"], {"長文": 1})
        self.assertEqual([f["line"] for f in result["new_findings"]], [5])
        self.assertFalse(result["ok"])

    def test_empty_baseline_is_not_within_length(self):
        result = check_style.compare("# 第1話\n", "# 第1話\n\n本文だ。\n")
        self.assertFalse(result["ok"])
        self.assertTrue(check_style.compare("# 第1話\n", "# 第1話\n")["ok"])

    def test_dialogue_changes_are_reported(self):
        before = "前置き。\n\n「行くよ」\n\n「待って」\n"
        after = "前置き。\n\n「行かない」\n"
        changes = check_style.compare(before, after)["dialogue_changes"]
        self.assertEqual(
            changes,
            [
                {"before_line": 3, "before": "行くよ", "after_line": 3, "after": "行かない"},
                {"before_line": 5, "before": "待って", "after_line": None, "after": None},
            ],
        )

    def test_double_bracket_dialogue_is_compared(self):
        changes = check_style.compare("前置き。\n\n『行くよ』\n", "前置き。\n\n『行かない』\n")["dialogue_changes"]
        self.assertEqual(len(changes), 1)
        nested = check_style.compare("前置き。\n\n「『題』を読んだ」\n", "前置き。\n\n「『題』を読んだ」\n")
        self.assertEqual(nested["dialogue_changes"], [])

    def test_length_change(self):
        result = check_style.compare("あ" * 100 + "。\n", "あ" * 79 + "。\n")
        self.assertEqual(result["chars"], {"before": 101, "after": 80})
        self.assertFalse(result["ok"])

    def test_golden_fix_of_ai_like(self):
        before = (FIXTURES / "ai_like.md").read_text(encoding="utf-8")
        after = (FIXTURES / "ai_like_fixed.md").read_text(encoding="utf-8")
        self.assertEqual(check_style.check(after), [])
        result = check_style.compare(before, after)
        self.assertEqual(result["new"], {})
        self.assertEqual(result["dialogue_changes"], [])


class CliTest(unittest.TestCase):
    def run_cli(self, name, *options):
        return self.run_args(*options, str(FIXTURES / name))

    def run_args(self, *args, stdin=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=stdin,
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

    def test_json_output(self):
        result = self.run_cli("ai_like.md", "--json")
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertEqual(set(data), {"findings", "stats"})
        first = data["findings"][0]
        self.assertEqual(set(first), {"kind", "line", "message", "match"})
        self.assertEqual(first["kind"], "冒頭")

    def test_fix_rewrites_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "ep.md"
            shutil.copy(FIXTURES / "ai_like.md", path)
            result = self.run_args("--fix", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("自動修正 句点 1件, 記号 1件", result.stdout)
            text = path.read_text(encoding="utf-8")
            self.assertIn("「おはよう。今日もいい天気だね」", text)
            self.assertNotIn("**", text)

    def test_fix_requires_file(self):
        result = self.run_args("--fix", stdin="「行くよ。」\n")
        self.assertEqual(result.returncode, 2)

    def test_baseline_passes_for_golden(self):
        result = self.run_args("--baseline", str(FIXTURES / "ai_like.md"), str(FIXTURES / "ai_like_fixed.md"))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("比較", result.stdout)
        self.assertIn("- 新規: なし", result.stdout)
        self.assertIn("- セリフ: 変更なし", result.stdout)

    def test_baseline_fails_on_dialogue_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "after.md"
            path.write_text("前置き。\n\n「行かない」\n", encoding="utf-8")
            base = pathlib.Path(tmp) / "before.md"
            base.write_text("前置き。\n\n「行くよ」\n", encoding="utf-8")
            result = self.run_args("--baseline", str(base), str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("3行目「行くよ」→ 3行目「行かない」", result.stdout)
            self.assertIn("違反 0件 / 比較 要確認", result.stdout)

    def test_baseline_lists_new_finding_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp) / "before.md"
            base.write_text("前置き。\n", encoding="utf-8")
            path = pathlib.Path(tmp) / "after.md"
            path.write_text("前置き。\n\n王都の学園の中庭の前だ。\n", encoding="utf-8")
            result = self.run_args("--baseline", str(base), str(path))
            self.assertIn("- 新規: の連続 1（3行目）", result.stdout)

    def test_fix_leaves_no_temp_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "ep.md"
            path.write_text("前置き。\n\n「行くよ。」\n", encoding="utf-8")
            self.run_args("--fix", str(path))
            self.assertEqual([p.name for p in pathlib.Path(tmp).iterdir()], ["ep.md"])
            self.assertEqual(path.read_text(encoding="utf-8"), "前置き。\n\n「行くよ」\n")


if __name__ == "__main__":
    unittest.main()
