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
PDF_HREF = "brochure/zaad-voor-de-zaaier-brochure.pdf"

# Vroege waarschuwing; de echte A4-bewaker is tools/test_print.py. Bij 661 woorden eindigde de
# afdruk (8,5 pt) op 278 van 288 mm, dus rond 700 woorden is de pagina vol.
WOORDBUDGET = 700
SECTIE_IDS = ["top", "leren", "waarom", "wat", "uitgangspunten", "positie", "anoniem", "projecten", "uitgaven", "voordeel"]
# Projectenlijst 2027 zoals aangeleverd door de eigenaren (bedragen in euro's).
PROJECTEN_2027 = [("Evangelisten Randstad", 60000), ("Evangelisatie landelijk", 48000),
                  ("Nieuwe evangelisten Hebron", 180000), ("Online discipelschapsvideo’s", 12000),
                  ("Moslimevangelisatie", 245000), ("Jongerenevangelisatie", 54000)]
# Hoofdlettergevoelig; tikfouten, verkeerde spellingen en dingen die niet op de site horen.
VERBODEN = ["Zaaiers", "logo-werkers-in-de-wijngaard.png", "daar nu ook echt door verkondigd", "anoninem", "zelfstandige evangelie ", "niet zelf teveel", "sommige sommige", "het nu van", "waarde-oordeel", "maarten.jpg", "stefan.jpg", "logo-anbi.png", "discipelschapsvideos",
            "Moslim evangelisatie", "Jongeren evangelisatie", "zaaiers richt", "NL.....", "Eein", "betekend", "opleverd", "vind u",
            "luid:", "hiemee", "bedieninsvarianten", "Matth.55", "1 kor.", "word vergeleken",
            "gebeurd er", "verspreid daarmee", "stichting ondersteund", "werkt zegent", "koffie kar",
            "Philadelphia", "Filadelphia", "omdat dat wij", "inloophuizen", "<script"]
# Moet in de leesbare tekst van main + voettekst staan (niet alleen in alt-teksten of attributen).
KERNINHOUD = ["We hebben het op ons hart gekregen", "2 Kor. 9:10", "Heer van de oogst", "welvaartsevangelie",
              "Werkers in de Wijngaard", "ANBI", "faciliteert sinds 2010 mensen", "Straatevangelisatie", "Kraam met boeken", "koffiekar",
              "moslims", "openbare scholen", "het Woord op straat klinkt",
              "1 Kor. 15:3–4", "0 euro aan administratieve kosten", "Anonimiteit;", "Hebron Missie", "Bijbelschool Filadelfia",
              "Arjan Baan", "Mogen we 5 minuten van uw tijd", "Open hier de brochure",
              "richt zich op het financieel ondersteunen van", "2027 projecten",
              "Waar wordt het geld aan uitgegeven?", "Inkomen werkers", "Drukwerk Bijbels en traktaten",
              "Waarom Zaad voor de Zaaier?", "een goed geefdoel te vinden", "waterputdonaties", "waardeoordeel",
              "zelfstandige evangelist, dan is het doorgaans niet anoniem",
              "Ik vind het lastig om een geefdoel te beoordelen, elk jaar weer opnieuw", "is het betrouwbaar?",
              "maar ik wil graag dat het evangelie meer verkondigd wordt",
              "Maar wel dat het direct gezaaid wordt", "Deze vragen hadden wij ook",
              "Anoniem geven", "laat dan uw linkerhand niet weten wat uw rechterhand doet",
              "Die in het verborgene ziet", "Mattheüs 6:2–4"]
STICHTINGEN = ("https://www.hebronmissie.nl", "https://www.werkersindewijngaard.nl")
TOKENS = ["--bruin", "--creme", "--papier", "--geel", "--oranje", "--sage", "--lichtblauw",
          "--lei", "--groen", "--roodbruin", "--tekst"]
# Alleen de hero staat boven de vouw en wordt niet lui geladen.
NIET_LUI = {"img/hero-zaaier.jpg"}


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


