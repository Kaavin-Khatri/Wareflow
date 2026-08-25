"""Barcode and QR code generation service.

Provides EAN-13 check-digit calculation, internal barcode generation for products
lacking an official UPC/EAN, and high-resolution PNG image rendering for barcodes
and QR codes.
"""

import io
import random
import re
from typing import Any

import barcode
import qrcode
from barcode.writer import ImageWriter


def calculate_ean13_checksum(digits12: str) -> int:
    """Calculate the 13th check digit for a 12-digit EAN-13 payload using modulo-10.

    Position weights from left to right (0-indexed):
    - Even index (0, 2, 4, 6, 8, 10): weight 1
    - Odd index (1, 3, 5, 7, 9, 11): weight 3
    """
    clean_digits = re.sub(r"\D", "", digits12)
    if len(clean_digits) != 12:
        raise ValueError(f"EAN-13 check digit requires exactly 12 digits, got {len(clean_digits)}")

    total = sum(int(d) * (3 if i % 2 == 1 else 1) for i, d in enumerate(clean_digits))
    return (10 - (total % 10)) % 10


def generate_internal_ean13(prefix: str = "20", sequence_id: int | None = None) -> str:
    """Generate a valid 13-digit EAN-13 barcode for internal warehouse items.

    Uses GS1 restricted circulation prefix '20' (or custom prefix) followed by
    10 data digits and the computed check digit.
    """
    prefix_clean = re.sub(r"\D", "", prefix)
    needed_len = 12 - len(prefix_clean)
    if needed_len < 1:
        prefix_clean = "20"
        needed_len = 10

    if sequence_id is not None:
        seq_str = str(abs(sequence_id))
        if len(seq_str) > needed_len:
            seq_str = seq_str[-needed_len:]
        data_middle = seq_str.zfill(needed_len)
    else:
        data_middle = "".join(str(random.randint(0, 9)) for _ in range(needed_len))

    base_12 = f"{prefix_clean}{data_middle}"
    check_digit = calculate_ean13_checksum(base_12)
    return f"{base_12}{check_digit}"


class BarcodeService:
    """Service handling barcode and QR code generation and image rendering."""

    @staticmethod
    def render_barcode_png(
        code: str,
        options: dict[str, Any] | None = None,
    ) -> bytes:
        """Render a barcode as PNG image bytes.

        Automatically selects EAN-13 if code consists of 12 or 13 numeric digits,
        otherwise falls back to Code 128 for arbitrary alphanumeric SKUs.
        """
        if not code or not code.strip():
            raise ValueError("Barcode value cannot be empty.")

        clean_code = code.strip()
        is_numeric = clean_code.isdigit()

        writer = ImageWriter()
        default_opts = {
            "module_width": 0.3,
            "module_height": 12.0,
            "quiet_zone": 3.0,
            "font_size": 10,
            "text_distance": 4.0,
            "background": "white",
            "foreground": "black",
        }
        if options:
            default_opts.update(options)

        buffer = io.BytesIO()

        if is_numeric and len(clean_code) in (12, 13):
            # If 13 digits, pass first 12 to python-barcode which recalculates and verifies check digit
            data_to_encode = clean_code[:12]
            barcode_cls = barcode.get_barcode_class("ean13")
            barcode_instance = barcode_cls(data_to_encode, writer=writer)
            barcode_instance.write(buffer, options=default_opts)
        else:
            # Code 128 supports full ASCII alphanumeric SKUs
            barcode_cls = barcode.get_barcode_class("code128")
            barcode_instance = barcode_cls(clean_code, writer=writer)
            barcode_instance.write(buffer, options=default_opts)

        return buffer.getvalue()

    @staticmethod
    def render_qr_code_png(
        data: str,
        box_size: int = 8,
        border: int = 2,
    ) -> bytes:
        """Render a 2D QR code as PNG image bytes."""
        if not data or not data.strip():
            raise ValueError("QR code data cannot be empty.")

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data.strip())
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
