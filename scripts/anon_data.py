"""Copie de démonstration (lien temporaire) : retire des fichiers data/*.json les champs qui nomment les fournisseurs
de données (src, source, sources, feeds, provider) et les adresses de dépôts ; les données elles-mêmes sont inchangées.
  python3 scripts/anon_data.py DOSSIER_DATA"""
import json, os, re, sys

DROP = {"src", "source", "sources", "feeds", "provider", "f", "url_src", "errors", "err", "fails", "report", "seen"}
NAMES = re.compile(r"\b(?:Yahoo Finance(?: France| UK| Canada)?|Yahoo|TradingView|Investing\.com|CNBC|MarketWatch|Benzinga|Motley Fool|Zacks|Nasdaq\.com|SikaFinance|Sika Finance|RichBourse|allAfrica|Financial Afrik|Agence Ecofin|Abidjan\.net)\b")
RX = re.compile(r"github|githubusercontent|jsdelivr|vercel", re.I)


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items() if k not in DROP and not (isinstance(v, str) and RX.search(v))}
    if isinstance(o, str) and o.startswith(("http://", "https://")):
        return ""
    if isinstance(o, list):
        return [clean(v) for v in o]
    return o


root = sys.argv[1]
n = 0
for d, _, fs in os.walk(root):
    for f in fs:
        if not f.endswith(".json"):
            continue
        p = os.path.join(d, f)
        try:
            with open(p, encoding="utf8") as h:
                o = json.load(h)
        except Exception:  # noqa: BLE001
            continue
        o = clean(o)
        if f in ("news.json", "events.json", "events_recent.json", "reports.json"):  # liens d'articles et d'avis : pas d'adresse d'origine
            t = json.dumps(o, ensure_ascii=False, separators=(",", ":"))
            t = re.sub(r'"(u|url|link|s|pdf)":"[^"]*"', lambda m_: f'"{m_.group(1)}":""', t)
            t = NAMES.sub("", t)
            o = json.loads(t)
        with open(p, "w", encoding="utf8") as h:
            json.dump(o, h, separators=(",", ":"), ensure_ascii=False)
        n += 1
print("fichiers nettoyés :", n)
