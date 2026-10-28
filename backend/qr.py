"""Screenshot OCR + QR extraction interfaces (optional dependencies).

OCR: Tesseract (mar/hin/eng) via pytesseract, if installed. QR: pyzbar,
if installed. Both return {"status": "unavailable", "reason": ...} when
the optional dependency is missing — never a fabricated result.
The frontend must show that status, not an invented transcription.
"""
from __future__ import annotations

def ocr_image(path: str, langs: str = "mar+hin+eng") -> dict:
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError:
        return {"status": "unavailable",
                "reason": "pytesseract/Pillow not installed. Install: pip install pytesseract Pillow (plus Tesseract mar/hin/eng language data)."}
    try:
        text = pytesseract.image_to_string(Image.open(path), lang=langs)
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}
    return {"status": "ok", "text": text, "langs": langs,
            "note": "OCR text is a transcription aid only; it is not a verdict on authenticity."}

def decode_qr(path: str) -> dict:
    try:
        from pyzbar.pyzbar import decode  # type: ignore
        from PIL import Image  # type: ignore
    except ImportError:
        return {"status": "unavailable",
                "reason": "pyzbar/Pillow not installed. Install: pip install pyzbar Pillow. Never open a decoded QR URL automatically."}
    try:
        codes = decode(Image.open(path))
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}
    return {"status": "ok", "codes": [c.data.decode(errors="replace") for c in codes],
            "note": "A decoded URL is never opened automatically; it is analysed as text only."}
