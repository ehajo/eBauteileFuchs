"""Offline QR and PDF rendering for location labels."""

from io import BytesIO
from pathlib import Path

import qrcode
import qrcode.image.svg
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from ebauteilefuchs.application.ports.labels import (
    LabelData,
    LabelSheetLayout,
)
from ebauteilefuchs.branding import BRANDING
from ebauteilefuchs.domain.errors import ValidationError

PACKAGE_DIR = Path(__file__).resolve().parents[1]
LOGO_PATH = PACKAGE_DIR / "static" / "branding" / "ehajo-logo.png"
A4_WIDTH_MM = A4[0] / mm
A4_HEIGHT_MM = A4[1] / mm


class ReportLabLabelRenderer:
    """Render compact printable labels without external services."""

    def render_qr_svg(self, payload: str) -> bytes:
        image = qrcode.make(
            payload,
            image_factory=qrcode.image.svg.SvgPathImage,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            border=2,
        )
        output = BytesIO()
        image.save(output)
        return output.getvalue()

    def render_single(self, label: LabelData) -> bytes:
        output = BytesIO()
        page_size = (70 * mm, 36 * mm)
        document = Canvas(output, pagesize=page_size)
        self._set_metadata(document, "Lagerplatz-Einzeletikett")
        self._draw_label(document, label, 0, 0, page_size[0], page_size[1])
        document.showPage()
        document.save()
        return output.getvalue()

    def render_sheet(self, labels: list[LabelData], layout: LabelSheetLayout) -> bytes:
        self._validate_layout(layout)
        output = BytesIO()
        document = Canvas(output, pagesize=A4)
        self._set_metadata(document, "Lagerplatz-QR-Etiketten")
        capacity = layout.columns * layout.rows

        for index, label in enumerate(labels):
            page_index = index % capacity
            column = page_index % layout.columns
            row = page_index // layout.columns
            x = (
                layout.margin_left_mm
                + column * (layout.label_width_mm + layout.horizontal_gap_mm)
            ) * mm
            y = (
                A4_HEIGHT_MM
                - layout.margin_top_mm
                - (row + 1) * layout.label_height_mm
                - row * layout.vertical_gap_mm
            ) * mm
            self._draw_label(
                document,
                label,
                x,
                y,
                layout.label_width_mm * mm,
                layout.label_height_mm * mm,
            )
            if page_index == capacity - 1 and index < len(labels) - 1:
                document.showPage()

        document.showPage()
        document.save()
        return output.getvalue()

    @staticmethod
    def _set_metadata(document: Canvas, title: str) -> None:
        document.setTitle(f"{BRANDING.product_name} - {title}")
        document.setAuthor(BRANDING.owner_name)
        document.setCreator(BRANDING.product_name)
        document.setSubject(BRANDING.tagline)

    @staticmethod
    def _validate_layout(layout: LabelSheetLayout) -> None:
        if not 1 <= layout.columns <= 6 or not 1 <= layout.rows <= 20:
            raise ValidationError("Das Raster muss 1-6 Spalten und 1-20 Zeilen haben.")
        if not 40 <= layout.label_width_mm <= 100:
            raise ValidationError(
                "Die Etikettenbreite muss zwischen 40 und 100 mm liegen."
            )
        if not 25 <= layout.label_height_mm <= 70:
            raise ValidationError(
                "Die Etikettenhöhe muss zwischen 25 und 70 mm liegen."
            )
        values = (
            layout.margin_left_mm,
            layout.margin_top_mm,
            layout.horizontal_gap_mm,
            layout.vertical_gap_mm,
        )
        if any(value < 0 or value > 50 for value in values):
            raise ValidationError(
                "Ränder und Abstände müssen zwischen 0 und 50 mm liegen."
            )
        used_width = (
            layout.margin_left_mm
            + layout.columns * layout.label_width_mm
            + (layout.columns - 1) * layout.horizontal_gap_mm
        )
        used_height = (
            layout.margin_top_mm
            + layout.rows * layout.label_height_mm
            + (layout.rows - 1) * layout.vertical_gap_mm
        )
        if used_width > A4_WIDTH_MM + 0.1 or used_height > A4_HEIGHT_MM + 0.1:
            raise ValidationError(
                "Das konfigurierte Etikettenraster passt nicht auf A4."
            )

    def _draw_label(
        self,
        document: Canvas,
        label: LabelData,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> None:
        padding = 2 * mm
        document.saveState()
        document.setStrokeColor(HexColor("#c7d0d8"))
        document.setLineWidth(0.2)
        document.rect(x + 0.2, y + 0.2, width - 0.4, height - 0.4, stroke=1, fill=0)

        qr_size = min(height - 2 * padding, 29 * mm)
        qr_image = ImageReader(self._qr_png(label.qr_url))
        document.drawImage(
            qr_image,
            x + padding,
            y + (height - qr_size) / 2,
            qr_size,
            qr_size,
            preserveAspectRatio=True,
            mask="auto",
        )

        text_x = x + padding + qr_size + 2 * mm
        text_width = max(10 * mm, width - (text_x - x) - padding)
        top = y + height - padding

        logo_width = min(text_width, 20 * mm)
        logo_height = logo_width * 0.5625
        document.drawImage(
            str(LOGO_PATH),
            text_x,
            top - logo_height,
            logo_width,
            logo_height,
            preserveAspectRatio=True,
            mask="auto",
        )

        cursor_y = top - logo_height - 1.2 * mm
        document.setFillColor(HexColor(BRANDING.primary_color))
        document.setFont("Helvetica-Bold", 10)
        document.drawString(
            text_x,
            cursor_y,
            self._fit_text(label.code, "Helvetica-Bold", 10, text_width),
        )

        cursor_y -= 4.2 * mm
        document.setFillColor(HexColor("#17212b"))
        document.setFont("Helvetica-Bold", 7.5)
        document.drawString(
            text_x,
            cursor_y,
            self._fit_text(label.name, "Helvetica-Bold", 7.5, text_width),
        )

        cursor_y -= 3.2 * mm
        document.setFillColor(HexColor("#4b5966"))
        document.setFont("Helvetica", 6)
        document.drawString(
            text_x,
            cursor_y,
            self._fit_text(label.path, "Helvetica", 6, text_width),
        )

        document.setFont("Helvetica", 5.5)
        document.drawString(text_x, y + padding + 2.8 * mm, label.qr_short_code)
        document.setFillColor(HexColor(BRANDING.secondary_color))
        document.setFont("Helvetica-Bold", 5.5)
        document.drawString(text_x, y + padding, "eBauteileFuchs | eHaJo")
        document.restoreState()

    @staticmethod
    def _qr_png(payload: str) -> BytesIO:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(payload)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white")
        output = BytesIO()
        image.save(output, format="PNG")
        output.seek(0)
        return output

    @staticmethod
    def _fit_text(text: str, font: str, size: float, max_width: float) -> str:
        cleaned = " ".join(text.split())
        if stringWidth(cleaned, font, size) <= max_width:
            return cleaned
        suffix = "..."
        while cleaned and stringWidth(cleaned + suffix, font, size) > max_width:
            cleaned = cleaned[:-1]
        return cleaned.rstrip() + suffix
