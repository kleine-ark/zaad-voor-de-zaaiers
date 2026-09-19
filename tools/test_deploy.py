"""Controles op de publicatie: de workflow en het provisioning-script horen bij elkaar."""
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "deploy.yml"
PROVISION = ROOT / "deploy" / "provision.py"


def laad_provision():
    spec = importlib.util.spec_from_file_location("provision", PROVISION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def workflow():
    return WORKFLOW.read_text(encoding="utf-8")


def test_publiceert_bij_elke_push_naar_main():
    tekst = workflow()
    assert re.search(r"on:\s*\n\s*push:\s*\n\s*branches:\s*\n\s*- main\n", tekst)
    assert "ssh root@167.235.54.105 python3 - < deploy/provision.py" in tekst
    assert "secrets.DEPLOY_SSH_KEY" in tekst


def test_workflow_en_script_gebruiken_hetzelfde_domein_en_adres():
    provision = laad_provision()
    tekst = workflow()
    assert re.search(r"deploy_path:\s*(\S+)", tekst).group(1) == f"/var/www/{provision.DOMEIN}"
    assert tekst.count(provision.ADRES) == 2


def test_alleen_de_site_gaat_naar_de_server():
    blok = re.search(r"rsync_excludes: \|\n((?: {8}\S[^\n]*\n)+)", workflow()).group(1)
    uitgesloten = blok.split()
    for pad in [".git/", ".github/", ".gitignore", "README.md", "deploy/", "docs/", "tools/"]:
        assert pad in uitgesloten, pad
    for nodig in ["index.html", "css/", "img/", "fonts/", "brochure/", "robots.txt"]:
        assert nodig not in uitgesloten, nodig


def test_zonder_certificaat_serveert_nginx_beide_namen_over_http():
    p = laad_provision()
    conf = p.nginx_config(tls=False)
    assert conf.startswith(p.MARKER)
    assert "server_name zaadvoordezaaiers.nl www.zaadvoordezaaiers.nl;" in conf
    assert "root /var/www/zaadvoordezaaiers.nl;" in conf
    assert "/.well-known/acme-challenge/" in conf and "443" not in conf and "ssl" not in conf
    assert conf.count("{") == conf.count("}")


def test_met_certificaat_komt_alles_uit_op_https_www():
    p = laad_provision()
    conf = p.nginx_config(tls=True)
    assert conf.count("listen 443 ssl") == 2
    assert conf.count("return 301 https://www.zaadvoordezaaiers.nl$request_uri;") == 2
    assert conf.count("ssl_certificate /etc/letsencrypt/live/zaadvoordezaaiers.nl/fullchain.pem;") == 2
    assert "server_name www.zaadvoordezaaiers.nl;" in conf
    assert "/.well-known/acme-challenge/" in conf
    assert conf.count("{") == conf.count("}")


def test_dns_controle_negeert_cname_regels():
    p = laad_provision()
    assert p.alleen_ipv4("zaadvoordezaaiers.nl.\n167.235.54.105\n") == {"167.235.54.105"}
    assert p.alleen_ipv4("") == set()
