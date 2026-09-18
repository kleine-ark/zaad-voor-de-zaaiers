"""Controles op index.html en css/style.css volgens de ontwerpspec (§5)."""
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
CSS = ROOT / "css" / "style.css"
BROCHURE = ROOT / "brochure" / "zaad-voor-de-zaaier-brochure.pdf"

SECTIE_IDS = ["top", "waarom", "rust-geven", "wie", "plan", "project", "rust-oogst",
              "bedieningspaden", "rust-gemeenschap", "geven", "fiscaal", "gegevens",
              "rust-volharding", "rust-boom", "rust-sikkel", "grondslag"]
NAV_ANKERS = ["#waarom", "#wie", "#plan", "#bedieningspaden", "#geven", "#grondslag"]
# Hoofdlettergevoelig; tikfouten uit de brochure en dingen die niet op de site horen.
VERBODEN = ["Zaaiers", "NL.....", "Eein", "betekend", "opleverd", "vind u",
            "luid:", "hiemee", "bedieninsvarianten", "Matth.55", "1 kor.", "word vergeleken",
            "gebeurd er", "verspreid daarmee", "stichting ondersteund", "<script"]
TOKENS = ["--bruin", "--creme", "--papier", "--geel", "--oranje", "--sage", "--lichtblauw",
          "--lei", "--groen", "--roodbruin", "--tekst"]
IBAN = "NL83 RABO 0310 5957 62"
# Beelden die niet lui geladen worden: de hero en het logo in de navigatiebalk.
NIET_LUI = {"img/hero-zaaier.jpg"}


class Dom(HTMLParser):
    """Platte lijst van (tag, attributen) in documentvolgorde; genoeg voor deze controles."""

    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


@pytest.fixture(scope="module")
def html():
    assert INDEX.exists(), "index.html ontbreekt"
    return INDEX.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def dom(html):
    d = Dom()
    d.feed(html)
    return d


@pytest.fixture(scope="module")
def css():
    assert CSS.exists(), "css/style.css ontbreekt"
    return CSS.read_text(encoding="utf-8")


def alle_ids(dom):
    return [a["id"] for _, a in dom.tags if "id" in a]


def iban_geldig(iban: str) -> bool:
    s = iban.replace(" ", "")
    verplaatst = s[4:] + s[:4]
    return int("".join(str(int(c, 36)) for c in verplaatst)) % 97 == 1


# ---- structuur ----

def test_lang_nl_en_precies_een_h1(html, dom):
    assert re.search(r'<html\s+lang="nl"', html)
    assert sum(1 for t, _ in dom.tags if t == "h1") == 1


def test_head_metadata(html):
    assert "<title>" in html and "Zaad voor de Zaaier" in html.split("</title>")[0]
    assert 'name="description"' in html
    assert 'property="og:image"' in html and "img/og-image.jpg" in html
    assert 'rel="icon"' in html and "img/favicon.png" in html
    assert 'href="css/style.css"' in html


def test_skip_link_en_main(html):
    assert 'class="skip-link" href="#inhoud"' in html
    assert '<main id="inhoud">' in html


def test_nav_ankers_verwijzen_naar_bestaande_secties(html, dom):
    ids = alle_ids(dom)
    nav = html.split("<nav")[1].split("</nav>")[0]
    for anker in NAV_ANKERS:
        assert f'href="{anker}"' in nav, f"{anker} ontbreekt in de navigatie"
        assert anker[1:] in ids, f"sectie {anker} bestaat niet"


def test_secties_in_volgorde_en_footer_erna(dom):
    ids = alle_ids(dom)
    posities = []
    for sid in SECTIE_IDS:
        assert sid in ids, f"sectie #{sid} ontbreekt"
        posities.append(ids.index(sid))
    assert posities == sorted(posities), "secties staan niet in de spec-volgorde"
    grondslag = next(i for i, (t, a) in enumerate(dom.tags) if a.get("id") == "grondslag")
    assert "footer" in [t for t, _ in dom.tags[grondslag:]], "footer moet na #grondslag komen"


def test_een_h2_per_sectie(dom):
    assert sum(1 for t, _ in dom.tags if t == "h2") == len(SECTIE_IDS) - 1  # de hero heeft de h1


def test_details_in_grondslag(html):
    na_grondslag = html.split('id="grondslag"')[1]
    assert "<details" in na_grondslag.split("<footer")[0]


# ---- beelden ----

def test_afbeeldingen_bestaan_met_alt_en_juiste_maten(dom):
    imgs = [a for t, a in dom.tags if t == "img"]
    assert imgs, "geen afbeeldingen gevonden"
    nav_logo_gezien = False
    for a in imgs:
        pad = ROOT / a["src"]
        assert pad.exists(), f"{a['src']} ontbreekt"
        assert "alt" in a, f"{a['src']} mist alt"
        w, h = Image.open(pad).size
        assert (int(a["width"]), int(a["height"])) == (w, h), \
            f"{a['src']}: attributen {a.get('width')}x{a.get('height')}, bestand {w}x{h}"
        eerste_logo = a["src"] == "img/logo-zaad-voor-de-zaaier.png" and not nav_logo_gezien
        if eerste_logo:
            nav_logo_gezien = True
        elif a["src"] not in NIET_LUI:
            assert a.get("loading") == "lazy", f"{a['src']} mist loading=lazy"


# ---- tekst ----

def test_geen_verboden_tekst(html):
    for woord in VERBODEN:
        assert woord not in html, f"gevonden: {woord!r}"


def test_iban_exact_en_geldig(html):
    assert IBAN in html
    assert iban_geldig(IBAN)
    assert "Stichting Werkers in de Wijngaard" in html
    assert "Project Zaad voor de Zaaier" in html


def test_geen_link_naar_niet_bestaande_projecturl(html):
    assert not re.search(r'href="[^"]*werkersindewijngaard\.nl/zaadvoordezaaier', html)
    assert "beoogd adres van deze pagina" in html


def test_downloadknop(html):
    assert 'href="brochure/zaad-voor-de-zaaier-brochure.pdf"' in html


# ---- css en gewicht ----

def test_tokens_en_fonts_in_css(css):
    for token in TOKENS:
        assert re.search(rf"{token}:\s*#", css), f"{token} ontbreekt in :root"
    for font in ("../fonts/bebas-neue.woff2", "../fonts/open-sans.woff2"):
        assert font in css
        assert (ROOT / "fonts" / font.split("/")[-1]).exists()


def test_gewicht():
    img_totaal = sum(p.stat().st_size for p in (ROOT / "img").iterdir() if p.is_file())
    assert img_totaal < 4_000_000
    assert BROCHURE.stat().st_size <= 6_000_000
    assert INDEX.stat().st_size + CSS.stat().st_size < 200_000
