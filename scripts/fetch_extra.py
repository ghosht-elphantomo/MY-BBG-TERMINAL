#!/usr/bin/env python3
"""Sources complémentaires du terminal FQT, relevées depuis GitHub Actions (bibliothèque standard).

  FRED (Réserve fédérale de St. Louis)  taux, crédit, liquidité, emploi, inflation, activité, stress
  Nasdaq                               ETF (secteurs, facteurs, pays, obligations, matières), indices, Nasdaq-100
  CBOE                                 VIX, VIX9D, VIX3M, VVIX, SKEW
  CNN                                  Fear & Greed officiel et ses 7 composantes
  Coinbase                             BTC, ETH, SOL (quotidien)
  Banque mondiale                      indicateurs des 8 pays de l'UEMOA
  SEC EDGAR (XBRL companyfacts)        comptes trimestriels et annuels des actions US -> flux de trésorerie, ratios

Chaque source est indépendante : une panne n'empêche pas les autres. report.json liste les erreurs.
Le dossier --out (branche quant-raw restaurée) sert aussi de base : on ne relit que les dernières
semaines d'une série déjà présente, sauf si un ajustement (split) est détecté. Un échec laisse l'ancien fichier.

Usage : fetch_extra.py --out RAW_DIR [--only nasdaq,fred,cboe,cnn,crypto,wb,sec,analyst,boc,probe] [--news FILE]
"""
import argparse, csv, datetime as dt, gzip, html as HTML, io, json, math, os, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_terminal import US  # noqa: E402  (univers US déjà suivi)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
SEC_UA = os.environ.get("SEC_UA") or "Mozilla/5.0 (compatible; FQT-Terminal/1.0; personal market research)"
RESEARCH_UA = "FQT-Terminal research ghosht-elphantomo@users.noreply.github.com"  # certains sites (FRED, MarketScreener) refusent les UA de navigateur depuis le cloud
NQ_H = {"Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/", "Accept": "application/json, text/plain, */*"}
TODAY = dt.date.today()
REPORT = {}

# ---------------------------------------------------------------- univers
ETFS = [  # symbole, nom, groupe
    ("SPY", "SPDR S&P 500", "ETF actions US"), ("DIA", "SPDR Dow Jones Industrial", "ETF actions US"), ("IWM", "iShares Russell 2000", "ETF actions US"),
    ("MDY", "SPDR S&P MidCap 400", "ETF actions US"), ("RSP", "Invesco S&P 500 équipondéré", "ETF actions US"),
    ("MTUM", "iShares MSCI USA Momentum", "ETF facteurs"), ("QUAL", "iShares MSCI USA Quality", "ETF facteurs"), ("USMV", "iShares MSCI USA Min Vol", "ETF facteurs"),
    ("VLUE", "iShares MSCI USA Value", "ETF facteurs"), ("SIZE", "iShares MSCI USA Size", "ETF facteurs"), ("SPHB", "Invesco S&P 500 High Beta", "ETF facteurs"),
    ("SPLV", "Invesco S&P 500 Low Volatility", "ETF facteurs"), ("VIG", "Vanguard Dividend Appreciation", "ETF facteurs"),
    ("XLK", "Technologie (SPDR)", "ETF secteurs US"), ("XLF", "Finance (SPDR)", "ETF secteurs US"), ("XLE", "Énergie (SPDR)", "ETF secteurs US"),
    ("XLV", "Santé (SPDR)", "ETF secteurs US"), ("XLY", "Conso. discrétionnaire (SPDR)", "ETF secteurs US"), ("XLP", "Conso. de base (SPDR)", "ETF secteurs US"),
    ("XLI", "Industrie (SPDR)", "ETF secteurs US"), ("XLB", "Matériaux (SPDR)", "ETF secteurs US"), ("XLU", "Services publics (SPDR)", "ETF secteurs US"),
    ("XLRE", "Immobilier (SPDR)", "ETF secteurs US"), ("XLC", "Communication (SPDR)", "ETF secteurs US"),
    ("SMH", "VanEck Semi-conducteurs", "ETF thématiques"), ("IGV", "iShares Logiciel", "ETF thématiques"), ("XBI", "SPDR Biotech", "ETF thématiques"),
    ("ITA", "iShares Aéronautique & défense", "ETF thématiques"), ("ARKK", "ARK Innovation", "ETF thématiques"), ("KWEB", "KraneShares Internet chinois", "ETF thématiques"),
    ("TQQQ", "ProShares UltraPro QQQ (3x)", "ETF à levier"), ("SQQQ", "ProShares UltraPro Short QQQ (-3x)", "ETF à levier"),
    ("QLD", "ProShares Ultra QQQ (2x)", "ETF à levier"), ("SOXL", "Direxion Semi-conducteurs (3x)", "ETF à levier"), ("SSO", "ProShares Ultra S&P 500 (2x)", "ETF à levier"),
    ("EFA", "iShares MSCI EAFE (pays développés)", "ETF pays"), ("EEM", "iShares MSCI Émergents", "ETF pays"), ("EWJ", "iShares MSCI Japon", "ETF pays"),
    ("EWG", "iShares MSCI Allemagne", "ETF pays"), ("EWU", "iShares MSCI Royaume-Uni", "ETF pays"), ("EWQ", "iShares MSCI France", "ETF pays"),
    ("FXI", "iShares China Large-Cap", "ETF pays"), ("INDA", "iShares MSCI Inde", "ETF pays"), ("EWZ", "iShares MSCI Brésil", "ETF pays"),
    ("EWT", "iShares MSCI Taïwan", "ETF pays"), ("EZA", "iShares MSCI Afrique du Sud", "ETF pays"), ("AFK", "VanEck Afrique", "ETF pays"),
    ("NGE", "Global X MSCI Nigeria", "ETF pays"),
    ("SHY", "iShares Trésor US 1-3 ans", "ETF obligations"), ("IEF", "iShares Trésor US 7-10 ans", "ETF obligations"), ("TLT", "iShares Trésor US 20 ans+", "ETF obligations"),
    ("TIP", "iShares obligations indexées (TIPS)", "ETF obligations"), ("LQD", "iShares crédit catégorie investissement", "ETF obligations"),
    ("HYG", "iShares haut rendement", "ETF obligations"), ("EMB", "iShares dette émergente USD", "ETF obligations"), ("AGG", "iShares obligations US agrégées", "ETF obligations"),
    ("GLD", "SPDR Gold Shares (or)", "ETF matières"), ("SLV", "iShares Silver (argent)", "ETF matières"), ("GDX", "VanEck mines d'or", "ETF matières"),
    ("USO", "United States Oil Fund", "ETF matières"), ("UNG", "United States Natural Gas", "ETF matières"), ("DBC", "Invesco matières premières", "ETF matières"),
    ("DBA", "Invesco agriculture", "ETF matières"), ("CPER", "United States Copper", "ETF matières"),
    ("UUP", "Invesco dollar US haussier", "ETF devises"), ("FXE", "Invesco euro", "ETF devises"), ("FXY", "Invesco yen", "ETF devises"),
    ("VNQ", "Vanguard immobilier coté (REIT)", "ETF immobilier"), ("IBIT", "iShares Bitcoin Trust", "ETF crypto"),
]
INDICES = [("SPX", "SPX", "S&P 500"), ("NDX", "NDX", "Nasdaq-100"), ("COMP", "CCMP", "Nasdaq Composite"), ("RUT", "RTY", "Russell 2000")]
FRED = [  # id, nom, groupe, unité
    ("DGS1MO", "Trésor US 1 mois", "Taux", "%"), ("DGS3MO", "Trésor US 3 mois", "Taux", "%"), ("DGS6MO", "Trésor US 6 mois", "Taux", "%"),
    ("DGS1", "Trésor US 1 an", "Taux", "%"), ("DGS2", "Trésor US 2 ans", "Taux", "%"), ("DGS3", "Trésor US 3 ans", "Taux", "%"),
    ("DGS5", "Trésor US 5 ans", "Taux", "%"), ("DGS7", "Trésor US 7 ans", "Taux", "%"), ("DGS10", "Trésor US 10 ans", "Taux", "%"),
    ("DGS20", "Trésor US 20 ans", "Taux", "%"), ("DGS30", "Trésor US 30 ans", "Taux", "%"), ("DFF", "Taux des Fed funds effectif", "Taux", "%"),
    ("T10Y2Y", "Pente 10 ans - 2 ans", "Taux", "pts"), ("T10Y3M", "Pente 10 ans - 3 mois", "Taux", "pts"),
    ("DFII10", "Taux réel 10 ans (TIPS)", "Taux", "%"), ("T10YIE", "Inflation anticipée 10 ans (point mort)", "Inflation", "%"),
    ("T5YIFR", "Inflation anticipée 5 ans dans 5 ans", "Inflation", "%"), ("MORTGAGE30US", "Taux immobilier 30 ans", "Taux", "%"),
    ("BAMLH0A0HYM2", "Écart haut rendement (OAS)", "Crédit", "%"), ("BAMLC0A0CM", "Écart catégorie investissement (OAS)", "Crédit", "%"),
    ("BAMLH0A3HYC", "Écart CCC et moins (OAS)", "Crédit", "%"), ("BAA10Y", "Écart Moody's Baa - 10 ans", "Crédit", "%"), ("AAA10Y", "Écart Moody's Aaa - 10 ans", "Crédit", "%"),
    ("WALCL", "Bilan de la Fed", "Liquidité", "M$"), ("WTREGEN", "Compte du Trésor à la Fed (TGA)", "Liquidité", "Md$"),
    ("RRPONTSYD", "Prises en pension inversées (RRP)", "Liquidité", "Md$"), ("M2SL", "Masse monétaire M2", "Liquidité", "Md$"),
    ("STLFSI4", "Indice de stress financier (St. Louis)", "Stress", "idx"), ("NFCI", "Conditions financières (Chicago)", "Stress", "idx"),
    ("VIXCLS", "VIX", "Stress", "pts"), ("VXNCLS", "VXN (volatilité Nasdaq-100)", "Stress", "pts"), ("OVXCLS", "OVX (volatilité du pétrole)", "Stress", "pts"),
    ("GVZCLS", "GVZ (volatilité de l'or)", "Stress", "pts"), ("DTWEXBGS", "Dollar US pondéré (large)", "Change", "idx"),
    ("UNRATE", "Taux de chômage", "Emploi", "%"), ("ICSA", "Inscriptions hebdo. au chômage", "Emploi", "k"), ("PAYEMS", "Emplois non agricoles", "Emploi", "k"),
    ("SAHMREALTIME", "Règle de Sahm (temps réel)", "Emploi", "pts"), ("JTSJOL", "Offres d'emploi (JOLTS)", "Emploi", "k"),
    ("CPIAUCSL", "Prix à la consommation (CPI)", "Inflation", "idx"), ("CPILFESL", "CPI hors alimentation et énergie", "Inflation", "idx"),
    ("PCEPILFE", "PCE sous-jacent", "Inflation", "idx"), ("PPIACO", "Prix à la production", "Inflation", "idx"),
    ("GDPC1", "PIB réel", "Activité", "Md$"), ("INDPRO", "Production industrielle", "Activité", "idx"), ("RSAFS", "Ventes au détail", "Activité", "M$"),
    ("HOUST", "Mises en chantier", "Activité", "k"), ("UMCSENT", "Confiance des ménages (Michigan)", "Activité", "idx"),
    ("CSUSHPINSA", "Prix des logements Case-Shiller", "Activité", "idx"), ("USREC", "Récession (NBER)", "Activité", "0/1"),
    ("RECPROUSM156N", "Probabilité de récession (lissée)", "Activité", "%"),
    ("SP500", "S&P 500", "Marchés", "pts"), ("NASDAQCOM", "Nasdaq Composite (depuis 1971)", "Marchés", "pts"),
    ("DCOILWTICO", "Pétrole WTI", "Marchés", "$"), ("DEXUSEU", "Dollar par euro", "Change", "$"),
]
CBOE = ["VIX", "VIX9D", "VIX3M", "VVIX", "SKEW"]
CRYPTO = [("BTC", "BTC-USD", "2015-07-20"), ("ETH", "ETH-USD", "2016-05-18"), ("SOL", "SOL-USD", "2021-06-01")]
UEMOA = ["BEN", "BFA", "CIV", "GNB", "MLI", "NER", "SEN", "TGO", "SSF", "WLD"]
WB = [  # indicateur, nom, unité
    ("NY.GDP.MKTP.KD.ZG", "Croissance du PIB réel", "%"), ("FP.CPI.TOTL.ZG", "Inflation (prix à la consommation)", "%"),
    ("NY.GDP.MKTP.CD", "PIB (dollars courants)", "$"), ("NY.GDP.PCAP.CD", "PIB par habitant", "$"), ("NY.GDP.PCAP.PP.CD", "PIB par habitant (PPA)", "$"),
    ("SP.POP.TOTL", "Population", "hab."), ("SP.POP.GROW", "Croissance démographique", "%"), ("SP.URB.TOTL.IN.ZS", "Population urbaine", "%"),
    ("GC.DOD.TOTL.GD.ZS", "Dette de l'État central", "% PIB"), ("BN.CAB.XOKA.GD.ZS", "Solde courant", "% PIB"),
    ("BX.KLT.DINV.WD.GD.ZS", "Investissements directs étrangers (entrées)", "% PIB"), ("BX.TRF.PWKR.DT.GD.ZS", "Envois de fonds des migrants", "% PIB"),
    ("NE.EXP.GNFS.ZS", "Exportations", "% PIB"), ("NE.IMP.GNFS.ZS", "Importations", "% PIB"), ("NE.GDI.TOTL.ZS", "Investissement (FBCF + stocks)", "% PIB"),
    ("GC.REV.XGRT.GD.ZS", "Recettes publiques hors dons", "% PIB"), ("FS.AST.PRVT.GD.ZS", "Crédit au secteur privé", "% PIB"),
    ("FM.LBL.BMNY.ZG", "Croissance de la masse monétaire", "%"), ("FR.INR.LEND", "Taux débiteur", "%"),
    ("IT.CEL.SETS.P2", "Abonnements mobiles", "/100 hab."), ("IT.NET.USER.ZS", "Utilisateurs d'internet", "%"), ("EG.ELC.ACCS.ZS", "Accès à l'électricité", "%"),
    ("SL.UEM.TOTL.ZS", "Chômage (OIT)", "%"), ("SI.POV.DDAY", "Pauvreté (2,15 $/jour)", "%"), ("SP.DYN.LE00.IN", "Espérance de vie", "ans"),
    ("NV.AGR.TOTL.ZS", "Agriculture", "% PIB"), ("NV.IND.TOTL.ZS", "Industrie", "% PIB"), ("NV.SRV.TOTL.ZS", "Services", "% PIB"),
]


