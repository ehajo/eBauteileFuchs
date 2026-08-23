import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def test_local_markdown_links_resolve() -> None:
    missing: list[str] = []

    for document in PROJECT_ROOT.rglob("*.md"):
        if any(
            part.startswith(".") for part in document.relative_to(PROJECT_ROOT).parts
        ):
            continue
        content = document.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(content):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = target.split("#", maxsplit=1)[0]
            if target_path and not (document.parent / target_path).resolve().exists():
                missing.append(f"{document.relative_to(PROJECT_ROOT)} -> {target}")

    assert not missing, "Ungültige lokale Dokumentationslinks:\n" + "\n".join(missing)
