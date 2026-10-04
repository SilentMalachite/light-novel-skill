# light-novel スキル

[![CI](https://github.com/SilentMalachite/light-novel-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/SilentMalachite/light-novel-skill/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/SilentMalachite/light-novel-skill)](LICENSE)
[![npx skills add](https://img.shields.io/badge/npx%20skills%20add-SilentMalachite%2Flight--novel--skill-blue)](https://github.com/vercel-labs/skills)
[![Agents](https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex%20%7C%20Grok%20Build-8A2BE2)](#エージェント別の置き場所)
[![Python](https://img.shields.io/badge/python-3.9%2B%20(stdlib%20only)-3776AB?logo=python&logoColor=white)](#ファイル構成)
[![Last commit](https://img.shields.io/github/last-commit/SilentMalachite/light-novel-skill)](https://github.com/SilentMalachite/light-novel-skill/commits/main)

日本語のライトノベルと Web 小説を、設計ファイルを正本にして書くためのエージェントスキル。企画からプロット、本文、推敲、レビュー、文体チェック、チェックした違反の書き換えまでを扱う。Claude Code、Codex、Grok Build で使える。

初めて使うときは「インストール」と「使い方」だけ読めば足りる。「エージェント別の置き場所」から後ろは、手で配置するときや中身を変えるときに引く。

## インストールは npx skills add の1行で済む

```bash
npx skills add SilentMalachite/light-novel-skill
```

エージェントを指定するときは `-a`、全プロジェクトで使う個人用にするときは `-g` を付ける。

```bash
npx skills add SilentMalachite/light-novel-skill -a claude-code
npx skills add SilentMalachite/light-novel-skill -a codex
npx skills add SilentMalachite/light-novel-skill -a grok
```

このコマンドで入るのはスキル本体だけで、常時指示の `CLAUDE.md` と `AGENTS.md` は入らない。使うプロジェクトの直下に手で置く。既にあれば末尾に追記する。

## 使い方: 依頼は構築、執筆、推敲のどれか1つにする

スキルは依頼を構築、執筆、推敲の3種類に分け、頼まれた種類の仕事だけをする。1回の依頼で設計と本文をまとめて頼んでも、設計が固まるまで本文は書かない。流れは次のとおり。

1. 書きたい話を頼む。作品フォルダに `plot.md` と `characters.md` の雛形が置かれ、質問が返る。
2. 質問に答えて、ログライン、視点、結末、キャラの口調を固める。
3. 話と場面を指定して本文を頼む。
4. 書けた本文の推敲か、文体チェックを頼む。チェックだけでは書き換えない。直すときは「直して」と頼む。

### 構築: 「〜を書いて」と頼むと、まず雛形が置かれる

```text
コンビニでバイトしてる元魔王が主人公のラノベを書いて
```

「〜を書いて」「〜を執筆して」「〜を作って」のどれで頼んでも、作品フォルダに `plot.md` か `characters.md` が無ければ、先に雛形が置かれる。作品フォルダを指定しなければ作業ディレクトリに置く。既にあるファイルは上書きしない。

雛形を置いたら、依頼文から分かる項目だけを埋め、ログライン、視点、結末のうち埋まらないものを質問して止まる。質問は最大3つで、この回は本文を書かない。答えると `plot.md` の先頭が次のように固まり、キャラごとに口調サンプルが3つ付く。

```markdown
- ログライン: 角を隠してコンビニで働く元魔王が、正体を知る勇者の末裔に追われながら、店と居場所を守る話。
- 視点: 一人称
- 一人称: 俺
- 結末: 魔王の名を捨て、店長代理として店に残る。勇者とは客と店員のまま決着する。
```

雛形を手で置くときは次を実行する。パスはインストール先に合わせる。

```bash
python3 .claude/skills/light-novel/scripts/init_work.py 作品フォルダ
```

### 執筆: 場面カードを埋めてから、指定した場面だけを書く

```text
plot.md の第1話、1場面目を書いて
```

視点人物、目的、入口の圧、出口の未解決、守る既出事実を場面カードに埋めてから、その場面の本文だけを返す。前後の場面、新しいキャラ、解説は付かない。口調サンプルが無いキャラのセリフは書かない。

本文をファイルに書いたときは、返す前に機械検査を回し、今回書いた範囲の違反だけを直す。前からあった本文は、「直して」と頼まない限り触らない。

### 推敲とレビュー: 推敲は最小限直し、レビューは直さずに違反を返す

```text
第1話を推敲して。筋は変えないで
```

視点の越境、説明台詞、AI調、口調の取り違えだけを直す。文体チェックの違反をまとめて直すときは、下の「文体の修正」のように頼む。

```text
第1話をレビューして
```

レビューを頼んだときは、どのエージェントでも本文を書き換えず、違反を箇所つきで返す。

```text
- [視点] 3章2場面: 一人称なのに相手の内心を断定している。伝聞か、観察できる動作に置換。
- [章末] 4章: 解決して終わっている。未解決を1つ残す。
```

### 文体チェック: 頼まれなければ書き換えず、違反と判定を返す

```text
episode01.md、AI臭くないか、ラノベらしい文体になってるかチェックして
```

機械検査のスクリプトで違反を拾い、テンポ、口調、掛け合い、AI臭さなど、機械では決められない項目の判定を足して返す。返す順は違反一覧、判定、統計で、前置きや講評は付かない。`plot.md` が無くてもチェックできる。

```text
- [冒頭] 3行目: 天気・目覚め・通学路で始まっている。視点人物の欠落かフックが見える場面から入る。
- [句点] 7行目: 閉じ括弧の前に句点がある。句点を取る。
- [感情ラベル] 11行目: 感情の名前で段落を終えている。動作か身体に置き換える。
- [文末] 13行目: 地の文の文末「いた」が3連続。1つ変える。
- [説明] 15行目: 段落が151字ある。会話か動作で割る。

判定
- テンポ: 要修正（13〜15行目）
- 口調: 要修正（7, 19行目）
- AI臭さ: 要修正（5, 9, 19, 21行目）

会話比率 14% / 地の文の平均文長 24.6字
```

上の出力は `tests/fixtures/ai_like.md` を検査したときの抜粋。違反の行はスクリプトの出力そのままで、判定はエージェントが付けたものなので実行ごとに変わりうる。

### 文体の修正: 「直して」と頼むと、チェックしてから書き換える

```text
episode01.md、AI臭さをチェックして直して
```

チェックだけの依頼と違い、本文のファイルを上書きする。流れは次のとおり。

1. 元の本文を、作品フォルダの外の一時ディレクトリに控える。
2. 句点と記号をスクリプトが直す。
3. AI定型、感情ラベル、文末、比喩、長文、説明、冒頭、章末などを、エージェントが `references/fix.md` の直し方で直す。直すのは違反のある文だけ。機械検査を通った文でも、予告調の締めや誰でも書ける美文はAI臭さとして直す。
4. 控えと比べて再検査する。違反が残っていれば3に戻る。直し直しは3回まで。
5. 控えを消して返す。

筋、固有名詞、セリフの中身、視点は変えず、字数は元の±15%以内に収める。山場で意図した長文やキャラの口癖のように、直すと作品が壊れる違反は理由を付けて残す。

チャットに返すのは、直した件数と、直さずに残した違反の理由だけ。前置きや講評は付かない。

```text
直した: 7件（句点 1, 比喩 2, 感情ラベル 1, 文末 1, AI定型 1, 章末 1）
残した:
- [長文] 31行目: 山場の独白。意図した長文として残す。
字数 3120 → 3015（-3%）/ セリフ変更なし
```

`tests/fixtures/ai_like.md` を直した見本が `tests/fixtures/ai_like_fixed.md` にある。

### 機械検査を自分で回す

エージェントを通さず、スクリプトだけを回せる。パスはインストール先に合わせる。

```bash
# 検査する。ファイルを渡さなければ標準入力から読む
python3 .claude/skills/light-novel/scripts/check_style.py episode01.md
# 句点と記号だけを直して書き戻し、残った違反を出す
python3 .claude/skills/light-novel/scripts/check_style.py --fix episode01.md
# 書き換え前と比べる
python3 .claude/skills/light-novel/scripts/check_style.py --baseline episode01.orig.md episode01.md
```

| オプション | すること |
| --- | --- |
| なし | 違反を行番号つきで出し、最後の行に会話比率、地の文の平均文長、違反の件数を出す |
| `--json` | 違反を種別、行番号、該当箇所、修正の指示つきの JSON で出す |
| `--fix` | 閉じ括弧前の句点と、太字記法・絵文字だけを直してファイルに書き戻す。♪♡★ などの記号は残す。改行コードは変えない。ファイルの指定が要る |
| `--baseline 元.md` | 書き換え前と比べ、違反の解消・残存・新規、セリフの中身の変更、字数の増減を出す。違反は種別と該当箇所の組で突き合わせるので、同じ種別でも別の箇所に出たものは新規に数える |

違反があると終了コードが1になる。`--baseline` では、新規の違反、セリフの変更、±15%を超える字数の増減があったときも1になる。

機械検査が見るのは、冒頭、章末、AI定型、感情ラベル、文末、句点、比喩、長文、説明、の連続、記号の11種類。基準は `references/check.md` にある。

## エージェント別の置き場所

`npx skills add` を使わず手で置くときは、`skills/light-novel/` をフォルダごと次の場所へコピーする。

| エージェント | `-a` の値 | プロジェクト用 | 個人用 | 常時指示 |
| --- | --- | --- | --- | --- |
| Claude Code | `claude-code` | `.claude/skills/light-novel/` | `~/.claude/skills/light-novel/` | `CLAUDE.md` |
| Codex | `codex` | `.agents/skills/light-novel/` | `~/.agents/skills/light-novel/` | `AGENTS.md` |
| Grok Build | `grok` | `.grok/skills/light-novel/` | `~/.grok/skills/light-novel/` | `AGENTS.md`（Codex と同じもの） |

- Claude Code では、依頼が呼び出し条件に合えば自動で起動する。明示するときは `/light-novel`。
- Grok Build は `.claude/skills` と `AGENTS.md` も読むので、同じスキルを二重に置かない。常時文脈に載せるのは `AGENTS.md` の呼び出し条件1行とルール5行だけにして、手順はスキルの起動時に読ませる。
- 常時指示に書いてあるのはスキルへのポインタと最小限のルールだけで、手順はすべて `SKILL.md` 側にある。

## ファイル構成

```text
skills/light-novel/
  SKILL.md                  スキル本体。依頼の分け方、手順、制約
  references/structure.md   ログラインから場面カードまでの構成
  references/style.md       視点、地の文と会話、表記、AI調として削る語
  references/review.md      レビューで違反を返す形
  references/check.md       文体チェックの手順と判断の項目
  references/fix.md         文体の修正の手順と直し方
  references/templates.md   雛形の書き方と置き方
  assets/plot.md            plot.md の雛形（正本）
  assets/characters.md      characters.md の雛形（正本）
  scripts/init_work.py      作品フォルダに雛形を置く
  scripts/check_style.py    文体チェックの機械検査、句点と記号の自動修正、書き換え前後の比較
```

2つのスクリプトは Python 3 の標準ライブラリだけで動く。Python が無い環境でもスキルは使え、雛形は `assets/` から書き写し、機械検査の項目は `references/check.md` を見て目で確かめる。

このリポジトリでは `.claude/skills/light-novel` を `skills/light-novel/` へのシンボリックリンクにしてあり、リポジトリ内の Claude Code からもそのまま使える。

## 呼び出し条件は4か所で同じ文言にしている

- 使う: 日本語のラノベ、ライトノベル、Web小説について、企画、プロット、キャラ、地の文、セリフ、章立て、文体の作成、執筆、推敲、レビュー、文体やAI臭さのチェックを頼まれたとき。
- 使わない: 純文学、脚本、論文、翻訳。

同じ文言が `SKILL.md` の description、`CLAUDE.md`、`AGENTS.md`、この README にある。条件を変えるときは4か所とも直す。

## 開発

```bash
python3 -m unittest discover -s tests
```

`tests/fixtures/` に検査用の本文が3つある。

| ファイル | 中身 |
| --- | --- |
| `natural.md` | 違反0件で通る本文 |
| `ai_like.md` | 機械検査の11種類の違反をすべて含む本文 |
| `ai_like_fixed.md` | `ai_like.md` を `references/fix.md` どおりに直した見本。違反0件で、`--baseline` も通る |

CI は GitHub Actions で、ubuntu、macOS、Windows と Python 3.9、3.13 の組み合わせでテストを回す。あわせて `npx skills add` で一時プロジェクトに入れ、必要なファイルが置かれることを確かめる。

`tests/` はスキルのフォルダの外にあるので、`npx skills add` では入らない。不具合や要望は GitHub の Issues へ。

## ライセンス

[Apache License 2.0](LICENSE)