def test_site_is_niet_vindbaar(dom):
    """Op verzoek van de eigenaren: geen indexering door zoekmachines, ook niet van de brochure."""
    robots = [a.get("content", "") for t, a in dom.tags if t == "meta" and a.get("name") == "robots"]
    assert robots and "noindex" in robots[0] and "nofollow" in robots[0], "meta robots met noindex, nofollow ontbreekt"
    regels = (ROOT / "robots.txt").read_text(encoding="utf-8").splitlines()
    assert "Disallow: /brochure/" in regels, "robots.txt moet de brochure-PDF afschermen"
    assert "Disallow: /" not in regels, "de pagina moet leesbaar blijven, anders ziet een zoekmachine de noindex niet"


def test_vragen_van_de_gever_als_lijst(html):
    """De zes vragen in het blok Waarom staan op een rij, elk met een vraagteken-bullet (klasse vragen)."""
    blok = html.split('id="waarom"')[1].split("</section>")[0]
    lijst = blok.split('<ul class="vragen"')[1].split("</ul>")[0]
    assert lijst.count("<li>") == 6


def test_eigen_logo_groot_in_voettekst(html, css):
    """Onderin staat het logo van Zaad voor de Zaaier groter dan de twee stichtingslogo's."""
    voet = html.split("<footer")[1]
    assert 'class="voet__logo--groot"><a href="#top"><img src="img/logo-zaad-voor-de-zaaier.png"' in voet
    groot = int(re.search(r"\.voet__logo--groot img \{ max-height: (\d+)px", css).group(1))
    gewoon = int(re.search(r"\.voet__logos img \{ max-height: (\d+)px", css).group(1))
    assert groot >= 2 * gewoon


def test_vier_brochurebeelden_naast_hun_blok(html):
    """Elk beeld staat in het blok waar het bij hoort, na de tekst van dat blok."""
    verwacht = {"waarom": "img/hand-zaden.jpg", "uitgangspunten": "img/bijbel-korenveld.jpg", "projecten": "img/hand-graan.jpg", "voordeel": "img/zakken-graan.jpg"}
    for sid, src in verwacht.items():
        blok = html.split(f'id="{sid}"')[1].split("</section>")[0]
        assert 'class="blok__tekst"' in blok and f'<figure class="blok__beeld"><img src="{src}"' in blok, sid


def test_anoniem_geven_met_markeringen_zonder_inleiding(html):
    blok = html.split('id="anoniem"')[1].split("</section>")[0]
    assert "<mark>laat dan uw linkerhand niet weten wat uw rechterhand doet</mark>" in blok
    assert "<mark>Die in het verborgene ziet</mark>" in blok
    assert "Wij benadrukken het belang" not in html


def test_geen_doelgroepbadge_bovenin(html):
    """Op verzoek weggehaald: de regel boven de titel over de doelgroep."""
    assert "christelijke ondernemers" not in html and "badge" not in html


def test_geen_kopregel_bovenin(html):
    """Op verzoek van de eigenaren: geen balk met logo en downloadknop boven het titelblok."""
    assert "<header" not in html and "kopregel" not in html


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


def test_een_h2_per_sectie(dom):
    """Elke sectie na de kopband heeft precies één h2; de kopband heeft de h1."""
    starts = [i for i, (t, a) in enumerate(dom.tags) if a.get("id") in SECTIE_IDS]
    footer = next(i for i, (t, _) in enumerate(dom.tags) if t == "footer")
    grenzen = starts + [footer]
    for begin, eind in zip(grenzen, grenzen[1:]):
        sid = dom.tags[begin][1]["id"]
        h2 = sum(1 for t, _ in dom.tags[begin:eind] if t == "h2")
        assert h2 == (0 if sid == "top" else 1), f"sectie #{sid} heeft {h2} h2-koppen"


# ---- beelden ----

def test_afbeeldingen_bestaan_met_alt_en_juiste_maten(dom):
    imgs = [a for t, a in dom.tags if t == "img"]
    assert imgs, "geen afbeeldingen gevonden"
    for a in imgs:
        pad = ROOT / a["src"]
        assert pad.exists(), f"{a['src']} ontbreekt"
        assert "alt" in a, f"{a['src']} mist alt"
        w, h = Image.open(pad).size
        assert (int(a["width"]), int(a["height"])) == (w, h), \
            f"{a['src']}: attributen {a.get('width')}x{a.get('height')}, bestand {w}x{h}"
        if a["src"] not in NIET_LUI:
            assert a.get("loading") == "lazy", f"{a['src']} mist loading=lazy"


# ---- tekst ----

