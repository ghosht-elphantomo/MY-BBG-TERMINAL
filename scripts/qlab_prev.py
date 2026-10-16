"""QLAB 3 — Prévisions : résultats trimestriels, semestriels et annuels des sociétés cotées à la BRVM.

Calculé chaque soir de semaine, après la valorisation (scripts/build_terminal.py, passage « base complète »), sans intervention.
Ne prédit jamais le cours, ne donne aucun objectif de cours et ne promet aucun rendement : seuls les résultats des entreprises sont
prévus (chiffre d'affaires ou produit net bancaire, résultat d'exploitation, résultat net, bénéfice par action, marges).

Données (toutes publiées à la BRVM) :
  - comptes annuels vérifiés du terminal (séries consolidées, date de publication de chaque exercice) ;
  - publications intermédiaires (1er trimestre, 1er semestre, 9 mois) lues dans les documents déposés par les sociétés, chaque
    chiffre contrôlé par la variation publiée sur la même ligne (scripts/periodiques.py) ;
  - documents et avis publiés depuis la dernière version (index des documents du terminal) : publications, communiqués,
    changements de dirigeants, opérations sur le capital, notations, assemblées.

Méthodes (calculs explicables, sans IA) : prévision naïve, tendance, marge normative, cumul de l'exercice comparé au même cumul de
l'exercice précédent, part saisonnière de la période dans l'exercice. Le choix de la méthode, pour chaque poste, chaque état
d'information (aucune publication de l'exercice, 1er trimestre, 1er semestre, 9 mois) et chaque horizon, se fait par validation
point-in-time à origine glissante : chaque prévision passée n'utilise que les publications disponibles à sa date. Une méthode
ne remplace la prévision naïve que si elle réduit l'erreur médiane d'au moins 10 % sur au moins 15 cas. Les fourchettes à 80 %
sont les quantiles des erreurs réellement mesurées pour la méthode retenue (elles s'élargissent donc avec l'horizon).

Révisions : une nouvelle version à chaque publication de résultats (mise à jour trimestrielle obligatoire), une révision
exceptionnelle quand des documents nouveaux (ou leur accumulation) peuvent modifier le résultat net prévu d'au moins 5 %
(seuil MAT_NI, réglable : déclencheur d'analyse, pas une variation automatique), une révision de méthode quand le moteur change.
Chaque version est conservée telle quelle, horodatée et chaînée à la précédente ; les erreurs de chaque version sont mesurées dès
que les résultats réels sont publiés.

Fichiers : data/qlabp/index.json, data/qlabp/<titre>.json, data/qlabp/hist/<titre>.json, data/qlabp/state.json ;
copie de sauvegarde dans le dossier des données brutes (qlabp/). Bibliothèque standard uniquement.
"""
import datetime as dt
import hashlib
import json
import os
import shutil
import time

import qlab_core as C
import periodiques as PER

ENGINE = "QLAB-P 1.0"
MAT_NI = 0.05          # seuil de matérialité : variation possible du résultat net prévu qui déclenche une analyse exceptionnelle
MIN_CASES = 15         # cas minimum pour qu'une méthode puisse remplacer la prévision naïve
GAIN_MIN = 0.10        # amélioration minimale de l'erreur médiane exigée
CO_MIN, CO_GAIN = 8, 0.20  # choix propre à une société : au moins 8 cas passés et 20 % d'erreur en moins (exigence plus forte)
H_MAX = 5
PERS = ("T1", "S1", "9M")
PER_M = {"T1": 3, "S1": 6, "9M": 9, "A": 12}
PER_N = {"T1": "1er trimestre", "S1": "1er semestre", "9M": "9 mois", "A": "exercice"}
MET = ("rev", "ebit", "ni")
MAP = {"ca": "rev", "pnb": "rev", "rex": "ebit", "rn": "ni", "rn_pg": "ni"}
M_REV = {"naive": "Exercice précédent reconduit (prévision naïve)", "drift": "Tendance : croissance médiane des derniers exercices",
         "ytd_g": "Croissance du cumul de l'exercice appliquée à l'exercice précédent", "ytd_s": "Cumul de l'exercice ÷ part saisonnière habituelle"}
M_NI = {"naive": "Exercice précédent reconduit (prévision naïve)", "margin": "Chiffre d'affaires prévu × marge médiane des 3 derniers exercices",
        "ytd_d": "Écart du cumul de l'exercice ajouté à l'exercice précédent", "ytd_s": "Cumul de l'exercice ÷ part saisonnière habituelle"}
M_FUT = {"naive": "Dernier niveau reconduit", "trend": "Tendance de la société rapprochée de la croissance de long terme ; marge ramenée vers sa médiane"}
EV_W = {"res": ("Publication de résultats", 1.0), "ef": ("États financiers", 1.0), "ra": ("Rapport d'activité", 1.0), "rann": ("Rapport annuel", 0.6),
        "dir": ("Changement de dirigeant", 0.5), "ost": ("Opération sur le capital", 0.8), "not": ("Notation financière", 0.4),
        "com": ("Communiqué", 0.4), "ag": ("Assemblée générale", 0.2), "div": ("Dividende", 0.1)}
WARN_KW = (("perte", "pertes"), ("avertissement", "profit warning"), ("incendie", "sinistre"), ("grève", "greve"),
           ("suspension de l'activité", "suspension des activités", "suspension de la production", "suspension de l'exploitation"),
           ("cession", "acquisition", "fusion", "absorption"),
           ("redressement", "contrôle fiscal", "controle fiscal", "litige", "contentieux"), ("dépréciation", "depreciation", "provision exceptionnelle"),
           ("augmentation de capital", "réduction de capital", "reduction de capital"), ("arrêt", "arret", "fermeture", "rupture"), ("sanction",))


