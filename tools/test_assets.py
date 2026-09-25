"""Controles op de gegenereerde beelden en de download-PDF (spec §4 en §5)."""
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "img"
BROCHURE = ROOT / "brochure" / "zaad-voor-de-zaaier-brochure.pdf"

# bestandsnaam -> maximale lange zijde (None = logo, ongewijzigd)
GRENZEN = {
    "hero-zaaier.jpg": 1800,
    "hand-zaden.jpg": 1000,
    "bijbel-korenveld.jpg": 1000,
    "hand-graan.jpg": 1000,
    "zakken-graan.jpg": 1000,
    "logo-zaad-voor-de-zaaier.png": None,
    "logo-hebron-missie.png": None,
}
AFGELEID = {"favicon.png", "og-image.jpg"}


@pytest.mark.parametrize("naam", sorted(GRENZEN))
def test_beeld_bestaat_en_past_binnen_grens(naam):
    pad = IMG / naam
    assert pad.exists(), f"{naam} ontbreekt; draai python tools/build-assets.py"
    im = Image.open(pad)
    grens = GRENZEN[naam]
    if grens:
        assert max(im.size) <= grens, f"{naam} is {im.size}, lange zijde > {grens}"
        assert im.format == "JPEG" and im.mode == "RGB"
    else:
        assert im.format == "PNG" and im.mode == "RGBA"


def test_geen_onverwachte_bestanden_in_img():
    """De pagina gebruikt negen beelden (hero, vier blokbeelden, twee logo's, favicon, og-image; geen portretten); alles daarbuiten is ballast in de repo."""
    aanwezig = {p.name for p in IMG.iterdir() if p.is_file()}
    assert aanwezig == set(GRENZEN) | AFGELEID, f"onverwacht in img/: {aanwezig ^ (set(GRENZEN) | AFGELEID)}"


def test_eigen_logo_is_bijgesneden():
    """Geen doorzichtige rand: de tekening vult het hele bestand."""
    im = Image.open(IMG / "logo-zaad-voor-de-zaaier.png")
    kader = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    assert kader == (0, 0, im.width, im.height)


def test_favicon_en_og_image():
    fav = Image.open(IMG / "favicon.png")
    assert fav.size == (64, 64) and fav.mode == "RGBA"
    og = Image.open(IMG / "og-image.jpg")
    assert og.size == (1200, 630)


def test_totaal_gewicht_img_onder_2_mb():
    totaal = sum(p.stat().st_size for p in IMG.iterdir() if p.is_file())
    assert totaal < 2_000_000, f"img/ weegt {totaal / 1e6:.2f} MB"


def test_brochure_pdf():
    assert BROCHURE.exists(), "download-PDF ontbreekt; draai python tools/build-assets.py"
    assert BROCHURE.stat().st_size <= 6_000_000, f"PDF weegt {BROCHURE.stat().st_size / 1e6:.2f} MB"
    assert len(PdfReader(str(BROCHURE)).pages) == 14


def test_brochure_heeft_rekeningnummer():
    """Pagina 8 draagt het rekeningnummer als opgeplakt blok; het Canva-origineel nog niet.
    Maakt build-assets.py de PDF opnieuw uit dat origineel, dan valt het rekeningnummer weg."""
    tekst = PdfReader(str(BROCHURE)).pages[7].extract_text()
    assert "NL83 RABO 0310 5957 62" in tekst, "rekeningnummer ontbreekt op pagina 8 van de brochure"
