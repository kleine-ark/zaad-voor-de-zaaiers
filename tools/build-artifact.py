"""Bouwt een deelbare versie van de site als claude.ai-artefact (map buiten git).

De pagina komt rechtstreeks uit index.html en css/style.css. Een artefact kan geen PDF in een
nieuw tabblad openen; daarom toont deze versie de brochure als paginabeelden in een venster.

Gebruik:  python tools/build-artifact.py [uitvoermap]      (standaard .claude/artifact)
"""
import re
import shutil
import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BROCHURE = ROOT / "brochure" / "zaad-voor-de-zaaier-brochure.pdf"
BREEDTE = 1000  # pixels per brochurepagina: leesbaar op een groot scherm, licht genoeg voor een telefoon
KWALITEIT = 72

BROCHURE_LINK = ('<a class="knop" href="brochure/zaad-voor-de-zaaier-brochure.pdf" '
                 'target="_blank" rel="noopener">Open hier de brochure</a>')
BROCHURE_KNOP = ('<button class="knop" type="button" id="brochure-open" '
                 'aria-haspopup="dialog">Open hier de brochure</button>')

EXTRA_CSS = """
/* ===== Alleen in het artefact: de brochure in een venster ===== */
button.knop { border: 0; cursor: pointer; line-height: inherit; }
button:focus-visible { outline: 3px solid var(--bruin); outline-offset: 2px; box-shadow: 0 0 0 6px var(--geel); }
body:has(dialog[open]) { overflow: hidden; }
.brochure {
  width: 100%; max-width: 62rem; height: 100%; max-height: 100%; margin: 0 auto; padding: 0;
  border: 0; background: var(--bruin); color: var(--creme); overflow-y: auto;
}
.brochure::backdrop { background: rgba(43, 33, 24, .75); }
.brochure__balk {
  position: sticky; top: 0; z-index: 1; display: flex; flex-wrap: wrap; align-items: center;
  justify-content: space-between; gap: .75rem; background: var(--bruin);
  padding: calc(.75rem + env(safe-area-inset-top, 0px)) var(--marge) .75rem;
}
.brochure__balk h2 { margin: 0; color: var(--creme); font-size: clamp(1.3rem, 3vw, 1.8rem); }
.brochure__sluit { font-size: 1.1rem; padding: .45em .9em .35em; }
.brochure__paginas { display: grid; gap: 1rem; padding: 0 var(--marge) calc(var(--marge) + env(safe-area-inset-bottom, 0px)); }
.brochure__paginas img { width: 100%; height: auto; background: var(--creme); }
@media print { .brochure { display: none; } }
"""

SCRIPT = """<script>
(() => {
  const venster = document.getElementById('brochure');
  const open = document.getElementById('brochure-open');
  if (!venster || !open || typeof venster.showModal !== 'function') return;
  open.addEventListener('click', () => {
    // De eerste pagina's direct laden; de rest laadt tijdens het scrollen.
    venster.querySelectorAll('img').forEach((img, i) => { if (i < 2) img.loading = 'eager'; });
    venster.showModal();
    venster.scrollTop = 0;
  });
  venster.querySelector('.brochure__sluit').addEventListener('click', () => venster.close());
  venster.addEventListener('click', (e) => { if (e.target === venster) venster.close(); });
})();
</script>
"""


def render_brochure(uit):
    """Zet elke PDF-pagina om naar een JPEG en geeft (pad, breedte, hoogte) per pagina terug."""
    (uit / "brochure").mkdir(parents=True, exist_ok=True)
    paginas = []
    with fitz.open(str(BROCHURE)) as doc:
        for nummer, pagina in enumerate(doc, 1):
            zoom = BREEDTE / pagina.rect.width
            pix = pagina.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            beeld = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            pad = f"brochure/pagina-{nummer:02d}.jpg"
            beeld.save(uit / pad, "JPEG", quality=KWALITEIT, optimize=True, progressive=True)
            paginas.append((pad, pix.width, pix.height))
    return paginas


def venster_html(paginas):
    beelden = "\n".join(
        f'    <img src="{pad}" alt="Brochure, pagina {n} van {len(paginas)}" width="{w}" height="{h}" loading="lazy">'
        for n, (pad, w, h) in enumerate(paginas, 1))
    return ('<dialog id="brochure" class="brochure" aria-labelledby="brochure-titel">\n'
            '  <div class="brochure__balk">\n'
            '    <h2 id="brochure-titel">Brochure</h2>\n'
            '    <button type="button" class="knop brochure__sluit">Sluiten</button>\n'
            '  </div>\n'
            '  <div class="brochure__paginas">\n' + beelden + '\n  </div>\n</dialog>\n')


def main():
    uit = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".claude" / "artifact"
    if uit.exists():
        shutil.rmtree(uit)
    uit.mkdir(parents=True)

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "css" / "style.css").read_text(encoding="utf-8").replace("url('../fonts/", "url('fonts/")
    body = re.search(r"<body>\n?(.*)</body>", html, re.S).group(1)
    if BROCHURE_LINK not in body:
        raise SystemExit("de brochurelink in index.html is veranderd; pas BROCHURE_LINK aan")
    body = body.replace(BROCHURE_LINK, BROCHURE_KNOP)
    # Een artefact draait in een afgeschermd frame: externe links openen in een nieuw tabblad.
    body = re.sub(r'<a ([^>]*?)href="(https://[^"]+)"', r'<a \1href="\2" target="_blank" rel="noopener"', body)

    for src in sorted(set(re.findall(r'src="(img/[^"]+)"', body))):
        (uit / src).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / src, uit / src)
    (uit / "fonts").mkdir()
    for font in sorted((ROOT / "fonts").glob("*")):
        if font.suffix in (".woff2", ".txt"):
            shutil.copy2(font, uit / "fonts" / font.name)

    paginas = render_brochure(uit)
    pagina = ("<title>Zaad voor de Zaaier</title>\n<style>\n" + css + EXTRA_CSS + "</style>\n"
              + body + venster_html(paginas) + SCRIPT)
    (uit / "index.html").write_text(pagina, encoding="utf-8")

    bestanden = sorted(p.relative_to(uit).as_posix() for p in uit.rglob("*") if p.is_file() and p.name != "index.html")
    totaal = sum((uit / b).stat().st_size for b in bestanden) + (uit / "index.html").stat().st_size
    print(f"{uit}: index.html {(uit / 'index.html').stat().st_size // 1024} kB + {len(bestanden)} bestanden, "
          f"samen {totaal / 1e6:.1f} MB")
    for b in bestanden:
        print("  " + b)


if __name__ == "__main__":
    main()
