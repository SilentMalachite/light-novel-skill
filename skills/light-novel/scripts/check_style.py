#!/usr/bin/env python3
"""ラノベ本文の機械チェック。

使い方: python3 check_style.py 本文.md   （省略時は標準入力）
違反を references/review.md と同じ形で出す。違反があれば終了コード 1。
判断が要る項目は references/check.md で見る。
"""
import re
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    kind: str
    line: int
    message: str


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
MARKUP = re.compile(r"\*\*|[\U0001F000-\U0001FAFF✨✅❌⭐]")
SCENE_BREAK = re.compile(r"^[※＊*◇◆]+[\s　※＊*◇◆]*$")
SENTENCE = re.compile(r"[^。！？!?]+[。！？!?]*")
TERMINATORS = "。！？!?"

LONG_SENTENCE = 60
LONG_PARAGRAPH = 120


def classify(raw):
    line = raw.strip().lstrip("　")
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

    def add(kind, line, message):
        findings.append(Finding(kind, line, message))

    if prose:
        i, _, line = prose[0]
        first = sentences(line)[0]
        main_clause = first.split("、")[-1]
        if OPENING.search(main_clause):
            add("冒頭", i, "天気・目覚め・通学路で始まっている。視点人物の欠落かフックが見える場面から入る。")
        i, _, line = prose[-1]
        if SUMMARY_END.search(line):
            add("章末", i, "要約で締めている。未解決を1つ残して切る。")

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
            for _ in re.finditer(pattern, line):
                seen[label] = seen.get(label, 0) + 1
                if seen[label] == 2:
                    add("AI定型", i, f"「{label}」が2回目。1話1回まで。動作か状況に置き換える。")

        if re.search(r"。[」』]", line):
            add("句点", i, "閉じ括弧の前に句点がある。句点を取る。")
        if MARKUP.search(line):
            add("記号", i, "本文に太字記法か絵文字がある。外す。")

        if kind == "dialogue":
            ending_key, ending_run = None, 0

        part = narration_part(kind, line)
        if not part:
            continue
        sents = sentences(part)

        if kind == "narration":
            if len(part) > LONG_PARAGRAPH:
                add("説明", i, f"段落が{len(part)}字ある。会話か動作で割る。")
            for s in sents:
                if not s.endswith("。"):
                    ending_key, ending_run = None, 0
                    continue
                key = body(s)[-2:]
                ending_run = ending_run + 1 if key == ending_key else 1
                ending_key = key
                if ending_run == 3:
                    add("文末", i, f"地の文の文末「{key}」が3連続。1つ変える。")

        if sents and EMOTION_END.search(sents[-1]):
            add("感情ラベル", i, "感情の名前で段落を終えている。動作か身体に置き換える。")
        if sents and SIMILE_END.search(sents[-1]):
            add("比喩", i, "段落を比喩で締めている。締めは事実か動作にする。")
        for s in sents:
            if len(body(s)) > LONG_SENTENCE:
                add("長文", i, f"1文が{len(body(s))}字ある。山場でなければ割る。")
            if SIMILE.search(s):
                simile_count += 1
                if simile_count == 2:
                    add("比喩", i, "この場面で比喩が2つ目。1場面1つまで。")
        if NO_CHAIN.search(part):
            add("の連続", i, "「の」が3つ以上続いている。語順を変えて切る。")

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


def main(argv):
    if len(argv) > 1:
        with open(argv[1], encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    findings = check(text)
    for f in findings:
        print(f"- [{f.kind}] {f.line}行目: {f.message}")
    s = stats(text)
    print(
        f"会話比率 {s['dialogue_ratio']:.0%} / 地の文の平均文長 {s['avg_sentence_len']}字 / 違反 {len(findings)}件"
    )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
