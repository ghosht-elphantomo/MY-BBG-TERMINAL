#!/usr/bin/env python3
"""Build the terminal's static data set (data/*.json) from public sources. Standard library only.

Sources
  US / Taiwan equities & ETFs : github.com/yennanliu/finance_data (Yahoo Finance daily, refreshed nightly)
  BRVM (48 stocks, 18 indices, fundamentals, dividends, official notices) : github.com/harzat/brvm-data-public
  Macro (gold, S&P 500, CPI, US 10Y, Brent, WTI, natural gas, VIX, FX) : github.com/datasets/*
  Same-day BRVM session (optional --session) : brvm.json written by scrape.py from brvm.org

Usage: build_terminal.py --brvm-src DIR --out DIR [--session brvm.json] [--cache DIR]
"""
import argparse, collections, csv, datetime as dt, io, json, math, os, re, sys, time, urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
YN = "https://raw.githubusercontent.com/yennanliu/finance_data/main/data/prices/{}.csv"
DS = "https://raw.githubusercontent.com/datasets/{}"
XOF_PER_EUR = 655.957

US = [  # ticker, name, type, group
    ("QQQ", "Invesco QQQ Trust", "ETF", "Indice"), ("VTI", "Vanguard Total Stock Market", "ETF", "Indice"),
    ("SOXX", "iShares Semiconductor", "ETF", "Semi-conducteurs"), ("SOXQ", "Invesco PHLX Semiconductor", "ETF", "Semi-conducteurs"),
    ("ROBO", "ROBO Global Robotics & Automation", "ETF", "Thématique"),
    ("NVDA", "NVIDIA", "Equity", "Semi-conducteurs"), ("AVGO", "Broadcom", "Equity", "Semi-conducteurs"),
    ("AMD", "Advanced Micro Devices", "Equity", "Semi-conducteurs"), ("TSM", "Taiwan Semiconductor ADR", "Equity", "Semi-conducteurs"),
    ("MU", "Micron Technology", "Equity", "Semi-conducteurs"), ("MRVL", "Marvell Technology", "Equity", "Semi-conducteurs"),
    ("INTC", "Intel", "Equity", "Semi-conducteurs"), ("WDC", "Western Digital", "Equity", "Matériel"), ("SNDK", "Sandisk", "Equity", "Matériel"),
    ("MSFT", "Microsoft", "Equity", "Logiciel"), ("ORCL", "Oracle", "Equity", "Logiciel"), ("PLTR", "Palantir Technologies", "Equity", "Logiciel"),
    ("GOOG", "Alphabet (C)", "Equity", "Communication"), ("META", "Meta Platforms", "Equity", "Communication"),
    ("AMZN", "Amazon.com", "Equity", "Conso. discrétionnaire"), ("TSLA", "Tesla", "Equity", "Automobile"),
    ("UBER", "Uber Technologies", "Equity", "Transport"), ("GRAB", "Grab Holdings", "Equity", "Transport"),
    ("SOFI", "SoFi Technologies", "Equity", "Finance"), ("NU", "Nu Holdings", "Equity", "Finance"),
    ("VST", "Vistra", "Equity", "Énergie"), ("IONQ", "IonQ", "Equity", "Quantique"), ("RKLB", "Rocket Lab", "Equity", "Spatial & défense"),
    ("PL", "Planet Labs", "Equity", "Spatial & défense"), ("KTOS", "Kratos Defense", "Equity", "Spatial & défense"),
    ("AVAV", "AeroVironment", "Equity", "Spatial & défense"), ("ONDS", "Ondas Holdings", "Equity", "Spatial & défense"),
    ("NBIS", "Nebius Group", "Equity", "Logiciel"),
]
TW = [("0050", "0050", "Yuanta Taiwan Top 50", "ETF", "Indice"), ("2330.tw", "2330", "TSMC (Taïwan)", "Equity", "Semi-conducteurs")]
CTY = {"B": "BJ", "BF": "BF", "C": "CI", "M": "ML", "N": "NE", "S": "SN", "T": "TG"}
CTY_NAME = {"CI": "Côte d'Ivoire", "SN": "Sénégal", "BF": "Burkina Faso", "BJ": "Bénin", "ML": "Mali", "NE": "Niger", "TG": "Togo"}


def log(*a):
    print("[build]", *a, flush=True)


def fetch(url, cache=None, tries=3):
    path = os.path.join(cache, re.sub(r"[^A-Za-z0-9._-]", "_", url)[-120:]) if cache else None
    if path and os.path.exists(path) and time.time() - os.path.getmtime(path) < 6 * 3600:
        return open(path, "rb").read()
    err = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                b = r.read()
            if path:
                os.makedirs(cache, exist_ok=True)
                open(path, "wb").write(b)
            return b
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 + 3 * k)
    raise err


def di(s):  # 'YYYY-MM-DD' or 'DD/MM/YYYY' or 'YYYY-MM' -> int YYYYMMDD
    s = s.strip().lstrip("﻿")
    if "/" in s:
        d, m, y = s.split("/")
        return int(y) * 10000 + int(m) * 100 + int(d)
    p = s.split("-")
    return int(p[0]) * 10000 + int(p[1]) * 100 + (int(p[2]) if len(p) > 2 else 1)


def fnum(x):
    x = (x or "").replace("\xa0", "").replace(" ", "").replace(" ", "").replace("%", "").replace(",", ".").strip()
    if x in ("", "-", "nan", "null"):
        return None
    try:
        return float(x)
    except ValueError:
        return None


def rnd(v, nd):
    return None if v is None or (isinstance(v, float) and not math.isfinite(v)) else round(v, nd)


# ------------------------------------------------------------------ loaders
def load_yn(sym, cache):
    rows = []
    for r in csv.DictReader(io.StringIO(fetch(YN.format(sym), cache).decode("utf8"))):
        c = fnum(r.get("close"))
        if not c:
            continue
        rows.append((di(r["date"]), fnum(r["open"]) or c, fnum(r["high"]) or c, fnum(r["low"]) or c, c, int(fnum(r["volume"]) or 0), fnum(r.get("div")) or 0))
    return rows


def load_brvm_csv(path):
    """harzat CSVs: real column order is Date;Close;Open;High;Low;Shares;Value;Var (header says otherwise)."""
    rows = {}
    with open(path, encoding="utf-8-sig") as f:
        next(f, None)
        for line in f:
            p = line.rstrip("\n").split(";")
            if len(p) < 5:
                continue
            try:
                d = di(p[0])
            except Exception:  # noqa: BLE001
                continue
            c, o, h, l = fnum(p[1]), fnum(p[2]), fnum(p[3]), fnum(p[4])
            if not c or c <= 0:
                continue
            vals = [x for x in (c, o, h, l) if x]
            o = o or c
            rows[d] = (d, o, max(vals), min(vals), c, int(fnum(p[5]) or 0) if len(p) > 5 else 0, int(fnum(p[6]) or 0) if len(p) > 6 else 0)
    return [rows[k] for k in sorted(rows)]


def series_from_csv(text, date_col, val_col, filt=None):
    out = {}
    for r in csv.DictReader(io.StringIO(text)):
        if filt and not filt(r):
            continue
        v = fnum(r.get(val_col))
        if v is None or v <= 0:
            continue
        out[di(r[date_col])] = v
    return sorted(out.items())


# ------------------------------------------------------------------ metrics
def stats_block(d, c, freq="D", h=None, l=None, v=None, val=None, ann=None):
    n = len(c)
    per_year = ann or (252 if freq == "D" else 12)
    last, prev = c[-1], c[-2] if n > 1 else c[-1]

    def back(k):
        return c[-1 - k] if n > k else None

    def ret(k):
        b = back(k)
        return (last / b - 1) if b else None
    wk, mo, q, yr, y3 = ((7, 30, 91, 365, 1095) if ann == 365 else (5, 21, 63, 252, 756)) if freq == "D" else (None, 1, 3, 12, 36)
    h6 = (182 if ann == 365 else 126) if freq == "D" else 6
    ly = d[-1] // 10000 - 1
    base = None
    for i in range(n - 1, -1, -1):
        if d[i] // 10000 <= ly:
            base = c[i]
            break
    lr = [math.log(c[i] / c[i - 1]) for i in range(max(1, n - per_year), n) if c[i - 1] > 0]
    mu = sum(lr) / len(lr) if lr else 0
    sd = math.sqrt(sum((x - mu) ** 2 for x in lr) / max(1, len(lr) - 1)) if len(lr) > 2 else 0
    win = c[-per_year:]
    hi = max((h or c)[-per_year:])
    lo = min((l or c)[-per_year:])
    sma = lambda k: sum(c[-k:]) / k if n >= k else None  # noqa: E731
    gains = losses = 0.0
    rsi = None
    if n > 15:
        for i in range(n - 14, n):
            ch = c[i] - c[i - 1]
            gains += max(ch, 0)
            losses += max(-ch, 0)
        rsi = 100 if losses == 0 else 100 - 100 / (1 + gains / losses)
    peak = max(c)
    return {"last": rnd(last, 4), "prev": rnd(prev, 4), "pct": rnd(last / prev - 1 if prev else 0, 6), "dt": d[-1], "first": d[0], "nobs": n,
            "r1w": rnd(ret(wk), 5) if wk else None, "r1m": rnd(ret(mo), 5), "r3m": rnd(ret(q), 5), "r6m": rnd(ret(h6), 5), "r1y": rnd(ret(yr), 5), "r3y": rnd(ret(y3), 5),
            "ytd": rnd(last / base - 1, 5) if base else None, "vol": rnd(sd * math.sqrt(per_year), 5), "hi52": rnd(hi, 4), "lo52": rnd(lo, 4),
            "sma50": rnd(sma(50), 4) if freq == "D" else None, "sma200": rnd(sma(200), 4) if freq == "D" else None, "rsi": rnd(rsi, 2),
            "ath": rnd(peak, 4), "dd": rnd(last / peak - 1, 5), "spark": [rnd(x, 4) for x in c[-60:]],
            "liq": rnd(sum(val[-63:]) / len(val[-63:]), 0) if val and any(val[-63:]) else (rnd(sum(a * b for a, b in zip(v[-63:], c[-63:])) / len(v[-63:]), 0) if v and any(v[-63:]) else None),
            "vday": (val[-1] if val else None) or (rnd(v[-1] * c[-1], 0) if v else None), "shd": v[-1] if v else None}


