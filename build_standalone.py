"""Generate the two single-file activities from the shared modules.

`minichess.py` and `research_compass.py` are promised to be self-contained,
but the logic inside them must not be a second, drifting copy of the modules
the main app runs. So they are generated: this script inlines theme.py, the
relevant engine and the relevant UI, in that order, with their module
docstrings and local imports removed and the remaining imports hoisted.

    python3 build_standalone.py            # write both files
    python3 build_standalone.py --check    # fail if either file is out of date

The check runs as part of the test suite, so a fix applied to a module can
never silently miss the standalone copies.
"""
import argparse
import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCAL_MODULES = {"theme", "chess_engine", "compass_engine", "chess_ui", "compass_ui"}

BUILDS = {
    "minichess.py": {
        "modules": ["theme.py", "chess_engine.py", "chess_ui.py"],
        "title": "MiniChess",
        "heading": "MiniChess",
    },
    "research_compass.py": {
        "modules": ["theme.py", "compass_engine.py", "compass_ui.py"],
        "title": "AI × Open Science Compass",
        "heading": "AI × Open Science Compass",
    },
}

HEADER = '''"""{heading} — Sinuhé Perea · OSA / MPG · 15 September 2026.

Run:     python3 -m streamlit run {filename}
Install: python3 -m pip install 'streamlit>=1.58,<2' 'plotly>=5.17,<7'

GENERATED FILE — do not edit by hand. It is assembled from {sources}
by build_standalone.py, so this activity and the combined app.py always run
identical logic. Edit those modules and run `python3 build_standalone.py`.

This file contains the activity and its complete calculation logic. No
companion Python modules, AI API keys or remote services are required. Keep
.streamlit/config.toml alongside it for the black and green workshop theme.
Public hosting runs this code on the host, not only in the participant's
browser. Original workshop code: MIT licence. See the accompanying LICENSE.
"""
'''


def dissect(path):
    """Split one module into (imports to hoist, body with docstring removed)."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()
    imports, drop = [], set()
    for index, node in enumerate(tree.body):
        if index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            drop.update(range(node.lineno, node.end_lineno + 1))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            drop.update(range(node.lineno, node.end_lineno + 1))
            module = node.module if isinstance(node, ast.ImportFrom) else None
            names = {module} if module else {alias.name for alias in node.names}
            if not names & LOCAL_MODULES:
                imports.append(ast.get_source_segment(source, node))
    body = "\n".join(line for number, line in enumerate(lines, 1) if number not in drop)
    return imports, body.strip("\n")


def build(filename):
    """Return the complete text of one generated single-file activity."""
    spec = BUILDS[filename]
    imports, blocks = [], []
    for module in spec["modules"]:
        module_imports, body = dissect(HERE / module)
        for statement in module_imports:
            if statement not in imports:
                imports.append(statement)
        if module.endswith("_ui.py"):
            body = body.replace(f'SOURCE_FILES = ("{spec["modules"][1]}",)',
                                "SOURCE_FILES = ()")
        blocks.append(f"# {'=' * 72}\n# {module}\n# {'=' * 72}\n\n{body}")
    plain = sorted(s for s in imports if s.startswith("import "))
    from_ = sorted(s for s in imports if s.startswith("from "))
    entry = ('# ' + '=' * 72 + "\n# entry point\n# " + '=' * 72 + "\n\n"
             f'page_setup("{spec["title"]}")\nsidebar_identity()\nrender()\n')
    return (HEADER.format(heading=spec["heading"], filename=filename,
                          sources=", ".join(spec["modules"]))
            + "\n" + "\n".join(plain + [""] + from_).strip("\n")
            + "\n\n\n" + "\n\n\n".join(blocks + [entry]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="report stale files instead of rewriting them")
    arguments = parser.parse_args(argv)
    stale = []
    for filename in BUILDS:
        target = HERE / filename
        fresh = build(filename)
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if fresh == current:
            print(f"up to date  {filename}")
        elif arguments.check:
            stale.append(filename)
            print(f"OUT OF DATE {filename}")
        else:
            target.write_text(fresh, encoding="utf-8")
            print(f"written     {filename}  ({len(fresh.splitlines())} lines)")
    if stale:
        print("\nRun: python3 build_standalone.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
