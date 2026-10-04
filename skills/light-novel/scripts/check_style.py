#!/usr/bin/env python3
"""ラノベ本文の機械チェック。

使い方: python3 check_style.py [--json] [--fix] [--baseline 元.md] 本文.md
  本文を省略すると標準入力から読む（--fix のときは省略できない）。
  --json      違反と統計を JSON で出す
  --fix       句点と記号だけを直して本文に書き戻し、残りの違反を出す
  --baseline  書き換え前の本文と比べ、違反の増減、セリフの変更、字数の増減を出す
違反を references/review.md と同じ形で出す。違反か要確認があれば終了コード 1。
判断が要る項目は references/check.md、直し方は references/fix.md で見る。
"""
import argparse
import difflib
import json
import os
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Finding:
    kind: str
    line: int
    message: str
    match: str = ""


AI_PHRASES = [
    (r"息を[呑の]ん", "息を呑んだ"),
    (r"深く息を吐", "深く息を吐いた"),
    (r"瞳が揺れ", "瞳が揺れた"),
    (r"言葉を失", "言葉を失った"),
    (r"胸の奥が熱く", "胸の奥が熱くなる"),
    (r"心臓が高鳴", "心臓が高鳴った"),
    (r"時間を忘れたかのよう", "時間を忘れたかのように"),
    (r"ずにはいられな", "〜せずにはいられなかった"),
    (r"という事実が", "〜という事実が"),
    (r"と言えるだろう", "〜と言えるだろう"),
    (r"心の奥で", "心の奥で"),
]

EMOTION_END = re.compile(
    r"((悲し|嬉し|うれし|寂し|さみし|淋し|怖|恐ろし|悔し|楽し|辛|つら|切な)かった"
    r"|(怒っ|驚い|戸惑っ|安堵し|困惑し|動揺し|緊張し|興奮し|絶望し|感動し)(てい)?た)。$"
)
SIMILE = re.compile(r"まるで|かのよう|(?<!その)(?<!この)(?<!あの)(?<!どの)ような|みたいな")
SIMILE_END = re.compile(r"(まるで.*|かの)(よう|みたい)だ(った)?。$")
NO_CHAIN = re.compile(r"の[^、。！？「」『』の\s]{1,6}の[^、。！？「」『』の\s]{1,6}の")
OPENING = re.compile(r"目を覚ま|目が覚め|目覚まし|アラーム|朝の光|朝日|日差し|陽射し|青空|快晴|雨が|晴れ|通学路|登校")
SUMMARY_END = re.compile(r"^こうして|一日が終わ")
EMOJI = "[\U0001F000-\U0001FAFF✨✅❌⭐]\uFE0F?(?:\u200D[\U0001F000-\U0001FAFF\u2600-\u27BF]\uFE0F?)*"
MARKUP = re.compile(r"\*\*|" + EMOJI)
TRAILING_EMOJI = re.compile("[ \t　]*(?:" + EMOJI + ")+[ \t　]*$")
PERIOD_BEFORE_CLOSE = re.compile(r"。(?=[」』])")
QUOTE = re.compile(r"「([^」]*)」|『([^』]*)』")
QUOTE_PUNCT = re.compile(r"[。！？!?…‥\s]")
SCENE_BREAK = re.compile(r"^[※＊*◇◆]+[\s　※＊*◇◆]*$")
SENTENCE = re.compile(r"[^。！？!?]+[。！？!?]*")
TERMINATORS = "。！？!?"

LONG_SENTENCE = 60
LONG_PARAGRAPH = 120
LENGTH_TOLERANCE = 0.15


def classify(raw):
    line = raw.lstrip("\ufeff").strip().lstrip("　")
    if not line:
        return "blank", line
    if line.startswith("#"):
        return "heading", line
    if SCENE_BREAK.match(line):
        return "break", line
    if line[0] in "「『":
        return "dialogue", line
    return "narration", line


def narration_part(kind, line):
    """地の文として検査する部分。会話行は閉じ括弧の後ろだけ。"""
    if kind == "narration":
        return line
    if kind == "dialogue":
        close = max(line.rfind("」"), line.rfind("』"))
        return line[close + 1:].strip()
    return ""


def sentences(text):
    return [s.strip() for s in SENTENCE.findall(text) if s.strip()]


def body(sentence):
    return sentence.rstrip(TERMINATORS)