# ------------------------------------------------------------------------------------------------------------- outils
def jload(p, default=None):
    try:
        with open(p, encoding="utf8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return default


def jdump(obj, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    os.replace(tmp, p)


def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def di(s):
    """date AAAA-MM-JJ ou AAAAMMJJ -> entier AAAAMMJJ"""
    if s is None:
        return None
    s = str(s).replace("-", "")[:8]
    return int(s) if s.isdigit() and len(s) == 8 else None


def fin(x):
    return C.fin(x)


def med(xs):
    xs = [x for x in xs if fin(x)]
    return C.med(xs) if xs else None


def q(xs, p):
    xs = sorted(x for x in xs if fin(x))
    return C.quant(xs, p) if xs else None


def r3(x):
    return C.sig(x, 4) if fin(x) else None


# ------------------------------------------------------------------------------------------------------------- données
def pubdate(S, fy):
    """date de publication des comptes annuels de l'exercice (30 juin de l'année suivante si elle n'est pas connue)"""
    return (S.get("pub") or {}).get(fy) or int(f"{fy + 1}0630")


def periodic_data(comptes_path, I, log):
    """publications intermédiaires vérifiées, en millions de FCFA : {titre: {exercice: {période: {poste: {...}}}}}, {url: intitulé}"""
    cj = jload(comptes_path, {}) if comptes_path else {}
    pubs = (cj or {}).get("periodic") or {}
    if not pubs:
        return {}, {}, 0
    annual = {}
    for t, S in I["S"].items():
        rv, ni = S["ser"].get("rev") or {}, S["ser"].get("ni") or {}
        annual[t] = {y: {"rev": rv.get(y), "ni": ni.get(y)} for y in set(rv) | set(ni)}
    R = PER.resolve(pubs, annual)
    out, titles = {}, {}
    for t, e in R.items():
        for dd in e["docs"]:
            titles[dd["u"]] = (dd.get("ti"), dd.get("d"))
        for fy, pers in e["p"].items():
            for per, mets in pers.items():
                if per == "A":
                    continue  # (exercice complet : comptes annuels vérifiés du terminal)
                for met, x in mets.items():
                    k = MAP.get(met)
                    if not k or not isinstance(x, dict) or not fin(x.get("v")):
                        continue
                    slot = out.setdefault(t, {}).setdefault(int(fy), {}).setdefault(per, {})
                    if k in slot and met == "rn_pg":
                        continue  # (résultat net total préféré à la part du groupe quand les deux sont publiés)
                    slot[k] = {"v": x["v"], "d": di(x.get("d")), "u": x.get("u"), "n_conf": x.get("n_conf", 0), "restated": x.get("restated")}
    return out, titles, len(pubs)


def view(S, P, tau):
    """informations disponibles à la date tau (AAAAMMJJ) : comptes annuels publiés et cumuls intermédiaires publiés"""
    A = {m: {y: v for y, v in (S["ser"].get(m) or {}).items() if fin(v) and pubdate(S, y) <= tau} for m in MET}
    Pv = {}
    for fy, pers in (P or {}).items():
        for per, mets in pers.items():
            for m, x in mets.items():
                if x.get("d") and x["d"] <= tau:
                    Pv.setdefault(fy, {}).setdefault(per, {})[m] = x["v"]
    return A, Pv


# ------------------------------------------------------------------------------------------------------------- méthodes
def growth_med(series, L, n=4):
    gs = []
    for y in range(L - n + 1, L + 1):
        a, b = series.get(y), series.get(y - 1)
        if fin(a) and fin(b) and b > 0 and a > 0:
            gs.append(a / b - 1)
    return C.clamp(med(gs), -0.15, 0.25) if len(gs) >= 3 else None


def margin_med(A, m, L, n=3):
    ms = [A[m][y] / A["rev"][y] for y in range(L - n + 1, L + 1) if fin(A[m].get(y)) and fin(A["rev"].get(y)) and A["rev"][y] > 0]
    return med(ms) if len(ms) >= 2 else None


def share_med(A, Pv, m, per, N):
    """part habituelle du cumul de la période dans l'exercice (médiane des exercices antérieurs, au moins deux)"""
    sh = []
    for y in range(N - 6, N):
        a, p = A[m].get(y), (Pv.get(y, {}).get(per) or {}).get(m)
        if fin(a) and fin(p) and a > 0 and p > 0 and 0.03 <= p / a <= 1.5:
            sh.append(p / a)
    return med(sh) if len(sh) >= 2 else None


def ytd_pair(Pv, m, N, state):
    cur = (Pv.get(N, {}).get(state) or {}).get(m)
    prev = (Pv.get(N - 1, {}).get(state) or {}).get(m)
    return cur, prev


def candidates(S, A, Pv, N, state, glt):
    """prévisions candidates de l'exercice N (tous postes) et des exercices suivants : {(poste, horizon): {méthode: valeur}}"""
    L = N - 1
    out = {}
    rev_L = A["rev"].get(L)
    g = growth_med(A["rev"], L)
    # chiffre d'affaires de l'exercice N
    cr = {}
    if fin(rev_L):
        cr["naive"] = rev_L
        if g is not None:
            cr["drift"] = rev_L * (1 + g)
    if state:
        c, p = ytd_pair(Pv, "rev", N, state)
        if fin(c) and fin(p) and p > 0 and c > 0 and fin(rev_L) and rev_L > 0 and 0.4 <= c / p <= 2.5:
            cr["ytd_g"] = rev_L * c / p
        sh = share_med(A, Pv, "rev", state, N)
        if fin(c) and c > 0 and sh:
            cr["ytd_s"] = c / sh
    out[("rev", 1)] = cr
    rev_base = cr.get("drift", cr.get("naive"))
    for m in ("ebit", "ni"):
        cm = {}
        a_L = A[m].get(L)
        if fin(a_L):
            cm["naive"] = a_L
        mm = margin_med(A, m, L)
        if mm is not None and fin(rev_base):
            cm["margin"] = rev_base * mm
        if state and fin(a_L):
            c, p = ytd_pair(Pv, m, N, state)
            if fin(c) and fin(p):
                cm["ytd_d"] = a_L + (c - p)
            sh = share_med(A, Pv, m, state, N)
            if fin(c) and sh and c > 0:
                cm["ytd_s"] = c / sh
        out[(m, 1)] = cm
    # exercices suivants (horizon 2 à 5, comptés depuis le dernier exercice publié), à partir de la prévision de N retenue plus tard
    out["_g"] = g
    out["_glt"] = glt
    out["_mm"] = {m: margin_med(A, m, L, n=5) for m in ("ebit", "ni")}
    return out


def future(base, h, g, glt, mm, m0):
    """trajectoire au-delà de l'exercice N : chiffre d'affaires selon la tendance de la société rapprochée de la croissance de long
    terme ; marges ramenées en trois ans vers leur médiane des 5 derniers exercices"""
    rev = {"naive": {}, "trend": {}}
    r = base.get("rev")
    if not fin(r):
        return {}
    gg = (0.5 * g + 0.5 * glt) if g is not None else glt
    for k in range(2, h + 1):
        rev["naive"][k] = r
        rev["trend"][k] = r * (1 + gg) ** (k - 1)
    res = {("rev", k): {"naive": rev["naive"][k], "trend": rev["trend"][k]} for k in range(2, h + 1)}
    for m in ("ebit", "ni"):
        b = base.get(m)
        if not fin(b):
            continue
        mN = b / r if r else None
        for k in range(2, h + 1):
            d_ = {"naive": b}
            if mN is not None:
                tgt = mm.get(m) if mm.get(m) is not None else mN
                w = min(1.0, (k - 1) / 3)
                d_["trend"] = rev["trend"][k] * (mN + (tgt - mN) * w)
            res[(m, k)] = d_
    return res


def periodic_fc(A, Pv, N, state, fcN):
    """cumuls attendus des périodes de l'exercice N pas encore publiées : même période de l'exercice précédent, ajustée de la
    variation prévue pour l'exercice (proportionnelle pour le chiffre d'affaires, au prorata du temps pour les résultats)"""
    out = {}
    later = [p for p in PERS if not state or PERS.index(p) > PERS.index(state)]
    L = N - 1
    for p in later:
        for m in MET:
            f, a_L = fcN.get(m), A[m].get(L)
            prev = (Pv.get(L, {}).get(p) or {}).get(m)
            v = None
            if fin(f) and fin(a_L) and fin(prev):
                v = prev * f / a_L if (m == "rev" and a_L > 0) else prev + (f - a_L) * PER_M[p] / 12
            elif fin(f):
                sh = share_med(A, Pv, m, p, N)
                v = f * sh if sh else None
            if fin(v):
                out[(m, p)] = v
    return out


# ------------------------------------------------------------------------------------------------------------- validation
def scale_of(m, A, L, f=None):
    """échelle des erreurs propre à la société : variation annuelle moyenne (en valeur absolue) du poste sur les 5 derniers
    exercices publiés, au moins 1 % du niveau du poste et 0,5 % du chiffre d'affaires. Une société aux résultats stables a ainsi
    une fourchette étroite, une société aux résultats heurtés une fourchette large (erreurs comparables d'une société à l'autre)."""
    ser = A[m]
    d = [abs(ser[y] - ser[y - 1]) for y in range(L - 4, L + 1) if fin(ser.get(y)) and fin(ser.get(y - 1))]
    if len(d) < 2:
        return None
    a, r = ser.get(L), A["rev"].get(L)
    floor = max(0.01 * abs(a) if fin(a) else 0, 0.005 * r if fin(r) and r > 0 else 0)
    s_ = max(sum(d) / len(d), floor)
    return s_ or None


def backtest(I, P, today_i, glt_of):
    """prévisions refaites à chaque date de publication passée, avec les seules informations de la date ; erreurs normalisées
    par méthode, poste, état d'information ou horizon, et type d'entreprise (banque / autre)"""
    cases = []
    for t, S in I["S"].items():
        Pt = P.get(t) or {}
        rev = S["ser"].get("rev") or {}
        yrs = sorted(y for y in rev if fin(rev[y]))
        if len(yrs) < 5:
            continue
        grp = "banque" if S.get("fin") else "autre"
        glt = glt_of(S)
        for N in range(max(yrs[0] + 4, 2008), (today_i // 10000) + 1):
            origins = [(pubdate(S, N - 1), None)]
            for p in PERS:
                x = (Pt.get(N, {}).get(p) or {})
                ds = [v["d"] for v in x.values() if v.get("d")]
                if ds:
                    origins.append((min(ds), p))
            for tau, st_ in origins:
                if tau > today_i:
                    continue
                A, Pv = view(S, Pt, tau)
                if not fin(A["rev"].get(N - 1)) or any(y >= N for y in A["rev"]):
                    continue  # (exercice N-1 pas encore publié à la date, ou N déjà publié)
                cand = candidates(S, A, Pv, N, st_, glt)
                key_state = st_ or "aucune"
                for m in MET:
                    act = (S["ser"].get(m) or {}).get(N)
                    if not fin(act):
                        continue
                    sc = scale_of(m, A, N - 1)
                    for meth, f in cand.get((m, 1), {}).items():
                        if sc and fin(f):
                            cases.append({"t": t, "g": grp, "m": m, "k": "A:" + key_state, "meth": meth, "e": (act - f) / sc, "N": N,
                                          "r": max(-5.0, min(5.0, (act - f) / abs(act))) if act else None})
                # horizons 2 à 5, depuis la publication de l'exercice N-1 seulement
                if st_ is None:
                    base = {m: cand.get((m, 1), {}).get("naive") for m in MET}
                    fut = future(base, H_MAX, cand["_g"], glt, cand["_mm"], None)
                    for (m, k), d_ in fut.items():
                        act = (S["ser"].get(m) or {}).get(N + k - 1)
                        if not fin(act):
                            continue
                        sc = scale_of(m, A, N - 1)
                        for meth, f in d_.items():
                            if sc and fin(f):
                                cases.append({"t": t, "g": grp, "m": m, "k": f"H{k}", "meth": meth, "e": (act - f) / sc, "N": N + k - 1})
                # cumuls intermédiaires à venir dans l'exercice
                fcN = {m: (cand.get((m, 1), {}).get("naive")) for m in MET}
                for (m, p), f in periodic_fc(A, Pv, N, st_, fcN).items():
                    act = ((Pt.get(N, {}).get(p) or {}).get(m) or {}).get("v")
                    sc = scale_of(m, A, N - 1)
                    if fin(act) and sc:
                        sc_p = sc * PER_M[p] / 12
                        cases.append({"t": t, "g": grp, "m": m, "k": f"P:{p}:{key_state}", "meth": "naive", "e": (act - f) / sc_p, "N": N})
    return cases


def select(cases):
    """méthode retenue et quantiles d'erreur par cellule (poste, état ou horizon, type d'entreprise) ; repli sur toutes les
    entreprises si la cellule est trop petite"""
    cells = {}
    for c in cases:
        for g in (c["g"], "tous", "t:" + c["t"]):
            cells.setdefault((c["m"], c["k"], g), {}).setdefault(c["meth"], []).append(c)
    sel = {}
    for (m, k, g), meths in cells.items():
        stats = {}
        for meth, L in meths.items():
            ae = [abs(x["e"]) for x in L]
            stats[meth] = {"n": len(L), "mae": r3(med(ae)), "bias": r3(med([x["e"] for x in L]))}
        nv = stats.get("naive")
        best = "naive" if nv else min(stats, key=lambda z: stats[z]["mae"])
        for meth, s_ in stats.items():
            if meth == best or s_["n"] < MIN_CASES or not fin(s_["mae"]):
                continue
            if nv and fin(nv["mae"]) and s_["mae"] <= (1 - GAIN_MIN) * nv["mae"] and s_["mae"] < stats[best]["mae"]:
                best = meth
        E = [x["e"] for x in meths[best]]
        # couverture hors échantillon : quantiles calibrés sur les exercices jusqu'en 2019, testés sur 2020 et après
        early = [x["e"] for x in meths[best] if x["N"] <= 2019]
        late = [x["e"] for x in meths[best] if x["N"] >= 2020]
        cov = None
        if len(early) >= 15 and len(late) >= 10:
            lo_, hi_ = q(early, 0.1), q(early, 0.9)
            cov = round(sum(1 for e in late if lo_ <= e <= hi_) / len(late), 3)
        qm = {meth: {"n": len(L), "q10": r3(q([x["e"] for x in L], 0.1)), "q90": r3(q([x["e"] for x in L], 0.9))} for meth, L in meths.items()}
        sel[f"{m}|{k}|{g}"] = {"best": best, "n": len(E), "q10": r3(q(E, 0.1)), "q50": r3(q(E, 0.5)), "q90": r3(q(E, 0.9)), "cov": cov, "stats": stats, "qm": qm}
    return sel


def pick(c, cm, nmin=MIN_CASES, gain=GAIN_MIN, ct=None):
    """meilleure méthode calculable pour la société, dans l'ordre de la validation : d'abord ce que montre l'historique propre de la
    société (au moins 8 cas et 20 % d'erreur en moins que la prévision naïve), sinon la cellule de son type d'entreprise (au moins
    15 cas et 10 % d'erreur en moins) ; à défaut, la prévision naïve"""
    if not cm:
        return None
    if ct:
        stc = ct.get("stats") or {}
        nvc = (stc.get("naive") or {}).get("mae")
        okc = [mm for mm, x in stc.items() if mm in cm and mm != "naive" and x["n"] >= CO_MIN and fin(x.get("mae")) and fin(nvc) and x["mae"] <= (1 - CO_GAIN) * nvc]
        if okc:
            return min(okc, key=lambda mm: stc[mm]["mae"])
    if not c:
        return "naive" if "naive" in cm else next(iter(cm))
    st_ = c.get("stats") or {}
    nv = (st_.get("naive") or {}).get("mae")
    ok = [mm for mm, x in st_.items() if mm in cm and mm != "naive" and x["n"] >= nmin and fin(x.get("mae")) and fin(nv) and x["mae"] <= (1 - gain) * nv]
    if ok:
        return min(ok, key=lambda mm: st_[mm]["mae"])
    if "naive" in cm:
        return "naive"
    return min((mm for mm in cm if mm in st_ and fin(st_[mm].get("mae"))), key=lambda mm: st_[mm]["mae"], default=next(iter(cm)))


def path_method(sel, m, g, t=None):
    """méthode des exercices suivants, la même pour tous les horizons : celle dont l'erreur médiane, additionnée sur les horizons
    2 à 5, est la plus faible, si elle bat la prévision naïve d'au moins 10 % (sinon la prévision naïve) ; l'historique propre
    de la société l'emporte s'il compte au moins 2 cas à chaque horizon et montre 20 % d'erreur en moins"""
    if t:
        tc, nc = {}, {}
        for k in range(2, H_MAX + 1):
            for meth, x in ((sel.get(f"{m}|H{k}|t:{t}") or {}).get("stats") or {}).items():
                if fin(x.get("mae")) and x["n"] >= 2:
                    tc[meth] = tc.get(meth, 0) + x["mae"]
                    nc[meth] = nc.get(meth, 0) + 1
        fc_ = [mm for mm in tc if nc[mm] == H_MAX - 1]
        if "naive" in fc_ and len(fc_) > 1:
            bc = min(fc_, key=lambda mm: tc[mm])
            if bc != "naive" and tc[bc] <= (1 - CO_GAIN) * tc["naive"]:
                return bc
    tot, n = {}, {}
    for k in range(2, H_MAX + 1):
        c = sel.get(f"{m}|H{k}|{g}") or {}
        if not c or c.get("n", 0) < MIN_CASES:
            c = sel.get(f"{m}|H{k}|tous") or {}
        for meth, x in (c.get("stats") or {}).items():
            if fin(x.get("mae")):
                tot[meth] = tot.get(meth, 0) + x["mae"]
                n[meth] = n.get(meth, 0) + 1
    full = [mm for mm in tot if n[mm] == H_MAX - 1]
    if "naive" not in full:
        return "naive"
    best = min(full, key=lambda mm: tot[mm])
    return best if tot[best] <= (1 - GAIN_MIN) * tot["naive"] else "naive"


def cell_m(sel, m, k, g, meth):
    """cellule où la méthode retenue a assez de cas pour ses quantiles d'erreur (type d'entreprise, sinon toutes)"""
    for gg in (g, "tous"):
        c = sel.get(f"{m}|{k}|{gg}")
        if c and ((c.get("qm") or {}).get(meth) or {}).get("n", 0) >= MIN_CASES:
            return c["qm"][meth], gg
    return None, None


def cell(sel, m, k, g):
    """cellule de validation la plus précise disponible (type d'entreprise, sinon toutes)"""
    for gg in (g, "tous"):
        c = sel.get(f"{m}|{k}|{gg}")
        if c and c["n"] >= MIN_CASES:
            return c, gg
    c = sel.get(f"{m}|{k}|tous")
    return (c, "tous") if c else (None, None)


# ------------------------------------------------------------------------------------------------------------- prévision
def forecast(t, S, Pt, sel, today_i, glt):
    """prévision complète d'une société à la date du jour"""
    A, Pv = view(S, Pt, today_i)
    yrs = sorted(y for y in A["rev"] if fin(A["rev"][y]))
    if len(yrs) < 3:
        return None, "moins de trois exercices de chiffre d'affaires publiés"
    L = yrs[-1]
    N = L + 1
    state = next((p for p in reversed(PERS) if (Pv.get(N, {}).get(p) or {}).get("rev") is not None or (Pv.get(N, {}).get(p) or {}).get("ni") is not None), None)
    grp = "banque" if S.get("fin") else "autre"
    cand = candidates(S, A, Pv, N, state, glt)
    key_state = state or "aucune"
    rows = {}
    for m in MET:
        cm = cand.get((m, 1)) or {}
        if not cm:
            continue
        c, gg = cell(sel, m, "A:" + key_state, grp)
        # (l'historique propre de la société ne départage les méthodes que sans publication de l'exercice : dès qu'un cumul est
        # publié, la règle validée sur l'ensemble des sociétés s'applique, l'information de l'exercice primant)
        best = pick(c, cm, ct=sel.get(f"{m}|A:{key_state}|t:{t}") if key_state == "aucune" else None)
        f = cm[best]
        sc = scale_of(m, A, L)
        qq, gq = cell_m(sel, m, "A:" + key_state, grp, best)
        lo = hi = None
        if qq and sc and fin(qq["q10"]) and fin(qq["q90"]):
            lo, hi = f + qq["q10"] * sc, f + qq["q90"] * sc
        rows[(m, 1)] = {"fy": N, "v": f, "lo": lo, "hi": hi, "meth": best, "cell": f"A:{key_state}|{gq or gg}", "n": qq["n"] if qq else 0,
                        "alts": {k: r3(v) for k, v in cm.items()}}
    base = {m: rows[(m, 1)]["v"] for m in MET if (m, 1) in rows}
    fut = future(base, H_MAX, cand["_g"], glt, cand["_mm"], None)
    path = {m: path_method(sel, m, grp, t) for m in MET}
    for (m, k), d_ in fut.items():
        best = path[m] if path[m] in d_ else ("naive" if "naive" in d_ else next(iter(d_)))
        f = d_[best]
        sc = scale_of(m, A, L)
        qq, gq = cell_m(sel, m, f"H{k}", grp, best)
        lo = hi = None
        if qq and sc and fin(qq["q10"]):
            lo, hi = f + qq["q10"] * sc, f + qq["q90"] * sc
        rows[(m, k)] = {"fy": N + k - 1, "v": f, "lo": lo, "hi": hi, "meth": best, "cell": f"H{k}|{gq or grp}", "n": qq["n"] if qq else 0}
    # cumuls intermédiaires attendus de l'exercice en cours
    per_rows = {}
    for (m, p), f in periodic_fc(A, Pv, N, state, base).items():
        qq, gq = cell_m(sel, m, f"P:{p}:{key_state}", grp, "naive")
        sc = scale_of(m, A, L)
        sc_p = sc * PER_M[p] / 12 if sc else None
        lo = hi = None
        if qq and sc_p and fin(qq["q10"]):
            lo, hi = f + qq["q10"] * sc_p, f + qq["q90"] * sc_p
        per_rows[(m, p)] = {"fy": N, "per": p, "v": f, "lo": lo, "hi": hi, "n": qq["n"] if qq else 0}
    return {"L": L, "N": N, "state": state, "grp": grp, "rows": rows, "per": per_rows, "g": cand["_g"], "mm": cand["_mm"]}, None


def pack(F, S):
    """forme publiée d'une prévision (millions de FCFA ; bénéfice par action en FCFA sur la base du nombre d'actions actuel)"""
    sh = S.get("shares_now")
    out = {"fy_last": F["L"], "fy": F["N"], "state": F["state"], "grp": F["grp"], "annual": [], "periods": []}
    for k in range(1, H_MAX + 1):
        row = {"fy": F["N"] + k - 1, "h": k}
        for m in MET:
            x = F["rows"].get((m, k))
            if x:
                row[m] = {"v": r3(x["v"]), "lo": r3(x["lo"]), "hi": r3(x["hi"]), "meth": x["meth"], "n": x["n"], **({"alts": x["alts"]} if x.get("alts") else {})}
        if row.get("ni") and sh:
            row["eps"] = {kk: (r3(row["ni"][kk] * 1e6 / sh) if fin(row["ni"].get(kk)) else None) for kk in ("v", "lo", "hi")}
        if row.get("rev") and fin(row["rev"]["v"]) and row["rev"]["v"] > 0:
            for m, key in (("ni", "nm"), ("ebit", "om")):
                if row.get(m) and fin(row[m]["v"]):
                    row[key] = r3(row[m]["v"] / row["rev"]["v"])
        out["annual"].append(row)
    for (m, p), x in sorted(F["per"].items(), key=lambda z: (PERS.index(z[0][1]), MET.index(z[0][0]))):
        out["periods"].append({"fy": x["fy"], "per": p, "m": m, "v": r3(x["v"]), "lo": r3(x["lo"]), "hi": r3(x["hi"]), "n": x["n"]})
    return out


def published(S, Pt, titles):
    """résultats publiés : 8 derniers exercices et cumuls intermédiaires des 4 derniers exercices, avec leur document et sa date"""
    yrs = sorted(y for y in (S["ser"].get("rev") or {}) if fin(S["ser"]["rev"][y]))[-8:]
    ann = []
    for y in yrs:
        row = {"fy": y, "d": (S.get("pub") or {}).get(y), "ver": y in (S.get("verified") or set())}
        for m in MET:
            v = (S["ser"].get(m) or {}).get(y)
            if fin(v):
                row[m] = r3(v)
        e = (S["ser"].get("eps") or {}).get(y)
        if fin(e):
            row["eps"] = r3(e)
        ann.append(row)
    per = []
    for fy in sorted(Pt or {})[-4:]:
        for p in PERS:
            x = (Pt[fy].get(p) or {})
            if not x:
                continue
            row = {"fy": fy, "per": p}
            src = None
            for m in MET:
                if m in x:
                    row[m] = r3(x[m]["v"])
                    row[m + "_c"] = x[m].get("n_conf", 0)
                    if x[m].get("restated") is not None:
                        row[m + "_r"] = r3(x[m]["restated"])
                    src = src or x[m].get("u")
            ti, d = titles.get(src, (None, None))
            row["src"] = ti
            row["d"] = di(d)
            per.append(row)
    return {"annual": ann, "periods": per}


# ------------------------------------------------------------------------------------------------------------- événements
def new_docs(I, t, since, until):
    """documents publiés par la société (ou la concernant) depuis la dernière version"""
    out = []
    for r in I["docs"]:
        if len(r) >= 7 and r[1] == t and r[3] and since < r[3] <= until and r[0] in EV_W:
            out.append({"k": r[0], "kn": EV_W[r[0]][0], "ti": r[4], "d": r[3]})
    return sorted(out, key=lambda e: e["d"])


NEG_KW = {"perte", "avertissement", "incendie", "grève", "suspension de l'activité", "redressement", "dépréciation", "arrêt", "sanction"}
# événements de marché sans effet direct sur le résultat (le bénéfice par action suit mécaniquement le nombre d'actions)
NEUTRAL = ("fractionnement", "regroupement", "division du nominal", "actions nouvelles pour", "action nouvelle pour", "actions gratuites",
           "première cotation", "premiere cotation", "admission", "suspension de la cotation", "levée de suspension", "levee de suspension",
           "reprise de la cotation", "reprise de cotation", "changement de symbole", "valeur théorique", "valeur theorique")


def kw_hits(title):
    txt = (title or "").lower()
    return [kw[0] for kw in WARN_KW if any(k in txt for k in kw)]


def event_effects(I, cases):
    """portée mesurée de chaque nature de document sur le résultat net : pour chaque société et exercice, erreur de la prévision
    naïve du résultat net faite à la publication de l'exercice précédent ; écart médian entre les exercices au cours desquels un
    document de cette nature a été publié et les autres (en part du résultat net). Les documents dont l'intitulé signale un
    événement exceptionnel forment une catégorie à part."""
    err = {(c["t"], c["N"]): abs(c["r"]) for c in cases if c["m"] == "ni" and c["k"] == "A:aucune" and c["meth"] == "naive" and c.get("r") is not None}
    seen = {}
    for r in I["docs"]:
        if len(r) < 7 or r[0] not in EV_W or not r[3] or not r[1]:
            continue
        S = I["S"].get(r[1])
        if not S:
            continue
        for N in (r[3] // 10000, r[3] // 10000 + 1):
            if (r[1], N) in err and pubdate(S, N - 1) < r[3] <= pubdate(S, N):
                seen.setdefault((r[1], N), set()).add(r[0])
                if kw_hits(r[4]):
                    seen[(r[1], N)].add("kw")
    # comparaison au sein de chaque société (exercices avec / sans document de cette nature), puis médiane entre sociétés : une
    # société qui publie beaucoup n'est pas confondue avec une société aux résultats plus heurtés
    out = {}
    base_all = list(err.values())
    for k in list(EV_W) + ["kw"]:
        diffs, nw = [], 0
        for t in {key[0] for key in err}:
            w = [e for key, e in err.items() if key[0] == t and k in seen.get(key, ())]
            wo = [e for key, e in err.items() if key[0] == t and k not in seen.get(key, ())]
            nw += len(w)
            if len(w) >= 1 and len(wo) >= 2:
                diffs.append(med(w) - med(wo))
        if len(diffs) >= 5:
            out[k] = {"n": nw, "co": len(diffs), "imp": r3(max(0.0, med(diffs))), "d": r3(med(diffs))}
    out["_base"] = r3(med(base_all))
    return out


def assess(evs, effects):
    """portée possible de chaque document sur le résultat net prévu (déclencheur d'analyse, pas une variation automatique) :
    les publications de résultats sont prises en compte directement par la mise à jour des chiffres ; les autres documents
    reçoivent la portée mesurée de leur nature (et des termes qui signalent un événement exceptionnel)"""
    out = []
    for e in evs:
        hits = kw_hits(e["ti"])
        if e["k"] in ("res", "ef", "ra"):
            out.append({**e, "imp": None, "why": "publication de résultats : prise en compte directement par la mise à jour des chiffres", "hits": hits, "neg": False})
            continue
        if any(k in (e["ti"] or "").lower() for k in NEUTRAL):
            out.append({**e, "imp": 0.0, "why": "événement de marché sans effet direct sur le résultat (le bénéfice par action suit mécaniquement le nombre d'actions)",
                        "hits": [], "neg": False})
            continue
        ek = effects.get(e["k"]) or {}
        imp = ek.get("imp") or 0.0
        why = [f"portée mesurée des documents « {EV_W[e['k']][0].lower()} » : {imp:.0%} du résultat net" + (f" ({ek['n']} exercices)" if ek.get("n") else "")]
        if hits:
            kk = effects.get("kw") or {}
            imp = max(imp, kk.get("imp") or 0.0)
            why.append("termes signalant un événement possiblement important : " + ", ".join(hits) + (f" (portée mesurée {kk.get('imp', 0):.0%})" if kk else ""))
        out.append({**e, "imp": imp, "why": "; ".join(why), "hits": hits, "neg": any(h in NEG_KW for h in hits)})
    return out


# ------------------------------------------------------------------------------------------------------------- exécution
def restore_if_needed(Q, extra, log):
    if not extra:
        return
    B = os.path.join(extra, "qlabp")
    sq = (jload(os.path.join(Q, "state.json"), {}) or {}).get("seq", -1)
    sb = (jload(os.path.join(B, "state.json"), {}) or {}).get("seq", -1)
    if sb > sq and os.path.isdir(B):
        if os.path.isdir(Q):
            shutil.rmtree(Q)
        shutil.copytree(B, Q)
        log(f"QLAB Prévisions : dossier restauré depuis la sauvegarde (exécution n° {sb})")


def backup(Q, extra):
    if not extra:
        return
    B = os.path.join(extra, "qlabp")
    tmp = B + ".tmp"
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    shutil.copytree(Q, tmp)
    if os.path.isdir(B):
        shutil.rmtree(B)
    os.replace(tmp, B)


def next_expected(S, Pt, N, state, today):
    """prochaine publication attendue (date médiane des publications passées de la même période) et retard éventuel"""
    order = list(PERS) + ["A"]
    nxt = "A"
    for p in order[(order.index(state) + 1) if state else 0:]:
        if p == "A" or any((Pt.get(y, {}).get(p) or {}) for y in range(N - 4, N)):
            nxt = p
            break
    if nxt == "A":
        ds = [(S.get("pub") or {}).get(y) for y in range(N - 6, N)]
        ds = [d for d in ds if d]
        md = [(d // 100 % 100, d % 100) for d in ds]
        yr = N + 1
    else:
        md = []
        for y in range(N - 6, N):
            x = (Pt.get(y, {}).get(nxt) or {})
            d = min((v["d"] for v in x.values() if v.get("d")), default=None)
            if d and d // 10000 == y:
                md.append((d // 100 % 100, d % 100))
        yr = N
    if not md:
        return {"per": nxt, "fy": N, "d": None, "late": None}
    mo = sorted(md)[len(md) // 2]
    try:
        d0 = dt.date(yr, mo[0], min(mo[1], 28))
    except ValueError:
        return {"per": nxt, "fy": N, "d": None, "late": None}
    late = (today - d0).days
    return {"per": nxt, "fy": N, "d": C.dint(d0), "late": late if late > 45 else None}


def run(out, extra=None, log=print, comptes=None, today=None, now=None):
    t0 = time.time()
    today = today or dt.date.today()
    now = now or dt.datetime.now(dt.timezone.utc)
    import qlab
    Q = os.path.join(out, "qlabp")
    os.makedirs(Q, exist_ok=True)
    restore_if_needed(Q, extra, log)
    sp = os.path.join(Q, "state.json")
    st = jload(sp, {}) or {}
    st["seq"] = st.get("seq", 0) + 1
    I, M = qlab.load_inputs(out, today)
    P, titles, n_pub = periodic_data(comptes, I, log)
    today_i = C.dint(today)
    glt_of = lambda S: (M.get("glt") or {}).get(S.get("cty")) or (M.get("glt") or {}).get("CI") or 0.04  # noqa: E731
    cases = backtest(I, P, today_i, glt_of)
    sel = select(cases)
    effects = event_effects(I, cases)
    sel_pub = {k: {kk: vv for kk, vv in v.items() if kk != "qm"} for k, v in sel.items() if "|t:" not in k}
    n_new = {"initiale": 0, "publication": 0, "exceptionnelle": 0, "trimestrielle": 0, "methode": 0}
    rows, fails, ev_tot = [], [], 0
    q_start = C.dint(dt.date(today.year, 3 * ((today.month - 1) // 3) + 1, 1))
    for t, S in sorted(I["S"].items()):
        Pt = P.get(t) or {}
        cp = os.path.join(Q, f"{t}.json")
        comp = jload(cp, {}) or {"t": t, "name": S.get("name"), "vers": []}
        try:
            F, why = forecast(t, S, Pt, sel, today_i, glt_of(S))
        except Exception as e:  # noqa: BLE001
            F, why = None, f"erreur de calcul ({type(e).__name__}: {e})"
        if not F:
            fails.append({"t": t, "n": S.get("name"), "why": why})
            comp["fail"] = {"d": today_i, "why": why}
            jdump(comp, cp)
            continue
        comp.pop("fail", None)
        fc = pack(F, S)
        inputs = {"ann": {m: sorted((y, v) for y, v in (S["ser"].get(m) or {}).items() if fin(v) and pubdate(S, y) <= today_i) for m in MET},
                  "per": {str(fy): {p: {m: x["v"] for m, x in mets.items()} for p, mets in pers.items()} for fy, pers in Pt.items()
                          if any(x.get("d") and x["d"] <= today_i for mets in pers.values() for x in mets.values())},
                  "sh": S.get("shares_now")}
        dig = digest(inputs)[:16]
        cur = comp.get("cur")
        vtype, reason, evs_a, exc = None, None, [], None
        if not cur:
            vtype, reason = "initiale", "première prévision de la société par le moteur QLAB Prévisions"
        elif cur.get("engine") != ENGINE:
            vtype, reason = "methode", f"nouvelle méthode du moteur ({cur.get('engine')} → {ENGINE})"
        elif cur.get("inputs") != dig:
            vtype, reason = "publication", "résultats publiés nouvellement intégrés (comptes annuels ou cumul intermédiaire) : mise à jour obligatoire"
        else:
            evs = new_docs(I, t, cur.get("d_docs") or cur["date"], today_i)
            if evs:
                evs_a = assess(evs, effects)
                ev_tot += len(evs_a)
                strong = [e for e in evs_a if e["imp"] is not None and e["imp"] >= MAT_NI]
                batch = sum(e["imp"] for e in evs_a if e["imp"] is not None)
                # (cumul de tous les documents examinés depuis la version en vigueur : un document n'est compté qu'une fois)
                acc = batch + sum(x.get("batch", 0) for x in (comp.get("events") or []) if x["d"] > cur["date"])
                neg = any(e["neg"] for e in evs_a)
                comp.setdefault("events", []).append({"d": today_i, "docs": [{k: e[k] for k in ("kn", "ti", "d", "imp", "why")} for e in evs_a][:12],
                                                       "batch": round(batch, 4), "acc": round(acc, 4), "dec": None})
                if strong or acc >= MAT_NI:
                    vtype = "exceptionnelle"
                    exc = {"imp": max([acc] + [e["imp"] for e in strong]), "neg": neg}
                    reason = ("document(s) pouvant modifier le résultat net prévu d'au moins 5 % : " + "; ".join(e["ti"] for e in strong)[:300] if strong
                              else f"accumulation de documents de faible portée depuis la dernière version (portée cumulée estimée {acc:.0%})")
                    comp["events"][-1]["dec"] = "révision exceptionnelle : prévisions recalculées, fourchettes élargies tant que l'effet n'est pas mesuré dans des chiffres publiés"
                else:
                    comp["events"][-1]["dec"] = f"portée estimée inférieure au seuil de {MAT_NI:.0%} du résultat net prévu (cumul {acc:.0%}) : prévision maintenue, documents conservés pour le cumul"
                comp["events"] = comp["events"][-40:]
            if not vtype and (cur.get("date") or 0) < q_start:
                vtype, reason = "trimestrielle", "mise à jour trimestrielle obligatoire"
        widen = None
        if exc:
            # la prévision centrale reste celle des chiffres publiés (aucun montant inventé) ; la fourchette du résultat net (et du
            # bénéfice par action) est élargie de la portée mesurée, du côté de la baisse seulement si les documents l'indiquent
            widen = {"imp": round(exc["imp"], 4), "neg": exc["neg"]}
            for row in fc["annual"]:
                x = row.get("ni")
                if x and fin(x.get("v")) and fin(x.get("lo")) and fin(x.get("hi")):
                    d_ = exc["imp"] * max(abs(x["v"]), 1.0)
                    x["lo"] = r3(x["lo"] - d_ * (1.5 if exc["neg"] else 1.0))
                    x["hi"] = r3(x["hi"] + (0 if exc["neg"] else d_))
                    if row.get("eps") and S.get("shares_now"):
                        row["eps"] = {kk: (r3(x[kk] * 1e6 / S["shares_now"]) if fin(x.get(kk)) else None) for kk in ("v", "lo", "hi")}
        if vtype:
            prev = cur
            rec = {"id": f"{t}-P{today_i}-{vtype[0].upper()}", "t": t, "type": vtype, "reason": reason, "date": today_i, "d_docs": today_i,
                   "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "engine": ENGINE, "inputs": dig, "prev": prev.get("hash") if prev else None,
                   "fc": fc, "widen": widen}
            rec["hash"] = digest({k: v for k, v in rec.items() if k != "hash"})
            hp = os.path.join(Q, "hist", f"{t}.json")
            hist = jload(hp, {"t": t, "v": []}) or {"t": t, "v": []}
            if not hist["v"] or hist["v"][-1]["id"] != rec["id"]:
                hist["v"].append(rec)
                jdump(hist, hp)
                comp["cur"] = rec
                comp["vers"] = (comp.get("vers") or []) + [{"id": rec["id"], "type": vtype, "date": today_i, "reason": reason,
                                                             "fy": fc["fy"], "state": fc["state"],
                                                             "ni": (fc["annual"][0].get("ni") or {}).get("v"), "rev": (fc["annual"][0].get("rev") or {}).get("v")}]
                n_new[vtype] += 1
        elif cur:
            comp["cur"]["d_docs"] = today_i
        # erreurs des versions passées dès que les résultats réels sont publiés
        hist = jload(os.path.join(Q, "hist", f"{t}.json"), {"v": []}) or {"v": []}
        errs = []
        for v in hist["v"]:
            for row in v["fc"]["annual"]:
                for m in MET:
                    x = row.get(m)
                    act = (S["ser"].get(m) or {}).get(row["fy"])
                    if x and fin(x.get("v")) and fin(act) and pubdate(S, row["fy"]) > v["date"]:
                        errs.append({"ver": v["id"], "d": v["date"], "fy": row["fy"], "h": row["h"], "m": m, "f": x["v"], "a": r3(act),
                                     "e": r3((act - x["v"]) / (abs(act) or 1)), "in": bool(fin(x.get("lo")) and x["lo"] <= act <= x["hi"])})
            for x in v["fc"]["periods"]:
                act = ((Pt.get(x["fy"], {}).get(x["per"]) or {}).get(x["m"]) or {}).get("v")
                if fin(act) and fin(x.get("v")):
                    errs.append({"ver": v["id"], "d": v["date"], "fy": x["fy"], "per": x["per"], "m": x["m"], "f": x["v"], "a": r3(act),
                                 "e": r3((act - x["v"]) / (abs(act) or 1)), "in": bool(fin(x.get("lo")) and x["lo"] <= act <= x["hi"])})
        comp["errors"] = errs[-200:]
        comp["name"] = S.get("name")
        comp["pub"] = published(S, Pt, titles)
        comp["next"] = next_expected(S, Pt, F["N"], F["state"], today)
        alerts = []
        if comp["next"].get("late"):
            alerts.append(f"publication attendue ({PER_N[comp['next']['per']]} {comp['next']['fy']}) en retard de {comp['next']['late']} jours : les prévisions reposent sur des données anciennes")
        if not Pt:
            alerts.append("aucune publication intermédiaire lue pour cette société : prévisions fondées sur les seuls comptes annuels")
        comp["alerts"] = alerts
        comp["status"] = {"d": today_i}
        jdump(comp, cp)
        a1 = comp["cur"]["fc"]["annual"][0]
        rows.append({"t": t, "n": S.get("name"), "grp": F["grp"], "fy": a1["fy"], "state": comp["cur"]["fc"]["state"],
                     "rev": (a1.get("rev") or {}).get("v"), "ni": (a1.get("ni") or {}).get("v"), "ni_lo": (a1.get("ni") or {}).get("lo"),
                     "ni_hi": (a1.get("ni") or {}).get("hi"), "eps": (a1.get("eps") or {}).get("v"), "ver": comp["cur"]["id"], "vtype": comp["cur"]["type"],
                     "vdate": comp["cur"]["date"], "next": comp["next"].get("d"), "late": comp["next"].get("late"), "n_per": sum(len(v) for v in Pt.values())})
    # erreurs mesurées de toutes les versions (suivi des performances par horizon et type d'entreprise)
    live = {}
    for r in rows:
        comp = jload(os.path.join(Q, f"{r['t']}.json"), {}) or {}
        for e in comp.get("errors") or []:
            k = f"{e['m']}|{'H' + str(e['h']) if e.get('h') else 'P:' + e.get('per', '')}|{r['grp']}"
            live.setdefault(k, []).append(e)
    live_s = {k: {"n": len(L), "bias": r3(med([x["e"] for x in L])), "mae": r3(med([abs(x["e"]) for x in L])),
                  "cover": round(sum(1 for x in L if x["in"]) / len(L), 3)} for k, L in live.items()}
    idx = {"engine": ENGINE, "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "date": today_i, "rows": rows, "fails": fails, "mat_ni": MAT_NI,
           "sel": sel_pub, "effects": effects, "bt_n": len(cases), "n_pub": n_pub, "n_per_companies": len(P), "live": live_s, "new": n_new}
    jdump(idx, os.path.join(Q, "index.json"))
    st.pop("lock", None)
    st["last"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    jdump(st, sp)
    backup(Q, extra)
    log(f"QLAB Prévisions : {len(rows)} sociétés ; {n_pub} publications intermédiaires lues, {len(P)} sociétés couvertes ; "
        f"{len(cases)} prévisions passées refaites pour la validation ; versions : " + ", ".join(f"{v} {k}" for k, v in n_new.items() if v)
        + f" ; {ev_tot} documents examinés ; {len(fails)} sans prévision ; {time.time() - t0:.0f} s")
    return idx
