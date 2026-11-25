#!/usr/bin/env python3
"""Check the docs system described in docs/global/docs-system.md.

Usage (from anywhere inside the repository):

    python3 docs/global/tools/docs_check.py           # check; exit code 1 on errors
    python3 docs/global/tools/docs_check.py --fix     # also rewrite the index block in CLAUDE.md
    python3 docs/global/tools/docs_check.py --no-git  # skip the staleness check

Errors: missing or incomplete front matter, broken relative links, an index
block in CLAUDE.md that does not match the docs, `code` entries that match
nothing. Warnings: docs whose `code` changed after their `verified` date,
broken anchors, oversized files.

Python 3.8+ standard library only, so the file can be copied to any project.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

INDEX_START = "<!-- docs-index:start -->"
INDEX_END = "<!-- docs-index:end -->"
REQUIRED_KEYS = ("description", "read_when")
ROOT_FILE = "CLAUDE.md"
ROOT_MAX_LINES = 200
DOC_MAX_LINES = 500
DOC_MAX_CHARS = 40_000

# Top-level project docs, in the order the index lists them.
PROJECT_ORDER = [
    "overview.md",
    "architecture.md",
    "development.md",
    "deployment.md",
    "decisions.md",
    "todo.md",
]
GROUP_TITLES = {
    "global": "Global — portable, identical in every project",
    "project": "Project",
    "project/features": "Features — business rules across all subprojects",
    "project/contracts": "Contracts — other teams' specs, verbatim",
    "project/testing": "Test plans — manual checks",
}

LINK_RE = re.compile(r"!?\[(?:[^\]\\]|\\.)*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
FENCE_RE = re.compile(r"^(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "data:")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def warn(self, where: str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")


class Doc:
    def __init__(self, path: Path, root: Path) -> None:
        self.path = path
        self.rel = path.relative_to(root).as_posix()
        self.text = path.read_text(encoding="utf-8")
        self.meta, self.body = parse_front_matter(self.text)

    @property
    def docs_rel(self) -> str:
        """Path relative to docs/ (what the index shows)."""
        return self.rel[len("docs/"):]


def parse_front_matter(text: str) -> tuple[dict | None, str]:
    """A YAML subset: `key: value` lines and `- item` lists under a bare `key:`."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    block = text[4:end]
    body = text[end + 4:].lstrip("\n")
    meta: dict = {}
    current_list: str | None = None
    for raw in block.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_list is not None:
            item = re.sub(r"\s+#\s.*$", "", stripped[2:].strip())
            meta[current_list].append(item.strip("'\""))
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            # A trailing " # comment" is dropped; "#" without a space stays.
            key, value = key.strip(), re.sub(r"(^|\s+)#\s.*$", "", value.strip())
            if value:
                meta[key] = value.strip("'\"")
                current_list = None
            else:
                meta[key] = []
                current_list = key
    return meta, body


def strip_code(text: str) -> str:
    """Drop fenced blocks and inline code spans so their examples are not checked."""
    out, in_fence = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else INLINE_CODE_RE.sub("", line))
    return "\n".join(out)


def slugify(heading: str) -> str:
    """GitHub's heading anchors: lower case, punctuation dropped, spaces to hyphens."""
    heading = INLINE_CODE_RE.sub(lambda m: m.group(0).strip("`"), heading)
    heading = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    heading = heading.replace("*", "")
    slug = re.sub(r"[^\w\- ]", "", heading.lower(), flags=re.UNICODE)
    return slug.replace(" ", "-")


def anchors_of(text: str) -> set[str]:
    anchors, seen = set(), {}
    for line in strip_code_keep_headings(text).splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        slug = slugify(match.group(2))
        count = seen.get(slug, 0)
        anchors.add(slug if count == 0 else f"{slug}-{count}")
        seen[slug] = count + 1
    return anchors


