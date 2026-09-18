"""Controles op index.html en css/style.css volgens de spec 'samenvatting op één A4' (§5)."""
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
CSS = ROOT / "css" / "style.css"
BROCHURE = ROOT / "brochure" / "zaad-voor-de-zaaier-brochure.pdf"

# Vroege waarschuwing; de echte A4-bewaker is tools/test_print.py.
WOORDBUDGET = 420
SECTIE_IDS = ["top", "wat", "hoe", "meedoen"]
# Hoofdlettergevoelig; tikfouten uit de brochure en dingen die niet op de site horen.
VERBODEN = ["Zaaiers", "NL.....", "Eein", "betekend", "opleverd", "vind u",
            "luid:", "hiemee", "bedieninsvarianten", "Matth.55", "1 kor.", "word vergeleken",
            "gebeurd er", "verspreid daarmee", "stichting ondersteund", "<script"]
# Moet in de leesbare tekst van main + voettekst staan (niet alleen in alt-teksten of attributen).
KERNINHOUD = ["Hebron Missie", "Werkers in de Wijngaard", "Parttime", "Fulltime", "ANBI",
              "periodieke gift", "2 Kor. 9:10", "2 Kor. 9:7", "Rom. 12:4–5", "Maarten Vroegindeweij",
              "Stefan de Heer", "Philadelphia", "Gospel Image", "kunnen binnen de wettelijke kaders aftrekbaar zijn"]
STICHTINGEN = ("https://www.hebronmissie.nl", "https://www.werkersindewijngaard.nl")
TOKENS = ["--bruin", "--creme", "--papier", "--geel", "--oranje", "--sage", "--lichtblauw",
          "--lei", "--groen", "--roodbruin", "--tekst"]
IBAN = "NL83 RABO 0310 5957 62"
# Beelden boven de vouw worden niet lui geladen: hero, portretten en (via de lus) het kopregel-logo.
NIET_LUI = {"img/hero-zaaier.jpg", "img/maarten.jpg", "img/stefan.jpg"}


class Dom(HTMLParser):
    """Platte lijst van (tag, attributen) plus de leesbare tekst van <main> en <footer>."""

    def __init__(self):
        super().__init__()
        self.tags = []
        self.main_tekst = []
        self.voet_tekst = []
        self._in = None

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag in ("main", "footer"):
            self._in = tag

    def handle_endtag(self, tag):
        if tag in ("main", "footer"):
            self._in = None

    def handle_data(self, data):
        if self._in == "main":
            self.main_tekst.append(data)
        elif self._in == "footer":
            self.voet_tekst.append(data)


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


def test_secties_in_volgorde_en_footer_erna(dom):
    ids = alle_ids(dom)
    posities = []
    for sid in SECTIE_IDS:
        assert sid in ids, f"sectie #{sid} ontbreekt"
        posities.append(ids.index(sid))
    assert posities == sorted(posities), "secties staan niet in de spec-volgorde"
    laatste = next(i for i, (t, a) in enumerate(dom.tags) if a.get("id") == SECTIE_IDS[-1])
    assert "footer" in [t for t, _ in dom.tags[laatste:]], "footer moet na de laatste sectie komen"


def test_drie_stappen(dom):
    stappen = [a for t, a in dom.tags if "stap" in a.get("class", "").split()]
    assert len(stappen) == 3, f"{len(stappen)} stappen gevonden, verwacht 3"


# ---- beelden ----

def test_afbeeldingen_bestaan_met_alt_en_juiste_maten(dom):
    imgs = [a for t, a in dom.tags if t == "img"]
    assert imgs, "geen afbeeldingen gevonden"
    kopregel_logo_gezien = False
    for a in imgs:
        pad = ROOT / a["src"]
        assert pad.exists(), f"{a['src']} ontbreekt"
        assert "alt" in a, f"{a['src']} mist alt"
        w, h = Image.open(pad).size
        assert (int(a["width"]), int(a["height"])) == (w, h), \
            f"{a['src']}: attributen {a.get('width')}x{a.get('height')}, bestand {w}x{h}"
        eerste_logo = a["src"] == "img/logo-zaad-voor-de-zaaier.png" and not kopregel_logo_gezien
        if eerste_logo:
            kopregel_logo_gezien = True
        elif a["src"] not in NIET_LUI:
            assert a.get("loading") == "lazy", f"{a['src']} mist loading=lazy"


