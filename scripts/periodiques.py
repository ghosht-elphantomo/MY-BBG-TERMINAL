"""QLAB 3 « Prévisions » — étape 1 : résultats trimestriels, semestriels et annuels publiés par les sociétés cotées à la BRVM.

Lit les textes des documents déposés à la BRVM (cache de la branche `comptes` : couche texte, sinon reconnaissance de caractères)
et en extrait, pour chaque publication périodique, le chiffre d'affaires (ou le produit net bancaire), le résultat d'exploitation,
le résultat brut d'exploitation, l'EBITDA, le résultat avant impôt et le résultat net de la période et de la même période de
l'exercice précédent.

Aucun chiffre n'est retenu sans contrôle : une ligne n'est gardée que si la variation publiée sur la même ligne (en % ou en
valeur) est égale à la variation calculée entre les deux montants lus (aux arrondis près). Ce contrôle désigne aussi la colonne
de la période en cours (la variation se calcule toujours par rapport à l'exercice précédent) et lève l'ambiguïté des séparateurs
de milliers lus par reconnaissance de caractères. L'unité (FCFA, milliers, millions, milliards) est celle écrite dans le document
quand elle est lisible et cohérente, sinon celle qui rend le montant cohérent avec les comptes annuels vérifiés de la société.

Montants en millions de FCFA, cumulés depuis le début de l'exercice : T1 (3 mois), S1 (6 mois), 9M (9 mois), A (12 mois).
Bibliothèque standard uniquement.
"""
import gzip
import json
import os
import re
import unicodedata

READER_V = 1
METRICS = [  # (clé, motif de l'intitulé) — l'ordre compte : le premier motif reconnu dans le segment l'emporte
    ("pnb", r"produit\s+net\s+bancaire|\bpnb\b"),
    ("rbe", r"r[eé]sultat\s+brut\s+d.?\s?exploitation|\brbe\b"),
    ("rai", r"r[eé]sultat\s+avant\s+imp[oô]ts?|r[eé]sultat\s+des\s+activit[eé]s\s+ordinaires\s+avant\s+imp"),
    ("rn_pg", r"r[eé]sultat\s+net\s+part\s+du\s+groupe|r[eé]sultat\s+net\s+\(?part\s+du\s+groupe"),
    ("rn", r"r[eé]sultat\s+net(?!\s*/)|b[eé]n[eé]fice\s+net|r[eé]sultat\s+de\s+l.?exercice|r[eé]sultat\s+de\s+la\s+p[eé]riode"),
    ("rex", r"r[eé]sultat\s+d.?\s?exploitation|r[eé]sultat\s+op[eé]rationnel"),
    ("ebitda", r"ebitda(?:al)?\b|exc[eé]dent\s+brut\s+d.?\s?exploitation|\bebe\b"),
    ("ca", r"chiffre\s+d.?\s?affaires|produits?\s+des\s+activit[eé]s\s+ordinaires|\bventes\s+(?:nettes|de\s+marchandises|totales)|revenus?\s+(?:consolid[eé]s?|totaux)"),
]
MRX = [(k, re.compile(p, re.I)) for k, p in METRICS]
ANY_LAB = re.compile("|".join(p for _, p in METRICS) + r"|\b(?:total|cr[eé]dits|d[eé]p[oô]ts|charges|marge|taux|ratio|co[uû]t|capitaux|fonds\s+propres|effectif|nombre|parc|abonn[eé]s|production|volume)\b", re.I)
SKIP = re.compile(r"/\s*(?:pnb|ca|chiffre)|marge|taux|ratio|coefficient|\bpar\s+action\b|\bpar\s+titre\b|%\s+du\b|en\s+%|rentabilit|roe\b|roa\b|cours|dividende|r[eé]serve", re.I)
NUM = re.compile(r"(?<![\w,.])[-–−(]?\s?\d{1,3}(?:[   .]\d{3})+(?:,\d+)?\)?|(?<![\w,.])[-–−(]?\s?\d+(?:,\d+)?\)?")
PCT = re.compile(r"([+\-–−]?\s?\d{1,4}(?:,\d{1,2})?)\s?%")


