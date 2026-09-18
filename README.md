# Zaad voor de Zaaier — website

Informatiepagina voor het project **Zaad voor de Zaaier**, ondergebracht in Stichting Werkers in de
Wijngaard (ANBI). De pagina brengt de brochure voor christelijke ondernemers naar het web: waarom,
wie, plan van aanpak, bedieningspaden, geven, fiscale informatie, giftgegevens en grondslag.

## Inhoud van de repo

| Pad | Wat |
|---|---|
| `index.html`, `css/style.css` | De pagina. Platte HTML en CSS, geen JavaScript, geen build-stap. |
| `img/` | Beelden uit de brochure, verkleind voor het web (< 4 MB totaal). |
| `fonts/` | Bebas Neue en Open Sans als woff2 (SIL Open Font License). |
| `brochure/zaad-voor-de-zaaier-brochure.pdf` | Verkleinde download-versie van de brochure (4,8 MB). |
| `tools/` | Generatiescripts en pytest-controles. |
| `docs/superpowers/` | Ontwerpspec en implementatieplan. |

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

Instellingen in `tools/build-assets.py`: hero max 1800 px, posters max 1400 px, portretten max 600 px,
JPEG kwaliteit 80; download-PDF met elk beeld op max 1200 px, JPEG kwaliteit 70 (maskers als
grijswaarden-JPEG, zodat transparantie behouden blijft).

## Lokaal bekijken

```bash
python -m http.server 8765 --bind 127.0.0.1
```

Open daarna http://127.0.0.1:8765/.

## Redactie

De tekst volgt de brochure, met deze afspraken: de naam is overal "Zaad voor de Zaaier";
tikfouten uit de brochure zijn hersteld; bijbelcitaten zijn inhoudelijk ongewijzigd. De
download-PDF is de bestaande brochure en bevat die correcties niet. De onderbouwing onder
"Grondslag" staat ingeklapt; bij afdrukken wordt hij in moderne browsers meegenomen.

Wat er ten opzichte van de brochure is aangepast, zodat de eigenaren het kunnen nalopen:

- Weggelaten: de interne werknotitie bovenaan brochurepagina 14; dubbel voorkomende citaten
  (2 Kor. 9:10, Rom. 12:4–5, 1 Kor. 12:21, Psalm 1:3) staan één keer.
- Toegevoegd: de verwijzing "Psalm 126:6" bij het citaat op de fiscale pagina (de brochure
  noemt de vindplaats niet); de inleidende vraag boven de bijbelse onderbouwing ("Wat zegt
  Gods Woord over 1. wie we moeten zijn en 2. wat we moeten doen?"); in de voettekst "in
  samenwerking met Stichting Hebron Missie".
- Verwijzingen naar "de volgende pagina" zijn herschreven naar deze webpagina.
- Taalcorrecties: "Eein" → "Een", "betekend" → "betekent", "opleverd" → "oplevert",
  "vind u" → "vindt u", "luid" → "luidt", "hiemee" → "hiermee", "ondersteund" → "ondersteunt",
  "Hier word" → "Hier wordt", "bedieninsvarianten" → "bedieningsvarianten", "verspreid daarmee"
  → "verspreidt daarmee", "word vergeleken" → "wordt vergeleken", "gebeurd er" → "gebeurt er",
  "omdat dat wij geven" → "omdat wij geven", "1 lichaam" → "één lichaam", "evangelisatie
  materiaal/projecten/acties" aaneengeschreven, "Moslims" → "moslims", "Matth.55:14" →
  "Matth. 5:14", "1 kor." → "1 Kor.".
- Twee foto's (Stefan, rijstveld) staan in de brochure gespiegeld; de site toont de
  oorspronkelijke foto.

Snelle controle op telefoonbreedte na wijzigingen (in de browserconsole op 375 px):
`document.documentElement.scrollWidth <= document.documentElement.clientWidth` moet `true` zijn.
