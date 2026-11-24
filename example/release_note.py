"""Render the release notes used in the isolated Harness exercise."""

import argparse
from pathlib import Path


def render_release_note(version, changes):
    version = version.strip()
    items = [change.strip() for change in changes if change.strip()]
    if not version or not items:
        raise ValueError("请提供版本和至少一条变更。")
    bullets = "\n".join(f"- {item}" for item in items)
    return f"# {version}\n\n{bullets}\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version")
    parser.add_argument("changes", nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        notes = render_release_note(args.version, args.changes)
    except ValueError as error:
        parser.error(str(error))
    args.output.write_text(notes, encoding="utf-8")


if __name__ == "__main__":
    main()
