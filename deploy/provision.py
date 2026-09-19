#!/usr/bin/env python3
"""Bereidt de hosting van Zaad voor de Zaaier voor en zet HTTPS aan zodra de DNS naar deze server wijst.

Draait als root op de server; de workflow roept het aan met `ssh root@<server> python3 - < deploy/provision.py`.
Het script beheert alleen de eigen nginx-site (herkenbaar aan MARKER) en laat andere sites ongemoeid.
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

DOMEIN = 'zaadvoordezaaiers.nl'
WWW = 'www.' + DOMEIN
NAMEN = (DOMEIN, WWW)
HOOFDNAAM = WWW  # na HTTPS komt elke bezoeker uit op https://www.zaadvoordezaaiers.nl
ADRES = '167.235.54.105'
ROOT = Path('/var/www') / DOMEIN
CERT = Path('/etc/letsencrypt/live') / DOMEIN
CONFIG = Path('/etc/nginx/sites-available') / DOMEIN
LINK = Path('/etc/nginx/sites-enabled') / DOMEIN
MARKER = '# Beheerd door het provisioning-script van de repo zaad-voor-de-zaaiers'
ACME = '    location ^~ /.well-known/acme-challenge/ { try_files $uri =404; }\n'


def nginx_config(tls):
    """De nginx-site: zonder certificaat beide namen over HTTP, met certificaat alles naar https://www."""
    root, cert, namen = ROOT.as_posix(), CERT.as_posix(), ' '.join(NAMEN)
    if not tls:
        return f'''{MARKER}
server {{
    listen 80;
    listen [::]:80;
    server_name {namen};
    root {root};
    index index.html;
{ACME}    location / {{ try_files $uri $uri/ =404; }}
}}
'''
    certificaat = f'''    ssl_certificate {cert}/fullchain.pem;
    ssl_certificate_key {cert}/privkey.pem;
'''
    return f'''{MARKER}
server {{
    listen 80;
    listen [::]:80;
    server_name {namen};
    root {root};
{ACME}    location / {{ return 301 https://{HOOFDNAAM}$request_uri; }}
}}
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {DOMEIN};
{certificaat}    return 301 https://{HOOFDNAAM}$request_uri;
}}
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {HOOFDNAAM};
    root {root};
    index index.html;
{certificaat}    location / {{ try_files $uri $uri/ =404; }}
}}
'''


def installeer_config(tls):
    """Schrijft de site, test nginx en herlaadt; bij een fout komt de vorige toestand terug."""
    tekst = nginx_config(tls)
    vorige = CONFIG.read_text() if CONFIG.exists() else None
    if vorige is not None and not vorige.startswith(MARKER):
        raise RuntimeError(f'{CONFIG} hoort bij een andere deployment en blijft ongewijzigd')
    if vorige == tekst and LINK.is_symlink() and LINK.resolve() == CONFIG:
        return
    gelinkt = LINK.is_symlink()
    assert not LINK.exists() or (gelinkt and LINK.resolve() == CONFIG), f'{LINK} wijst naar iets anders'
    try:
        CONFIG.write_text(tekst)
        if not gelinkt:
            LINK.symlink_to(CONFIG)
        subprocess.run(['nginx', '-t'], check=True)
        subprocess.run(['systemctl', 'reload', 'nginx'], check=True)
    except BaseException:
        if vorige is None:
            CONFIG.unlink(missing_ok=True)
        else:
            CONFIG.write_text(vorige)
        if not gelinkt:
            LINK.unlink(missing_ok=True)
        raise


def alleen_ipv4(uitvoer):
    """IPv4-adressen uit `dig +short`; een CNAME-regel ervoor telt niet mee."""
    return {regel for regel in uitvoer.split() if re.fullmatch(r'\d{1,3}(\.\d{1,3}){3}', regel)}


def wijst_hierheen(naam):
    ipv4 = alleen_ipv4(subprocess.check_output(['dig', '+short', naam, 'A'], text=True))
    ipv6 = [r for r in subprocess.check_output(['dig', '+short', naam, 'AAAA'], text=True).split() if ':' in r]
    return ipv4 == {ADRES} and not ipv6


def main():
    assert os.geteuid() == 0, 'dit script moet als root draaien'
    for opdracht in ('nginx', 'systemctl', 'certbot', 'dig'):
        assert shutil.which(opdracht), opdracht + ' is nodig'
    ROOT.mkdir(exist_ok=True)
    tls = (CERT / 'fullchain.pem').is_file() and (CERT / 'privkey.pem').is_file()
    installeer_config(tls)
    if tls:
        print('HTTPS voor Zaad voor de Zaaier staat aan.')
        return
    ontbreekt = [naam for naam in NAMEN if not wijst_hierheen(naam)]
    if ontbreekt:
        print('Bestanden kunnen synchroniseren. HTTPS wacht op DNS: '
              + ', '.join(f'{naam} A {ADRES}' for naam in ontbreekt) + ', zonder AAAA-record.')
        return
    domeinen = [argument for naam in NAMEN for argument in ('-d', naam)]
    subprocess.run(['certbot', 'certonly', '--webroot', '-w', str(ROOT), '--cert-name', DOMEIN, *domeinen,
                    '--non-interactive', '--deploy-hook', 'systemctl reload nginx'], check=True)
    installeer_config(True)
    print('HTTPS voor Zaad voor de Zaaier is aangezet; Certbot vernieuwt het certificaat automatisch.')


if __name__ == '__main__':
    main()
