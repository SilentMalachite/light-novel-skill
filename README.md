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
```

呼び出し条件は SKILL.md の description、CLAUDE.md、AGENTS.md で同じ文言にしている。

- 使う: 日本語のラノベ、ライトノベル、Web小説について、企画、プロット、キャラ、地の文、セリフ、章立て、文体の作成、執筆、推敲、レビューを頼まれたとき。
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

1. `references/templates.md` から `plot.md` と `characters.md` を作品フォルダに置く。
2. 構築を頼む。本文はまだ書かせない。
3. 話を指定して執筆を頼む。
4. 推敲は Codex にレビューとして頼む。

## ライセンス

[Apache License 2.0](LICENSE)