def check(text):
    rows = [(i, *classify(raw)) for i, raw in enumerate(text.splitlines(), 1)]
    prose = [(i, k, l) for i, k, l in rows if k in ("narration", "dialogue")]
    findings = []

    def add(kind, line, message, match=""):
        findings.append(Finding(kind, line, message, match))

    if prose:
        i, _, line = prose[0]
        first = sentences(line)[0]
        main_clause = first.split("、")[-1]
        if OPENING.search(main_clause):
            add("冒頭", i, "天気・目覚め・通学路で始まっている。視点人物の欠落かフックが見える場面から入る。", first)
        i, _, line = prose[-1]
        if SUMMARY_END.search(line):
            add("章末", i, "要約で締めている。未解決を1つ残して切る。", line)

    seen = {}
    simile_count = 0
    blank_run = 0
    ending_key, ending_run = None, 0

    for i, kind, line in rows:
        if kind == "blank":
            blank_run += 1
            if blank_run >= 2:
                simile_count = 0
            continue
        blank_run = 0
        if kind in ("heading", "break"):
            simile_count = 0
            ending_key, ending_run = None, 0
            continue

        for pattern, label in AI_PHRASES:
            for m in re.finditer(pattern, line):
                seen[label] = seen.get(label, 0) + 1
                if seen[label] == 2:
                    add("AI定型", i, f"「{label}」が2回目。1話1回まで。動作か状況に置き換える。", m.group())

        m = re.search(r"。[」』]", line)
        if m:
            add("句点", i, "閉じ括弧の前に句点がある。句点を取る。", m.group())
        m = MARKUP.search(line)
        if m:
            add("記号", i, "本文に太字記法か絵文字がある。外す。", m.group())

        if kind == "dialogue":
            ending_key, ending_run = None, 0

        part = narration_part(kind, line)
        if not part:
            continue
        sents = sentences(part)

        if kind == "narration":
            if len(part) > LONG_PARAGRAPH:
                add("説明", i, f"段落が{len(part)}字ある。会話か動作で割る。", part)
            for s in sents:
                if not s.endswith("。"):
                    ending_key, ending_run = None, 0
                    continue
                key = body(s)[-2:]
                ending_run = ending_run + 1 if key == ending_key else 1
                ending_key = key
                if ending_run == 3:
                    add("文末", i, f"地の文の文末「{key}」が3連続。1つ変える。", s)

        if sents and EMOTION_END.search(sents[-1]):
            add("感情ラベル", i, "感情の名前で段落を終えている。動作か身体に置き換える。", sents[-1])
        if sents and SIMILE_END.search(sents[-1]):
            add("比喩", i, "段落を比喩で締めている。締めは事実か動作にする。", sents[-1])
        for s in sents:
            if len(body(s)) > LONG_SENTENCE:
                add("長文", i, f"1文が{len(body(s))}字ある。山場でなければ割る。", s)
            if SIMILE.search(s):
                simile_count += 1
                if simile_count == 2:
                    add("比喩", i, "この場面で比喩が2つ目。1場面1つまで。", s)
        m = NO_CHAIN.search(part)
        if m:
            add("の連続", i, "「の」が3つ以上続いている。語順を変えて切る。", m.group())

    findings.sort(key=lambda f: f.line)
    return findings


def stats(text):
    dialogue = narration = 0
    lengths = []
    for raw in text.splitlines():
        kind, line = classify(raw)
        if kind == "dialogue":
            dialogue += len(line)
        elif kind == "narration":
            narration += len(line)
            lengths += [len(body(s)) for s in sentences(line)]
    total = dialogue + narration
    return {
        "dialogue_ratio": dialogue / total if total else 0.0,
        "avg_sentence_len": round(sum(lengths) / len(lengths), 1) if lengths else 0.0,
    }


def fix(text):
    """機械的に直せる句点と記号だけを直す。行数、見出し、改行コードは変えない。"""
    out = []
    for raw in text.splitlines(keepends=True):
        content = raw.splitlines()[0]
        ending = raw[len(content):]
        kind, line = classify(content)
        if kind in ("narration", "dialogue"):
            closed_by_emoji = TRAILING_EMOJI.search(narration_part(kind, line))
            if closed_by_emoji:
                content = TRAILING_EMOJI.sub("", content)
            content = PERIOD_BEFORE_CLOSE.sub("", MARKUP.sub("", content))
            if closed_by_emoji and content and content[-1] not in TERMINATORS + "」』…―":
                content += "。"
        out.append(content + ending)
    return "".join(out)


def quotes(text):
    """本文中の「」と『』の中身を (行番号, 中身) で返す。行をまたぐセリフは拾わない。"""
    found = []
    for i, raw in enumerate(text.splitlines(), 1):
        kind, line = classify(raw)
        if kind in ("narration", "dialogue"):
            found += [(i, m.group(1) if m.group(1) is not None else m.group(2)) for m in QUOTE.finditer(line)]
    return found


def prose_chars(text):
    total = 0
    for raw in text.splitlines():
        kind, line = classify(raw)
        if kind in ("narration", "dialogue"):
            total += len(line)
    return total


def length_change(chars):
    """字数の増減率と、許容内かを返す。元が0字なら、後も0字のときだけ許容内。"""
    if not chars["before"]:
        return None, not chars["after"]
    rate = chars["after"] / chars["before"] - 1
    return rate, abs(rate) <= LENGTH_TOLERANCE