# ---- tekst ----

def test_woordbudget(dom):
    tekst = " ".join(dom.main_tekst)
    woorden = len(re.findall(r"\S+", tekst))
    assert woorden <= WOORDBUDGET, f"{woorden} woorden in <main>, budget {WOORDBUDGET}"


def test_kerninhoud_in_leesbare_tekst(dom):
    tekst = " ".join(dom.main_tekst + dom.voet_tekst)
    for term in KERNINHOUD:
        assert term in tekst, f"ontbreekt in de leesbare tekst: {term!r}"


def test_geen_verboden_tekst(html):
    for woord in VERBODEN:
        assert woord not in html, f"gevonden: {woord!r}"


def test_iban_exact_en_geldig(dom):
    tekst = " ".join(dom.main_tekst)
    assert IBAN in tekst
    assert iban_geldig(IBAN)
    assert "Stichting Werkers in de Wijngaard" in tekst
    assert "Project Zaad voor de Zaaier" in tekst


def test_links_naar_beide_stichtingen_en_geen_projecturl(dom):
    hrefs = [a.get("href", "") for t, a in dom.tags if t == "a"]
    for host in STICHTINGEN:
        assert any(h.startswith(host) for h in hrefs), f"link naar {host} ontbreekt"
    assert not any("werkersindewijngaard.nl/zaadvoordezaaier" in h for h in hrefs)


def test_downloadknop(dom):
    assert any(a.get("href") == "brochure/zaad-voor-de-zaaier-brochure.pdf" for t, a in dom.tags if t == "a")


def test_alleen_relatieve_bronnen_en_toegestane_hosts(dom):
    """Geen externe scripts, stijlen of beelden; links alleen intern of naar de twee stichtingen."""
    for tag, a in dom.tags:
        bron = a.get("src") or a.get("href")
        if not bron or bron.startswith("#"):
            continue
        if tag == "a":
            assert bron.startswith(STICHTINGEN) or not re.match(r"^[a-z]+:", bron), f"onverwachte link: {bron}"
        else:
            assert not re.match(r"^(https?:)?//", bron), f"externe bron in <{tag}>: {bron}"


# ---- css en gewicht ----

def test_tokens_en_fonts_in_css(css):
    for token in TOKENS:
        assert re.search(rf"{token}:\s*#", css), f"{token} ontbreekt in :root"
    for font in ("../fonts/bebas-neue.woff2", "../fonts/open-sans.woff2"):
        assert font in css
        assert (ROOT / "fonts" / font.split("/")[-1]).exists()


def test_iban_breekt_niet(css):
    regel = re.search(r"\.gegevens__iban\s*\{([^}]*)\}", css).group(1)
    assert "white-space: nowrap" in regel, "IBAN moet op een regel blijven"


def test_print_op_a4(css):
    print_blok = css.split("@media print")[1]
    assert re.search(r"@page\s*\{[^}]*size:\s*A4", print_blok), "@page met size: A4 ontbreekt in het print-blok"
    assert ".voet__logos" in print_blok and ".voet { display: none" not in print_blok, \
        "in print blijft de voettekstregel staan; alleen logo's en knop verdwijnen"


def test_gewicht():
    img_totaal = sum(p.stat().st_size for p in (ROOT / "img").iterdir() if p.is_file())
    assert img_totaal < 1_000_000
    assert BROCHURE.stat().st_size <= 6_000_000
    assert INDEX.stat().st_size + CSS.stat().st_size < 60_000
