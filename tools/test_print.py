"""Proefdruk: de pagina moet op één A4 passen. Gebruikt headless Chrome; overgeslagen als dat ontbreekt."""
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
KANDIDATEN = [
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/chromium"),
]


def chrome() -> Path | None:
    return next((p for p in KANDIDATEN if p.is_file()), None)


@pytest.mark.skipif(chrome() is None, reason="geen Chrome gevonden voor de proefdruk")
def test_pagina_past_op_een_a4(tmp_path):
    fitz = pytest.importorskip("fitz")
    uit = tmp_path / "proefdruk.pdf"
    subprocess.run(
        [str(chrome()), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={uit}", "--virtual-time-budget=4000", (ROOT / "index.html").resolve().as_uri()],
        check=True, capture_output=True, timeout=90,
    )
    doc = fitz.open(str(uit))
    breedte_mm, hoogte_mm = doc[0].rect.width / 72 * 25.4, doc[0].rect.height / 72 * 25.4
    assert (round(breedte_mm), round(hoogte_mm)) == (210, 297), "papierformaat is geen A4"
    assert len(doc) == 1, f"proefdruk beslaat {len(doc)} pagina's"
    assert "NL83 RABO 0310 5957 62" in doc[0].get_text().replace("\n", " ")