def compare(before, after):
    """書き換え前後を比べる。違反の増減、セリフの変更、字数を返す。

    違反は種別と該当箇所の組で突き合わせる。同じ種別でも箇所が違えば新規に数える。
    """
    old_findings, new_findings = check(before), check(after)
    old = Counter((f.kind, f.match) for f in old_findings)
    new = Counter((f.kind, f.match) for f in new_findings)
    added = new - old
    unmatched = Counter(added)
    listed = []
    for f in new_findings:
        key = (f.kind, f.match)
        if unmatched[key]:
            unmatched[key] -= 1
            listed.append(asdict(f))
    old_q, new_q = quotes(before), quotes(after)
    matcher = difflib.SequenceMatcher(
        a=[QUOTE_PUNCT.sub("", q) for _, q in old_q],
        b=[QUOTE_PUNCT.sub("", q) for _, q in new_q],
        autojunk=False,
    )
    changes = []
    for tag, a1, a2, b1, b2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        olds, news = old_q[a1:a2], new_q[b1:b2]
        for k in range(max(len(olds), len(news))):
            o = olds[k] if k < len(olds) else (None, None)
            n = news[k] if k < len(news) else (None, None)
            changes.append({"before_line": o[0], "before": o[1], "after_line": n[0], "after": n[1]})
    chars = {"before": prose_chars(before), "after": prose_chars(after)}
    _, within = length_change(chars)

    def by_kind(counter):
        kinds = Counter()
        for (kind, _), n in counter.items():
            kinds[kind] += n
        return dict(kinds)

    return {
        "resolved": by_kind(old - new),
        "remaining": by_kind(old & new),
        "new": by_kind(added),
        "new_findings": listed,
        "dialogue_changes": changes,
        "chars": chars,
        "ok": not added and not changes and within,
    }


def counts(counter):
    return ", ".join(f"{k} {v}" for k, v in counter.items()) or "なし"


def print_compare(result):
    print("比較")
    print(f"- 解消: {counts(result['resolved'])}")
    print(f"- 残存: {counts(result['remaining'])}")
    new = counts(result["new"])
    if result["new_findings"]:
        new += "（" + ", ".join(f"{f['line']}行目" for f in result["new_findings"]) + "）"
    print(f"- 新規: {new}")
    if result["dialogue_changes"]:
        for c in result["dialogue_changes"]:
            old = f"{c['before_line']}行目「{c['before']}」" if c["before"] is not None else "なし"
            new = f"{c['after_line']}行目「{c['after']}」" if c["after"] is not None else "削除"
            print(f"- セリフ: {old}→ {new}" if c["before"] is not None else f"- セリフ: 追加 {new}")
    else:
        print("- セリフ: 変更なし")
    before, after = result["chars"]["before"], result["chars"]["after"]
    rate, within = length_change(result["chars"])
    shown = f"（{rate:+.0%}）" if rate is not None else ""
    mark = "" if within else "（要確認）"
    print(f"- 字数: {before} → {after}{shown}{mark}")


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def main(argv):
    for stream in (sys.stdin, sys.stdout):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="ラノベ本文の機械チェック")
    parser.add_argument("file", nargs="?", help="本文。省略すると標準入力")
    parser.add_argument("--json", action="store_true", help="JSON で出す")
    parser.add_argument("--fix", action="store_true", help="句点と記号を直して本文に書き戻す")
    parser.add_argument("--baseline", metavar="元.md", help="書き換え前の本文と比べる")
    args = parser.parse_args(argv[1:])
    if args.fix and not args.file:
        parser.error("--fix には本文のファイルを指定する")

    text = read(args.file) if args.file else sys.stdin.read()
    fixed = None
    if args.fix:
        before = Counter(f.kind for f in check(text))
        text, original = fix(text), text
        if text != original:
            tmp = args.file + ".tmp"
            with open(tmp, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            os.replace(tmp, args.file)
        fixed = dict(before - Counter(f.kind for f in check(text)))
    findings = check(text)
    s = stats(text)
    result = compare(read(args.baseline), text) if args.baseline else None

    if args.json:
        data = {"findings": [asdict(f) for f in findings], "stats": s}
        if fixed is not None:
            data["fixed"] = fixed
        if result is not None:
            data["compare"] = result
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        if fixed is not None:
            print("自動修正 " + (", ".join(f"{k} {v}件" for k, v in fixed.items()) or "なし"))
        for f in findings:
            print(f"- [{f.kind}] {f.line}行目: {f.message}")
        if result is not None:
            print_compare(result)
        summary = f"会話比率 {s['dialogue_ratio']:.0%} / 地の文の平均文長 {s['avg_sentence_len']}字 / 違反 {len(findings)}件"
        if result is not None and not result["ok"]:
            summary += " / 比較 要確認"
        print(summary)
    return 1 if findings or (result is not None and not result["ok"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
