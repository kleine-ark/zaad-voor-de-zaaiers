# Zaad voor de Zaaier — website

Eén pagina die het project **Zaad voor de Zaaier** samenvat op één A4: wat het is, hoe het
werkt en hoe u meedoet. Het project is ondergebracht in Stichting Werkers in de Wijngaard
(ANBI). De volledige brochure voor christelijke ondernemers staat op de pagina als PDF-download.

## Inhoud van de repo

| Pad | Wat |
|---|---|
| `index.html`, `css/style.css` | De pagina. Platte HTML en CSS, geen JavaScript, geen build-stap. Printstijl voor één A4. |
| `img/` | Negen beelden uit de brochure (hero, twee portretten, vier logo's, favicon, og-image). |
| `fonts/` | Bebas Neue en Open Sans als woff2, met OFL-licentiebestanden. |
| `brochure/zaad-voor-de-zaaier-brochure.pdf` | Verkleinde download-versie van de brochure (4,8 MB). |
| `tools/` | Generatiescripts en pytest-controles. |
| `docs/superpowers/` | Ontwerpspecs en implementatieplannen. |

Een uitgebreide versie van de pagina met de volledige brochure-inhoud (alle bijbelteksten,
bedieningspaden en grondslag) staat in de git-geschiedenis, laatst in commit `8676075`.

## Hosten

De site werkt vanaf de root van deze repo (GitHub Pages: Settings → Pages → branch `main`, map `/`)
en, dankzij relatieve paden, ook als submap op een bestaande site, bijvoorbeeld
`werkersindewijngaard.nl/zaadvoordezaaier/`. Kopieer daarvoor `index.html`, `css/`, `img/`, `fonts/`
en `brochure/`.

Na publicatie: vul in `index.html` bij `og:image` de volledige URL van `img/og-image.jpg` in, zodat
sociale media het voorbeeld tonen.

## Opnieuw genereren

Het Canva-origineel van de brochure (`Zaad voor de Zaaier -- Werkers in de Wijngaard -- Hebron Missie (7).pdf`,
24 MB) staat in `.gitignore` en blijft lokaal; Canva is de bron. Vereist: Python 3.12 met
`pillow`, `pypdf`, `pymupdf` en `pytest`.

```bash
python tools/build-assets.py      # beelden, favicon, og-image en download-PDF uit het origineel
python tools/fetch-fonts.py       # lettertypen ophalen (alleen nodig als fonts/ leeg is)
python -m pytest tools -q         # alle controles
```

Instellingen in `tools/build-assets.py`: hero max 1800 px, portretten max 600 px, JPEG kwaliteit 80;
download-PDF met elk beeld op max 1200 px, JPEG kwaliteit 70 (maskers als grijswaarden-JPEG, zodat
transparantie behouden blijft). De PDF krijgt bij elke run nieuwe metadata; commit hem alleen als
de inhoud is veranderd.

## Lokaal bekijken

```bash
python -m http.server 8765 --bind 127.0.0.1
```

Open daarna http://127.0.0.1:8765/. Afdrukken: Ctrl+P, A4, "achtergronden" mag uit; de
printstijl zet alle vlakken om naar wit met een rand.

## Redactie

De tekst is een samenvatting van de brochure, met deze afspraken: de naam is overal
"Zaad voor de Zaaier"; bijbelcitaten zijn woordelijk overgenomen; de fiscale regels volgen de
brochure, inclusief het voorbehoud "kunnen aftrekbaar zijn". IBAN en tenaamstelling zijn door de
eigenaren aangeleverd (de brochure bevat op die plek een invulveld). De verwijzing "vgl.
Rom. 12:4–5" staat bij een parafrase van de brochure, niet bij een citaat. De download-PDF is de
bestaande brochure.

Ter controle door de eigenaren: de brochure noemt de periodieke gift "volledig aftrekbaar,
zonder drempel of maximum"; sinds 2023 kent de inkomstenbelasting wel een plafond voor
periodieke giften. De pagina neemt de brochuretekst over en verwijst naar de eigen adviseur.

Snelle controle op telefoonbreedte na wijzigingen (in de browserconsole op 375 px):
`document.documentElement.scrollWidth <= document.documentElement.clientWidth` moet `true` zijn.
