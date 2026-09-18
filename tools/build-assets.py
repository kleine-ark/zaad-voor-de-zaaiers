"""Genereert de webbeelden, favicon, og-image en de verkleinde brochure-PDF
uit het Canva-origineel van de brochure.

Gebruik:  python tools/build-assets.py [pad-naar-origineel.pdf]
Zonder argument wordt het origineel in de repo-root gezocht (staat in .gitignore).
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageOps
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
ORIGINEEL = ROOT / "Zaad voor de Zaaier -- Werkers in de Wijngaard -- Hebron Missie (7).pdf"
IMG = ROOT / "img"
BROCHURE = ROOT / "brochure" / "zaad-voor-de-zaaier-brochure.pdf"

CREME = (248, 238, 197)
PAPIER = (255, 250, 240)
KWALITEIT = 80
MAX_HERO, MAX_POSTER, MAX_PORTRET = 1800, 1400, 600

# (pagina 1-based, index in page.images) -> (bestandsnaam, max lange zijde,
#   achtergrondkleur voor RGBA->JPEG of None, rotatie in graden met de klok mee)
BEELDEN = {
    (1, 0): ("hero-zaaier.jpg", MAX_HERO, None, 0),
    (1, 1): ("maarten.jpg", MAX_PORTRET, CREME, 0),
    (2, 0): ("bijbel-markeerstift.jpg", MAX_POSTER, None, 0),
    (2, 2): ("logo-werkers-in-de-wijngaard.png", None, None, 0),
    (2, 3): ("logo-hebron-missie.png", None, None, 0),
    (3, 0): ("hand-zaden.jpg", MAX_POSTER, None, 0),
    (4, 0): ("hand-planten.jpg", MAX_POSTER, None, 0),
    (5, 0): ("hand-graan.jpg", MAX_POSTER, None, 0),
    (6, 0): ("bijbel-korenveld.jpg", MAX_POSTER, None, 0),
    (7, 0): ("biddende-man.jpg", MAX_POSTER, None, 0),
    (8, 0): ("zakken-graan.jpg", MAX_POSTER, None, 0),
    (8, 1): ("logo-anbi.png", None, None, 0),
    (9, 0): ("logo-zaad-voor-de-zaaier.png", None, None, 0),
    (9, 2): ("rijstveld.jpg", MAX_POSTER, PAPIER, 0),
    (10, 0): ("handen-hemel.jpg", MAX_POSTER, None, 0),
    (11, 0): ("boom.jpg", MAX_POSTER, None, 0),
    (12, 0): ("maaidorser.jpg", MAX_POSTER, None, 0),
    # Op brochurepagina 13 staat dit beeld een kwartslag gedraaid.
    (13, 0): ("luchtfoto-veld.jpg", MAX_POSTER, None, 90),
    (14, 0): ("stefan.jpg", MAX_PORTRET, CREME, 0),
}


# Verwachte maat van elk bronbeeld in het origineel (vóór rotatie); wijkt die af, dan is de
# koppeling (pagina, index) in BEELDEN waarschijnlijk verschoven door een nieuwe export.
BRONMATEN = {
    "hero-zaaier.jpg": (1725, 2609), "maarten.jpg": (560, 374), "bijbel-markeerstift.jpg": (1728, 1152),
    "logo-werkers-in-de-wijngaard.png": (292, 53), "logo-hebron-missie.png": (324, 126),
    "hand-zaden.jpg": (1296, 1936), "hand-planten.jpg": (960, 1365), "hand-graan.jpg": (1730, 2457),
    "bijbel-korenveld.jpg": (1550, 2193), "biddende-man.jpg": (1200, 1690), "zakken-graan.jpg": (1200, 1696),
    "logo-anbi.png": (231, 183), "logo-zaad-voor-de-zaaier.png": (615, 410), "rijstveld.jpg": (1549, 1033),
    "handen-hemel.jpg": (1200, 1702), "boom.jpg": (922, 1383), "maaidorser.jpg": (1200, 1697),
    "luchtfoto-veld.jpg": (2163, 1446), "stefan.jpg": (776, 516),
}


def verklein(im: Image.Image, max_zijde: int | None) -> Image.Image:
    if not max_zijde or max(im.size) <= max_zijde:
        return im
    schaal = max_zijde / max(im.size)
    return im.resize((round(im.width * schaal), round(im.height * schaal)), Image.Resampling.LANCZOS)


def op_achtergrond(im: Image.Image, kleur: tuple[int, int, int]) -> Image.Image:
    """Legt een RGBA-beeld op een effen kleur (JPEG kent geen transparantie)."""
    bg = Image.new("RGB", im.size, kleur)
    bg.paste(im, mask=im.getchannel("A"))
    return bg


def bewaar(im: Image.Image, pad: Path) -> None:
    pad.parent.mkdir(parents=True, exist_ok=True)
    if pad.suffix == ".png":
        im.save(pad, "PNG", optimize=True)
    else:
        im.convert("RGB").save(pad, "JPEG", quality=KWALITEIT, optimize=True, progressive=True)


def maak_beelden(origineel: Path) -> None:
    reader = PdfReader(str(origineel))
    for (pagina, index), (naam, max_zijde, achtergrond, rotatie) in BEELDEN.items():
        bron = reader.pages[pagina - 1].images[index]
        im = Image.open(io.BytesIO(bron.data))
        if im.size != BRONMATEN[naam]:
            raise SystemExit(f"{naam}: bronbeeld op pagina {pagina} is {im.size}, verwacht {BRONMATEN[naam]}; "
                             "controleer de koppeling in BEELDEN")
        if rotatie == 90:
            im = im.transpose(Image.Transpose.ROTATE_270)  # 270° tegen de klok = 90° met de klok
        im = verklein(im, max_zijde)
        if achtergrond and im.mode == "RGBA":
            im = op_achtergrond(im, achtergrond)
        pad = IMG / naam
        bewaar(im, pad)
        print(f"{naam:34s} {im.width:5d} x {im.height:<5d} {pad.stat().st_size // 1024:5d} kB")


def maak_favicon_en_og() -> None:
    logo = Image.open(IMG / "logo-zaad-voor-de-zaaier.png").convert("RGBA")
    # Favicon: de zaaier-figuur (linker derde van het logo), passend in 64x64 op transparant.
    zaaier = logo.crop((0, 0, int(logo.width * 0.34), logo.height))
    zaaier = ImageOps.contain(zaaier, (64, 64), Image.Resampling.LANCZOS)
    fav = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    fav.paste(zaaier, ((64 - zaaier.width) // 2, (64 - zaaier.height) // 2), zaaier)
    bewaar(fav, IMG / "favicon.png")
    # og-image: 1200x630-uitsnede uit de hero, iets boven het midden (de zaaier).
    hero = Image.open(IMG / "hero-zaaier.jpg")
    og = ImageOps.fit(hero, (1200, 630), Image.Resampling.LANCZOS, centering=(0.5, 0.45))
    bewaar(og, IMG / "og-image.jpg")
    for naam in ("favicon.png", "og-image.jpg"):
        print(f"{naam:34s} {(IMG / naam).stat().st_size // 1024:5d} kB")


def zet_jpeg_stream(doc: fitz.Document, xref: int, im: Image.Image, kwaliteit: int, grijs: bool = False) -> None:
    """Overschrijft een beeldobject in de PDF met een JPEG van hetzelfde beeld (of masker)."""
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=kwaliteit, optimize=True)
    doc.update_stream(xref, buf.getvalue(), compress=False)
    doc.xref_set_key(xref, "Filter", "/DCTDecode")
    doc.xref_set_key(xref, "Width", str(im.width))
    doc.xref_set_key(xref, "Height", str(im.height))
    doc.xref_set_key(xref, "ColorSpace", "/DeviceGray" if grijs else "/DeviceRGB")
    doc.xref_set_key(xref, "BitsPerComponent", "8")
    for sleutel in ("DecodeParms", "Decode", "Mask", "Interpolate"):
        if doc.xref_get_key(xref, sleutel)[0] != "null":
            doc.xref_set_key(xref, sleutel, "null")


def maak_brochure(origineel: Path, max_zijde: int = 1200, kwaliteit: int = 70) -> None:
    """Zelfde inhoud en paginavolgorde, maar elk beeld verkleind en als JPEG opgeslagen.

    Transparantie blijft behouden: het zachte masker (SMask) wordt als grijswaarden-JPEG
    meeverkleind. De streams worden direct overschreven, zodat er geen dubbele beelden
    achterblijven.
    """
    doc = fitz.open(str(origineel))
    gedaan: set[int] = set()
    for page in doc:
        for info in page.get_image_info(xrefs=True):
            xref = info["xref"]
            if not xref or xref in gedaan:
                continue
            gedaan.add(xref)
            basis = doc.extract_image(xref)
            im = Image.open(io.BytesIO(basis["image"]))
            smask = basis.get("smask") or 0
            mask = Image.open(io.BytesIO(doc.extract_image(smask)["image"])).convert("L") if smask else None
            im = verklein(im, max_zijde)
            zet_jpeg_stream(doc, xref, im.convert("RGB"), kwaliteit)
            if mask is not None:
                if mask.size != im.size:
                    mask = mask.resize(im.size, Image.Resampling.LANCZOS)
                zet_jpeg_stream(doc, smask, mask, kwaliteit, grijs=True)
    BROCHURE.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(BROCHURE), garbage=4, deflate=True, deflate_images=True, deflate_fonts=True)
    paginas = doc.page_count
    doc.close()
    print(f"{BROCHURE.name:34s} {BROCHURE.stat().st_size / 1e6:.2f} MB, {paginas} pagina's")


def main() -> int:
    origineel = Path(sys.argv[1]) if len(sys.argv) > 1 else ORIGINEEL
    if not origineel.exists():
        print(f"Origineel niet gevonden: {origineel}", file=sys.stderr)
        return 1
    maak_beelden(origineel)
    maak_favicon_en_og()
    maak_brochure(origineel)
    totaal = sum(p.stat().st_size for p in IMG.iterdir() if p.is_file())
    print(f"{'img/ totaal':34s} {totaal / 1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