# ---------------------------------------------------------------- outils
def log(*a):
    print("[extra]", *a, flush=True)


def note(src, ok=True, err=None):
    r = REPORT.setdefault(src, {"ok": 0, "err": 0, "errors": []})
    if ok:
        r["ok"] += 1
    else:
        r["err"] += 1
        if len(r["errors"]) < 12:
            r["errors"].append(str(err)[:200])


def get(url, headers=None, tries=3, timeout=60, pause=2.0, ua=None):
    err = None
    for k in range(tries):
        try:
            h = {"User-Agent": ua or UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9", "Accept-Encoding": "gzip"}
            h.update(headers or {})
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
                b = r.read()
                if r.headers.get("Content-Encoding") == "gzip" or b[:2] == b"\x1f\x8b":
                    b = gzip.decompress(b)
                return b
        except urllib.error.HTTPError as e:
            err = e
            if e.code in (400, 403, 404):
                break
            time.sleep(pause * (1 + 2 * k))
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(pause * (1 + 2 * k))
    raise err


def curl(url, timeout=40, ua=None):
    """Téléchargement par curl (certains sites filtrent l'empreinte TLS de Python)."""
    import subprocess
    r = subprocess.run(["curl", "-sSL", "--compressed", "-m", str(timeout), "-A", ua or RESEARCH_UA, "-w", "\n%{http_code}", url], capture_output=True, timeout=timeout + 10)
    body, _, code = r.stdout.rpartition(b"\n")
    if code.strip() != b"200":
        raise urllib.error.HTTPError(url, int(code.strip() or 0), "curl", None, None)
    return body


_WB_LAST = [0.0]


def get_wb(url):
    """web.archive.org : une requête toutes les 5 s, pause longue si le site demande de ralentir (429)."""
    for k in range(3):
        wait = 5 - (time.time() - _WB_LAST[0])
        if wait > 0:
            time.sleep(wait)
        _WB_LAST[0] = time.time()
        try:
            return get(url, tries=1, timeout=60, ua=RESEARCH_UA)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(40 * (k + 1))
    raise urllib.error.HTTPError(url, 429, "Too Many Requests", None, None)


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf8") as f:
        json.dump(obj, f, separators=(",", ":"), ensure_ascii=False)


def i2d(i):
    return dt.date(i // 10000, i // 100 % 100, i % 100)


def d2i(d):
    return d.year * 10000 + d.month * 100 + d.day


def prev_series(prev, sid, sub="nasdaq"):
    if not prev:
        return None
    p = os.path.join(prev, sub, sid + ".json")
    try:
        with open(p, encoding="utf8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return None


def find_rows(obj):
    """Premier tableau 'rows' trouvé dans une réponse JSON Nasdaq (la structure varie selon les points d'accès)."""
    if isinstance(obj, dict):
        if isinstance(obj.get("rows"), list):
            return obj["rows"]
        for v in obj.values():
            r = find_rows(v)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_rows(v)
            if r is not None:
                return r
    return None


def money(x):
    if x in (None, "", "N/A", "--"):
        return None
    try:
        return float(str(x).replace("$", "").replace(",", "").strip())
    except ValueError:
        return None


# ---------------------------------------------------------------- Nasdaq
def nasdaq_hist(sym, assetclass, start):
    url = (f"https://api.nasdaq.com/api/quote/{urllib.parse.quote(sym)}/historical?assetclass={assetclass}"
           f"&fromdate={start.isoformat()}&limit=9999&todate={TODAY.isoformat()}")
    j = json.loads(get(url, headers=NQ_H, timeout=60))
    rows = find_rows(j.get("data") or {}) or []
    out = {}
    for r in rows:
        try:
            m, d, y = r["date"].split("/")
            k = int(y) * 10000 + int(m) * 100 + int(d)
        except Exception:  # noqa: BLE001
            continue
        c = money(r.get("close"))
        if not c:
            continue
        o, h, l = money(r.get("open")) or c, money(r.get("high")) or c, money(r.get("low")) or c
        v = money(r.get("volume")) or 0
        out[k] = (k, o, max(h, o, c), min(l, o, c), c, int(v))
    return [out[k] for k in sorted(out)]


def nasdaq_series(sid, sym, assetclass, prev):
    """Historique quotidien : 10 ans au premier passage, puis les 3 dernières semaines recollées sur la série publiée."""
    old = prev_series(prev, sid)
    full_start = dt.date(TODAY.year - 11, 1, 1)
    rows = None
    if old and old.get("d") and (TODAY - i2d(old["d"][-1])).days < 40 and len(old["d"]) > 300:
        start = i2d(old["d"][-1]) - dt.timedelta(days=21)
        new = nasdaq_hist(sym, assetclass, start)
        if new:
            od = dict(zip(old["d"], old["c"]))
            overlap = [(od[r[0]], r[4]) for r in new if r[0] in od]
            if overlap and all(abs(n / o - 1) < 0.004 for o, n in overlap if o):
                first = new[0][0]
                keep = [i for i, d in enumerate(old["d"]) if d < first]
                g = lambda k: old.get(k) or old["c"]  # noqa: E731
                rows = [(old["d"][i], g("o")[i], g("h")[i], g("l")[i], old["c"][i], (old.get("v") or [0] * len(old["d"]))[i]) for i in keep] + new
            else:
                log(sid, "ajustement détecté, relecture complète")
    if rows is None:
        rows = nasdaq_hist(sym, assetclass, full_start)
    if len(rows) < 30:
        raise ValueError(f"{sym}: {len(rows)} lignes")
    return {"d": [r[0] for r in rows], "o": [r[1] for r in rows], "h": [r[2] for r in rows], "l": [r[3] for r in rows],
            "c": [r[4] for r in rows], "v": [r[5] for r in rows]}


def run_nasdaq(out, prev):
    meta = {"etf": [], "idx": [], "ndx": [], "screener": {}}
    # Composition du Nasdaq-100 et secteurs (screener complet)
    ndx = []
    try:
        j = json.loads(get("https://api.nasdaq.com/api/quote/list-type/nasdaq100", headers=NQ_H))
        for r in find_rows(j.get("data") or {}) or []:
            s = (r.get("symbol") or "").strip().upper()
            if s:
                ndx.append({"s": s, "n": r.get("companyName") or r.get("name"), "mcap": money(r.get("marketCap"))})
        note("nasdaq-ndx", ok=bool(ndx), err=None if ndx else "liste vide")
    except Exception as e:  # noqa: BLE001
        note("nasdaq-ndx", False, e)
    try:
        j = json.loads(get("https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=25&offset=0&download=true", headers=NQ_H, timeout=90))
        want = {x["s"] for x in ndx} | {s for s, *_ in US}
        for r in find_rows(j.get("data") or {}) or []:
            s = (r.get("symbol") or "").strip().upper()
            if s in want:
                meta["screener"][s] = {"n": r.get("name"), "sector": r.get("sector"), "ind": r.get("industry"), "cty": r.get("country"),
                                       "mcap": money(r.get("marketCap")), "ipo": r.get("ipoyear")}
        note("nasdaq-screener", ok=bool(meta["screener"]), err=None if meta["screener"] else "vide")
    except Exception as e:  # noqa: BLE001
        note("nasdaq-screener", False, e)
    if not ndx and prev and os.path.exists(os.path.join(prev, "nasdaq_meta.json")):
        ndx = json.load(open(os.path.join(prev, "nasdaq_meta.json"), encoding="utf8")).get("ndx", [])
        log("composition Nasdaq-100 reprise du site précédent", len(ndx))
    meta["ndx"] = ndx
    if not meta["screener"] and prev and os.path.exists(os.path.join(prev, "nasdaq_meta.json")):
        meta["screener"] = json.load(open(os.path.join(prev, "nasdaq_meta.json"), encoding="utf8")).get("screener", {})
    already = {s for s, *_ in US}
    jobs = [(s, s, "etf", "etf", n, g) for s, n, g in ETFS if s not in already]
    jobs += [(sid, sym, "index", "idx", n, "Indices US") for sym, sid, n in INDICES]
    jobs += [(x["s"], x["s"], "stocks", "ndx", x["n"], None) for x in ndx if x["s"] not in already]

    def one(job):
        sid, sym, ac, kind, name, grp = job
        try:
            ser = nasdaq_series(sid, sym, ac, prev)
            save(os.path.join(out, "nasdaq", sid + ".json"), ser)
            note("nasdaq-" + kind)
            return kind, {"id": sid, "sym": sym, "n": name, "g": grp, "rows": len(ser["d"])}
        except Exception as e:  # noqa: BLE001
            note("nasdaq-" + kind, False, f"{sym}: {e}")
            return kind, None
        finally:
            time.sleep(0.25)
    with ThreadPoolExecutor(4) as ex:
        for kind, r in ex.map(one, jobs):
            if r and kind in ("etf", "idx"):
                meta[kind].append(r)
    save(os.path.join(out, "nasdaq_meta.json"), meta)


# ---------------------------------------------------------------- FRED, CBOE, CNN, crypto, Banque mondiale
def run_fred(out):
    fails = [0]

    def one(x):
        sid = x[0]
        if fails[0] >= 6:
            note("fred", False, f"{sid}: source injoignable, abandon")
            return
        try:
            b = get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", timeout=25, tries=2, ua=RESEARCH_UA)
            fails[0] = 0
            txt = b.decode("utf8", "replace")
            if "," not in txt.splitlines()[0]:
                raise ValueError("réponse inattendue")
            os.makedirs(os.path.join(out, "fred"), exist_ok=True)
            open(os.path.join(out, "fred", sid + ".csv"), "w", encoding="utf8").write(txt)
            note("fred")
        except Exception as e:  # noqa: BLE001
            fails[0] += 1
            note("fred", False, f"{sid}: {e}")
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(one, FRED))
    save(os.path.join(out, "fred_meta.json"), [{"id": a, "n": b, "g": c, "u": d} for a, b, c, d in FRED])


def run_cboe(out):
    for s in CBOE:
        try:
            txt = get(f"https://cdn.cboe.com/api/global/us_indices/daily_prices/{s}_History.csv").decode("utf8", "replace")
            os.makedirs(os.path.join(out, "cboe"), exist_ok=True)
            open(os.path.join(out, "cboe", s + ".csv"), "w", encoding="utf8").write(txt)
            note("cboe")
        except Exception as e:  # noqa: BLE001
            note("cboe", False, f"{s}: {e}")


def run_cnn(out):
    h = {"Accept": "application/json, text/plain, */*", "Referer": "https://edition.cnn.com/", "Origin": "https://edition.cnn.com"}
    for start in ("2020-07-15", "2021-01-01", "2023-01-01", None):
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata" + (f"/{start}" if start else "")
        try:
            j = json.loads(get(url, headers=h, tries=2))
            if j.get("fear_and_greed"):
                save(os.path.join(out, "cnn_fg.json"), j)
                note("cnn")
                return
        except Exception as e:  # noqa: BLE001
            note("cnn", False, f"{start}: {e}")


def run_crypto(out, prev):
    for sid, prod, first in CRYPTO:
        try:
            old = prev_series(prev, sid, "crypto")
            rows = {}
            start = dt.date.fromisoformat(first)
            if old and old.get("d") and len(old["d"]) > 300:
                for i, d in enumerate(old["d"]):
                    rows[d] = (d, old["o"][i], old["h"][i], old["l"][i], old["c"][i], (old.get("v") or [0] * len(old["d"]))[i])
                start = i2d(old["d"][-1]) - dt.timedelta(days=5)
            while start < TODAY:
                end = min(start + dt.timedelta(days=299), TODAY)
                url = (f"https://api.exchange.coinbase.com/products/{prod}/candles?granularity=86400"
                       f"&start={start.isoformat()}T00:00:00Z&end={end.isoformat()}T00:00:00Z")
                for t, lo, hi, op, cl, vol in json.loads(get(url, headers={"Accept": "application/json"})):
                    d = d2i(dt.datetime.fromtimestamp(t, dt.timezone.utc).date())
                    if d2i(TODAY) > d:  # jour en cours exclu (bougie incomplète)
                        rows[d] = (d, op, hi, lo, cl, int(vol))
                start = end + dt.timedelta(days=1)
                time.sleep(0.35)
            r = [rows[k] for k in sorted(rows)]
            save(os.path.join(out, "crypto", sid + ".json"), {"d": [x[0] for x in r], "o": [x[1] for x in r], "h": [x[2] for x in r],
                                                              "l": [x[3] for x in r], "c": [x[4] for x in r], "v": [x[5] for x in r]})
            note("coinbase")
        except Exception as e:  # noqa: BLE001
            note("coinbase", False, f"{sid}: {e}")


def run_wb(out):
    res = {"countries": {}, "ind": {}}
    cs = ";".join(UEMOA)
    for code, name, unit in WB:
        try:
            j = json.loads(get(f"https://api.worldbank.org/v2/country/{cs}/indicator/{code}?format=json&per_page=2000&date=1990:{TODAY.year}"))
            vals = {}
            for r in (j[1] if len(j) > 1 and j[1] else []):
                c = r.get("countryiso3code") or r["country"]["id"]
                res["countries"][c] = r["country"]["value"]
                if r.get("value") is not None:
                    vals.setdefault(c, {})[r["date"]] = r["value"]
            res["ind"][code] = {"n": name, "u": unit, "v": vals}
            note("worldbank")
        except Exception as e:  # noqa: BLE001
            note("worldbank", False, f"{code}: {e}")
        time.sleep(0.3)
    if res["ind"]:
        save(os.path.join(out, "worldbank.json"), res)


# ---------------------------------------------------------------- SEC XBRL
FLOW = {  # clé : (concepts us-gaap, concepts ifrs-full) par ordre de préférence
    "rev": (["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax",
             "SalesRevenueNet", "SalesRevenueGoodsNet", "SalesRevenueServicesNet", "RevenuesNetOfInterestExpense"], ["Revenue", "RevenueFromContractsWithCustomers"]),
    "cogs": (["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold", "CostOfServices"], ["CostOfSales"]),
    "gp": (["GrossProfit"], ["GrossProfit"]),
    "opi": (["OperatingIncomeLoss"], ["ProfitLossFromOperatingActivities"]),
    "ni": (["NetIncomeLoss", "NetIncomeLossAvailableToCommonStockholdersBasic", "ProfitLoss"], ["ProfitLossAttributableToOwnersOfParent", "ProfitLoss"]),
    "pti": (["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
             "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
             "IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic"], ["ProfitLossBeforeTax"]),
    "tax": (["IncomeTaxExpenseBenefit"], ["IncomeTaxExpenseContinuingOperations"]),
    "int": (["InterestExpense", "InterestExpenseNonoperating", "InterestExpenseDebt", "InterestAndDebtExpense"], ["FinanceCosts", "InterestExpense"]),
    "rnd": (["ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"], ["ResearchAndDevelopmentExpense"]),
    "da": (["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet", "DepreciationAndAmortization",
            "DepreciationAmortizationAndOther", "Depreciation"], ["DepreciationAndAmortisationExpense",
                                                                   "AdjustmentsForDepreciationAndAmortisationExpense"]),
    "sbc": (["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"], ["AdjustmentsForSharebasedPayments"]),
    "ocf": (["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
            ["CashFlowsFromUsedInOperatingActivities"]),
    "capex": (["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets", "PaymentsForCapitalImprovements",
               "PaymentsToAcquireOtherPropertyPlantAndEquipment"], ["PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
                                                                     "PurchaseOfPropertyPlantAndEquipment"]),
    "capi": (["PaymentsToAcquireIntangibleAssets"], ["PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities"]),
    "acq": (["PaymentsToAcquireBusinessesNetOfCashAcquired"], ["CashFlowsUsedInObtainingControlOfSubsidiariesOrOtherBusinessesClassifiedAsInvestingActivities"]),
    "div": (["PaymentsOfDividends", "PaymentsOfDividendsCommonStock"], ["DividendsPaidClassifiedAsFinancingActivities"]),
    "buy": (["PaymentsForRepurchaseOfCommonStock"], ["PaymentsToAcquireOrRedeemEntitysShares"]),
}
INST = {
    "assets": (["Assets"], ["Assets"]),
    "ca": (["AssetsCurrent"], ["CurrentAssets"]),
    "cl": (["LiabilitiesCurrent"], ["CurrentLiabilities"]),
    "liab": (["Liabilities"], ["Liabilities"]),
    "eq": (["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"], ["EquityAttributableToOwnersOfParent", "Equity"]),
    "cash": (["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "Cash"], ["CashAndCashEquivalents"]),
    "sti": (["MarketableSecuritiesCurrent", "ShortTermInvestments", "AvailableForSaleSecuritiesDebtSecuritiesCurrent"], ["CurrentInvestments"]),
    "ltd": (["LongTermDebt", "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities", "DebtInstrumentCarryingAmount"], []),
    "ltdnc": (["LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations", "LongTermNotesPayable", "ConvertibleNotesPayable"],
              ["NoncurrentPortionOfNoncurrentBorrowings", "LongtermBorrowings", "NoncurrentBorrowings"]),
    "dcur": (["DebtCurrent", "LongTermDebtCurrent", "LongTermDebtAndCapitalLeaseObligationsCurrent"], ["CurrentBorrowings", "CurrentPortionOfNoncurrentBorrowings"]),
    "cp": (["CommercialPaper"], []),
    "stb": (["ShortTermBorrowings"], ["ShorttermBorrowings"]),
    "re": (["RetainedEarningsAccumulatedDeficit"], ["RetainedEarnings"]),
    "inv": (["InventoryNet"], ["Inventories"]),
    "ar": (["AccountsReceivableNetCurrent"], ["TradeAndOtherCurrentReceivables"]),
    "gw": (["Goodwill"], ["Goodwill"]),
}
SHARES = (["WeightedAverageNumberOfDilutedSharesOutstanding"], ["WeightedAverageNumberOfSharesOutstandingDiluted", "AdjustedWeightedAverageShares"])
SHARES_OUT = ["EntityCommonStockSharesOutstanding"]


def days(a, b):
    return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days


def sec_pick(facts, tax, names, unit_kind):
    """Faits d'une liste de concepts : [(rang, start, end, val, filed)] dans l'unité monétaire dominante."""
    rows, unit = [], None
    node = facts.get(tax) or {}
    for rank, nm in enumerate(names):
        c = node.get(nm)
        if not c:
            continue
        units = c.get("units") or {}
        if unit_kind == "shares":
            u = "shares" if "shares" in units else None
        else:
            cands = [k for k in units if re.fullmatch(r"[A-Z]{3}", k)]
            u = "USD" if "USD" in cands else (max(cands, key=lambda k: len(units[k])) if cands else None)
        if not u:
            continue
        unit = unit or u
        if u != unit:
            continue
        for f in units[u]:
            if f.get("val") is None or not f.get("end"):
                continue
            rows.append((rank, f.get("start"), f["end"], float(f["val"]), f.get("filed", "")))
    return rows, unit


def by_period(rows):
    best = {}
    for rank, s, e, v, filed in rows:
        k = (s, e)
        if k not in best or (rank, -int(filed.replace("-", "") or 0)) < (best[k][0], -int(best[k][2].replace("-", "") or 0)):
            best[k] = (rank, v, filed)
    return {k: v[1] for k, v in best.items()}


def quarterize(per):
    """Valeurs trimestrielles discrètes : trimestres publiés directement, sinon différences des cumuls depuis le début d'exercice."""
    q, annual = {}, {}
    for (s, e), v in per.items():
        if not s:
            continue
        n = days(s, e)
        if 75 <= n <= 105:
            q[e] = v
        if 350 <= n <= 380:
            annual[e] = v
    by_s = {}
    for (s, e), v in per.items():
        if not s:
            continue
        n = days(s, e)
        b = round(n / 91.3)
        if b in (1, 2, 3, 4) and abs(n - b * 91.3) <= 22:
            by_s.setdefault(s, {})[b] = (e, v)
    for s, cum in by_s.items():
        for b in (2, 3, 4):
            if b in cum and b - 1 in cum and cum[b][0] not in q:
                q[cum[b][0]] = cum[b][1] - cum[b - 1][1]
    return q, annual


def ttm(q):
    ends = sorted(q)
    out = {}
    for i in range(3, len(ends)):
        if 250 <= days(ends[i - 3], ends[i]) <= 300:
            out[ends[i]] = q[ends[i - 3]] + q[ends[i - 2]] + q[ends[i - 1]] + q[ends[i]]
    return out


def sec_company(cik, t, facts_json):
    facts = facts_json.get("facts") or {}
    tax = "us-gaap" if "us-gaap" in facts else ("ifrs-full" if "ifrs-full" in facts else None)
    if not tax:
        return None
    ti = 0 if tax == "us-gaap" else 1
    ccy = None
    flows_q, flows_a = {}, {}
    for k, names in FLOW.items():
        rows, u = sec_pick(facts, tax, names[ti], "money")
        if not rows:
            continue
        if k in ("rev", "ni", "ocf"):
            ccy = ccy or u
        q, a = quarterize(by_period(rows))
        flows_q[k], flows_a[k] = q, a
    inst = {}
    for k, names in INST.items():
        rows, _ = sec_pick(facts, tax, names[ti], "money")
        if rows:
            per = by_period(rows)
            inst[k] = {e: v for (s, e), v in per.items()}
    rows, _ = sec_pick(facts, tax, SHARES[ti], "shares")
    shd = {}
    if rows:
        best = {}
        for rank, s, e, v, filed in rows:  # durée la plus courte = trimestre
            n = days(s, e) if s else 999
            key = (rank, n, -int(filed.replace("-", "") or 0))
            if e not in best or key < best[e][0]:
                best[e] = (key, v)
        shd = {e: x[1] for e, x in best.items()}
    rows, _ = sec_pick(facts, "dei", SHARES_OUT, "shares")
    sho = by_period(rows) if rows else {}
    sho_last = None
    if sho:
        e = max(e for (_, e) in sho)
        sho_last = (e, sum(v for (s, ee), v in sho.items() if ee == e))
    ttms = {k: ttm(q) for k, q in flows_q.items()}
    ends = sorted(set(ttms.get("rev", {})) | set(ttms.get("ni", {})) | set(ttms.get("ocf", {})))
    annual_mode = len(ends) < 4
    if annual_mode:  # émetteurs étrangers (20-F) : exercices annuels seulement
        ends = sorted(set(flows_a.get("rev", {})) | set(flows_a.get("ni", {})))
        ttms = flows_a
    ends = ends[-48:]

    def near(m, e, tol=12):
        if e in m:
            return m[e]
        best = None
        for k, v in m.items():
            dd = abs(days(k, e))
            if dd <= tol and (best is None or dd < best[0]):
                best = (dd, v)
        return best[1] if best else None
    res = {"t": t, "cik": cik, "name": facts_json.get("entityName"), "tax": tax, "ccy": ccy or "USD", "annual_only": annual_mode, "q": ends,
           "ttm": {k: [near(m, e, 5) for e in ends] for k, m in ttms.items() if m},
           "bs": {k: [near(m, e) for e in ends] for k, m in inst.items() if m},
           "shd": [near(shd, e, 15) for e in ends] if shd else None, "sho": sho_last}
    ya = sorted(set(flows_a.get("rev", {})) | set(flows_a.get("ni", {})) | set(flows_a.get("ocf", {})))[-16:]
    res["y"] = ya
    res["a"] = {k: [near(m, e, 5) for e in ya] for k, m in flows_a.items() if m}
    res["abs"] = {k: [near(m, e) for e in ya] for k, m in inst.items() if m}
    for blk in ("ttm", "bs", "a", "abs"):
        res[blk] = {k: [None if v is None else round(v) for v in arr] for k, arr in res[blk].items() if any(v is not None for v in arr)}
    if res["shd"]:
        res["shd"] = [None if v is None else round(v) for v in res["shd"]]
    return res


def run_sec(out, prev, max_age_days):
    cache = None
    if os.path.exists(os.path.join(out, "secfacts.json")):
        try:
            cache = json.load(open(os.path.join(out, "secfacts.json"), encoding="utf8"))
        except Exception:  # noqa: BLE001
            cache = None
    nd = os.path.join(out, "nasdaq_meta.json")
    ndx = [x["s"] for x in json.load(open(nd, encoding="utf8")).get("ndx", [])] if os.path.exists(nd) else []
    wanted = sorted({s for s, _, typ, _ in US if typ == "Equity"} | set(ndx))
    if cache and (time.time() - cache.get("ts", 0)) < max_age_days * 86400 and set(wanted) <= set(cache.get("co", {})) | set(cache.get("missing", [])):
        save(os.path.join(out, "secfacts.json"), cache)
        log("SEC : cache récent conservé", len(cache.get("co", {})))
        note("sec-cache")
        return
    h = {"User-Agent": SEC_UA, "Accept-Encoding": "gzip", "Accept": "application/json", "Host": None}
    h.pop("Host")
    cikmap = {}
    seed = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "seed", "sec_cik.json")
    if os.path.exists(seed):  # correspondance ticker -> CIK conservée dans le dépôt (la SEC bloque parfois www.sec.gov depuis le cloud)
        cikmap.update(json.load(open(seed, encoding="utf8")))
    for url in ("https://www.sec.gov/files/company_tickers.json", "https://www.sec.gov/include/ticker.txt"):
        try:
            b = get(url, headers=h, tries=2, timeout=30)
            if url.endswith(".json"):
                for v in json.loads(b).values():
                    cikmap[v["ticker"].upper()] = v["cik_str"]
            else:
                for line in b.decode("utf8", "replace").splitlines():
                    p_ = line.split()
                    if len(p_) == 2 and p_[1].isdigit():
                        cikmap[p_[0].upper()] = int(p_[1])
            note("sec-tickers")
            break
        except Exception as e:  # noqa: BLE001
            note("sec-tickers", False, f"{url}: {e}")
    if not cikmap:
        if cache:
            save(os.path.join(out, "secfacts.json"), cache)
        return
    res = {"ts": int(time.time()), "co": {}, "missing": []}

    names = {s: n for s, n, _, _ in US}
    nm_ = os.path.join(out, "nasdaq_meta.json")
    if os.path.exists(nm_):
        for k, v in (json.load(open(nm_, encoding="utf8")).get("screener") or {}).items():
            names.setdefault(k, v.get("n") or "")
    stop = {"inc", "corp", "corporation", "holdings", "holding", "group", "the", "company", "co", "ltd", "plc", "sa", "nv", "class", "common", "stock", "technologies", "technology", "and"}
    tok = lambda x: {w for w in re.sub(r"[^a-z0-9 ]", " ", (x or "").lower()).split() if len(w) > 2 and w not in stop}  # noqa: E731

    def one(t):
        cik = cikmap.get(t) or cikmap.get(t.replace(".", "-"))
        if not cik:
            return t, None, "CIK introuvable"
        try:
            j = json.loads(get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json", headers=h, timeout=90))
            time.sleep(0.25)
            if names.get(t) and not (tok(names[t]) & tok(j.get("entityName"))):
                return t, None, f"CIK {cik} = {j.get('entityName')} (ne correspond pas à {names[t]})"
            return t, sec_company(cik, t, j), None
        except Exception as e:  # noqa: BLE001
            return t, None, str(e)
    with ThreadPoolExecutor(3) as ex:
        for t, r, err in ex.map(one, wanted):
            if r:
                res["co"][t] = r
                note("sec")
            else:
                res["missing"].append(t)
                note("sec", False, f"{t}: {err}")
                if cache and t in cache.get("co", {}):
                    res["co"][t] = cache["co"][t]
    save(os.path.join(out, "secfacts.json"), res)


# ---------------------------------------------------------------- SikaFinance archivé (web.archive.org) : exercices plus anciens
def sika_table(html_):
    """Tableau « chiffres clés » d'une page société SikaFinance : {année: {ca, rn, bnpa, per, div}} (millions FCFA, FCFA/action)."""
    import html as H
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html_, flags=re.S)
    cells = [re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", c))).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", t, re.S)]
    out = {}
    for i, c in enumerate(cells):
        if re.fullmatch(r"20\d\d", c) and i + 4 < len(cells) and all(re.fullmatch(r"20\d\d", cells[i + k]) for k in range(1, 3)):
            yrs = []
            j = i
            while j < len(cells) and re.fullmatch(r"20\d\d", cells[j]):
                yrs.append(int(cells[j]))
                j += 1
            keys = {"chiffre d'affaires": "ca", "chiffre d’affaires": "ca", "résultat net": "rn", "bnpa": "bnpa", "per": "per", "dividende": "div", "produit net bancaire": "ca"}
            while j < len(cells):
                lab = cells[j].lower()
                k = keys.get(lab)
                if k is None and lab.startswith("croissance"):
                    j += 1 + len(yrs) - 1
                    continue
                if k is None:
                    if re.fullmatch(r"20\d\d", cells[j]):
                        break
                    j += 1
                    continue
                vals = cells[j + 1:j + 1 + len(yrs)]
                for y, v in zip(yrs, vals):
                    x = v.replace(" ", "").replace("\xa0", "").replace(" ", "").replace(",", ".")
                    try:
                        out.setdefault(y, {})[k] = float(x)
                    except ValueError:
                        pass
                j += 1 + len(yrs)
            break
    return out


def run_sikah(out):
    path = os.path.join(out, "sika_hist.json")
    db = json.load(open(path, encoding="utf8")) if os.path.exists(path) else {"t": {}, "miss": {}}
    try:
        fund = json.loads(get("https://raw.githubusercontent.com/harzat/brvm-data-public/main/fundamentals.json", timeout=60))
    except Exception as e:  # noqa: BLE001
        note("sikah", False, f"fundamentals: {e}")
        return
    todo = [(t, v.get("source_url")) for t, v in fund.items() if t != "_meta" and v.get("source_url") and t not in db["t"] and db["miss"].get(t, 0) < 3]
    t_end = time.time() + 900
    for t, url in todo:
        if time.time() > t_end:
            break
        base = url.split("://", 1)[1].replace("www.", "")
        try:
            rows = json.loads(get_wb("http://web.archive.org/cdx/search/cdx?url=" + urllib.parse.quote(base) + "&output=json&fl=timestamp,original,statuscode&filter=statuscode:200&collapse=timestamp:6&limit=60") or b"[]")
        except Exception as e:  # noqa: BLE001
            note("sikah", False, f"{t} cdx: {e}")
            db["miss"][t] = db["miss"].get(t, 0) + 1
            time.sleep(3)
            continue
        snaps = sorted([r for r in rows[1:] if r and r[0] < "2025"], key=lambda r: r[0])
        got = {}
        # la plus ancienne capture donne les exercices les plus anciens ; une capture par année au plus
        seen_y = set()
        for ts, orig, _ in snaps:
            if ts[:4] in seen_y or len(seen_y) >= 3:
                continue
            seen_y.add(ts[:4])
            try:
                h_ = get_wb(f"http://web.archive.org/web/{ts}id_/{orig}").decode("utf8", "replace")
                tb = sika_table(h_)
                for y, rec in tb.items():
                    if y not in got:
                        got[y] = dict(rec, src=ts[:8])
            except Exception as e:  # noqa: BLE001
                note("sikah", False, f"{t} {ts}: {e}")
        if got:
            db["t"][t] = {str(y): r for y, r in sorted(got.items())}
            note("sikah")
        else:
            db["miss"][t] = db["miss"].get(t, 0) + 1
            note("sikah", False, f"{t}: aucune capture exploitable")
        save(path, db)
    save(path, db)


# ---------------------------------------------------------------- états financiers BRVM (PDF) : comptes des exercices anciens et nouvelles publications
FIN_LAB = [("rev", r"^(chiffre d.affaires( hors taxes)?( et autres produits)?|chiffre d.affaires net|produit net bancaire|total chiffre d.affaires)\b"),
           ("ni", r"^(benifice net|benefice net|resultat net( de l.exercice)?|resultat net \(perte\)|resultat de l.exercice)\b(?!.*(par action|minoritaire))"),
           ("ebitda", r"^excedent brut d.exploitation"), ("ebit", r"^resultat d.exploitation"),
           ("eq", r"^(total )?capitaux propres$|^capitaux propres( et ressources assimilees)?$"), ("assets", r"^total (actif|bilan|general actif)"),
           ("capex_c", r"^(-\s*)?(acquisitions?|decaissements lies aux acquisitions) d.immobilisations corporelles"),
           ("capex_i", r"^(-\s*)?(acquisitions?|decaissements lies aux acquisitions) d.immobilisations incorporelles"),
           ("cfo", r"^flux de tresorerie (provenant|provenants|issus?|nets?) (des|de l.) ?activites? (operationnelles|d.exploitation)")]
FIN_NUM = re.compile(r"^\(?-?\s*\d{1,3}(?:[ . \xa0]\d{3})*(?:,\d+)?\)?$")


def _nrm(x):
    import unicodedata
    return unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().lower()


def fin_parse(txt):
    """Postes clés d'états financiers (texte pdftotext -layout) : {poste: [N, N-1]}, unité annoncée."""
    lines = txt.splitlines()
    unit = None
    for ln in lines[:250]:
        l_ = _nrm(ln)
        if "millions" in l_ and ("fcfa" in l_ or "f cfa" in l_ or "xof" in l_):
            unit = unit or 1.0
        elif "milliers" in l_ and ("fcfa" in l_ or "f cfa" in l_ or "xof" in l_):
            unit = unit or 1e-3
    found = {}
    for ln in lines:
        segs = [x for x in re.split(r"\s{3,}", ln.strip()) if x]
        i = 0
        while i < len(segs):
            lab = _nrm(segs[i]).strip(" :.-")
            if FIN_NUM.match(segs[i].strip()) or not re.search(r"[a-z]", lab):
                i += 1
                continue
            nums, j = [], i + 1
            while j < len(segs) and FIN_NUM.match(segs[j].strip()) and len(nums) < 4:
                t_ = segs[j].strip()
                neg = t_.startswith("(") or t_.startswith("-")
                try:
                    v = float(re.sub(r"[()\s. \xa0-]", "", t_).replace(",", "."))
                    nums.append(-v if neg else v)
                except ValueError:
                    pass
                j += 1
            lab = re.sub(r"\s+", " ", lab)
            for k, pat in FIN_LAB:
                if k not in found and nums and re.search(pat, lab):
                    found[k] = nums[:2]
            i = j if j > i + 1 else i + 1
    return found, unit


def fin_scale(found, unit, ref):
    """Facteur vers les millions de FCFA : unité annoncée, sinon ordre de grandeur face au chiffre d'affaires de référence."""
    v = (found.get("rev") or found.get("assets") or found.get("ni") or [None])[0]
    if ref and v:
        best = None
        for dv in (1.0, 1e-3, 1e-6):
            r = abs(v * dv) / ref
            sc = abs(math.log10(r)) if r > 0 else 99
            if best is None or sc < best[0]:
                best = (sc, dv)
        if best and best[0] < 0.8:  # à moins d'un facteur ~6 de la référence
            return best[1]
    return unit


def fin_record(found, div_):
    rec = [{}, {}]
    for k, vals in found.items():
        for c in (0, 1):
            if c < len(vals) and vals[c] is not None:
                rec[c][k] = round(vals[c] * div_, 1)
    for r in rec:
        if "capex_c" in r or "capex_i" in r:
            r["capex"] = round(abs(r.pop("capex_c", 0) or 0) + abs(r.pop("capex_i", 0) or 0), 1)
        if "cfo" in r and "capex" in r:
            r["fcf"] = round(r["cfo"] - r["capex"], 1)
    return rec


def run_pdffin(out, budget=600):
    path = os.path.join(out, "pdf_fin.json")
    db = json.load(open(path, encoding="utf8")) if os.path.exists(path) else {"t": {}, "docs": {}}
    try:
        evs = json.loads(get("https://raw.githubusercontent.com/harzat/brvm-data-public/main/events.json", timeout=60))["events"]
        fund = json.loads(get("https://raw.githubusercontent.com/harzat/brvm-data-public/main/fundamentals.json", timeout=60))
    except Exception as e:  # noqa: BLE001
        note("pdffin", False, e)
        return
    sh = (json.load(open(os.path.join(out, "sika_hist.json"), encoding="utf8")).get("t", {}) if os.path.exists(os.path.join(out, "sika_hist.json")) else {})

    def ref_ca(t, y):
        ca = dict(((fund.get(t) or {}).get("series") or {}).get("ca") or {})
        for yy, r in (sh.get(t) or {}).items():
            if r.get("ca") and yy not in ca:
                ca[yy] = r["ca"]
        ca = {int(k): v for k, v in ca.items() if v}
        if not ca:
            return None
        return ca[min(ca, key=lambda k: abs(k - y))]
    cand = {}
    for e in evs:
        t, fy, u = e.get("ticker"), e.get("fiscal_year"), e.get("document_url") or ""
        if not t or not fy or e.get("category") != "financial_statements" or not u.lower().endswith(".pdf"):
            continue
        ti = _nrm(e.get("title") or "")
        rank = (0 if ("certifi" in ti or "approuv" in ti or "annule et remplace" in ti) else 1, -(int((e.get("published_at") or "0")[:10].replace("-", "") or 0)))
        cand.setdefault((t, int(fy)), []).append((rank, u))
    todo = [(k, sorted(v)[0][1]) for k, v in cand.items() if k[1] >= 2012 and sorted(v)[0][1] not in db["docs"]]
    todo.sort(key=lambda x: -x[0][1])
    t_end = time.time() + budget
    for (t, fy), u in todo:
        if time.time() > t_end:
            break
        try:
            txt = pdftext(get(u, tries=2, timeout=60))
        except Exception as e:  # noqa: BLE001
            db["docs"][u] = f"erreur {str(e)[:80]}"
            continue
        if len(txt.strip()) < 300:
            db["docs"][u] = "scan sans texte"
            note("pdffin", False, f"{t} {fy}: scan")
            continue
        found, unit = fin_parse(txt)
        div_ = fin_scale(found, unit, ref_ca(t, fy))
        if not found or div_ is None:
            db["docs"][u] = "postes introuvables" if not found else "échelle incertaine"
            note("pdffin", False, f"{t} {fy}: {db['docs'][u]}")
            continue
        cur, prev = fin_record(found, div_)
        tt = db["t"].setdefault(t, {})
        for y, r in ((fy, cur), (fy - 1, prev)):
            if r and (str(y) not in tt or y == fy):
                tt[str(y)] = dict(r, src=u)
        db["docs"][u] = "ok"
        note("pdffin")
    save(path, db)


# ---------------------------------------------------------------- consensus des analystes (Nasdaq)
def us_equities(out):
    nd = os.path.join(out, "nasdaq_meta.json")
    ndx = [x["s"] for x in json.load(open(nd, encoding="utf8")).get("ndx", [])] if os.path.exists(nd) else []
    return sorted({s for s, _, typ, _ in US if typ == "Equity"} | set(ndx))


def run_analyst(out):
    """Résumé (PER prévisionnel, objectif de cours), prévisions de BPA (révisions), surprises, date des résultats.
    Les surprises et les instantanés du consensus s'accumulent d'un jour à l'autre (historique des révisions)."""
    path = os.path.join(out, "analyst.json")
    old = json.load(open(path, encoding="utf8")) if os.path.exists(path) else {}
    today = TODAY.isoformat()

    def one(sym):
        rec = {"ts": today}
        for key, url in (("sum", f"https://api.nasdaq.com/api/quote/{sym}/summary?assetclass=stocks"),
                         ("fc", f"https://api.nasdaq.com/api/analyst/{sym}/earnings-forecast"),
                         ("sur", f"https://api.nasdaq.com/api/company/{sym}/earnings-surprise"),
                         ("ed", f"https://api.nasdaq.com/api/analyst/{sym}/earnings-date"),
                         ("tp", f"https://api.nasdaq.com/api/analyst/{sym}/targetprice")):
            try:
                j = json.loads(get(url, headers=NQ_H, tries=2, timeout=30))
                rec[key] = j.get("data")
            except Exception as e:  # noqa: BLE001
                rec[key] = None
                note("nasdaq-analyst", False, f"{sym} {key}: {e}")
            time.sleep(0.15)
        return sym, rec
    res = {}
    with ThreadPoolExecutor(4) as ex:
        for sym, rec in ex.map(one, us_equities(out)):
            prev = old.get(sym) or {}
            # surprises : on garde tous les trimestres déjà vus
            hist = {r["q"]: r for r in prev.get("surh", [])}
            for r in (find_rows((rec.get("sur") or {}).get("earningsSurpriseTable") or {}) or []):
                q = r.get("fiscalQtrEnd")
                if q:
                    hist[q] = {"q": q, "d": r.get("dateReported"), "eps": money(r.get("eps")), "cons": money(r.get("consensusForecast")),
                               "pct": money(r.get("percentageSurprise"))}
            rec["surh"] = sorted(hist.values(), key=lambda r: r.get("d") or "")
            # instantané quotidien du consensus annuel (pour suivre les révisions)
            snaps = [x for x in prev.get("snap", []) if x[0] != today][-400:]
            yrows = find_rows(((rec.get("fc") or {}).get("yearlyForecast")) or {}) or []
            if yrows:
                snaps.append([today] + [[r.get("fiscalEnd"), money(r.get("consensusEPSForecast")), money(r.get("noOfEstimates"))] for r in yrows[:3]])
            rec["snap"] = snaps
            ok = any(rec.get(k) for k in ("sum", "fc", "sur"))
            if not ok and prev:
                rec = {**prev, "stale": True}
            res[sym] = rec
            note("nasdaq-analyst", ok, None if ok else f"{sym}: vide")
    save(path, res)


# ---------------------------------------------------------------- BRVM : bulletin officiel de la cote (PER du marché)
def pdftext(b):
    import subprocess, tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(b)
        f.flush()
        r = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, timeout=120)
    return r.stdout.decode("utf8", "replace")


def frnum(tok):
    t = tok.replace("\xa0", " ").replace(" ", " ").strip()
    t = re.sub(r"(?<=\d)[ .](?=\d{3}\b)", "", t).replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


NUMTOK = re.compile(r"-?\d{1,3}(?:[  \xa0.]\d{3})+(?:,\d+)?|-?\d+(?:,\d+)?")


def boc_parse(txt):
    out = {}
    pats = {"per": r"PER moyen du march", "rdt": r"Taux de rendement moyen du march", "rent": r"Taux de rentabilit[ée] moyen du march",
            "prime": r"Prime de risque du march", "cap": r"Capitalisation boursi[èe]re \(FCFA\)\s*\(Actions"}
    lines = txt.splitlines()
    for k, pat in pats.items():
        for i, ln in enumerate(lines):
            m = re.search(pat, ln, re.I)
            if not m:
                continue
            rest = re.sub(r"\(\*+\)", " ", ln[m.end():])
            rest = re.sub(r"\([^)]*\)", " ", rest)
            nums = [frnum(x) for x in NUMTOK.findall(rest)]
            nums = [x for x in nums if x is not None]
            if not nums and i + 1 < len(lines):
                nums = [x for x in (frnum(y) for y in NUMTOK.findall(lines[i + 1])) if x is not None]
            if nums:
                out[k] = nums[0]
                break
    for k, lo, hi in (("per", 2, 80), ("rdt", 0.1, 30), ("rent", 0.1, 40), ("prime", -20, 30)):
        if k in out and not (lo <= out[k] <= hi):
            out.pop(k)
    return out


def run_boc(out):
    import calendar
    path = os.path.join(out, "boc.json")
    db = json.load(open(path, encoding="utf8")) if os.path.exists(path) else {"d": {}, "miss": []}
    miss = set(db.get("miss", []))

    def try_day(d):
        k = d.strftime("%Y%m%d")
        for url in (f"https://bfin.brvm.org/boc/BOC_JOUR/BOC_{k}.pdf", f"https://www.brvm.org/sites/default/files/boc_{k}_2.pdf",
                    f"https://www.brvm.org/sites/default/files/boc_{k}.pdf"):
            try:
                b = get(url, tries=1, timeout=20)
                if b[:4] != b"%PDF":
                    continue
                txt = pdftext(b)
                rec = boc_parse(txt)
                if rec:
                    rec["u"] = url
                    return k, rec, txt
            except Exception:  # noqa: BLE001
                continue
        return k, None, None
    # derniers jours ouvrés
    latest_txt = None
    for back in range(0, 8):
        d = TODAY - dt.timedelta(days=back)
        if d.weekday() >= 5 or d.strftime("%Y%m%d") in db["d"]:
            continue
        k, rec, txt = try_day(d)
        if rec:
            db["d"][k] = rec
            latest_txt = latest_txt or txt
            note("boc")
    # rattrapage : un bulletin par mois (premiers jours ouvrés) depuis 2012, 30 mois par passage
    have_m = {k[:6] for k in db["d"]}
    todo = []
    y, m = 2012, 1
    while (y, m) <= (TODAY.year, TODAY.month):
        km = f"{y}{m:02d}"
        if km not in have_m and km not in miss:
            todo.append((y, m))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    todo = todo[::-1][:14]

    def month(ym):
        y, m = ym
        for day in range(1, min(10, calendar.monthrange(y, m)[1]) + 1):
            d = dt.date(y, m, day)
            if d.weekday() >= 5 or d > TODAY:
                continue
            k, rec, txt = try_day(d)
            if rec:
                return ym, k, rec, txt
        return ym, None, None, None
    with ThreadPoolExecutor(3) as ex:
        for (y, m), k, rec, txt in ex.map(month, todo):
            if rec:
                db["d"][k] = rec
                latest_txt = latest_txt or txt
                note("boc-hist")
            elif (y, m) < (TODAY.year, TODAY.month):
                miss.add(f"{y}{m:02d}")
                note("boc-hist", False, f"{y}-{m:02d}: aucun bulletin lisible")
    db["miss"] = sorted(miss)
    db["d"] = dict(sorted(db["d"].items()))
    save(path, db)
    if latest_txt:
        os.makedirs(os.path.join(out, "debug"), exist_ok=True)
        open(os.path.join(out, "debug", "boc_sample.txt"), "w", encoding="utf8").write(latest_txt[:20000])


# ---------------------------------------------------------------- sondes (PER prévisionnel, archives SikaFinance)
def run_probe(out):
    """Pages brutes enregistrées dans debug/ pour écrire les analyseurs (sources de PER prévisionnel, archives)."""
    dd = os.path.join(out, "debug")
    os.makedirs(dd, exist_ok=True)
    pages = {
        "ms_search_sonatel": "https://www.marketscreener.com/search/?q=sonatel",
        "ms_sonatel": "https://www.marketscreener.com/quote/stock/SONATEL-SA-6500147/",
        "ms_sonatel_fin": "https://www.marketscreener.com/quote/stock/SONATEL-SA-6500147/finances/",
        "valora_home": "https://www.valora-intelligence.com/",
        "afm_brvm": "https://www.african-markets.com/fr/bourse/brvm",
        "afm_brvm_cos": "https://www.african-markets.com/fr/bourse/brvm/listed-companies",
        "richbourse": "https://www.richbourse.com/common/apprendre/details/per",
        "sika_snts": "https://www.sikafinance.com/marches/societe/SNTS.sn",
        "sika_pro_snts": "https://pro.sikafinance.com/finance/SNTS.sn",
    }
    for k, url in pages.items():
        try:
            b = curl(url) if "marketscreener" in url else get(url, tries=2, timeout=40, headers={"Accept": "text/html,application/xhtml+xml"})
            open(os.path.join(dd, k + ".html"), "wb").write(b[:1_500_000])
            note("probe")
        except Exception as e:  # noqa: BLE001
            note("probe", False, f"{k}: {e}")
    sec_t = {}
    for ua in (SEC_UA, "FQT Terminal research contact@fqt-terminal.app", "Mozilla/5.0 (compatible; research-bot)", UA):
        try:
            b = get("https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/Revenues.json", headers={"Accept-Encoding": "gzip"}, tries=1, timeout=20, ua=ua)
            sec_t[ua] = f"ok {len(b)}"
        except urllib.error.HTTPError as e:
            sec_t[ua] = f"{e.code} {e.read()[:300]!r}"
        except Exception as e:  # noqa: BLE001
            sec_t[ua] = str(e)
    save(os.path.join(dd, "sec_ua_test.json"), sec_t)
    cdx = {}
    for t in ("SNTS", "SGBC", "ORAC", "SIBC"):
        for pat in (f"sikafinance.com/marches/societe/{t}*", f"sikafinance.com/marches/cotation_{t}*", f"pro.sikafinance.com/finance/{t}*"):
            try:
                url = ("http://web.archive.org/cdx/search/cdx?url=" + urllib.parse.quote(pat, safe="*/") +
                       "&output=json&fl=timestamp,original,statuscode&filter=statuscode:200&collapse=timestamp:6&limit=200")
                cdx[pat] = json.loads(get(url, tries=2, timeout=60) or b"[]")
                note("probe-wayback")
            except Exception as e:  # noqa: BLE001
                note("probe-wayback", False, f"{pat}: {e}")
            time.sleep(1)
    save(os.path.join(dd, "wayback_cdx.json"), cdx)
    # échantillon d'états financiers (texte extrait) pour l'analyseur des comptes sur 10 exercices
    try:
        evs = json.loads(get("https://raw.githubusercontent.com/harzat/brvm-data-public/main/events.json", timeout=60))["events"]
        picks = {}
        for e in evs:
            t, fy, u = e.get("ticker"), e.get("fiscal_year"), e.get("document_url") or ""
            if e.get("category") == "financial_statements" and t in ("SNTS", "ORAC", "SLBC", "PALC", "SPHC", "TTLC", "CIEC", "SGBC", "SIBC", "NTLC") and fy in (2017, 2019) and u.lower().endswith(".pdf"):
                picks.setdefault((t, fy), u)
        for (t, fy), u in list(picks.items())[:14]:
            try:
                txt = pdftext(get(u, tries=2, timeout=60))
                open(os.path.join(dd, f"pdf_{t}_{fy}.txt"), "w", encoding="utf8").write(f"{u}\n" + txt[:120000])
                note("probe-pdf", ok=len(txt.strip()) > 200, err=None if len(txt.strip()) > 200 else f"{t} {fy}: texte vide (scan)")
            except Exception as e:  # noqa: BLE001
                note("probe-pdf", False, f"{t} {fy}: {e}")
    except Exception as e:  # noqa: BLE001
        note("probe-pdf", False, e)
    # un instantané ancien de chaque motif trouvé
    for pat, rows in cdx.items():
        rows = [r for r in rows[1:] if r and r[0][:4] in ("2016", "2017", "2018", "2019", "2020")] if rows else []
        if not rows:
            continue
        ts, orig = rows[len(rows) // 2][0], rows[len(rows) // 2][1]
        try:
            b = get(f"http://web.archive.org/web/{ts}id_/{orig}", tries=2, timeout=60)
            open(os.path.join(dd, "wb_" + re.sub(r"\W", "_", pat)[:40] + f"_{ts}.html"), "wb").write(b[:1_500_000])
        except Exception as e:  # noqa: BLE001
            note("probe-wayback", False, f"snapshot {pat}: {e}")
        time.sleep(1)


# ---------------------------------------------------------------- veille : publications BRVM et dépôts SEC (chaque passage)
def norm_name(x):
    import unicodedata
    x = unicodedata.normalize("NFKD", x or "").encode("ascii", "ignore").decode().lower()
    x = re.sub(r"\b(sa|s\.a\.|ci|cote d.?ivoire|cote divoire|senegal|burkina( faso)?|benin|mali|niger|togo|bf|sn|bn|ml|ng|tg|groupe|group|holding|societe|ste)\b", " ", x)
    return re.sub(r"[^a-z0-9]+", " ", x).strip()


def run_watch(raw, site_data):
    """Nouvelles publications des sociétés cotées (brvm.org) et nouveaux 10-K/10-Q (SEC) : actualités + données à jour."""
    path = os.path.join(site_data, "reports.json")
    st = json.load(open(path, encoding="utf8")) if os.path.exists(path) else {"issuers": {}, "docs": {}, "its": 0}
    summ = json.load(open(os.path.join(site_data, "summary.json"), encoding="utf8")) if os.path.exists(os.path.join(site_data, "summary.json")) else {"secs": []}
    brvm = [x for x in summ.get("secs", []) if x.get("mkt") == "BRVM" and x.get("cls") == "Equity"]
    if not st["issuers"] or time.time() - st.get("its", 0) > 86400:
        iss = {}
        for pg in range(0, 4):
            try:
                html = get("https://www.brvm.org/fr/rapports-societes-cotees" + (f"?page={pg}" if pg else ""), tries=2, timeout=30).decode("utf8", "replace")
            except Exception as e:  # noqa: BLE001
                note("watch-brvm", False, f"liste p{pg}: {e}")
                break
            found = re.findall(r'href="(?:https://www\.brvm\.org)?/fr/rapports-societe-cotes/([a-z0-9\-]+)"[^>]*>([^<]+)</a>', html)
            if not found:
                break
            for slug, name in found:
                iss[slug] = {"n": re.sub(r"\s+", " ", name).strip()}
        if iss:
            for slug, x in iss.items():  # rapprochement nom -> ticker
                a = set(norm_name(x["n"] + " " + slug.replace("-", " ")).split())
                best = None
                for s in brvm:
                    b = set(norm_name((s.get("n") or "") + " " + (s.get("short") or "")).split())
                    sc = len(a & b) / max(1, len(a | b))
                    if sc > (best[0] if best else 0.34):
                        best = (sc, s["id"])
                x["t"] = best[1] if best else None
            st["issuers"], st["its"] = iss, int(time.time())
    fresh = []

    def one(slug):
        try:
            html = get(f"https://www.brvm.org/fr/rapports-societe-cotes/{slug}", tries=2, timeout=30).decode("utf8", "replace")
        except Exception as e:  # noqa: BLE001
            return slug, None, str(e)
        rows = []
        for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.S):
            cell = m.group(1)
            u = re.search(r'href="([^"]+\.pdf)"', cell)
            if not u:
                continue
            title = re.sub(r"<[^>]+>", " ", cell)
            title = re.sub(r"\s+", " ", title).replace("Télécharger", "").strip()
            url = u.group(1) if u.group(1).startswith("http") else "https://www.brvm.org" + u.group(1)
            dm = re.search(r"/(20\d{6})", url)
            rows.append({"d": dm.group(1) if dm else None, "ti": title[:200], "u": url})
        return slug, rows, None
    with ThreadPoolExecutor(8) as ex:
        for slug, rows, err in ex.map(one, list(st["issuers"])):
            if rows is None:
                note("watch-brvm", False, f"{slug}: {err}")
                continue
            note("watch-brvm")
            old = {r["u"] for r in st["docs"].get(slug, [])}
            if st["docs"].get(slug) is not None:
                fresh += [dict(r, slug=slug) for r in rows if r["u"] not in old]
            st["docs"][slug] = rows[:40]
    st["ts"] = int(time.time())
    # dépôts SEC récents (10-K, 10-Q, 20-F, 6-K) des sociétés suivies
    sec_new = []
    facts_p = os.path.join(raw, "secfacts.json")
    co = (json.load(open(facts_p, encoding="utf8")).get("co") or {}) if os.path.exists(facts_p) else {}
    cik2t = {int(v["cik"]): t for t, v in co.items() if v.get("cik")}
    seen = set(st.get("sec_seen", []))
    h = {"User-Agent": SEC_UA, "Accept-Encoding": "gzip"}
    for form in ("10-Q", "10-K", "20-F", "6-K", "8-K"):
        try:
            x = get(f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type={form}&company=&dateb=&owner=include&start=0&count=100&output=atom", headers=h, tries=2, timeout=30).decode("utf8", "replace")
        except Exception as e:  # noqa: BLE001
            note("watch-sec", False, f"{form}: {e}")
            continue
        note("watch-sec")
        for ent in re.findall(r"<entry>(.*?)</entry>", x, re.S):
            t_ = re.search(r"<title>([^<]+)</title>", ent)
            l_ = re.search(r'<link[^>]+href="([^"]+)"', ent)
            c_ = re.search(r"\((\d{10})\)", t_.group(1) if t_ else "")
            if not (t_ and c_):
                continue
            cik = int(c_.group(1))
            key = (l_.group(1) if l_ else t_.group(1))
            if cik in cik2t and key not in seen:
                seen.add(key)
                sec_new.append({"t": cik2t[cik], "form": form, "ti": t_.group(1), "u": l_.group(1) if l_ else ""})
    st["sec_seen"] = sorted(seen)[-500:]
    save(path, st)
    # actualités : publications officielles
    np_ = os.path.join(site_data, "news.json")
    news = json.load(open(np_, encoding="utf8")) if os.path.exists(np_) else {"items": [], "feeds": {}}
    now = int(time.time())
    for r in fresh:
        tk = st["issuers"].get(r["slug"], {}).get("t")
        news["items"].insert(0, {"t": now, "ti": r["ti"], "u": r["u"], "s": "brvm.org", "c": "BRVM", "f": "brvm-rapports", "x": f"Nouvelle publication officielle{(' · ' + tk) if tk else ''}"})
    for r in sec_new:
        news["items"].insert(0, {"t": now, "ti": f"Dépôt SEC {r['form']} : {r['ti']}", "u": r["u"], "s": "SEC EDGAR", "c": "Tech US", "f": "sec", "x": r["t"]})
    if fresh or sec_new:
        news["feeds"]["brvm-rapports"], news["feeds"]["sec"] = "brvm.org", "SEC EDGAR"
        save(np_, news)
    # états financiers publiés à l'instant : comptes lus tout de suite (si pdftotext est disponible)
    import shutil
    newfs = [r for r in fresh if re.search(r"etats? financiers", _nrm(r["ti"])) and st["issuers"].get(r["slug"], {}).get("t")]
    if newfs and not shutil.which("pdftotext"):
        os.system("sudo apt-get install -y -qq poppler-utils >/dev/null 2>&1")
    if newfs and shutil.which("pdftotext"):
        pp = os.path.join(raw, "pdf_fin.json")
        db = json.load(open(pp, encoding="utf8")) if os.path.exists(pp) else {"t": {}, "docs": {}}
        for r in newfs:
            t = st["issuers"][r["slug"]]["t"]
            m = re.search(r"(20\d\d)", re.sub(r"^.*exercice", "", _nrm(r["ti"])))
            if not m:
                continue
            fy = int(m.group(1))
            try:
                found, unit = fin_parse(pdftext(get(r["u"], tries=2, timeout=60)))
                tt = db["t"].get(t, {})
                ref = None
                for yy in sorted(tt, reverse=True):
                    if tt[yy].get("rev"):
                        ref = tt[yy]["rev"]
                        break
                div_ = fin_scale(found, unit, ref)
                if found and div_:
                    cur, prev = fin_record(found, div_)
                    db["t"].setdefault(t, {})[str(fy)] = dict(cur, src=r["u"])
                    db["t"][t].setdefault(str(fy - 1), dict(prev, src=r["u"]))
                    db["docs"][r["u"]] = "ok"
                    note("watch-pdf")
            except Exception as e:  # noqa: BLE001
                note("watch-pdf", False, f"{t}: {e}")
        save(pp, db)
        open(os.path.join(raw, ".dirty"), "a").write(" pdf")
    # comptes SEC rafraîchis tout de suite pour les sociétés qui viennent de déposer
    dirty = sorted({r["t"] for r in sec_new if r["form"] in ("10-Q", "10-K", "20-F", "6-K")})
    if dirty and co:
        h2 = {"User-Agent": SEC_UA, "Accept-Encoding": "gzip", "Accept": "application/json"}
        allf = json.load(open(facts_p, encoding="utf8"))
        for t in dirty:
            try:
                cik = allf["co"][t]["cik"]
                j = json.loads(get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json", headers=h2, timeout=90))
                r = sec_company(cik, t, j)
                if r:
                    allf["co"][t] = r
                    note("watch-sec-refresh")
            except Exception as e:  # noqa: BLE001
                note("watch-sec-refresh", False, f"{t}: {e}")
            time.sleep(0.3)
        save(facts_p, allf)
        open(os.path.join(raw, ".dirty"), "w").write(" ".join(dirty))
    log(f"veille : {len(fresh)} publications BRVM, {len(sec_new)} dépôts SEC, comptes rafraîchis : {dirty}")


# ---------------------------------------------------------------- actualités (RSS)
NEWS = [  # id, libellé, url, catégorie
    ("gn-brvm", "Google Actualités", "https://news.google.com/rss/search?q=BRVM&hl=fr&gl=FR&ceid=FR:fr", "BRVM"),
    ("gn-bourse-abidjan", "Google Actualités", "https://news.google.com/rss/search?q=%22Bourse+r%C3%A9gionale%22+OR+%22bourse+d%27Abidjan%22+OR+Sonatel+OR+%22Orange+C%C3%B4te+d%27Ivoire%22+OR+SGBCI+OR+%22Ecobank+Transnational%22&hl=fr&gl=FR&ceid=FR:fr", "BRVM"),
    ("gn-uemoa", "Google Actualités", "https://news.google.com/rss/search?q=BCEAO+OR+UEMOA+OR+%22UMOA-Titres%22&hl=fr&gl=FR&ceid=FR:fr", "UEMOA"),
    ("financialafrik", "Financial Afrik", "https://www.financialafrik.com/feed/", "Afrique"),
    ("allafrica-eco", "allAfrica", "https://fr.allafrica.com/tools/headlines/rdf/business/headlines.rdf", "Afrique"),
    ("ecofin", "Agence Ecofin", "https://www.agenceecofin.com/finance?format=feed&type=rss", "Afrique"),
    ("gn-marches", "Google Actualités", "https://news.google.com/rss/search?q=%22march%C3%A9s+financiers%22+OR+%22Wall+Street%22+OR+%22CAC+40%22&hl=fr&gl=FR&ceid=FR:fr", "Marchés"),
    ("lesechos", "Les Echos", "https://syndication.lesechos.fr/rss/rss_finance-marches.xml", "Marchés"),
    ("investing-fr", "Investing.com", "https://fr.investing.com/rss/news.rss", "Marchés"),
    ("cnbc-markets", "CNBC", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258", "Marchés"),
    ("cnbc-top", "CNBC", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "Marchés"),
    ("marketwatch", "MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories", "Marchés"),
    ("yahoo", "Yahoo Finance", "https://finance.yahoo.com/news/rssindex", "Marchés"),
    ("gn-tech", "Google Actualités", "https://news.google.com/rss/search?q=Nasdaq+OR+Nvidia+OR+semiconductors+stocks&hl=en-US&gl=US&ceid=US:en", "Tech US"),
    ("fed", "Réserve fédérale", "https://www.federalreserve.gov/feeds/press_all.xml", "Banques centrales"),
    ("ecb", "BCE", "https://www.ecb.europa.eu/rss/press.html", "Banques centrales"),
    ("gn-bceao", "Google Actualités", "https://news.google.com/rss/search?q=BCEAO+taux+directeur+OR+%22politique+mon%C3%A9taire%22+BCEAO&hl=fr&gl=FR&ceid=FR:fr", "Banques centrales"),
    ("gn-matieres", "Google Actualités", "https://news.google.com/rss/search?q=cacao+OR+%22prix+du+p%C3%A9trole%22+OR+%22cours+de+l%27or%22&hl=fr&gl=FR&ceid=FR:fr", "Matières premières"),
]


def parse_feed(b):
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    b = re.sub(rb"^\s+", b"", b)
    root = ET.fromstring(b)
    items = []
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        g = {}
        for ch in it:
            ct = ch.tag.split("}")[-1]
            if ct == "link" and ch.get("href"):
                g.setdefault("link", ch.get("href"))
            elif ct in ("title", "link", "pubDate", "published", "updated", "date", "description", "summary", "source"):
                g.setdefault(ct, (ch.text or "").strip())
        t = None
        for k in ("pubDate", "published", "updated", "date"):
            if g.get(k):
                try:
                    t = parsedate_to_datetime(g[k])
                except Exception:  # noqa: BLE001
                    try:
                        t = dt.datetime.fromisoformat(g[k].replace("Z", "+00:00"))
                    except Exception:  # noqa: BLE001
                        t = None
                if t:
                    break
        if not g.get("title") or not t:
            continue
        if t.tzinfo is None:
            t = t.replace(tzinfo=dt.timezone.utc)
        title = re.sub(r"\s+", " ", g["title"])
        src = g.get("source") or ""
        if "news.google" in (g.get("link") or "") and " - " in title:
            head, tail = title.rsplit(" - ", 1)
            if not src or tail.strip() == src.strip():
                title, src = head, src or tail
        desc = re.sub(r"<[^>]+>", " ", g.get("description") or g.get("summary") or "")
        desc = re.sub(r"\s+", " ", desc).strip()[:280]
        items.append({"t": int(t.timestamp()), "ti": title[:300], "u": g.get("link"), "s": src[:60], "x": desc if desc and desc[:60] not in title else ""})
    return items


def run_news(path):
    old = []
    if os.path.exists(path):
        try:
            old = json.load(open(path, encoding="utf8")).get("items", [])
        except Exception:  # noqa: BLE001
            old = []
    seen, items = set(), []

    def one(f):
        fid, label, url, cat = f
        try:
            its = parse_feed(get(url, tries=2, timeout=25, headers={"Accept": "application/rss+xml, application/xml, text/xml, */*"}))
            for x in its:
                x["c"] = cat
                x["f"] = fid
                x["s"] = x["s"] or label
            note("news")
            return its
        except Exception as e:  # noqa: BLE001
            note("news", False, f"{fid}: {e}")
            return []
    with ThreadPoolExecutor(6) as ex:
        fresh = [x for lst in ex.map(one, NEWS) for x in lst]
    cutoff = time.time() - 45 * 86400
    for x in sorted(fresh + old, key=lambda x: -x["t"]):
        k = re.sub(r"[^a-z0-9]", "", x["ti"].lower())[:90]
        if k in seen or x["t"] < cutoff or x["t"] > time.time() + 3600:
            continue
        seen.add(k)
        items.append(x)
    items = tag_news(items[:900], os.path.join(os.path.dirname(path), "summary.json"))
    save(path, {"ts": int(time.time()), "items": items, "feeds": {f[0]: f[1] for f in NEWS}})


# ---------------------------------------------------------------- profils des sociétés BRVM (SikaFinance, page « Société »)
def _sika_profile(h):
    """Description, coordonnées, dirigeants, titres, flottant, actionnaires et chiffres clés d'une page société SikaFinance."""
    import html as H_
    o = {}
    m = re.search(r"\b([A-Z]{2}[0-9A-Z]{9}[0-9])\b - [A-Z]{3,6}", h)
    if m:
        o["isin"] = m.group(1)
    m = re.search(r'id="lstActionnaires"[^>]*>(.*?)</span>', h, re.S)
    if m:
        hold = []
        for part in H_.unescape(m.group(1)).split(";"):
            if "*" in part:
                nm, pc = part.rsplit("*", 1)
                try:
                    hold.append([nm.strip(), float(pc.replace(",", ".").strip())])
                except ValueError:
                    pass
        o["holders"] = hold
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    t = H_.unescape(re.sub(r"<[^>]+>", "\n", t)).replace("\xa0", " ")
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    flat = re.sub(r"\s*\n\s*", "\n", t)
    one = re.sub(r"\s+", " ", t)
    m = re.search(r"La société :\s*(.*?)\s*(?:Téléphone|Telephone|Adresse|Dirigeants)\s*:", one)
    if m:
        o["desc"] = m.group(1).strip()[:2500]
    for k, lab in (("tel", "Téléphone"), ("fax", "Fax"), ("addr", "Adresse")):
        m = re.search(lab + r"\s*:\s*(.*?)\s*(?:Fax|Adresse|Dirigeants|Nombre de titres)\s*:", one)
        if m and m.group(1).strip():
            o[k] = m.group(1).strip()[:200]
    m = re.search(r"Dirigeants\s*:\s*(.*?)\s*Nombre de titres", flat, re.S)
    if m:
        mg = []
        for line in m.group(1).split("\n"):
            if ":" in line:
                r_, n_ = line.split(":", 1)
                if r_.strip() and n_.strip():
                    mg.append([r_.strip(), n_.strip()])
        if not mg:  # tout sur une ligne
            for r_, n_ in re.findall(r"([A-ZÉ][^:]{3,60}?)\s*:\s*([A-ZÉÈ][A-Za-zÀ-ÿ'’\-\. ]{2,60}?)(?=\s+[A-ZÉ][a-zé]|$)", re.sub(r"\s+", " ", m.group(1))):
                mg.append([r_.strip(), n_.strip()])
        o["mgmt"] = mg[:8]
    def numfr(x):
        try:
            return float(re.sub(r"[^0-9,\-]", "", x).replace(",", "."))
        except ValueError:
            return None
    m = re.search(r"Nombre de titres\s*:\s*([\d  .]+)", one)
    if m:
        o["shares"] = numfr(m.group(1))
    m = re.search(r"Flottant\s*:\s*([\d,]+)\s*%", one)
    if m:
        o["float"] = numfr(m.group(1))
    m = re.search(r"Valorisation de la société\s*:\s*([\d  .]+)\s*MFCFA", one)
    if m:
        o["val_m"] = numfr(m.group(1))
    tb = re.search(r'<table[^>]*tabSociete[^>]*>(.*?)</table>', h, re.S)
    if tb:
        cells = lambda r: [re.sub(r"\s+", " ", H_.unescape(re.sub(r"<[^>]+>", " ", c))).replace("\xa0", " ").strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
        rows = [cells(r) for r in re.findall(r"<tr[^>]*>(.*?)</tr>", tb.group(1), re.S)]
        years = [c for c in (rows[0][1:] if rows else []) if re.fullmatch(r"20\d\d", c)]
        keys = {"Chiffre d'affaires": "ca", "Croissance CA": "g_ca", "Résultat net": "rn", "Croissance RN": "g_rn", "BNPA": "bnpa", "PER": "per", "Dividende": "dps"}
        kf = {}
        for r in rows[1:]:
            k = keys.get(r[0].strip()) if r else None
            if not k:
                continue
            kf[k] = {y: numfr(v.replace(" ", "").replace("%", "")) for y, v in zip(years, r[1:]) if v and v.strip() not in ("-", "")}
            kf[k] = {y: v for y, v in kf[k].items() if v is not None}
        o["kf"] = kf
    return o


def run_prof(out):
    path = os.path.join(out, "profiles.json")
    db = json.load(open(path, encoding="utf8")) if os.path.exists(path) else {}
    try:
        fund = json.loads(get("https://raw.githubusercontent.com/harzat/brvm-data-public/main/fundamentals.json", timeout=60))
    except Exception as e:  # noqa: BLE001
        note("prof", False, f"fundamentals: {e}")
        return
    todo = [(t, v.get("source_url")) for t, v in fund.items() if t != "_meta" and v.get("source_url") and "sikafinance" in v.get("source_url", "")]
    def one(tu):
        t, url = tu
        url = url.replace("http://", "https://")
        try:
            h = get(url, tries=2, timeout=30, headers={"Accept-Language": "fr-FR,fr;q=0.9"}).decode("utf8", "replace")
        except Exception:  # noqa: BLE001
            try:
                h = curl(url, ua=UA)
                h = h.decode("utf8", "replace") if isinstance(h, bytes) else h
            except Exception as e:  # noqa: BLE001
                return t, None, str(e)
        if "lstActionnaires" not in h and "La société" not in h:
            return t, None, "page sans profil"
        return t, _sika_profile(h), url
    with ThreadPoolExecutor(4) as ex:
        for t, o, info in ex.map(one, todo):
            if o is None:
                note("prof", False, f"{t}: {info}")
                continue
            o["src"] = info
            o["d"] = TODAY.isoformat()
            db[t] = o
            note("prof")
    save(path, db)


def run_profus(out):
    """Fiches des sociétés et ETF US : description et site (Nasdaq), résumé (objectif à 1 an, dividende, encours et frais des ETF),
    principaux détenteurs institutionnels (déclarations 13F agrégées par Nasdaq), adresse et exercice (SEC)."""
    path = os.path.join(out, "profiles_us.json")
    db = json.load(open(path, encoding="utf8")) if os.path.exists(path) else {}
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cik = json.load(open(os.path.join(root, "seed", "sec_cik.json"), encoding="utf8"))
    etfs = [t for t, _, ty, _ in US if ty == "ETF"]
    def dv(d, k):
        v = (d.get(k) or {}).get("value") if isinstance(d.get(k), dict) else None
        return None if v in (None, "", "N/A") else v
    def nq(url):
        return json.loads(get(url, tries=2, timeout=25, headers=NQ_H)).get("data") or {}
    def one(t, kind):
        o = {"d": TODAY.isoformat()}
        try:
            sm = (nq(f"https://api.nasdaq.com/api/quote/{t}/summary?assetclass={kind}").get("summaryData")) or {}
            for k, key in (("OneYrTarget", "tgt"), ("AverageVolume", "avgvol"), ("AnnualizedDividend", "divA"), ("ExDividendDate", "exdiv"), ("DividendPaymentDate", "paydiv"),
                           ("Yield", "yld"), ("Exchange", "exch"), ("Sector", "sector"), ("Industry", "ind"), ("AUM", "aum"), ("ExpenseRatio", "er"), ("Beta", "beta"), ("MarketCap", "mcap")):
                v = dv(sm, k)
                if v is not None:
                    o[key] = v
        except Exception as e:  # noqa: BLE001
            o["err_sum"] = str(e)[:120]
        if kind == "stocks":
            try:
                pr = nq(f"https://api.nasdaq.com/api/company/{t}/company-profile")
                for k, key in (("CompanyDescription", "desc"), ("CompanyUrl", "url"), ("Sector", "sector"), ("Industry", "ind"), ("Region", "region")):
                    v = dv(pr, k)
                    if v is not None:
                        o[key] = v
            except Exception as e:  # noqa: BLE001
                o["err_prof"] = str(e)[:120]
            try:
                ih = nq(f"https://api.nasdaq.com/api/company/{t}/institutional-holdings?limit=15&type=TOTAL&sortColumn=marketValue")
                osum = ih.get("ownershipSummary") or {}
                rows = (((ih.get("holdingsTransactions") or {}).get("table") or {}).get("rows")) or []
                o["inst"] = {"pct": dv(osum, "SharesOutstandingPCT"), "sh_m": dv(osum, "ShareoutstandingTotal"), "n": (ih.get("holdingsTransactions") or {}).get("totalRecords"),
                             "rows": [[r.get("ownerName"), r.get("date"), r.get("sharesHeld"), r.get("sharesChange"), r.get("sharesChangePCT"), r.get("marketValue")] for r in rows[:15]],
                             "pos": [[r.get("positions"), r.get("holders"), r.get("shares")] for r in ((ih.get("activePositions") or {}).get("rows") or [])]}
            except Exception as e:  # noqa: BLE001
                o["err_inst"] = str(e)[:120]
            if t in cik:
                try:
                    sb = json.loads(get(f"https://data.sec.gov/submissions/CIK{int(cik[t]):010d}.json", tries=2, timeout=30, headers={"User-Agent": SEC_UA, "Accept-Encoding": "gzip"}))
                    a_ = (sb.get("addresses") or {}).get("business") or {}
                    o["addr"] = ", ".join(x for x in (a_.get("street1"), a_.get("street2"), a_.get("city"), a_.get("stateOrCountryDescription"), a_.get("zipCode")) if x)
                    o["phone"] = sb.get("phone")
                    o["fye"] = sb.get("fiscalYearEnd")
                    o["sic"] = sb.get("sicDescription")
                    o["inc"] = sb.get("stateOfIncorporation")
                except Exception as e:  # noqa: BLE001
                    o["err_sec"] = str(e)[:120]
        return t, o
    jobs = [(t, "stocks") for t in cik] + [(t, "etf") for t in etfs]
    t_end = time.time() + 540
    with ThreadPoolExecutor(4) as ex:
        futs = [ex.submit(one, t, k) for t, k in jobs]
        for f in futs:
            try:
                t, o = f.result(timeout=max(1, t_end - time.time()))
            except Exception as e:  # noqa: BLE001
                note("profus", False, str(e)[:100])
                continue
            if any(k in o for k in ("desc", "tgt", "aum", "inst")):
                o["src"] = "nasdaq.com" + (" · sec.gov" if "addr" in o else "")
                db[t] = o
                note("profus")
            else:
                note("profus", False, f"{t}: vide")
    save(path, db)

# ---------------------------------------------------------------- actualités reliées aux titres et typées
NEWS_ALIAS = {  # noms usuels des sociétés dans la presse (en plus du nom officiel)
    "SNTS": ["Sonatel"], "ORAC": ["Orange Côte d'Ivoire", "Orange CI"], "SGBC": ["Société Générale Côte d'Ivoire", "SGBCI", "SGCI"],
    "ETIT": ["Ecobank Transnational", "Ecobank TI", "Ecobank", "ETI"], "ECOC": ["Ecobank Côte d'Ivoire", "Ecobank CI"], "SIBC": ["Société Ivoirienne de Banque", "SIB"],
    "CBIBF": ["Coris Bank"], "PALC": ["Palm Côte d'Ivoire", "Palmci"], "SPHC": ["SAPH"], "SOGC": ["SOGB"], "NTLC": ["Nestlé Côte d'Ivoire", "Nestlé CI"],
    "SLBC": ["Solibra"], "UNLC": ["Unilever Côte d'Ivoire"], "TTLC": ["TotalEnergies Marketing Côte d'Ivoire"], "TTLS": ["TotalEnergies Marketing Sénégal"],
    "CIEC": ["Compagnie Ivoirienne d'Electricité", "CIE"], "SDCC": ["SODECI"], "ONTBF": ["Onatel"], "BOAC": ["BOA Côte d'Ivoire", "Bank of Africa Côte d'Ivoire"],
    "BOABF": ["BOA Burkina", "Bank of Africa Burkina"], "BOAB": ["BOA Bénin", "Bank of Africa Bénin"], "BOAS": ["BOA Sénégal", "Bank of Africa Sénégal"],
    "BOAM": ["BOA Mali", "Bank of Africa Mali"], "BOAN": ["BOA Niger", "Bank of Africa Niger"], "NSBC": ["NSIA Banque"], "BICC": ["BICICI", "BICI CI"],
    "SMBC": ["SMB"], "STBC": ["SITAB"], "SDSC": ["Africa Global Logistics", "AGL Côte d'Ivoire"], "ORGT": ["Oragroup"], "SNTS ": [],
    "SAFC": ["Safca"], "SICC": ["SICOR"], "SEMC": ["Eviosys", "SIEM"], "FTSC": ["Filtisac"], "CABC": ["Sicable"], "SIVC": ["Air Liquide Côte d'Ivoire"],
    "PRSC": ["Tractafric Motors"], "BNBC": ["Bernabé"], "SCRC": ["Sucrivoire"], "ABJC": ["Servair Abidjan"], "LNBB": ["Loterie Nationale du Bénin"],
    "BICB": ["BIIC Bénin", "Banque Internationale pour l'Industrie et le Commerce"], "SHEC": ["Vivo Energy Côte d'Ivoire"], "STAC": ["SETAO"], "UNXC": ["Uniwax"],
    "NVDA": ["Nvidia"], "AAPL": ["Apple"], "MSFT": ["Microsoft"], "GOOG": ["Alphabet", "Google"], "GOOGL": ["Alphabet", "Google"], "AMZN": ["Amazon"],
    "META": ["Meta Platforms", "Facebook"], "TSLA": ["Tesla"], "AVGO": ["Broadcom"], "AMD": ["AMD"], "NFLX": ["Netflix"], "COST": ["Costco"], "INTC": ["Intel"],
}
NEWS_STOP = {"meta", "arm", "apple"}  # trop ambigus seuls en minuscules : exigés avec la majuscule
EVENT_RX = [  # (type, motif) — premier qui correspond
    ("Résultats", r"\b(r[ée]sultats?|b[ée]n[ée]fices?|chiffre d.affaires|earnings|revenue|profit|quarterly|trimestriel|semestriel|annual results|[ée]tats financiers|rapport.{0,4}activit)"),
    ("Dividende", r"\b(dividendes?|dividend|coupon|d[ée]tachement)"),
    ("Assemblée", r"\b(assembl[ée]e g[ée]n[ée]rale|\bAGO\b|\bAGE\b|shareholder meeting)"),
    ("Dirigeants", r"\b(nomm[ée]|nomination|directeur g[ée]n[ée]ral|PDG|CEO|appoint|steps down|d[ée]mission|conseil d.administration)"),
    ("Analystes", r"(potentiel de hausse|r[ée]it[èe]re|abaisse son objectif|rel[èe]ve son objectif|rehausse|mise [àa] niveau|surpond[ée]r|sous-pond[ée]r|d[ée]grade|rel[èe]ve (sa|son)|recommandation|objectif de cours|price target|downgrades?|upgrades?|initiates coverage|forecasts)"),
    ("Notation", r"\b(notation|note souveraine|moody|fitch|s&p global ratings|bloomfield|\bWARA\b|credit rating)"),
    ("Émission", r"\b(emprunt obligataire|[ée]mission obligataire|eurobond|bond issue|sukuk|appel public|APE\b|obligations? du tr[ée]sor|bons du tr[ée]sor|UMOA-Titres|lev[ée]e de fonds)"),
    ("Opération", r"\b(acquisition|rachat|fusion|merger|takeover|OPA|OPR|cession|stake|participation|introduction en bourse|IPO|division de (son|l.)action|fractionnement|stock split|split)"),
    ("Régulation", r"\b(AMF-UMOA|CREPMF|SEC charges|amende|fine|sanction|enqu[êe]te|investigation|suspension|antitrust|r[ée]gulateur)"),
    ("Banques centrales", r"\b(BCEAO|Fed\b|Federal Reserve|FOMC|BCE|ECB|taux directeurs?|policy rate|rate cut|rate hike|politique mon[ée]taire)"),
    ("Macro", r"\b(inflation|PIB|GDP|croissance [ée]conomique|ch[ôo]mage|unemployment|payrolls|CPI|IPC|budget|dette publique|FMI|IMF|Banque mondiale)"),
    ("Matières premières", r"\b(p[ée]trole|oil|brent|wti|OPEP|OPEC|gaz|gas|or\b|gold|cacao|cocoa|caf[ée]|coton|cotton|anacarde|cashew|uranium|lithium|cuivre|copper)"),
    ("Crypto", r"\\b(bitcoin|ethereum|crypto|stablecoin)"),
    ("Marchés", r"\b(bourse|BRVM|wall street|nasdaq|s&p 500|dow jones|cac 40|stocks?|actions?|indice|index|rally|selloff|march[ée]s?)"),
]


def _fold(t):
    import unicodedata
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def _alias_map(summary_path):
    try:
        secs = json.load(open(summary_path, encoding="utf8")).get("secs", [])
    except Exception:  # noqa: BLE001
        return []
    out = []
    for x in secs:
        if x.get("cls") != "Equity" or x.get("typ") == "ETF":
            continue
        names = set(NEWS_ALIAS.get(x["id"], []))
        n = re.sub(r"\b(SA|S\.A\.|Inc\.?|Corp\.?|Corporation|Holdings?|Ltd|PLC|plc|Group|Class [A-C]|Common Stock|Co\.|N\.V\.|SE)\b", "", x.get("short") or x.get("n") or "")
        n = re.sub(r"[,.]", " ", n).strip()
        n = re.sub(r"\s+", " ", n)
        if len(n) >= 4:
            names.add(n)
        rx = []
        for a in names:
            if not a:
                continue
            if a.isupper() and len(a) <= 5:
                rx.append((0, re.compile(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])")))
            elif a.lower() in NEWS_STOP:
                rx.append((0, re.compile(r"\b" + re.escape(a) + r"\b")))
            else:  # sans accents ni casse : « SENEGAL » = « Sénégal »
                rx.append((1, re.compile(r"\b" + re.escape(_fold(a)) + r"\b")))
        if len(x["id"]) >= 3 and x.get("mkt") == "BRVM":
            rx.append((0, re.compile(r"(?<![A-Za-z])" + re.escape(x["id"]) + r"(?![A-Za-z])")))
        out.append((x["id"], rx))
    return out


def tag_news(items, summary_path):
    """Relie chaque dépêche aux titres cités (tk) et lui donne un type d'événement (ev). Correspondance sur le titre et le résumé."""
    amap = _alias_map(summary_path)
    erx = [(k, re.compile(r, re.I)) for k, r in EVENT_RX]
    for x in items:
        x["ti"] = HTML.unescape(HTML.unescape(x.get("ti") or "")).replace("\xa0", " ").strip()
        if x.get("x"):
            x["x"] = re.sub(r"\s+", " ", HTML.unescape(HTML.unescape(x["x"])).replace("\xa0", " ")).strip()
        if x.get("s"):
            x["s"] = HTML.unescape(x["s"])
        txt = x["ti"] + " " + (x.get("x") or "")
        ftx = _fold(txt)
        tk = [sid for sid, rx in amap if any(r.search(ftx if f else txt) for f, r in rx)]
        if tk:
            x["tk"] = tk[:6]
        else:
            x.pop("tk", None)
        ev = next((k for k, r in erx if r.search(x["ti"])), None)
        if ev:
            x["ev"] = ev
    return items


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="dossier brut (branche quant-raw), lu et réécrit sur place")
    ap.add_argument("--only", default="nasdaq,fred,cboe,cnn,crypto,wb,sec,analyst,boc,probe")
    ap.add_argument("--news", default=None, help="fichier news.json à mettre à jour (mode séance)")
    ap.add_argument("--site", default=None, help="dossier data/ du site (veille : reports.json, news.json)")
    ap.add_argument("--sec-max-age-days", type=float, default=6)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    only = set(a.only.split(",")) if a.only else set()
    t0 = time.time()
    steps = [("nasdaq", lambda: run_nasdaq(a.out, a.out)), ("fred", lambda: run_fred(a.out)), ("cboe", lambda: run_cboe(a.out)),
             ("cnn", lambda: run_cnn(a.out)), ("crypto", lambda: run_crypto(a.out, a.out)), ("wb", lambda: run_wb(a.out)),
             ("sec", lambda: run_sec(a.out, a.out, a.sec_max_age_days)), ("analyst", lambda: run_analyst(a.out)),
             ("probe", lambda: run_probe(a.out)), ("boc", lambda: run_boc(a.out)), ("sikah", lambda: run_sikah(a.out)), ("pdffin", lambda: run_pdffin(a.out)), ("watch", lambda: run_watch(a.out, a.site)), ("prof", lambda: run_prof(a.out)), ("profus", lambda: run_profus(a.out))]
    if a.news:
        steps.insert(0, ("news", lambda: run_news(a.news)))
        only.add("news")
    rp = os.path.join(a.out, "report_" + "-".join(sorted(only)) + ".json")
    for name, fn in steps:
        if name not in only:
            continue
        t = time.time()
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            import traceback
            note(name, False, f"étape interrompue : {e} {traceback.format_exc()[-300:]}")
        REPORT.setdefault("_steps", {})[name] = round(time.time() - t)
        REPORT["_"] = {"ts": int(time.time()), "secs": round(time.time() - t0)}
        save(rp, REPORT)  # écrit après chaque étape : visible même si le passage est interrompu
        log(f"{name}: {time.time() - t:.0f} s", json.dumps({k: (v['ok'], v['err']) for k, v in REPORT.items() if isinstance(v, dict) and 'ok' in v}))
    log(f"terminé en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