def strip_code_keep_headings(text: str) -> str:
    out, in_fence = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def check_links(path: Path, text: str, root: Path, report: Report) -> None:
    where = path.relative_to(root).as_posix()
    for line_no, line in enumerate(strip_code(text).splitlines(), start=1):
        for match in LINK_RE.finditer(line):
            target = match.group(1)
            if target.startswith(EXTERNAL_PREFIXES):
                continue
            file_part, _, anchor = target.partition("#")
            if not file_part:
                if anchor and anchor not in anchors_of(text):
                    report.warn(f"{where}:{line_no}", f"no heading for anchor #{anchor}")
                continue
            resolved = (path.parent / file_part).resolve()
            if not resolved.exists():
                report.error(f"{where}:{line_no}", f"broken link → {target}")
                continue
            if anchor and resolved.suffix == ".md" and resolved.is_file():
                if anchor not in anchors_of(resolved.read_text(encoding="utf-8")):
                    report.warn(f"{where}:{line_no}", f"no heading for anchor → {target}")


def glob_to_regex(pattern: str) -> re.Pattern:
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def is_glob(pattern: str) -> bool:
    return any(ch in pattern for ch in "*?[")


def matches(pattern: str, rel_path: str) -> bool:
    if is_glob(pattern):
        return bool(glob_to_regex(pattern).match(rel_path))
    pattern = pattern.rstrip("/")
    return rel_path == pattern or rel_path.startswith(pattern + "/")


def git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return None
    return result.stdout if result.returncode == 0 else None


def pathspecs(patterns: list[str]) -> list[str]:
    return [f":(glob){p}" if is_glob(p) else p for p in patterns]


def check_code(doc: Doc, root: Path, report: Report) -> list[str]:
    patterns = doc.meta.get("code") or []
    if isinstance(patterns, str):
        patterns = [patterns]
    for pattern in patterns:
        if is_glob(pattern):
            if not any(root.glob(pattern)):
                report.error(doc.rel, f"code entry matches nothing: {pattern}")
        elif not (root / pattern).exists():
            report.error(doc.rel, f"code path does not exist: {pattern}")
    return patterns


def check_staleness(doc: Doc, patterns: list[str], root: Path, changed: set[str], report: Report) -> None:
    if not patterns:
        return
    today = dt.date.today()
    verified_raw = doc.meta.get("verified")
    verified = None
    if isinstance(verified_raw, str):
        try:
            verified = dt.date.fromisoformat(verified_raw)
        except ValueError:
            report.error(doc.rel, f"verified is not a YYYY-MM-DD date: {verified_raw}")
            return
    if verified is None:
        last = git(root, "log", "-1", "--format=%cs", "--", doc.rel)
        verified = dt.date.fromisoformat(last.strip()) if last and last.strip() else today

    code_last = git(root, "log", "-1", "--format=%cs", "--", *pathspecs(patterns))
    if code_last and code_last.strip():
        code_date = dt.date.fromisoformat(code_last.strip())
        if code_date > verified:
            report.warn(
                doc.rel,
                f"code changed on {code_date} after verified {verified}: re-check the doc, then set verified",
            )

    dirty_code = sorted(p for p in changed if any(matches(pat, p) for pat in patterns))
    if dirty_code and doc.rel not in changed and verified < today:
        sample = ", ".join(dirty_code[:3]) + (" …" if len(dirty_code) > 3 else "")
        report.warn(doc.rel, f"uncommitted code changes ({sample}) but the doc is untouched")


def changed_paths(root: Path) -> set[str]:
    out = git(root, "status", "--porcelain", "-uall")
    paths: set[str] = set()
    for line in (out or "").splitlines():
        entry = line[3:]
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        paths.add(entry.strip('"'))
    return paths


def group_key(doc: Doc) -> str:
    parent = Path(doc.docs_rel).parent.as_posix()
    return parent


def group_sort(key: str) -> tuple:
    if key == "global":
        return (0, "")
    if key == "project":
        return (1, "")
    if key == "project/features":
        return (2, "")
    return (3, key)


def doc_sort(doc: Doc) -> tuple:
    name = Path(doc.rel).name
    if group_key(doc) == "project" and name in PROJECT_ORDER:
        return (0, PROJECT_ORDER.index(name), name)
    return (0 if name == "README.md" else 1, 0, name)


