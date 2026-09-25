# Zaad voor de Zaaier — website

Eén pagina die het project **Zaad voor de Zaaier** samenvat op één A4: wat het is, hoe het
werkt en hoe u meedoet. Het project is ondergebracht in Stichting Werkers in de Wijngaard
(ANBI). De volledige brochure voor christelijke ondernemers opent vanaf de pagina als PDF in een nieuw tabblad.

## Inhoud van de repo

| Pad | Wat |
|---|---|
| `index.html`, `css/style.css` | De pagina. Platte HTML en CSS, geen JavaScript, geen build-stap. Printstijl voor één A4. |
| `img/` | Negen beelden uit de brochure (hero, vier beelden naast de tekstblokken, twee logo's, favicon, og-image); bewust geen portretten. |
| `fonts/` | Bebas Neue en Open Sans als woff2, met OFL-licentiebestanden. |
| `brochure/zaad-voor-de-zaaier-brochure.pdf` | Verkleinde download-versie van de brochure (4,8 MB). |
| `tools/` | Generatiescripts en pytest-controles. |
| `docs/` | Ontwerpspecs en implementatieplannen: alleen lokaal, staat in `.gitignore` en niet in deze openbare repo. |

Een uitgebreide versie van de pagina met de volledige brochure-inhoud (alle bijbelteksten,
bedieningspaden en grondslag) staat in de git-geschiedenis, laatst in commit `e55173e`.

## Hosten

De site komt vanzelf online op **https://www.zaadvoordezaaiers.nl**: elke push naar `main` start de
workflow `.github/workflows/deploy.yml` (zelfde opzet als de website van Didache Dordrecht, geen
GitHub Pages).

1. `deploy/provision.py` draait via SSH op de server `167.235.54.105` en maakt of vernieuwt de
   nginx-site voor `zaadvoordezaaiers.nl` en `www.zaadvoordezaaiers.nl`.
2. De gedeelde deploy-workflow van OpenAEC kopieert de site met rsync naar `/var/www/zaadvoordezaaiers.nl`,
   zonder `README.md`, `deploy/`, `docs/`, `tools/` en `.gitignore`.
3. Sinds 21 september 2026 wijzen beide namen naar de server en draait de site onder HTTPS: het script
   heeft toen een Let's Encrypt-certificaat aangevraagd en stuurt alles naar
   `https://www.zaadvoordezaaiers.nl`. Certbot vernieuwt het certificaat zelf. De records bij TransIP,
   zonder AAAA-records:

   | Naam | Type | Waarde |
   |---|---|---|
   | `@` | A | `167.235.54.105` |
   | `www` | A | `167.235.54.105` |

   Een nieuwe deploy zonder push kan via *Actions → Deploy website → Run workflow*.

De workflow gebruikt de organisatiesecret `DEPLOY_SSH_KEY` van `kleine-ark`. Dat werkt omdat deze repo
openbaar is: de organisatie zit op GitHub Free, en daar krijgen privé-repo's organisatiesecrets niet
doorgegeven (de workflow stopt dan met "The ssh-private-key argument is empty"). Wordt de repo weer
privé, zet dan dezelfde sleutel als repository-secret (Settings → Secrets and variables → Actions).
Dankzij relatieve paden
werkt de site ook als submap op een andere site; kopieer dan `index.html`, `css/`, `img/`, `fonts/`,
`brochure/` en `robots.txt`.

De site is bewust **niet vindbaar**: `index.html` draagt `noindex, nofollow, noarchive` en `robots.txt`
schermt de brochure-PDF af (een PDF kan zelf geen noindex dragen). Zet `robots.txt` in de root van het
domein; staat de site in een submap, neem dan de regel `Disallow: /<submap>/brochure/` over in de
`robots.txt` van dat domein. Dit houdt zoekmachines buiten, niet mensen die de link hebben.

`og:url` en `og:image` in `index.html` wijzen naar `https://www.zaadvoordezaaiers.nl/`, zodat een
gedeelde link een voorbeeld met afbeelding toont.

## Delen als artefact

`python tools/build-artifact.py` zet een deelbare versie voor claude.ai in `.claude/artifact/` (buiten git):
dezelfde pagina en beelden, met de brochure als paginabeelden in een venster, omdat een artefact geen
PDF in een nieuw tabblad kan openen.

## Opnieuw genereren

Het Canva-origineel van de brochure (`Zaad voor de Zaaier -- Werkers in de Wijngaard -- Hebron Missie (7).pdf`,
24 MB) staat in `.gitignore` en blijft lokaal; Canva is de bron. Vereist: Python 3.12 met
`pillow`, `pypdf`, `pymupdf` en `pytest`.

```bash
python tools/build-assets.py      # beelden, favicon, og-image en download-PDF uit het origineel
python tools/fetch-fonts.py       # lettertypen ophalen (alleen nodig als fonts/ leeg is)
python -m pytest tools -q         # alle controles
```

Instellingen in `tools/build-assets.py`: hero max 1800 px, blokbeelden max 1000 px, JPEG kwaliteit 80;
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

De tekst van de voorpagina is door de eigenaren aangeleverd (2026-09-19) en licht geredigeerd:
de naam is overal "Zaad voor de Zaaier"; taalcorrecties ("hiermee", "ons werk zegent", "koffiekar",
"moslims", "in het verspreiden"); de school heet volgens haar eigen site "Bijbelschool Filadelfia";
de afgebroken toevoeging "voor zover" achter "Verspreiding van het evangelie online" is weggelaten
tot hij wordt aangevuld. In "Waarom Zaad voor de Zaaier?" zijn tikfouten hersteld ("het nu van" → "het nut van",
dubbel "sommige", "waardeoordeel" aaneen, "christen" met kleine letter, vraagteken bij de vraag over diaconaal werk). In de projectenlijst 2027 zijn de bedragen overgenomen zoals aangeleverd;
alleen de spelling is aangepast ("Randstad", "discipelschapsvideo’s", "Moslimevangelisatie",
"Jongerenevangelisatie"). De totaalregel (€ 599.000) is de som van de zes bedragen; een test bewaakt dat hij klopt als een bedrag wijzigt. Het paneel "Meedoen" (IBAN, tenaamstelling, fiscale regels) is op verzoek van de eigenaren van de
pagina gehaald; onderaan de pagina staan alleen nog "Stichting Werkers in de Wijngaard" en het rekeningnummer.
Op 2026-09-23 hebben de eigenaren "We leren hieruit" en het begin van "Waarom Zaad voor de Zaaier?"
zelf herschreven en aangevuld; de printletter ging daarvoor van 8,5 naar 8 pt, zodat de pagina op één A4 blijft.

De brochure-PDF is de bestaande brochure met twee aanpassingen buiten Canva om:

- sinds 2026-09-23 een opgeplakt rekeningblok op pagina 8 (IBAN, t.n.v., kenmerk); het bedekt ook
  grotendeels de kop "Zekerheden:";
- sinds 2026-09-25 "Gospel Mission" in plaats van "Gospel Image" op pagina 2 en 3 (de bijbelschool
  van Hebron Missie), opnieuw gezet in de oorspronkelijke letters.

Het Canva-origineel heeft beide nog niet: maakt `tools/build-assets.py` de PDF opnieuw uit dat
origineel, dan vallen ze weg (tests slaan dan alarm). Verder bekende onvolkomenheden: werknotitie
op pagina 14, taalfouten. Een nieuwe export uit Canva met beide aanpassingen erin lost dit allemaal op.

Ter controle door de eigenaren: de brochure noemt de periodieke gift "volledig aftrekbaar,
zonder drempel of maximum"; sinds 2023 kent de inkomstenbelasting wel een plafond voor
periodieke giften. Dat staat alleen nog in de brochure-PDF, niet meer op de pagina.

Snelle controle op telefoonbreedte na wijzigingen (in de browserconsole op 375 px):
`document.documentElement.scrollWidth <= document.documentElement.clientWidth` moet `true` zijn.
