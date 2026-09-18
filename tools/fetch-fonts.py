"""Haalt de latin-subsets van Bebas Neue en Open Sans (variabel gewicht) op via de
Google Fonts-CSS-API en zet ze als woff2 in fonts/. Beide fonts vallen onder de
SIL Open Font License 1.1.

Gebruik:  python tools/fetch-fonts.py
"""
import re
import urllib.request
from pathlib import Path

FONTS = Path(__file__).resolve().parent.parent / "fonts"
# Een moderne user-agent is nodig, anders levert de API geen woff2-adressen.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
CSS_URL = ("https://fonts.googleapis.com/css2"
           "?family=Bebas+Neue&family=Open+Sans:wght@400;600;700&display=swap")
DOEL = {"Bebas Neue": "bebas-neue.woff2", "Open Sans": "open-sans.woff2"}


def haal(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as antwoord:
        return antwoord.read()


def main() -> None:
    css = haal(CSS_URL).decode()
    FONTS.mkdir(exist_ok=True)
    for subset, blok in re.findall(r"/\* (\w[\w-]*) \*/\s*@font-face \{(.*?)\}", css, re.S):
        if subset != "latin":
            continue
        familie = re.search(r"font-family: '([^']+)'", blok).group(1)
        bron = re.search(r"url\(([^)]+)\)", blok).group(1)
        doel = FONTS / DOEL[familie]
        if doel.exists():
            continue  # Open Sans: de API noemt per gewicht hetzelfde variabele bestand
        doel.write_bytes(haal(bron))
        print(f"{doel.name}: {doel.stat().st_size} bytes van {bron}")


if __name__ == "__main__":
    main()
