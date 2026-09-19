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
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/chromium"),
    Path("/usr/bin/chromium-browser"),
]


def chrome() -> Path | None:
    return next((p for p in KANDIDATEN if p.is_file()), None)


@pytest.mark.skipif(chrome() is None, reason="geen Chrome gevonden voor de proefdruk; de A4-eis is dan niet getoetst")
def test_pagina_past_op_een_a4(tmp_path):
    fitz = pytest.importorskip("fitz")
    uit = tmp_path / "proefdruk.pdf"
    opdracht = [
        str(chrome()), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
        f"--user-data-dir={tmp_path / 'profiel'}",  # eigen profiel: geen extensies of open sessie
        f"--print-to-pdf={uit}", "--virtual-time-budget=4000",
        (ROOT / "index.html").resolve().as_uri(),
    ]
    try:
        subprocess.run(opdracht, check=True, capture_output=True, timeout=90)
    except subprocess.CalledProcessError as fout:
        pytest.fail(f"Chrome gaf exitcode {fout.returncode}:\n{fout.stderr.decode(errors='replace')[-2000:]}")
    doc = fitz.open(str(uit))
    breedte_mm, hoogte_mm = doc[0].rect.width / 72 * 25.4, doc[0].rect.height / 72 * 25.4
    assert (round(breedte_mm), round(hoogte_mm)) == (210, 297), "papierformaat is geen A4"
    assert len(doc) == 1, f"proefdruk beslaat {len(doc)} pagina's"
    tekst = doc[0].get_text().replace("\n", " ")
    assert "Arjan Baan" in tekst, "het einde van de tekst ontbreekt in de afdruk"
    assert "NL83 RABO 0310 5957 62" in tekst, "het rekeningnummer ontbreekt in de afdruk"
    assert "Stichting Werkers in de Wijngaard · NL83" in tekst, "de rekeningregel ontbreekt onderaan de afdruk"
