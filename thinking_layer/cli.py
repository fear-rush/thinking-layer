from __future__ import annotations

import argparse

from .config.paths import CORPUS_DIR, OCR_NEEDED_PATH, RAW_LITEPARSE_DIR
from .corpus.builder import cmd_build


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Thinking Layer hard-cutover migration utilities."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser(
        "build",
        help="Build the clean corpus from eligible saved non-OCR raw pages.",
    )
    build_parser.add_argument("--raw-dir", default=str(RAW_LITEPARSE_DIR))
    build_parser.add_argument("--output-dir", default=str(CORPUS_DIR))
    build_parser.add_argument("--ocr-needed", default=str(OCR_NEEDED_PATH))
    build_parser.set_defaults(func=cmd_build)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
