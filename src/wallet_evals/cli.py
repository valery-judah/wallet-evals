from __future__ import annotations

import argparse

from wallet_evals import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wallet_evals", description="Project CLI entrypoint.")
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(__version__)
        return 0

    print("wallet_evals: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