def test_woordbudget(dom):
    tekst = " ".join(dom.main_tekst)
    woorden = len(re.findall(r"\S+", tekst))
    assert woorden <= WOORDBUDGET, f"{woorden} woorden in <main>, budget {WOORDBUDGET}"


def test_kerninhoud_in_leesbare_tekst(dom):
    tekst = re.sub(r"\s+", " ", " ".join(dom.main_tekst + dom.voet_tekst))
    for term in KERNINHOUD:
        assert term in tekst, f"ontbreekt in de leesbare tekst: {term!r}"


def test_projecten_2027_met_exacte_bedragen(html):
    """Namen en bedragen in de tabel komen een-op-een overeen met de aangeleverde lijst."""
    patroon = r'<tr><th scope="row">([^<]+)</th><td>€&nbsp;([\d.]+)</td></tr>'
    romp, voet = html.split("<tfoot>")
    gevonden = [(naam, int(bedrag.replace(".", ""))) for naam, bedrag in re.findall(patroon, romp)]
    assert gevonden == PROJECTEN_2027
    totaal = [(naam, int(bedrag.replace(".", ""))) for naam, bedrag in re.findall(patroon, voet)]
    assert totaal == [("Totaal", sum(bedrag for _, bedrag in PROJECTEN_2027))], "totaalregel moet de som van de projecten zijn"


def test_geen_verboden_tekst(html):
    for woord in VERBODEN:
        assert woord not in html, f"gevonden: {woord!r}"


def iban_geldig(iban: str) -> bool:
    s = iban.replace(" ", "")
    verplaatst = s[4:] + s[:4]
    return int("".join(str(int(c, 36)) for c in verplaatst)) % 97 == 1


def test_rekeningnummer_onderaan_en_geen_blok_meedoen(html, dom):
    """Onderaan staan de stichting en het rekeningnummer; het blok Meedoen (fiscale regels) blijft weg."""
    voet = re.sub(r"\s+", " ", " ".join(dom.voet_tekst))
    assert "Stichting Werkers in de Wijngaard NL83 RABO 0310 5957 62" in voet
    assert iban_geldig("NL83 RABO 0310 5957 62")
    assert " ".join(dom.main_tekst).count("NL83 RABO 0310 5957 62") == 1, \
        "in <main> staat het nummer alleen in de alleen-print-regel onderaan"
    assert 'id="meedoen"' not in html and "periodieke gift" not in html


def test_links_naar_beide_stichtingen_en_geen_projecturl(dom):
    hrefs = [a.get("href", "") for t, a in dom.tags if t == "a"]
    for host in STICHTINGEN:
        assert any(h.startswith(host) for h in hrefs), f"link naar {host} ontbreekt"
    assert not any("werkersindewijngaard.nl/zaadvoordezaaier" in h for h in hrefs)


def test_brochure_opent_in_nieuw_tabblad_en_geen_downloadknop(dom):
    """De brochure opent alleen via de oproep; de downloadknoppen zijn op verzoek weggehaald."""
    links = [a for t, a in dom.tags if t == "a" and a.get("href") == PDF_HREF]
    assert len(links) == 1 and "download" not in links[0], "alleen de oproep hoort naar de brochure te linken"
    openers = [a for a in links if a.get("target") == "_blank"]
    assert openers, "de oproep moet de brochure in een nieuw tabblad openen"
    assert all("noopener" in a.get("rel", "") for a in openers), "target=_blank vraagt om rel=noopener"


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


def test_print_op_a4(css):
    print_blok = css.split("@media print")[1]
    assert re.search(r"@page\s*\{[^}]*size:\s*A4", print_blok), "@page met size: A4 ontbreekt in het print-blok"
    assert re.search(r"\.alleen-print\s*\{[^}]*display:\s*block", print_blok), \
        "de voettekstregel moet in print meelopen als .alleen-print"
    assert re.search(r"\.alleen-print\s*\{\s*display:\s*none", css.split("@media print")[0]), \
        ".alleen-print hoort op het scherm verborgen te zijn"


def test_gewicht():
    img_totaal = sum(p.stat().st_size for p in (ROOT / "img").iterdir() if p.is_file())
    assert img_totaal < 2_000_000
    assert BROCHURE.stat().st_size <= 6_000_000
    assert INDEX.stat().st_size + CSS.stat().st_size < 60_000