def weekly(d, c):
    """Friday (week-ending) closes keyed by ISO week end date."""
    out = {}
    for di_, ci in zip(d, c):
        t = dt.date(di_ // 10000, di_ // 100 % 100, di_ % 100)
        fri = t + dt.timedelta(days=(4 - t.weekday()) % 7)
        out[fri.year * 10000 + fri.month * 100 + fri.day] = ci
    return out


def beta_corr(x, y):
    n = len(x)
    if n < 20:
        return None, None
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None, None
    return sxy / syy, sxy / math.sqrt(sxx * syy)  # beta of x on y, correlation


# ------------------------------------------------------------------ main
def _nm(x):
    import unicodedata
    x = unicodedata.normalize("NFKD", x or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", x.replace("&", " ")).strip()


AV_GENERIC = re.compile(r"^(avis|brvm|rappel|communique|annonce|bourse regionale)( |$)")


def brvm_avis(items, ev_src, acts, out):
    """Avis lus directement sur brvm.org (secours de la base tierce) : rattachés à un titre par le nom de société tel que brvm.org l'écrit
    (noms appris de la base d'avis, du registre des titres et des pages des sociétés). Renvoie (avis, nombre de sociétés non rattachées)."""
    m = collections.defaultdict(collections.Counter)
    for x in ev_src:
        t, ti = x.get("ticker"), x.get("title") or ""
        if t:
            for k in (x.get("issuer"), x.get("company"), ti.split(" : ")[0] if " : " in ti else None):
                if k and not AV_GENERIC.match(_nm(k)):
                    m[_nm(k)][t] += 1
    for a_ in acts:
        for k in (a_.get("nom"), a_.get("nom_officiel"), a_.get("ticker")):
            if k:
                m[_nm(k)][a_["ticker"]] += 3
    rp = os.path.join(out, "reports.json")
    if os.path.exists(rp):
        for x in (json.load(open(rp, encoding="utf8")).get("issuers") or {}).values():
            if x.get("t") and x.get("n"):
                m[_nm(x["n"])][x["t"]] += 1
    tick = {a_["ticker"] for a_ in acts if a_.get("actif", True) is not False}  # titres radiés exclus

    def find(*names):
        for n in names:
            k = _nm(n)
            if k and k in m and not AV_GENERIC.match(k):
                t_ = m[k].most_common(1)[0][0]
                return t_ if t_ in tick else None  # actions cotées seulement (pas d'obligations, d'États ni de sociétés radiées)
        for n in names:  # ticker cité entre parenthèses, ex. « (BBGC) »
            x = re.search(r"\(([A-Z]{4,5})\)", n or "")
            if x and x.group(1) in tick:
                return x.group(1)
        return None
    res, nomap = [], set()
    for u, r in items.items():
        t = find(r.get("soc"), (r.get("ti") or "").split(" : ")[0] if " : " in (r.get("ti") or "") else None)
        if r.get("soc") and not t:
            nomap.add(r["soc"])
        res.append({**r, "u": u, "t": t})
    return res, nomap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brvm-src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--session", default=None, help="brvm.json from scrape.py (same-day official BRVM values)")
    ap.add_argument("--cache", default=None)
    ap.add_argument("--extra", default=None, help="dossier brut écrit par fetch_extra.py (branche quant-raw)")
    ap.add_argument("--fcf", default=None, help="history/fcf.json : flux de trésorerie BRVM lus dans les états financiers")
    ap.add_argument("--quotes", default=None, help="quotes.json du relevé (cours du jour appliqués à toutes les séries)")
    ap.add_argument("--live", action="store_true", help="passage de séance : séries existantes non réécrites, tous les calculs refaits")
    ap.add_argument("--boc", default=None, help="dossier boc_px (branche boc) : tableaux des actions lus dans les bulletins officiels de la cote")
    ap.add_argument("--comptes", default=None, help="comptes.json (branche comptes) : états financiers publiés à la BRVM, lus et vérifiés")
    a = ap.parse_args()
    QUOTES = {}
    if a.quotes and os.path.exists(a.quotes):
        try:
            QUOTES = (json.load(open(a.quotes, encoding="utf8")) or {}).get("q") or {}
        except Exception:  # noqa: BLE001
            QUOTES = {}
    out, sdir = a.out, os.path.join(a.out, "s")
    os.makedirs(sdir, exist_ok=True)
    secs, files = [], {}

    def add(meta, d, c, o=None, h=None, l=None, v=None, val=None, div=None, freq="D", nd=2, ann=None, replace=False):
        sid = meta["id"]
        if replace and sid in files:
            secs[:] = [x for x in secs if x["id"] != sid]
        qt = QUOTES.get(sid) if freq == "D" and meta.get("mkt") != "BRVM" else None
        if qt and qt.get("last") and qt.get("d") and d:
            # cours du jour (Nasdaq, Coinbase) : nouvelle séance ajoutée ou dernière séance mise à jour
            k = di(qt["d"])
            d, c = list(d), list(c)
            o, h, l = (list(o), list(h), list(l)) if o else (None, None, None)
            v = list(v) if v else v
            px_ = qt["last"]
            if k > d[-1]:
                d.append(k)
                c.append(px_)
                if o:
                    o.append(qt.get("o") or c[-2]); h.append(max(qt.get("h") or px_, px_)); l.append(min(qt.get("l") or px_, px_))
                if v is not None:
                    v.append(int(qt.get("vol") or 0))
                if div is not None:
                    div = list(div) + [0]
                if val is not None:
                    val = list(val) + [0]
            elif k == d[-1]:
                c[-1] = px_
                if o:
                    h[-1], l[-1] = max(h[-1], px_), min(l[-1], px_)
                if v is not None and qt.get("vol"):
                    v[-1] = int(qt["vol"])
        body = {"id": sid, "f": freq, "d": d, "c": [rnd(x, nd) for x in c]}
        if o:
            body.update(o=[rnd(x, nd) for x in o], h=[rnd(x, nd) for x in h], l=[rnd(x, nd) for x in l])
        if v and any(v):
            body["v"] = v
        if val and any(val):
            body["val"] = val
        if div and any(div):
            body["div"] = [rnd(x, 4) for x in div]
        files[sid] = body
        st = stats_block(d, c, freq, h, l, v, val, ann)
        secs.append({**meta, "f": freq, **st})

    # US & Taiwan -----------------------------------------------------------
    for sym, name, typ, grp in US:
        try:
            r = load_yn(sym.lower(), a.cache)
        except Exception as e:  # noqa: BLE001
            log("skip", sym, e)
            continue
        add({"id": sym, "tk": f"{sym} US", "n": name, "cls": "Equity", "typ": typ, "mkt": "US", "grp": grp, "ccy": "USD", "bench": "QQQ"},
            [x[0] for x in r], [x[4] for x in r], [x[1] for x in r], [x[2] for x in r], [x[3] for x in r], [x[5] for x in r], div=[x[6] for x in r])
    for f, sym, name, typ, grp in TW:
        try:
            r = load_yn(f, a.cache)
        except Exception as e:  # noqa: BLE001
            log("skip", sym, e)
            continue
        add({"id": sym, "tk": f"{sym} TT", "n": name, "cls": "Equity", "typ": typ, "mkt": "TW", "grp": grp, "ccy": "TWD", "bench": "0050"},
            [x[0] for x in r], [x[4] for x in r], [x[1] for x in r], [x[2] for x in r], [x[3] for x in r], [x[5] for x in r], div=[x[6] for x in r])

    # BRVM ------------------------------------------------------------------
    src = a.brvm_src
    acts = json.load(open(os.path.join(src, "actions.json"), encoding="utf8"))["actions"]
    fund = json.load(open(os.path.join(src, "fundamentals.json"), encoding="utf8"))
    # états financiers publiés à la BRVM (branche comptes), lus et vérifiés par les identités comptables : prioritaires sur la base
    # tierce pour les exercices qu'ils couvrent, quand leur périmètre est le même (comptes sociaux ou consolidés)
    cpt_chk = {"t": 0, "y": 0, "set": 0, "fix": 0, "fill": 0, "detail_only": [], "ex": []}
    # exercices plus anciens : pages SikaFinance archivées (web.archive.org) — chiffres publiés (CA, résultat net, BNPA, dividende)
    sh_path = os.path.join(a.extra, "sika_hist.json") if a.extra else None
    hist = {}
    if sh_path and os.path.exists(sh_path):
        sh_ = json.load(open(sh_path, encoding="utf8"))
        for src_ in (sh_.get("old") or {}, sh_.get("t") or {}):  # (lecture précédente conservée tant que la nouvelle n'est pas faite)
            for t, yrs in src_.items():
                hist.setdefault(t, {}).update(yrs)
    if a.comptes and os.path.exists(a.comptes):
        try:
            import comptes as CPT
            mir = {t: {k_: dict(s_) for k_, s_ in (v.get("series") or {}).items() if isinstance(s_, dict)}
                   for t, v in fund.items() if t != "_meta" and isinstance(v, dict)}  # (copie : la base elle-même n'est pas modifiée ici)
            # la base de recoupement des comptes lus comprend aussi les archives SikaFinance (chiffre d'affaires, résultat net)
            # pour les exercices que la base tierce ne couvre pas : un montant isolé qu'elles contredisent n'est pas retenu
            for t, yrs in hist.items():
                ser_ = mir.setdefault(t, {})
                for y, rec in yrs.items():
                    for k, sk in (("ca", "ca"), ("rn", "resultat_net")):
                        if rec.get(k) is not None and (ser_.get(sk) or {}).get(str(y)) is None:
                            ser_.setdefault(sk, {})[str(y)] = rec[k]
            CONS = CPT.consolidate(json.load(open(a.comptes, encoding="utf8")), mir)
            bank_t = {x.get("symbole") or x.get("ticker"): bool(x.get("banque")) for x in acts}
            MAPC = (("resultat_net", "resultat_net"), ("total_bilan", "total_actif"), ("capitaux_propres", "capitaux_propres"),
                    ("ebit", "resultat_exploitation"), ("ebitda", "ebe"), ("depots_clientele", "b_dettes_clientele"),
                    ("credits_clientele", "b_creances_clientele"))
            DERIVED = ("roe", "roa", "marge_nette", "marge_exploitation", "croissance_ca", "croissance_resultat_net")
            for t, cc in CONS.items():
                f = fund.get(t)
                if not f or not isinstance(f, dict):
                    continue
                f["cpt"] = cc
                cpt_chk["t"] += 1
                # même périmètre et mêmes normes que la base : la plupart des montants communs concordent, et le résultat net aussi
                # (des écarts isolés sont des erreurs ou des chiffres provisoires de la base, corrigés par les comptes publiés) ;
                # sinon l'autre référentiel publié par la société, s'il est celui de la base, sert aux chiffres clés
                def same_basis(g_):
                    return g_["ncmp"] < 3 or (g_["agree"] >= .5 and (g_.get("n_rn", 0) < 2 or (g_.get("agree_rn") or 0) >= .5))
                src_g = cc if same_basis(cc) else (cc["alt"] if cc.get("alt") and cc["alt"].get("ncmp", 0) >= 3 and same_basis(cc["alt"]) else None)
                if src_g is None:
                    cpt_chk["detail_only"].append(f'{t} ({cc["per"]}, {cc["agree"]:.0%} de {cc["ncmp"]})')
                    continue
                if src_g is not cc:
                    cpt_chk.setdefault("alt_used", []).append(f'{t} ({src_g["per"]} {src_g["std"]})')
                ser = f.setdefault("series", {})
                bank = bank_t.get(t) or any("b_pnb" in r["v"] for r in src_g["y"].values())
                for y, r in src_g["y"].items():
                    v, ys = r["v"], str(y)
                    cpt_chk["y"] += 1
                    pairs = [("ca", "b_pnb" if bank else "chiffre_affaires")] + list(MAPC)
                    if v.get("resultat_net") is None and v.get("resultat_bilan") is not None:
                        v = dict(v, resultat_net=v["resultat_bilan"])  # (résultat de l'exercice au bilan : même montant publié)
                    # coût du risque (charge comptée positivement) : signe lu d'après le compte de résultat
                    # (résultat brut d'exploitation ± coût du risque = résultat d'exploitation)
                    if bank and v.get("b_cout_risque") is not None and v.get("b_rbe") is not None and v.get("resultat_exploitation") is not None:
                        cr_, rbe_, re_ = v["b_cout_risque"], v["b_rbe"], v["resultat_exploitation"]
                        if abs(rbe_ + cr_ - re_) <= max(1.0, abs(re_) * .002):
                            v = dict(v, _cdr=-cr_)
                        elif abs(rbe_ - cr_ - re_) <= max(1.0, abs(re_) * .002):
                            v = dict(v, _cdr=cr_)
                        if "_cdr" in v:
                            pairs.append(("cout_du_risque", "_cdr"))
                    changed = False
                    weak_ = set(r.get("w") or ())
                    for sk, ck in pairs:
                        if v.get(ck) is None:
                            continue
                        o = ser.setdefault(sk, {})
                        old = o.get(ys)
                        new = round(v[ck], 1)
                        if old is not None and abs(old - new) <= 0.6:
                            continue  # même montant (arrondi au million près)
                        if old is not None and ck in weak_:
                            continue  # montant d'un seul document, sans identité vérifiée : ne remplace pas un montant existant
                        if old is None:
                            cpt_chk["fill"] += 1
                        elif abs(old - new) > max(1.0, abs(old) * .005):
                            cpt_chk["fix"] += 1
                            changed = True
                            if len(cpt_chk["ex"]) < 25:
                                cpt_chk["ex"].append(f"{t} {y} {sk} {old:g} -> {new:g}")
                        o[ys] = new
                        cpt_chk["set"] += 1
                    if changed:  # ratios de la base tierce calculés sur les montants corrigés : retirés (recalculés plus loin)
                        for dk in DERIVED:
                            (ser.get(dk) or {}).pop(ys, None)
            log("comptes publiés BRVM :", {k: v for k, v in cpt_chk.items() if k not in ("ex", "detail_only", "alt_used")},
                ("; périmètre différent de la base, détail seulement : " + ", ".join(cpt_chk["detail_only"])) if cpt_chk["detail_only"] else "",
                ("; chiffres clés pris dans l'autre référentiel publié : " + ", ".join(cpt_chk["alt_used"])) if cpt_chk.get("alt_used") else "")
            if cpt_chk["ex"]:
                log("comptes corrigés d'après les états publiés :", "; ".join(cpt_chk["ex"]))
        except Exception as e:  # noqa: BLE001
            import traceback
            log("comptes publiés BRVM illisibles :", e, traceback.format_exc()[-400:])
    # exercices plus anciens : archives SikaFinance, ajoutées seulement là où la source actuelle n'a rien
    if hist:
        kmap = {"ca": "ca", "rn": "resultat_net", "bnpa": "bnpa", "div": "dividende"}  # (chiffres publiés seulement, pas de ratio)
        for t, yrs in hist.items():
            f = fund.get(t)
            if not f:
                continue
            ser = f.setdefault("series", {})
            src_y = f.setdefault("src_years", {})
            for y, rec in yrs.items():
                added = False
                for k, sk in kmap.items():
                    if rec.get(k) is None:
                        continue
                    o = ser.setdefault(sk, {})
                    if o.get(y) is None:
                        o[y] = rec[k]
                        added = True
                if added:
                    src_y[y] = "archive SikaFinance " + rec.get("src", "")
    # flux de trésorerie : ceux des états financiers publiés à la BRVM et vérifiés (flux des activités opérationnelles et
    # acquisitions d'immobilisations du même document) ; l'ancienne lecture sans contrôle (pdf_fin.json) n'est plus utilisée
    pdf_cf = {}
    for t, f in fund.items():
        cc = f.get("cpt") if isinstance(f, dict) else None
        for y, r in ((cc or {}).get("y") or {}).items():
            v = r["v"]
            if v.get("flux_operationnels") is not None and (v.get("capex_corp") is not None or v.get("capex_incorp") is not None):
                cap = abs(v.get("capex_corp") or 0) + abs(v.get("capex_incorp") or 0)
                pdf_cf.setdefault(t, {})[str(y)] = {"cfo": v["flux_operationnels"], "capex": round(cap, 3), "fcf": round(v["flux_operationnels"] - cap, 3)}
    divs = json.load(open(os.path.join(src, "dividendes.json"), encoding="utf8"))["all"]
    # avis lus directement sur brvm.org (relevés toutes les 15 min) : secours si la base d'avis tierce s'arrête
    AV = []
    try:
        avp = os.path.join(a.out, "avis_brvm.json")
        if os.path.exists(avp):
            AV, nomap = brvm_avis(json.load(open(avp, encoding="utf8")).get("items") or {}, json.load(open(os.path.join(src, "events.json"), encoding="utf8"))["events"], acts, a.out)
            log("avis brvm.org :", len(AV), "lus" + (", sociétés non rattachées : " + ", ".join(sorted(nomap)) if nomap else ""))
    except Exception as e:  # noqa: BLE001
        log("avis brvm.org illisibles :", e)
    av_chk = {"div": 0, "split": 0, "ev": 0, "ag": 0, "div_fix": 0}
    # montant du dividende lu dans l'avis officiel le plus récent de la BRVM pour chaque titre et exercice (un avis « modification du
    # montant du dividende » remplace le précédent) ; le calendrier de la BRVM n'est pas toujours mis à jour après un rectificatif
    AVD = {}
    for r in AV:
        o = r.get("ocr") or {}
        ex_ = o.get("ex") or r.get("ex")
        if r.get("t") and o.get("net") and o["net"] > 0 and ex_ and (r.get("k") == "div" or r.get("c") == "Modification du dividende"):
            k_ = (r["t"], int(ex_))
            if k_ not in AVD or (r.get("d") or "") > (AVD[k_].get("d") or ""):
                AVD[k_] = {**o, "d": r.get("d"), "u": r["u"], "mod": r.get("c") == "Modification du dividende"}
    if AVD:
        fixes = []
        for x in divs:
            a_ = AVD.get((x.get("ticker"), x.get("exercice")))
            if not a_ or not x.get("dividende"):
                continue
            if not a_["mod"] and re.search(r"rectif|modif", str(x.get("dividende_remarque") or ""), re.I):
                continue  # la base a déjà appliqué un avis rectificatif plus récent que celui qui a été lu
            q_ = a_["net"] / x["dividende"]
            if abs(q_ - 1) > .005 and .2 < q_ < 5:  # lecture plausible et différente : l'avis officiel l'emporte
                fixes.append(f'{x["ticker"]} {x["exercice"]} : {x["dividende"]} -> {a_["net"]}{" (rectificatif)" if a_["mod"] else ""}')
                x["dividende"], x["avis"] = a_["net"], 1
                av_chk["div_fix"] += 1
            for kk, kd in (("date_detachement", "det"), ("date_paiement", "pay")):
                if not x.get(kk) and a_.get(kd):
                    x[kk] = a_[kd]
        if fixes:
            log("dividendes d'après les avis officiels :", "; ".join(fixes))
    if AV:  # dividendes annoncés sur brvm.org (montant net, détachement, paiement) absents de la base : ajoutés
      try:
        have = collections.defaultdict(list)
        for x in divs:
            if x.get("ticker"):
                have[x["ticker"]].append(x)

        def near(d1, d2, n=10):
            try:
                return abs((dt.date.fromisoformat(d1[:10]) - dt.date.fromisoformat(d2[:10])).days) <= n
            except (TypeError, ValueError):
                return False
        for r in AV:
            if r.get("k") != "div" or not r.get("t") or not r.get("dps") or not (r.get("det") or r.get("pay")):
                continue
            if any((r.get("ex") and x.get("exercice") == r["ex"] and abs((x.get("dividende") or 0) - r["dps"]) < 0.5)
                   or near(x.get("date_detachement"), r.get("det")) or near(x.get("date_paiement"), r.get("pay")) for x in have[r["t"]]):
                continue
            # montant de la colonne du calendrier brvm.org : net pour certaines sociétés, brut pour d'autres (l'avis PDF précise le net) -> signalé
            a_ = AVD.get((r["t"], r.get("ex")))
            nx = {"ticker": r["t"], "dividende": a_["net"] if a_ else r["dps"], "exercice": r.get("ex"), "date_annonce": r.get("d"), "date_detachement": r.get("det"),
                  "date_paiement": r.get("pay"), "source": "BRVM", **({} if a_ else {"cal": 1})}
            divs.append(nx)
            have[r["t"]].append(nx)
            av_chk["div"] += 1
      except Exception as e:  # noqa: BLE001
        log("dividendes brvm.org ignorés :", e)
    # bulletins officiels de la cote (BRVM) : contrôle et secours des cours et des dividendes
    BOC = {}
    if a.boc and os.path.isdir(a.boc):
        cols = ("prev", "o", "c", "var", "vol", "val", "ref", "ytd", "div", "div_d", "yld", "per")
        for fn in sorted(os.listdir(a.boc)):
            if not re.match(r"^\d{4}\.json$", fn):
                continue
            for k, rows_ in json.load(open(os.path.join(a.boc, fn), encoding="utf8")).items():
                for sym, v in rows_.items():
                    BOC.setdefault(sym, {})[int(k)] = dict(zip(cols, v))
        log("bulletins officiels :", len(BOC), "titres,", sum(len(v) for v in BOC.values()), "lignes")
    boc_chk = {"n": 0, "diff": 0, "added": 0, "div_added": 0, "by": {}}
    if BOC:  # dividendes payés lus dans les bulletins, ajoutés seulement quand la base n'a aucun versement à ±120 jours
        # (la date du bulletin peut suivre de plusieurs semaines celle de l'avis : un même dividende ne doit pas compter deux fois ;
        # un dividende payé en plusieurs fractions espacées de plus de 4 mois reste compté une fois par fraction)
        have_pay = collections.defaultdict(list)
        have_amt = collections.defaultdict(list)
        for x in divs:
            for kk in ("date_paiement", "date_detachement"):
                if x.get(kk) and x.get("ticker"):
                    try:
                        have_pay[x["ticker"]].append(dt.date.fromisoformat(x[kk][:10]))
                        if x.get("dividende"):
                            have_amt[x["ticker"]].append((dt.date.fromisoformat(x[kk][:10]), float(x["dividende"])))
                    except ValueError:
                        pass
        for sym, days in BOC.items():
            seen = set()
            for k in sorted(days):
                r = days[k]
                if not r.get("div") or not r.get("div_d") or (r["div_d"], r["div"]) in seen:
                    continue
                seen.add((r["div_d"], r["div"]))
                try:
                    pd_ = dt.date.fromisoformat(r["div_d"])
                except ValueError:
                    continue
                if pd_.year < 2008 or any(abs((pd_ - h).days) <= 120 for h in have_pay[sym]) \
                        or any(abs((pd_ - h).days) <= 200 and abs(a_ / r["div"] - 1) < .01 for h, a_ in have_amt[sym]):
                    boc_chk["div_dup"] = boc_chk.get("div_dup", 0) + 1
                    continue
                divs.append({"ticker": sym, "dividende": r["div"], "date_paiement": r["div_d"], "exercice": pd_.year - 1, "source": "BOC"})
                have_pay[sym].append(pd_)
                boc_chk["div_added"] += 1
    # Fractionnements (avis BRVM) : cours, dividendes et données par action ramenés sur la base des actions actuelles.
    # Un fractionnement n'est appliqué qu'une fois effectif (date d'effet atteinte par les cours) et seulement s'il manque dans la source.
    SPL = collections.defaultdict(list)
    try:
        for x in json.load(open(os.path.join(src, "events.json"), encoding="utf8"))["events"]:
            dd_ = x.get("details") or {}
            if x.get("category") in ("stock_split", "reverse_split") and x.get("ticker") and x.get("event_at") and dd_.get("ratio_new") and dd_.get("ratio_old"):
                k_ = float(dd_["ratio_new"]) / float(dd_["ratio_old"])
                e_ = di(x["event_at"][:10])
                if k_ > 0 and abs(k_ - 1) > 1e-9 and all(abs(e_ - e0) > 20 for e0, _ in SPL[x["ticker"]]):
                    SPL[x["ticker"]].append((e_, k_))
    except Exception as e:  # noqa: BLE001
        log("fractionnements illisibles :", e)
    for r in AV:  # fractionnements publiés sur brvm.org (date et parité) absents de la base d'avis
      try:
        if r.get("k") == "frac" and r.get("t") and r.get("e") and r.get("ratio") and r["ratio"][0] and r["ratio"][1]:
            k_, e_ = r["ratio"][0] / r["ratio"][1], di(r["e"][:10])
            if k_ > 0 and abs(k_ - 1) > 1e-9 and all(abs(e_ - e0) > 20 for e0, _ in SPL[r["t"]]):
                SPL[r["t"]].append((e_, k_))
                av_chk["split"] += 1
      except Exception as e:  # noqa: BLE001
        log("fractionnement brvm.org ignoré :", r.get("u"), e)
    split_log, force_write, PX_DATE = [], set(), {}

    def split_factor(t, date_int, upto):
        """Produit des fractionnements effectifs après `date_int` (et au plus tard à `upto`)."""
        f_ = 1.0
        for e_, k_ in SPL.get(t, []):
            if date_int < e_ <= upto:
                f_ *= k_
        return f_
    today_i = int(os.environ.get("FQT_TODAY") or dt.date.today().strftime("%Y%m%d"))

    def adj_divs(tk, only=None):
        """Dividendes publiés par action ancienne ramenés sur la base actuelle (tous les fractionnements, ou seulement `only`)."""
        for x in divs:
            if x.get("ticker") != tk or not x.get("dividende"):
                continue
            ds_ = x.get("date_detachement") or x.get("date_paiement") or (f"{int(x['exercice']) + 1}-06-30" if x.get("exercice") else None)
            if not ds_:
                continue
            d0 = di(ds_[:10])
            f_ = (only[1] if d0 < only[0] <= today_i else 1.0) if only else split_factor(tk, d0, today_i)
            if f_ != 1.0:
                x.setdefault("dividende_publie", x["dividende"])
                x["dividende"] = round(x["dividende"] / f_, 4)
                x["ajust"] = round((x.get("ajust") or 1.0) * f_, 6)

    status = json.load(open(os.path.join(src, "trading_status.json"), encoding="utf8"))
    session = json.load(open(a.session, encoding="utf8")) if a.session and os.path.exists(a.session) else None
    sess_rows = {r["t"]: r for r in (session or {}).get("rows", [])}
    sess_d = di(session["asof"]) if session else None
    last_div = {}
    for x in divs:
        t = x.get("ticker")
        if not t or not x.get("dividende"):
            continue
        k = (x.get("exercice") or 0, x.get("date_paiement") or "")
        if t not in last_div or k > last_div[t][0]:
            last_div[t] = (k, x)
    for act in acts:
        t = act["ticker"]
        p = os.path.join(src, act["csv"] + ".csv")
        if not os.path.exists(p):
            log("missing csv", t)
            continue
        rows = load_brvm_csv(p)
        if BOC.get(t) and rows:  # contrôle des clôtures, puis séances manquantes après la fin de la base complétées par les bulletins
            B_ = BOC[t]
            ck = [(r[4], B_[r[0]]["c"]) for r in rows if r[0] in B_ and B_[r[0]].get("c")]
            nd_ = sum(1 for x, y in ck if abs(x / y - 1) > .005)
            boc_chk["n"] += len(ck)
            boc_chk["diff"] += nd_
            if ck:
                boc_chk["by"][t] = [len(ck), nd_]
            last_d = rows[-1][0]
            for k in sorted(B_):
                if k <= last_d:
                    continue
                r = B_[k]
                c_ = r.get("c") or r.get("ref")
                if not c_:
                    continue
                o_ = r.get("o") or c_
                rows.append((k, o_, max(o_, c_), min(o_, c_), c_, int(r.get("vol") or 0), int(r.get("val") or 0)))
                boc_chk["added"] += 1
        if t in sess_rows and sess_d and rows and sess_d >= rows[-1][0]:
            s = sess_rows[t]
            bar = (sess_d, s.get("o") or s["c"], max(s["c"], s.get("o") or s["c"]), min(s["c"], s.get("o") or s["c"]), s["c"], s.get("vol", 0), int((s.get("vol") or 0) * s["c"]))
            rows = [r for r in rows if r[0] != sess_d] + [bar]
        # volumes et montants échangés : ceux du bulletin officiel de la cote quand il existe (montant jugé lisible s'il est à ±30 % de volume × cours) ;
        # sinon le montant du jour n'est qu'une estimation (volume × cours de clôture), signalée comme telle
        val_est = bool(rows) and rows[-1][0] == sess_d and t in sess_rows
        if BOC.get(t) and rows:
            B_ = BOC[t]
            for i_, r in enumerate(rows):
                b_ = B_.get(r[0])
                if b_ and b_.get("val") and b_.get("vol") and r[4] and 0.7 < b_["val"] / (b_["vol"] * r[4]) < 1.3:
                    if (int(b_["vol"]), int(b_["val"])) != (r[5], r[6]):
                        boc_chk["val_fix"] = boc_chk.get("val_fix", 0) + 1
                    rows[i_] = tuple(r[:5]) + (int(b_["vol"]), int(b_["val"]))
                    if r[0] == rows[-1][0]:
                        val_est = False
        if len(rows) < 3:
            continue
        f = fund.get(t, {})
        shares = f.get("nb_titres")
        bnpa_, dfund_ = f.get("bnpa"), f.get("dividende")
        # fractionnement ou regroupement absent de la base d'avis : sur la BRVM la variation d'une séance est bornée (±7,5 %),
        # un écart égal à un rapport usuel (2, 5, 10…) et confirmé par les deux séances suivantes ne peut être qu'une opération sur titres
        STD_ = [2, 3, 4, 5, 10, 20, 25, 40, 50, 64, 100]
        i2d = lambda x: dt.date(x // 10000, x // 100 % 100, x % 100)  # noqa: E731

        def jump_at(e0, k0):  # le cours saute-t-il du rapport k0 à la date e0 ?
            j0 = next((j for j, r in enumerate(rows) if r[0] >= e0), None)
            return bool(j0 and rows[j0 - 1][4] and rows[j0][4] and abs(math.log((rows[j0 - 1][4] / rows[j0][4]) / k0)) < math.log(1.4))
        for i_ in range(1, len(rows) - 1):
            a_, b_ = rows[i_ - 1][4], rows[i_][4]
            if not a_ or not b_ or 0.6 < a_ / b_ < 1.65:
                continue
            r_ = a_ / b_
            k_ = next((float(k) for k in STD_ if abs(math.log(r_ / k)) < math.log(1.12)), None) or next((1.0 / k for k in STD_ if abs(math.log(r_ * k)) < math.log(1.12)), None)
            if not k_ or not (rows[i_ + 1][4] and abs(rows[i_ + 1][4] / b_ - 1) < .25):
                continue  # confirmé par la séance suivante (une erreur de saisie isolée est ignorée)
            e_ = rows[i_][0]
            near = [(e0, k0) for e0, k0 in SPL.get(t, []) if abs((i2d(e0) - i2d(e_)).days) < 400 and abs(k0 - k_) < 1e-6]
            if any(abs((i2d(e0) - i2d(e_)).days) < 45 for e0, _ in near):
                continue  # même opération que l'avis
            if near and not jump_at(near[0][0], near[0][1]):
                # la source des cours a appliqué l'opération à une autre date que l'avis : les cours sont ajustés à la date du saut,
                # les dividendes et données par action restent rattachés à la date d'effet de l'avis
                PX_DATE[(t, near[0][0])] = e_
                split_log.append(f"{t} {e_} x{k_:g} : saut de cours rattaché à l'avis du {near[0][0]}")
            else:
                SPL[t].append((e_, k_))
                split_log.append(f"{t} {e_} x{k_:g} : opération détectée sur les cours (sans avis dans la base)")
        if t in SPL:
            adj_divs(t)
        for e_, k_ in sorted(SPL.get(t, [])):
            if e_ > rows[-1][0]:
                continue  # pas encore effectif
            ep_ = PX_DATE.get((t, e_), e_)
            i_ = next((j for j, r in enumerate(rows) if r[0] >= ep_), None)
            if i_ and rows[i_ - 1][4] and rows[i_][4] and abs(math.log((rows[i_ - 1][4] / rows[i_][4]) / k_)) < math.log(1.4):
                rows = [(r[0], r[1] / k_, r[2] / k_, r[3] / k_, r[4] / k_, int(round(r[5] * k_)), r[6]) if j < i_ else r for j, r in enumerate(rows)]
                split_log.append(f"{t} {e_} x{k_:g} : cours antérieurs ajustés")
                force_write.add(t)
            # données par action de la fiche société : ajustées si elles datent d'avant le fractionnement
            src_d = di(str(f.get("date_source") or "2000-01-01")[:10])
            per_boc = None
            if BOC.get(t):
                kb = max(BOC[t])
                per_boc = BOC[t][kb].get("per") if kb >= e_ else None
            stale = src_d < e_
            if per_boc and bnpa_ and bnpa_ > 0 and rows[-1][4]:
                r_ = (rows[-1][4] / bnpa_) / per_boc
                stale = abs(math.log(r_ * k_)) < math.log(1.4)  # PER calculé ≈ PER officiel ÷ k : BNPA encore par action ancienne
            if stale:
                bnpa_ = bnpa_ / k_ if bnpa_ else bnpa_
                dfund_ = dfund_ / k_ if dfund_ else dfund_
                ser_ = f.get("series") or {}
                for key_ in ("bnpa", "dividende"):
                    for y_, v_ in list((ser_.get(key_) or {}).items()):
                        if v_ is not None and di(f"{int(y_) + 1}-04-30") < e_:
                            ser_[key_][y_] = v_ / k_
                split_log.append(f"{t} {e_} x{k_:g} : BNPA et dividende par action ajustés")
            if shares and not (sess_rows.get(t) or {}).get("sh") and (f.get("provenance_champs") or {}).get("nb_titres") == "fichier_initial" and e_ >= 20250101:
                shares = shares * k_
                f["nb_titres"] = shares
                split_log.append(f"{t} {e_} x{k_:g} : nombre de titres ajusté")
        # cours de clôture officiels (bulletin de la cote) prioritaires : la série reste ajustée des opérations sur titres
        # (facteur local = rapport médian série / bulletin sur les séances voisines) ; une clôture qui s'en écarte de plus de 0,5 %
        # est remplacée par la clôture officielle, si le bulletin est cohérent (cours précédent × variation = clôture)
        if BOC.get(t) and rows:
            B_ = BOC[t]
            qs = [(j, r[4] / B_[r[0]]["c"]) for j, r in enumerate(rows) if r[4] and (B_.get(r[0]) or {}).get("c")]
            for n_q, (j, q) in enumerate(qs):
                win = sorted(x for _, x in qs[max(0, n_q - 10):n_q + 11])
                m_ = win[len(win) // 2]
                if abs(q / m_ - 1) <= .005 or sum(1 for x in win if abs(x / m_ - 1) <= .005) < .7 * len(win):
                    continue
                b_ = B_[rows[j][0]]
                if b_.get("prev") and b_.get("var") is not None and abs(b_["prev"] * (1 + b_["var"] / 100) / b_["c"] - 1) > .006:
                    continue  # bulletin incohérent ce jour-là : la série est gardée
                c_new = b_["c"] * m_
                o_new = b_["o"] * m_ if b_.get("o") else rows[j][1]
                r = rows[j]
                rows[j] = (r[0], o_new, max(r[2], o_new, c_new), min(r[3], o_new, c_new), c_new) + tuple(r[5:])
                boc_chk["close_fix"] = boc_chk.get("close_fix", 0) + 1
                cfb_ = boc_chk.setdefault("close_fix_by", {})
                cfb_[t] = cfb_.get(t, 0) + 1
                if not a.live:
                    force_write.add(t)
        # données officielles de la BRVM, prioritaires sur les sites tiers :
        # nombre de titres et capitalisation flottante (page « Capitalisations » de brvm.org), PER et dividende du bulletin officiel de la cote
        so_ = sess_rows.get(t) or {}
        flt_off = None
        if so_.get("sh"):
            shares = float(so_["sh"])
            if so_.get("capf") and so_.get("capg"):
                flt_off = round(so_["capf"] / so_["capg"] * 100, 2)
        bnpa_off = None
        if BOC.get(t):
            for kb in sorted(BOC[t], reverse=True)[:10]:  # dernier PER publié (le bulletin du jour peut manquer)
                rb = BOC[t][kb]
                cb = rb.get("c") or rb.get("ref")
                if rb.get("per") and rb["per"] > 0 and cb:
                    f_split = split_factor(t, kb, rows[-1][0])  # cours du bulletin antérieur à un fractionnement
                    bnpa_off = cb / rb["per"] / f_split
                    break
        if bnpa_off and bnpa_ and bnpa_ > 0 and abs(math.log(bnpa_ / bnpa_off)) > math.log(1.25):
            split_log.append(f"{t} : BNPA de la fiche ({bnpa_:g}) écarté, base officielle {bnpa_off:.2f}")
        if so_.get("sh"):
            f["nb_titres"] = shares
        if flt_off is not None:
            f["flottant"] = flt_off
        pso_ = "off" if bnpa_off else ("alt" if bnpa_ else None)
        # BNPA du bulletin = cours ÷ PER (PER arrondi à 2 décimales) : le BNPA publié par la société, s'il concorde à 1 % près, est gardé tel quel
        if bnpa_off and not (bnpa_ and bnpa_ > 0 and abs(bnpa_ / bnpa_off - 1) < .01):
            bnpa_ = bnpa_off
        cty = "BF" if t.endswith("BF") else CTY.get(t[-1], "CI")
        ld = last_div.get(t, (None, {}))[1]
        last = rows[-1][4]
        meta = {"id": t, "tk": f"{t} BC", "n": act.get("nom_officiel") or act.get("nom"), "short": act.get("nom"), "cls": "Equity", "typ": "Equity",
                "mkt": "BRVM", "grp": act.get("secteur"), "ccy": "XOF", "bench": "BRVMC", "cty": cty, "bank": bool(act.get("banque")),
                "shares": shares, "float": flt_off if flt_off is not None else f.get("flottant"), "mcap": rnd(shares * last, 0) if shares else None, "pso": pso_,
                "bnpa": rnd(bnpa_, 2) if bnpa_ else bnpa_, "dps": ld.get("dividende") or dfund_, "dps_ex": ld.get("exercice"), "dps_pay": ld.get("date_paiement"),
                "dps_adj": ld.get("ajust"), "split": [[e_, k_] for e_, k_ in sorted(SPL.get(t, []))] or None,
                "per": rnd(last / bnpa_, 2) if bnpa_ and bnpa_ > 0 else None,
                "yld": rnd((ld.get("dividende") or 0) / last, 5) if ld.get("dividende") else None,
                "susp": (status.get(t) or {}).get("statut") == "suspendue", **({"vde": 1} if val_est else {})}
        add(meta, [r[0] for r in rows], [r[4] for r in rows], [r[1] for r in rows], [r[2] for r in rows], [r[3] for r in rows],
            [r[5] for r in rows], [r[6] for r in rows], nd=2)
    rep = json.load(open(os.path.join(src, "indices", "indices_report.json"), encoding="utf8"))
    imap = {"BRVM-C": "BRVMC", "BRVM-30": "BRVM30", "BRVM-PRES": "BRVMPR", "BRVM-PRIN": "BRVMPA", "TL": "BRVM-TEL", "CD": "BRVM-CD",
            "SF": "BRVM-SF", "CB": "BRVM-CB", "IN": "BRVM-IN", "EN": "BRVM-EN", "SP": "BRVM-SP"}
    sess_idx = {imap[x["k"]]: x for x in (session or {}).get("idx", []) + (session or {}).get("sect", []) if x.get("k") in imap}
    for e in rep["entries"]:
        p = os.path.join(src, "indices", e["fichier"])
        if not os.path.exists(p):
            continue
        rows = load_brvm_csv(p)
        code = e["code"]
        if code in sess_idx and sess_d and rows and sess_d >= rows[-1][0]:
            v = sess_idx[code]["v"]
            rows = [r for r in rows if r[0] != sess_d] + [(sess_d, v, v, v, v, 0, rows[-1][6])]
        if len(rows) < 30:
            continue
        add({"id": code, "tk": f"{code} Index", "n": e["nom"], "cls": "Index", "typ": "Index", "mkt": "BRVM", "grp": "Indice " + e.get("type", ""), "ccy": "XOF", "bench": "BRVMC"},
            [r[0] for r in rows], [r[4] for r in rows], nd=2, val=[r[6] for r in rows])

    # Macro -----------------------------------------------------------------
    def macro(sid, tk, name, grp, path, dcol, vcol, freq, nd=2, filt=None, ccy="USD", cls="Comdty"):
        try:
            s = series_from_csv(fetch(DS.format(path), a.cache).decode("utf8"), dcol, vcol, filt)
        except Exception as e:  # noqa: BLE001
            log("skip", sid, e)
            return []
        add({"id": sid, "tk": tk, "n": name, "cls": cls, "typ": cls, "mkt": "MACRO", "grp": grp, "ccy": ccy}, [x[0] for x in s], [x[1] for x in s], freq=freq, nd=nd)
        return s
    macro("XAU", "XAU Curncy", "Or (USD/once, mensuel)", "Métaux", "gold-prices/main/data/monthly.csv", "Date", "Price", "M")
    macro("SPXM", "SPX Index (mensuel)", "S&P 500 depuis 1871 (mensuel)", "Actions", "s-and-p-500/main/data/data.csv", "Date", "SP500", "M", cls="Index")
    macro("CAPE", "CAPE Index", "S&P 500 PER de Shiller (CAPE)", "Valorisation", "s-and-p-500/main/data/data.csv", "Date", "PE10", "M", cls="Index")
    macro("CPI", "CPI INDX", "Indice des prix US (CPI-U)", "Inflation", "cpi-us/main/data/cpiai.csv", "Date", "Index", "M", cls="Index")
    macro("US10Y", "USGG10YR Index", "Taux US 10 ans (%)", "Taux", "bond-yields-us-10y/main/data/monthly.csv", "Date", "Rate", "M", cls="Rate", ccy="%")
    # prix au comptant publiés par l'EIA (J-1) : Brent daté (physique), WTI Cushing, gaz Henry Hub. Les contrats à terme
    # (CO1, CL1, NG1 : ceux d'Investing, TradingView, Bloomberg) sont ajoutés par build_extra.ingest sous BRENT, WTI, NATGAS.
    import build_extra
    fut_dir = os.path.join(a.extra, "futures") if a.extra else None
    for sid, sid_f, tk, name, path, nd_ in (("BRENTS", "BRENT", "EUCRBRDT Index", "Brent daté, prix au comptant (EIA, USD/baril)", "oil-prices/main/data/brent-daily.csv", 2),
                                            ("WTIS", "WTI", "USCRWTIC Index", "WTI Cushing, prix au comptant (EIA, USD/baril)", "oil-prices/main/data/wti-daily.csv", 2),
                                            ("NGS", "NATGAS", "NGUSHHUB Index", "Gaz Henry Hub, prix au comptant (EIA, USD/MMBtu)", "natural-gas/main/data/daily.csv", 3)):
        sp = macro(sid, tk, name, "Énergie", path, "Date", "Price", "D", nd=nd_)
        if sp and not (fut_dir and build_extra.futures_ok(os.path.join(fut_dir, sid_f + ".json"))):
            QUOTES.pop(sid_f, None)  # cours du contrat à terme : jamais greffé sur la série au comptant (ni ici, ni dans la page)
            if a.quotes and os.path.exists(a.quotes):
                qj = json.load(open(a.quotes, encoding="utf8"))
                if (qj.get("q") or {}).pop(sid_f, None) is not None:
                    json.dump(qj, open(a.quotes, "w", encoding="utf8"), separators=(",", ":"), ensure_ascii=False)
            macro(sid_f, tk, name, "Énergie", path, "Date", "Price", "D", nd=nd_)
    macro("VIX", "VIX Index", "Volatilité implicite S&P 500", "Volatilité", "finance-vix/main/data/vix-daily.csv", "DATE", "CLOSE", "D", cls="Index", ccy="pts")
    try:
        fx = fetch(DS.format("exchange-rates/main/data/daily.csv"), a.cache).decode("utf8")
        eur = series_from_csv(fx, "Date", "Exchange rate", lambda r: r.get("Country") == "Euro")
        twd = series_from_csv(fx, "Date", "Exchange rate", lambda r: r.get("Country") == "Taiwan")
        add({"id": "EURUSD", "tk": "EURUSD Curncy", "n": "Euro / Dollar US", "cls": "Curncy", "typ": "Curncy", "mkt": "MACRO", "grp": "Change", "ccy": "USD"},
            [x[0] for x in eur], [1 / x[1] for x in eur], nd=5)
        add({"id": "USDXOF", "tk": "USDXOF Curncy", "n": "Dollar US / Franc CFA (BCEAO)", "cls": "Curncy", "typ": "Curncy", "mkt": "MACRO", "grp": "Change", "ccy": "XOF"},
            [x[0] for x in eur], [x[1] * XOF_PER_EUR for x in eur], nd=3)
        add({"id": "USDTWD", "tk": "USDTWD Curncy", "n": "Dollar US / Dollar taïwanais", "cls": "Curncy", "typ": "Curncy", "mkt": "MACRO", "grp": "Change", "ccy": "TWD"},
            [x[0] for x in twd], [x[1] for x in twd], nd=4)
    except Exception as e:  # noqa: BLE001
        log("skip FX", e)

    # Sources complémentaires : ETF, indices US, Nasdaq-100, CBOE, crypto ----------
    import build_extra
    xinfo = build_extra.ingest(a.extra, add, set(files), log)
    # dividendes US (Nasdaq) ajoutés aux séries à la date de détachement : rendement total, backtests et DVD
    try:
        usd_p = os.path.join(a.extra, "us_divs.json") if a.extra else None
        USDIV = (json.load(open(usd_p, encoding="utf8")).get("s") or {}) if usd_p and os.path.exists(usd_p) else {}
        spl_p = os.path.join(a.extra, "us_splits.json") if a.extra else None
        USSPL = (json.load(open(spl_p, encoding="utf8")).get("s") or {}) if spl_p and os.path.exists(spl_p) else {}
        n_usd = n_ser = 0
        for sid, rows in USDIV.items():
            b = files.get(sid)
            if not b or not rows:
                continue
            idx = {d: i for i, d in enumerate(b["d"])}
            div = list(b.get("div") or [0] * len(b["d"]))
            if any(div):
                continue  # série qui porte déjà ses dividendes (Yahoo)
            spl = [(x[0], x[1]) for x in USSPL.get(sid, []) if x[1] and x[1] > 0]
            for d_, amt, _pay in rows:
                k = di(d_)
                for sd, ratio in spl:  # montant nominal de l'époque ramené à la base d'actions actuelle (cours déjà ajustés)
                    if sd > d_:
                        amt = amt / ratio
                i = idx.get(k)
                if i is None:  # détachement un jour sans cotation dans la série : première séance suivante
                    nxt = [j for j, dd in enumerate(b["d"]) if dd >= k]
                    i = nxt[0] if nxt else None
                if i is not None:
                    div[i] = round(div[i] + amt, 4)
                    n_usd += 1
            b["div"] = div
            n_ser += 1
        log("dividendes US :", n_usd, "versements placés dans", n_ser, "séries (écrits à la base du soir)")
    except Exception as e:  # noqa: BLE001
        log("dividendes US illisibles :", e)

    for s in secs:  # métadonnées Nasdaq des titres US déjà suivis
        if s["mkt"] == "US" and s["id"] in xinfo["ndx"]:
            s["ndx"] = True
        sc = xinfo["screener"].get(s["id"]) if s["mkt"] == "US" else None
        if sc:
            s["mcap"] = s.get("mcap") or sc.get("mcap")
            s["sector"] = build_extra.SECT_FR.get(sc.get("sector"), sc.get("sector"))
            s["ind"] = sc.get("ind")

    # Betas / correlations on weekly returns (2 years) ----------------------
    wk = {sid: weekly(b["d"], b["c"]) for sid, b in files.items() if b["f"] == "D"}
    for s in secs:
        bm = s.get("bench")
        if s["f"] != "D" or not bm or bm == s["id"] or bm not in wk:
            continue
        a_, b_ = wk[s["id"]], wk[bm]
        keys = sorted(set(a_) & set(b_))[-105:]
        x = [math.log(a_[keys[i]] / a_[keys[i - 1]]) for i in range(1, len(keys))]
        y = [math.log(b_[keys[i]] / b_[keys[i - 1]]) for i in range(1, len(keys))]
        s["beta"], s["corr"] = (rnd(v, 3) for v in beta_corr(x, y))
    # weekly matrix (10 years) for CORR / PCA
    allw = sorted({k for v in wk.values() for k in v})
    allw = [k for k in allw if k >= allw[-1] - 100000][-530:]
    wm = {"w": allw, "s": {}}
    for sid, ser in wk.items():
        last = None
        col = []
        for k in allw:
            if k in ser:
                last = ser[k]
            col.append(rnd(last, 4) if last is not None else None)
        if sum(1 for v in col if v is not None) > 52:
            wm["s"][sid] = col

    # BRVM breadth (since 2008) -------------------------------------------
    stocks = [s["id"] for s in secs if s["mkt"] == "BRVM" and s["cls"] == "Equity"]
    days = sorted({d for sid in stocks for d in files[sid]["d"] if d >= 20080101})
    above200, above50, adv, dec, nh, nl = ({} for _ in range(6))
    for sid in stocks:
        b = files[sid]
        d, c = b["d"], b["c"]
        s50 = s200 = 0.0
        for i in range(len(c)):
            s50 += c[i]
            s200 += c[i]
            if i >= 50:
                s50 -= c[i - 50]
            if i >= 200:
                s200 -= c[i - 200]
            if d[i] < 20080101 or i < 1:
                continue
            day = d[i]
            if i >= 199:
                above200.setdefault(day, [0, 0])
                above200[day][1] += 1
                above200[day][0] += c[i] > s200 / 200
            if i >= 49:
                above50.setdefault(day, [0, 0])
                above50[day][1] += 1
                above50[day][0] += c[i] > s50 / 50
            if c[i] > c[i - 1]:
                adv[day] = adv.get(day, 0) + 1
            elif c[i] < c[i - 1]:
                dec[day] = dec.get(day, 0) + 1
            if i >= 251:
                w = c[i - 251:i]
                if c[i] > max(w):
                    nh[day] = nh.get(day, 0) + 1
                elif c[i] < min(w):
                    nl[day] = nl.get(day, 0) + 1
    adl, run = [], 0
    for day in days:
        run += adv.get(day, 0) - dec.get(day, 0)
        adl.append(run)
    breadth = {"d": days, "a200": [rnd(above200[x][0] / above200[x][1], 4) if x in above200 and above200[x][1] >= 10 else None for x in days],
               "a50": [rnd(above50[x][0] / above50[x][1], 4) if x in above50 and above50[x][1] >= 10 else None for x in days],
               "adv": [adv.get(x, 0) for x in days], "dec": [dec.get(x, 0) for x in days], "adl": adl,
               "nh": [nh.get(x, 0) for x in days], "nl": [nl.get(x, 0) for x in days]}

    # BRVM meta: fundamentals, dividends, notices ---------------------------
    keep = ["ca", "resultat_net", "bnpa", "dividende", "per", "capitaux_propres", "roe", "roa", "marge_nette", "marge_exploitation",
            "croissance_ca", "croissance_resultat_net", "total_bilan", "depots_clientele", "credits_clientele", "coefficient_d_exploitation",
            "cout_du_risque", "ratio_endettement_net", "dette_nette", "tresorerie", "ebitda", "ebit"]
    fmeta = {k: {"nom": v.get("nom"), "secteur": v.get("secteur"), "shares": v.get("nb_titres"), "float": v.get("flottant"), "ex": v.get("exercice"),
                 "series": {s: v["series"][s] for s in keep if v.get("series", {}).get(s)}}
             for k, v in fund.items() if k != "_meta"}
    dmeta = [{"t": x.get("ticker"), "ex": x.get("exercice"), "dps": x.get("dividende"), "ann": x.get("date_annonce"), "det": x.get("date_detachement"),
              "pay": x.get("date_paiement"), "src": x.get("source"), **({"dps0": x["dividende_publie"], "adj": x["ajust"]} if x.get("ajust") else {}),
              **({"cal": 1} if x.get("cal") else {})} for x in divs if x.get("ticker")]
    if split_log:
        log("fractionnements :", "; ".join(split_log[:40]))
    ev = json.load(open(os.path.join(src, "events.json"), encoding="utf8"))["events"]
    emeta = [{"d": x.get("published_at") or x.get("event_at"), "e": x.get("event_at"), "t": x.get("ticker"), "c": "Modification du dividende" if x.get("category") == "dividend_amount_change" else x.get("category_label"),
              "ti": x.get("title"), "u": x.get("document_url")} for x in ev if (x.get("published_at") or x.get("event_at"))]
    try:
        avd = {}
        for r in AV:
            if r.get("k") == "div" and r.get("t"):
                for k_ in (r.get("det"), r.get("pay"), r.get("d")):
                    if k_:
                        avd[(r["t"], k_)] = r["u"]
        for x in emeta:
            if x.get("u") and "brvm.org" not in x["u"] and x.get("t"):
                x["u"] = avd.get((x["t"], x.get("e"))) or avd.get((x["t"], x.get("d"))) or x["u"]
    except Exception as e:  # noqa: BLE001
        log("liens d'avis :", e)
    known_u = {x["u"] for x in emeta if x.get("u")}
    known_k = {(x.get("t"), x.get("c"), x.get("d")) for x in emeta if x.get("t")}
    known_e = {(x.get("t"), x.get("e")) for x in emeta if x.get("t") and x.get("c") in ("Annonce dividende", "Paiement dividende", "Détachement dividende")}

    def dup(r):  # même document, ou même avis déjà repris par la base sous une autre adresse
        if r["u"] in known_u:
            return True
        try:
            d0 = dt.date.fromisoformat(r["d"][:10])
        except (TypeError, ValueError):
            return False
        if r.get("t") and any((r["t"], r.get("c"), (d0 + dt.timedelta(days=k)).isoformat()) in known_k for k in range(-3, 4)):
            return True
        if r.get("k") in ("frac", "capital") and r.get("t"):  # opérations déjà connues sous un autre avis (date d'effet à ±15 jours)
            try:
                e0 = dt.date.fromisoformat((r.get("e") or r["d"])[:10])
                if any(x.get("t") == r["t"] and x.get("c") == r.get("c") and x.get("e") and abs((dt.date.fromisoformat(x["e"][:10]) - e0).days) <= 15 for x in emeta):
                    return True
            except ValueError:
                pass
        return r.get("k") == "div" and r.get("t") and ((r["t"], r.get("det")) in known_e or (r["t"], r.get("pay")) in known_e)
    AV_BOND = re.compile(r"%|\betat\b|emprunt|obligat|fctc|\btp[a-z]{2}\b|diaspora|souscription|sukuk|\bo\d{2,3}\b")
    for r in AV:  # avis brvm.org pas encore dans la base : ajoutés tels que publiés (date de publication ; date de l'AG quand elle a été lue dans la convocation)
        try:
            # même périmètre que la base : actions cotées, et avis de marché généraux (pas les obligations ni les États)
            if not r.get("d") or (not r.get("t") and (r.get("k") != "marche" or AV_BOND.search(_nm(r.get("ti"))))) or dup(r):
                continue
        except Exception:  # noqa: BLE001
            continue
        emeta.append({"d": r["d"], "e": r.get("e") or r["d"], "t": r.get("t"), "c": r.get("c"), "ti": r.get("ti"), "u": r["u"]})
        av_chk["ev"] += 1
        if r.get("k") == "ag" and r.get("ag"):
            emeta.append({"d": r["d"], "e": r["ag"], "t": r.get("t"), "c": "Assemblée générale", "ti": r.get("ti"), "u": r["u"]})
            av_chk["ag"] += 1
    if AV:
        log("avis brvm.org ajoutés :", av_chk)
    emeta.sort(key=lambda x: x["d"] or "", reverse=True)

    # Calculs dérivés (macro, sentiment, liquidité, comptes, consensus, valorisation BRVM, UEMOA) ----
    # flux de trésorerie : uniquement ceux lus et vérifiés dans les états financiers publiés (pdf_cf). L'ancien fichier de départ
    # (--fcf, lecture sans contrôle d'identités : unités et lignes erronées sur 31 des 32 exercices recoupés) n'est plus utilisé.
    fcf_path = None
    if pdf_cf:
        import tempfile
        fcf_path = os.path.join(tempfile.gettempdir(), "fqt_fcf_verified.json")
        json.dump({"series": pdf_cf}, open(fcf_path, "w", encoding="utf8"))
    log("flux de trésorerie vérifiés :", sum(len(v) for v in pdf_cf.values()), "exercices,", len(pdf_cf), "sociétés")
    build_extra.derive(a.extra, out, files, secs, fund, fcf_path, dmeta, xinfo["ndx"], log)

    # write ------------------------------------------------------------------
    for sid, body in files.items():
        p_ = os.path.join(sdir, sid.replace(".", "_") + ".json")
        if a.live and os.path.exists(p_) and sid not in force_write:
            continue  # séance : la page applique elle-même les cours du jour (quotes.json) aux séries
        with open(p_, "w", encoding="utf8") as fh:
            json.dump(body, fh, separators=(",", ":"))
    asof = max(s["dt"] for s in secs if s["mkt"] in ("US", "BRVM"))
    summ = {"asof": asof, "built": int(time.time()), "secs": secs, "sectors": sorted({s["grp"] for s in secs if s["mkt"] == "BRVM" and s["cls"] == "Equity"}),
            "session": {"asof": session.get("asof"), "label": session.get("session"), "capA": session.get("capA")} if session else None, "cty": CTY_NAME}
    # notations financières (PDF de brvm.org lus le soir) : une ligne par document, dernière note par émetteur
    try:
        rp_ = os.path.join(a.extra, "ratings.json") if a.extra else None
        RT = (json.load(open(rp_, encoding="utf8")).get("docs") or {}) if rp_ and os.path.exists(rp_) else {}
        if RT:
            tick = {s_["id"] for s_ in secs if s_.get("mkt") == "BRVM"}
            ev_t = {x.get("u"): x.get("t") for x in emeta if x.get("u") and x.get("t") in tick}  # avis rattachés à une société cotée
            rows_ = []
            for u_, r_ in RT.items():
                if not (r_.get("lt") or r_.get("st")):
                    continue
                # un fonds de titrisation (FCTC, note « (SF) ») n'est pas la société qui l'a créé : rangé avec les émetteurs d'obligations
                sf_ = "(SF)" in (r_.get("lt") or "") or bool(re.search(r"(?<![a-z])fctc(?![a-z])", ((r_.get("ti") or "") + " " + u_).lower()))
                t_ = None if sf_ else r_.get("t") if r_.get("t") in tick else ev_t.get(u_)
                soc_ = r_.get("soc")
                if not t_ and ":" in (r_.get("ti") or ""):  # émetteur non coté : nom tel qu'il figure dans l'intitulé de l'avis
                    soc_ = r_["ti"].split(":")[0].strip()
                rows_.append({"u": u_, "t": t_, "soc": soc_, "ti": r_.get("ti"), "d": r_.get("d"), "ag": r_.get("ag"), "lt": r_.get("lt"), "lt0": r_.get("lt0"),
                              "st": r_.get("st"), "st0": r_.get("st0"), "out": r_.get("out"), "exp": r_.get("exp"), "val": r_.get("val"), "scale": r_.get("scale")})
            rows_.sort(key=lambda x: x.get("d") or "", reverse=True)
            last_ = {}
            for x in rows_:  # dernière notation connue par société cotée
                if x["t"] and x["t"] not in last_:
                    last_[x["t"]] = x
            for s_ in secs:
                x = last_.get(s_["id"])
                if x:
                    s_["rating"] = {k: x.get(k) for k in ("ag", "lt", "st", "out", "d", "exp")}
            with open(os.path.join(out, "ratings.json"), "w", encoding="utf8") as fh:
                json.dump({"rows": rows_, "n_docs": len(RT), "n_read": len(rows_)}, fh, separators=(",", ":"), ensure_ascii=False)
    except Exception as e:  # noqa: BLE001
        log("notations illisibles :", e)
    # annuaires des intervenants (brvm.org)
    try:
        sg_ = os.path.join(a.extra, "sgi.json") if a.extra else None
        if sg_ and os.path.exists(sg_):
            shutil_copy = json.load(open(sg_, encoding="utf8"))
            with open(os.path.join(out, "sgi.json"), "w", encoding="utf8") as fh:
                json.dump(shutil_copy, fh, separators=(",", ":"), ensure_ascii=False)
    except Exception as e:  # noqa: BLE001
        log("intervenants illisibles :", e)
    # flottant officiel (avis de la BRVM lu la veille au soir) : publié tel quel, et rattaché à chaque action
    try:
        fp_ = os.path.join(a.extra, "flottant.json") if a.extra else None
        FLO = json.load(open(fp_, encoding="utf8")) if fp_ and os.path.exists(fp_) else None
        if FLO and FLO.get("rows"):
            for s_ in secs:
                r_ = FLO["rows"].get(s_["id"])
                if s_.get("mkt") == "BRVM" and r_:
                    s_["flo"] = r_["pct"]
            with open(os.path.join(out, "flottant.json"), "w", encoding="utf8") as fh:
                json.dump(FLO, fh, separators=(",", ":"), ensure_ascii=False)
    except Exception as e:  # noqa: BLE001
        log("flottant officiel illisible :", e)
    for name, obj in (("summary", summ), ("weekly", wm), ("breadth", breadth), ("fundamentals", fmeta), ("dividends", dmeta), ("events", emeta),
                      ("events_recent", emeta[:80]), ("boc_check", {**boc_chk, "avis": av_chk, "d": dt.date.today().isoformat()} if BOC else {"n": 0, "avis": av_chk})):
        with open(os.path.join(out, name + ".json"), "w", encoding="utf8") as fh:
            json.dump(obj, fh, separators=(",", ":"), ensure_ascii=False)
    tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(out) for f in fs)
    log(f"{len(secs)} securities, {sum(len(b['d']) for b in files.values())} rows, {tot / 1e6:.1f} MB -> {out}")


if __name__ == "__main__":
    sys.exit(main())