def group_title(key: str) -> str:
    if key in GROUP_TITLES:
        return GROUP_TITLES[key]
    tail = key.split("/", 1)[1] if key.startswith("project/") else key
    return tail.replace("-", " ").replace("/", " / ").capitalize()


def build_index(docs: list[Doc]) -> str:
    groups: dict[str, list[Doc]] = {}
    for doc in docs:
        groups.setdefault(group_key(doc), []).append(doc)
    lines = [INDEX_START]
    for key in sorted(groups, key=group_sort):
        lines.append(f"### {group_title(key)}")
        lines.append("")
        for doc in sorted(groups[key], key=doc_sort):
            description = str(doc.meta.get("description", "")).strip()
            read_when = str(doc.meta.get("read_when", "")).strip().rstrip(".")
            lines.append(f"- [{doc.docs_rel}]({doc.rel}) — {description} Read when: {read_when}.")
        lines.append("")
    lines.append(INDEX_END)
    return "\n".join(lines)


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "docs" / "global" / "docs-system.md").exists():
            return candidate
    raise SystemExit("docs_check: no docs/global/docs-system.md found above " + str(start))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fix", action="store_true", help="rewrite the index block in CLAUDE.md")
    parser.add_argument("--no-git", action="store_true", help="skip the staleness check")
    parser.add_argument("--root", type=Path, help="repository root (default: found from this file)")
    args = parser.parse_args()

    root = (args.root or find_root(Path(__file__).resolve().parent)).resolve()
    report = Report()

    doc_paths = sorted(
        p for p in (root / "docs").rglob("*.md")
        if "templates" not in p.relative_to(root / "docs").parts
    )
    docs = [Doc(p, root) for p in doc_paths]

    use_git = not args.no_git and git(root, "rev-parse", "--is-inside-work-tree") is not None
    changed = changed_paths(root) if use_git else set()

    for doc in docs:
        if doc.meta is None:
            report.error(doc.rel, "no front matter (--- block with description and read_when)")
            doc.meta = {}
        for key in REQUIRED_KEYS:
            if not str(doc.meta.get(key, "")).strip():
                report.error(doc.rel, f"front matter lacks {key}")
        check_links(doc.path, doc.text, root, report)
        patterns = check_code(doc, root, report)
        if use_git:
            check_staleness(doc, patterns, root, changed, report)
        lines = doc.text.count("\n") + 1
        try:
            max_lines = int(str(doc.meta.get("max_lines", DOC_MAX_LINES)))
        except ValueError:
            report.error(doc.rel, f"max_lines is not a number: {doc.meta.get('max_lines')}")
            max_lines = DOC_MAX_LINES
        if lines > max_lines or len(doc.text) > DOC_MAX_CHARS:
            report.warn(doc.rel, f"{lines} lines / {len(doc.text)} chars: consider splitting")

    root_file = root / ROOT_FILE
    if not root_file.exists():
        report.error(ROOT_FILE, "missing")
    else:
        text = root_file.read_text(encoding="utf-8")
        check_links(root_file, text, root, report)
        start, end = text.find(INDEX_START), text.find(INDEX_END)
        if start == -1 or end == -1 or end < start:
            report.error(ROOT_FILE, f"no index markers ({INDEX_START} … {INDEX_END})")
        else:
            expected = build_index([d for d in docs if d.meta])
            current = text[start:end + len(INDEX_END)]
            if current.strip() != expected.strip():
                if args.fix:
                    text = text[:start] + expected + text[end + len(INDEX_END):]
                    root_file.write_text(text, encoding="utf-8")
                    print(f"docs_check: rewrote the index in {ROOT_FILE}")
                else:
                    report.error(ROOT_FILE, "index is out of date: run docs_check.py --fix")
        root_lines = text.count("\n") + 1
        if root_lines > ROOT_MAX_LINES:
            report.warn(ROOT_FILE, f"{root_lines} lines (keep under {ROOT_MAX_LINES})")

    for message in report.errors:
        print(f"error   {message}")
    for message in report.warnings:
        print(f"warning {message}")
    print(
        f"docs_check: {len(docs)} docs, {len(report.errors)} errors, "
        f"{len(report.warnings)} warnings"
    )
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
