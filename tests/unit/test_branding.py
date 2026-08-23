import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]
TOKENS_PATH = (
    PROJECT_ROOT / "src" / "ebauteilefuchs" / "static" / "css" / "design-tokens.css"
)


def _relative_luminance(color: str) -> float:
    values = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in values
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(first), _relative_luminance(second)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def _tokens() -> dict[str, str]:
    content = TOKENS_PATH.read_text(encoding="utf-8")
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6});", content))


def test_packaged_logo_matches_approved_branding_asset() -> None:
    approved = PROJECT_ROOT / "branding" / "ehajo-logo.svg"
    packaged = (
        PROJECT_ROOT
        / "src"
        / "ebauteilefuchs"
        / "static"
        / "branding"
        / "ehajo-logo.svg"
    )

    assert packaged.read_bytes() == approved.read_bytes()


def test_core_text_colors_have_wcag_aa_contrast() -> None:
    tokens = _tokens()

    assert _contrast(tokens["color-text"], tokens["color-bg"]) >= 4.5
    assert _contrast(tokens["color-text-muted"], tokens["color-surface"]) >= 4.5
    assert _contrast(tokens["color-link"], tokens["color-bg"]) >= 4.5


def test_required_brand_colors_remain_unchanged() -> None:
    tokens = _tokens()

    assert tokens["color-brand-primary"] == "#0b72b5"
    assert tokens["color-brand-secondary"] == "#e67c23"
