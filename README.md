# ライトノベル・スキルの置き方

本体は1本。配置だけ分ける。常時指示はポインタだけ。

## インストール

```bash
npx skills add SilentMalachite/light-novel-skill
```

エージェントを指定するときは `-a` を付ける。個人用（全プロジェクト共通）にするときは `-g` を付ける。

```bash
npx skills add SilentMalachite/light-novel-skill -a claude-code
npx skills add SilentMalachite/light-novel-skill -a codex
npx skills add SilentMalachite/light-novel-skill -a grok
```

CLAUDE.md と AGENTS.md は入らない。下の各節のとおり手で置く。

## 共通

手で置くときは `skills/light-novel/` をそのままコピーする。

```text
skills/light-novel/
  SKILL.md
  references/structure.md
  references/style.md
  references/review.md
  references/templates.md
  references/check.md
  assets/plot.md
  assets/characters.md
  scripts/check_style.py
  scripts/init_work.py
```

`assets/` は雛形の正本。`scripts/init_work.py` は作品フォルダに雛形を置く。`scripts/check_style.py` は文体チェックの機械検査に使う。どちらも Python 3 の標準ライブラリだけで動く。Python が無くてもスキルは使える。

呼び出し条件は SKILL.md の description、CLAUDE.md、AGENTS.md で同じ文言にしている。

- 使う: 日本語のラノベ、ライトノベル、Web小説について、企画、プロット、キャラ、地の文、セリフ、章立て、文体の作成、執筆、推敲、レビュー、文体やAI臭さのチェックを頼まれたとき。
- 使わない: 純文学、脚本、論文、翻訳。

変えるときは3つとも直す。

## Claude Code

```text
.claude/skills/light-novel/     ← skills/light-novel/ をここへ
CLAUDE.md                       ← 同梱の CLAUDE.md をプロジェクト直下へ（既存があれば末尾に追記）
```

個人用なら `~/.claude/skills/light-novel/`。このリポジトリでは `.claude/skills/light-novel` を `skills/light-novel/` へのシンボリックリンクにしている。

呼び出し: 依頼が上の呼び出し条件に合えば自動。明示は `/light-novel`。

## Codex

```text
.agents/skills/light-novel/     ← skills/light-novel/ をここへ
AGENTS.md                       ← 同梱の AGENTS.md をリポジトリ直下へ（既存があれば末尾に追記）
```

個人用なら `~/.agents/skills/light-novel/`。

Codex はレビューを主にする。本文の書き換えを頼まれていないときは `references/review.md` の形で違反だけ返す。

## Grok Build

```text
.grok/skills/light-novel/       ← skills/light-novel/ をここへ
AGENTS.md                       ← 同梱の AGENTS.md（Codex と同一でよい）
```

Grok Build は `.claude/skills` と `AGENTS.md` も読む。二重に置かない。常時文脈は `AGENTS.md` の呼び出し条件1行とルール5行だけにし、手順はスキル起動時に読ませる。

個人用なら `~/.grok/skills/light-novel/`。

## 使わせ方

1. 「〜を書いて」「〜を執筆して」「〜を作って」と頼むと、作品フォルダに `plot.md` と `characters.md` の雛形が自動で置かれる。作品フォルダを指定しなければ作業ディレクトリに置く。既にあるファイルは上書きしない。手で置くときは次を実行する。

   ```bash
   python3 .claude/skills/light-novel/scripts/init_work.py 作品フォルダ
   ```

2. 構築を頼む。本文はまだ書かせない。
3. 話を指定して執筆を頼む。
4. 推敲は Codex にレビューとして頼む。
5. 文体やAI臭さを確かめたいときは、本文を渡してチェックを頼む。機械検査だけなら次を実行する。

   ```bash
   python3 .claude/skills/light-novel/scripts/check_style.py 本文.md
   ```

   パスはインストール先に合わせる。Codex なら `.agents/skills/`、Grok Build なら `.grok/skills/`。

   ```bash
   cat 本文.md | python3 .claude/skills/light-novel/scripts/check_style.py
   ```

## 使い方の例

依頼は1回に1種類だけ出す。構築、執筆、推敲（チェックを含む）のどれかにする。

### 構築

```text
コンビニで働く魔王の話を作りたい。一人称の俺で、Web連載。plot.md と characters.md を作って。本文はまだいらない。
```

`plot.md` の先頭にログライン、視点、一人称、結末、クライマックスが入る。キャラごとに口調サンプルが3つ付く。

```markdown
- ログライン: 角を隠してコンビニで働く元魔王が、正体を知る勇者の末裔に追われながら、店と居場所を守る話。
- 視点: 一人称
- 一人称: 俺
- 結末: 魔王の名を捨て、店長代理として店に残る。勇者とは客と店員のまま決着する。
```

`plot.md` と `characters.md` が無ければ、先に雛形が置かれる。「魔王の話を書いて」のように本文を頼んだ場合も同じで、雛形を置いて分かる項目を埋めたところで止まる。

ログライン、視点、結末のどれかが決まっていないときは、質問が返る（最大3つ）。足りないまま本文は書かない。

### 執筆

```text
plot.md の第1話、1場面目を書いて。
```

先に場面カードを埋めて、その場面の本文だけを返す。前後の場面、新しいキャラ、解説は付かない。口調サンプルが無いキャラのセリフは書かない。

### 推敲

```text
第1話を推敲して。筋は変えないで。
```

視点の越境、説明台詞、AI調、口調の取り違えを最小限だけ直す。Codex に頼むときは本文を書き換えず、違反を箇所つきで返す。

```text
- [視点] 3章2場面: 一人称なのに相手の内心を断定している。伝聞か、観察できる動作に置換。
- [章末] 4章: 解決して終わっている。未解決を1つ残す。
```

### 文体チェック、AI臭さチェック

```text
episode01.md、AI臭くないか、ラノベらしい文体になってるかチェックして。
```

本文は書き換えない。機械検査の結果に判断の項目を足して、違反一覧、判定、統計の順で返す。

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

上の例は `tests/fixtures/ai_like.md` を検査したときの出力の抜粋。違反の行はスクリプトの出力そのまま。判定はエージェントが付けたもので、実行ごとに変わることがある。

## 開発

```bash
python3 -m unittest discover -s tests
```

`tests/` はスキルの外にあるので、`npx skills add` では入らない。

## ライセンス

[Apache License 2.0](LICENSE)
