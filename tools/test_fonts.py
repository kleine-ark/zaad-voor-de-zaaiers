"""Controles op de zelf-gehoste lettertypen."""
from pathlib import Path

import pytest

FONTS = Path(__file__).resolve().parent.parent / "fonts"


@pytest.mark.parametrize("naam", ["bebas-neue.woff2", "open-sans.woff2"])
def test_font_is_geldig_woff2(naam):
    pad = FONTS / naam
    assert pad.exists(), f"{naam} ontbreekt; draai python tools/fetch-fonts.py"
    data = pad.read_bytes()
    assert data[:4] == b"wOF2", f"{naam} is geen woff2-bestand"
    assert 10_000 < len(data) < 200_000, f"{naam} heeft een onverwachte grootte: {len(data)} bytes"


def test_licentievermelding_aanwezig():
    tekst = (FONTS / "README.md").read_text(encoding="utf-8")
    assert "SIL Open Font License" in tekst
    assert "Bebas Neue" in tekst and "Open Sans" in tekst


@pytest.mark.parametrize("naam, notice", [
    ("OFL-bebas-neue.txt", "Dharma Type"),
    ("OFL-open-sans.txt", "Open Sans"),
])
def test_licentietekst_meegeleverd(naam, notice):
    """De OFL eist dat elke kopie de copyright-notice én de volledige licentietekst bevat."""
    pad = FONTS / naam
    assert pad.exists(), f"{naam} ontbreekt"
    tekst = pad.read_text(encoding="utf-8")
    assert "SIL OPEN FONT LICENSE Version 1.1" in tekst
    assert "Copyright" in tekst and notice in tekst
