#!/usr/bin/env python3
"""作品フォルダに plot.md と characters.md の雛形を置く。

使い方: python3 init_work.py [作品フォルダ]   （省略時は作業ディレクトリ）
雛形は assets/ から複製する。既にあるファイルは上書きしない。
"""
import pathlib
import shutil
import sys

ASSETS = pathlib.Path(__file__).resolve().parent.parent / "assets"
NAMES = ["plot.md", "characters.md"]


def main(argv):
    work = pathlib.Path(argv[1]) if len(argv) > 1 else pathlib.Path.cwd()
    work.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        target = work / name
        if target.exists():
            print(f"既存: {target}")
            continue
        shutil.copyfile(ASSETS / name, target)
        print(f"作成: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
