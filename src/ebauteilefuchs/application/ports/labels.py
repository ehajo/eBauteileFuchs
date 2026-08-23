"""Port for rendering location QR labels."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LabelData:
    code: str
    name: str
    path: str
    qr_url: str
    qr_short_code: str


@dataclass(frozen=True, slots=True)
class LabelSheetLayout:
    columns: int = 3
    rows: int = 8
    label_width_mm: float = 70.0
    label_height_mm: float = 36.0
    margin_left_mm: float = 0.0
    margin_top_mm: float = 4.5
    horizontal_gap_mm: float = 0.0
    vertical_gap_mm: float = 0.0


class LabelRenderer(Protocol):
    def render_single(self, label: LabelData) -> bytes: ...

    def render_sheet(
        self, labels: list[LabelData], layout: LabelSheetLayout
    ) -> bytes: ...

    def render_qr_svg(self, payload: str) -> bytes: ...