def nrm(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower().replace("’", "'")


# ------------------------------------------------------------------ période de la publication
MOIS = {"janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10,
        "novembre": 11, "decembre": 12}


def period_of(title, url="", text=""):
    """(exercice, période) d'une publication : T1, S1, 9M (cumul à 9 mois) ou A ; None si la période n'est pas lisible.
    L'intitulé l'emporte ; le texte ne sert qu'à distinguer un 3e trimestre seul d'un cumul à 9 mois (on ne garde que le cumul)."""
    t = nrm(title) + " " + nrm(url.rsplit("/", 1)[-1].replace("_", " ").replace("-", " "))
    y = re.findall(r"\b(20\d\d|19\d\d)\b", t)
    fy = int(y[-1]) if y else None
    if not fy:
        return None
    head = nrm(text[:6000])
    if re.search(r"\b(1er|premier|1e|1)\s*(?:er\s*)?semestre|\bs1\b|semestriel|30\s*juin", t):
        return fy, "S1"
    if re.search(r"\b(1er|premier|1e)\s*trimestre|\bt1\b|\bq1\b|31\s*mars", t):
        return fy, "T1"
    if re.search(r"\b(3e|3eme|3ème|troisieme|3)\s*(?:eme\s*)?trimestre|\bt3\b|\bq3\b|9\s*mois|neuf\s*mois|30\s*septembre", t):
        if re.search(r"9\s*mois|neuf\s*mois|30\s*septembre|cumul|au\s+30/09|30/09/", t + " " + head):
            return fy, "9M"
        return None  # (trimestre isolé : non retenu tant que le cumul n'est pas lisible)
    if re.search(r"\b(2e|2eme|deuxieme|2)\s*(?:eme\s*)?trimestre|\bt2\b|\bq2\b", t):
        return (fy, "S1") if re.search(r"30\s*juin|semestre|6\s*mois|six\s*mois|cumul", t + " " + head) else None
    if re.search(r"exercice|annuel|31\s*decembre|etats\s+financiers\s+20\d\d|resultats?\s+(?:financiers\s+)?(?:annuels|20\d\d)", t):
        return fy, "A"
    return None


def units_of(text):
    """unité écrite dans le document (multiplicateur pour obtenir des millions de FCFA), si elle est unique"""
    t = nrm(text)
    found = set()
    for pat, s in ((r"en\s+milliards|\bmds?\s*(?:de\s*)?f?cfa|\bmilliards\s+(?:de\s+)?f?cfa|\(?mds\)?", 1e3), (r"en\s+millions|\bm\s*f?cfa\b|\bmf?cfa\b|millions\s+(?:de\s+)?f?cfa", 1.0),
                   (r"en\s+milliers|\bk\s*f?cfa\b|\bkf?cfa\b|milliers\s+(?:de\s+)?f?cfa", 1e-3)):
        if re.search(pat, t):
            found.add(s)
    return found.pop() if len(found) == 1 else None


# ------------------------------------------------------------------ lecture d'une ligne
def _num(tok):
    s = tok.strip()
    neg = s.startswith(("-", "–", "−", "(")) or s.endswith(")")
    s = re.sub(r"[^\d,]", "", s).replace(",", ".")
    if not s or s == ".":
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def _groups(seg):
    """séquences de nombres possibles d'un segment : les séparateurs de milliers (espace) sont ambigus ; toutes les lectures
    où chaque groupe après le premier compte exactement trois chiffres sont proposées (au plus 512)"""
    toks = re.findall(r"\(?[-–−]?\d+(?:,\d+)?\)?", seg)
    out = []

    def rec(i, cur):
        if len(out) >= 512:
            return
        if i == len(toks):
            out.append(list(cur))
            return
        # un nombre commence au jeton i et absorbe k groupes de 3 chiffres
        first = toks[i]
        digits_first = re.sub(r"\D", "", first.split(",")[0])
        if not digits_first or (len(digits_first) > 1 and digits_first[0] == "0"):
            return  # (« 030 » ne peut être que la suite d'un nombre : cette lecture est abandonnée)
        # lectures possibles du nombre qui commence ici, de la plus longue à la plus courte (les montants financiers ont
        # en général plusieurs groupes de chiffres)
        opts, j, txt = [], i, first
        while True:
            v = _num(txt)
            if v is not None:
                opts.append((j, v))
            if "," in txt or ")" in txt or j + 1 >= len(toks):
                break
            nxt = toks[j + 1]
            if not re.fullmatch(r"\d{3}(?:,\d+)?\)?", nxt) or len(digits_first) > 3:
                break
            txt = txt + nxt
            j += 1
        for j, v in reversed(opts):
            rec(j + 1, cur + [v])
    rec(0, [])
    return out


def _tol_pct(p_txt):
    dec = len(p_txt.split(",")[1]) if "," in p_txt else 0
    return 0.55 if dec == 0 else 0.055 if dec == 1 else 0.006


def verify(nums, pct_txt):
    """(courant, précédent) dont la variation est égale à celle publiée (en %) ou à l'écart publié (3e nombre) ; sinon None.
    Les deux montants sont consécutifs dans la ligne ; la variation désigne la colonne courante."""
    p = None
    if pct_txt is not None:
        try:
            p = float(re.sub(r"[\s+]", "", pct_txt).replace(",", ".").replace("–", "-").replace("−", "-"))
        except ValueError:
            p = None
    best = None
    for i in range(len(nums) - 1):
        a, b = nums[i], nums[i + 1]
        if a is None or b is None or (a == 0 and b == 0):
            continue
        for cur, prev in ((a, b), (b, a)):
            ok_p = ok_d = False
            if p is not None and prev not in (0,) and prev > 0:
                calc = (cur / prev - 1) * 100
                ok_p = abs(calc - p) <= _tol_pct(pct_txt) and not (abs(p) < 0.05 and abs(cur - prev) > 0.002 * abs(prev))
            if i + 2 < len(nums):
                d = nums[i + 2]
                ok_d = d is not None and abs((cur - prev) - d) <= max(1.0, abs(d) * 0.002) and abs(d) > 0
            # (la variation en % publiée est exigée : un écart en valeur seul se retrouve trop souvent par hasard dans une
            # ligne dont les séparateurs de milliers sont ambigus ; il ne sert que de confirmation)
            if ok_p:
                sc = (2 if ok_p else 0) + (1 if ok_d else 0)
                if not best or sc > best[0]:
                    best = (sc, cur, prev, p, nums[i + 2] if ok_d else None)
    return best


def read_lines(text):
    """lignes vérifiées d'un texte : [(métrique, courant, précédent, % publié, écart publié, ligne)]"""
    rows = []
    for raw in text.splitlines():
        line = raw.replace(" ", " ").replace(" ", " ")
        if not re.search(r"\d", line):
            continue
        # une ligne peut porter deux tableaux côte à côte : chaque intitulé ouvre un segment jusqu'au suivant
        cuts = [m.start() for m in ANY_LAB.finditer(line)]
        if not cuts:
            continue
        cuts.append(len(line))
        for a_, b_ in zip(cuts, cuts[1:]):
            seg = line[a_:b_]
            lab = nrm(seg[:90])
            met = next((k for k, rx in MRX if rx.match(lab) or rx.search(lab[:60])), None)
            if not met or SKIP.search(lab[:70]):
                continue
            mlab = next(rx for k, rx in MRX if k == met).search(lab)
            body = seg[mlab.end() if mlab else 0:] if mlab and mlab.end() < len(seg) else seg
            body = re.sub(r"\b(19|20)\d\d\b(?!\s*\d{3})", " ", body)  # (années)
            pm = list(PCT.finditer(body))
            pct_txt = pm[-1].group(1) if pm else None
            nb = PCT.sub(" ", body)
            best = None
            for nums in _groups(nb):
                if len(nums) < 2 or len(nums) > 8:
                    continue
                r = verify(nums, pct_txt)
                if r and (not best or r[0] > best[0]):
                    best = r
            if best:
                rows.append((met, best[1], best[2], best[3], best[4], re.sub(r"\s+", " ", seg.strip())[:160]))
    return rows


# ------------------------------------------------------------------ unité
WIN = {"T1": (0.08, 0.6), "S1": (0.2, 0.9), "9M": (0.4, 1.15), "A": (0.6, 1.8)}
SCALES = (1.0, 1e3, 1e-3, 1e-6)  # millions, milliards, milliers, FCFA -> millions
USD_REPORTERS = {"ETIT"}  # (comptes publiés en dollars : conversion des publications intermédiaires à développer)


# ------------------------------------------------------------------ tous les documents
PERIODIC_CATS = {"activity_report", "financial_results", "financial_statements", "auditor_report", "company_report", "communique", "annual_report"}


def texts_of(d, h):
    out = []
    for suf in (".txt.gz", ".fra4.gz", ".fra.gz", ".eng4.gz", ".eng.gz"):
        p = os.path.join(d, "txt", h + suf)
        if os.path.exists(p):
            try:
                out.append((suf, gzip.open(p, "rt", encoding="utf8").read()))
            except Exception:  # noqa: BLE001
                pass
    return out


def extract_doc(d, u, m):
    """étape A (branche comptes, là où sont les textes) : période, unité écrite et lignes vérifiées d'un document, sans échelle"""
    per = period_of(m.get("ti") or "", u)
    if not per:
        return None
    best = None
    for suf, txt in texts_of(d, m.get("h") or ""):
        rows = read_lines(txt)
        if not rows:
            continue
        fy, p = per
        pp = period_of(m.get("ti") or "", u, txt) if p == "9M" else None
        if pp:
            fy, p = pp
        if not best or len(rows) > len(best["rows"]):
            best = {"fy": fy, "per": p, "unit": units_of(txt), "src": "ocr" if suf != ".txt.gz" else "texte",
                    "rows": [[met, cur, prev, pct, line] for met, cur, prev, pct, dif, line in rows][:40]}
    if best:
        best.update({"t": m.get("t"), "d": m.get("d"), "ti": (m.get("ti") or "")[:160]})
    return best


def extract_all(d):
    """étape A sur tout le cache : {url: publication} des documents périodiques lus"""
    idx = json.load(open(os.path.join(d, "index.json"), encoding="utf8")).get("docs") or {}
    out = {}
    for u, m in idx.items():
        if m.get("st") != "lu" or not m.get("t") or m.get("cat") not in PERIODIC_CATS:
            continue
        try:
            r = extract_doc(d, u, m)
        except Exception:  # noqa: BLE001
            r = None
        if r:
            out[u] = r
    return {"v": READER_V, "docs": out}


def resolve(pubs, annual):
    """étape B (passage du soir, avec les comptes annuels consolidés du terminal, en millions de FCFA) : unité de chaque
    publication, une valeur par société, exercice, période et poste, recoupements entre documents.
    annual : {titre: {exercice: {"rev": chiffre d'affaires ou PNB, "ni": résultat net}}}.
    Renvoie {titre: {"p": {exercice: {période: {poste: {...}}}}, "docs": [...]}}."""
    res = {}
    for u, x in (pubs or {}).items():
        t = x.get("t")
        if not t or not x.get("rows") or t in USD_REPORTERS:
            continue
        A = annual.get(t) or {}
        ref = next((A[y] for y in (x["fy"] - 1, x["fy"], x["fy"] - 2) if A.get(y)), {})
        rows = [tuple(r) for r in x["rows"]]
        top = next((r for r in rows if r[0] in ("ca", "pnb")), None)
        lo, hi = WIN[x["per"]]
        ok = []
        if top and ref.get("rev") and ref["rev"] > 0:
            ok = [s for s in SCALES if lo <= top[1] * s / ref["rev"] <= hi]
            how = "unité recoupée avec le chiffre d'affaires annuel"
        else:
            rn = next((r for r in rows if r[0] in ("rn", "rn_pg")), None)
            if rn and ref.get("ni"):
                ok = [s for s in SCALES if 0.02 <= abs(rn[1] * s) / abs(ref["ni"]) <= 5]
                how = "unité recoupée avec le résultat net annuel"
        scale = x.get("unit") if x.get("unit") in ok else (ok[0] if len(ok) == 1 else None)
        if scale is None:
            continue
        if scale != x.get("unit"):
            how += " (unité du document illisible ou absente)"
        # chaque poste est recoupé avec le chiffre d'affaires de la même publication (marge entre -150 % et +150 %) ou, à défaut,
        # avec le résultat net annuel ; un poste dont l'unité diffère du reste du tableau est remis à l'échelle si une seule unité
        # le rend cohérent, sinon il est écarté
        tv = top[1] * scale if top else None
        same = A.get(x["fy"]) or {}
        got = {}
        for met, cur, prev, pct, line in rows:
            if met in got:
                continue
            s_ = scale
            if met not in ("ca", "pnb") and tv:
                fit = [s2 for s2 in SCALES if 0.0003 <= abs(cur * s2 / tv) <= 1.5 or cur == 0]
                if s_ not in fit:
                    s_ = fit[0] if len(fit) == 1 else None
            elif met not in ("ca", "pnb") and ref.get("ni"):
                fit = [s2 for s2 in SCALES if 0.02 <= abs(cur * s2) / abs(ref["ni"]) <= 5]
                if s_ not in fit:
                    s_ = fit[0] if len(fit) == 1 else None
            if s_ is None:
                continue
            v_ = cur * s_
            # cumul de la période cohérent avec l'exercice complet quand il est déjà publié
            if met in ("ca", "pnb") and same.get("rev") and same["rev"] > 0 and x["per"] != "A":
                lo2, hi2 = {"T1": (0.06, 0.5), "S1": (0.15, 0.85), "9M": (0.4, 1.0)}[x["per"]]
                if not lo2 <= v_ / same["rev"] <= hi2:
                    continue
            got[met] = {"v": round(v_, 3), "p": round(prev * s_, 3), "pct": pct, "l": line}
        if not got:
            continue
        e = res.setdefault(t, {"p": {}, "docs": []})
        e["docs"].append({"u": u, "d": x.get("d"), "ti": x.get("ti"), "fy": x["fy"], "per": x["per"], "src": x.get("src"), "how": how, "m": sorted(got)})
        for met, g in got.items():
            for fy_, val, kind in ((x["fy"], g["v"], "cur"), (x["fy"] - 1, g["p"], "prev")):
                slot = e["p"].setdefault(str(fy_), {}).setdefault(x["per"], {}).setdefault(met, [])
                slot.append({"v": val, "u": u, "d": x.get("d"), "k": kind, "pct": g["pct"]})
    # une valeur par poste : la publication de la période elle-même ; une valeur confirmée par la colonne « exercice précédent »
    # de la publication suivante (à 1 % près) est notée comme recoupée ; un désaccord est signalé (comptes retraités ou lecture)
    for t, e in res.items():
        for fy_, pers in e["p"].items():
            for per, mets in pers.items():
                for met, L in mets.items():
                    cur = sorted([z for z in L if z["k"] == "cur"], key=lambda z: z["d"] or "", reverse=True)
                    prv = [z for z in L if z["k"] == "prev"]
                    base = cur[0] if cur else (prv[0] if prv else None)
                    if base is None:
                        continue
                    conf = [z for z in prv + cur[1:] if abs(z["v"] - base["v"]) <= max(0.5, 0.01 * abs(base["v"]))]
                    diff = [z for z in prv if abs(z["v"] - base["v"]) > max(0.5, 0.01 * abs(base["v"]))]
                    mets[met] = {"v": base["v"], "u": base["u"], "d": base["d"], "pub": base["k"] == "cur", "n_conf": len(conf),
                                 **({"restated": diff[0]["v"]} if diff else {})}
    return res


if __name__ == "__main__":
    import sys
    D = sys.argv[1]
    res = extract_all(D)
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(D, "periodiques.json")
    json.dump(res, open(out, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print(f"[periodiques] {len(res['docs'])} publications périodiques avec des lignes vérifiées")
