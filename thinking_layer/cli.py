from __future__ import annotations

import argparse

from .config.paths import (
    CORPUS_DIR,
    DOWNLOADS_DIR,
    OCR_NEEDED_PATH,
    RAW_LITEPARSE_DIR,
    SOURCE_RECORDS_DIR,
)
from .corpus.builder import cmd_build
from .corpus.extraction import cmd_extract


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Thinking Layer hard-cutover migration utilities."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser(
        "build",
        help="Build the clean corpus from eligible fresh OCR-disabled raw pages.",
    )
    build_parser.add_argument("--raw-dir", default=str(RAW_LITEPARSE_DIR))
    build_parser.add_argument("--output-dir", default=str(CORPUS_DIR))
    build_parser.add_argument("--ocr-needed", default=str(OCR_NEEDED_PATH))
    build_parser.set_defaults(func=cmd_build)

    extract_parser = subparsers.add_parser(
        "extract",
        help="Create a fresh OCR-disabled LiteParse corpus input from downloaded PDFs.",
    )
    extract_parser.add_argument("--downloads-dir", default=str(DOWNLOADS_DIR))
    extract_parser.add_argument("--source-records-dir", default=str(SOURCE_RECORDS_DIR))
    extract_parser.add_argument("--raw-dir", default=str(RAW_LITEPARSE_DIR))
    extract_parser.add_argument("--ocr-needed", default=str(OCR_NEEDED_PATH))
    extract_parser.set_defaults(func=cmd_extract)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
