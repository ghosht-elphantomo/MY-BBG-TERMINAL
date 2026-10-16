"""QLAB — validation historique « point-in-time » du moteur de valorisation.

Chaque année depuis 2012, chaque société est réévaluée à la date où ses comptes annuels de l'exercice précédent ont été publiés
(document de l'index de la BRVM ; à défaut le 30 juin), avec les seules données disponibles à cette date : exercices publiés,
dividendes annoncés, cours, multiples et bêta mesurés jusqu'à cette date, paramètres de marché de la date. Puis on observe :
  - le résultat net effectivement publié l'exercice suivant (erreur de prévision, comparaison à la prévision naïve, calibration
    des intervalles à 80 %) ;
  - le rendement total du titre (cours + dividendes versés) sur 1 an et 3 ans, comparé à la moyenne des titres évalués à la même
    date (pouvoir de classement de l'écart valeur / cours, par modèle et pour la synthèse) ;
  - la vitesse à laquelle l'écart entre cours et valeur estimée se réduit (erreur de valorisation ≠ erreur de prévision du cours).
Limites (affichées) : voir LIMITS.
"""
import datetime as dt
import math
import time

import qlab_core as C

LIMITS = [
    "Biais du survivant : seules les sociétés cotées aujourd'hui sont testées ; les sociétés radiées de la cote ne figurent pas dans les données.",
    "Taux sans risque : les courbes des emprunts d'État ne sont disponibles que depuis 2025 ; la plus ancienne courbe disponible est utilisée pour les dates antérieures. "
    "Le niveau du rendement exigé suit en revanche le marché de chaque date (rendement du dividende agrégé).",
    "La croissance de long terme utilisée pour mesurer le rendement exigé du marché est celle d'aujourd'hui.",
    "Les comptes historiques ont pu être relus ou corrigés après leur publication ; les données utilisées sont celles connues aujourd'hui pour chaque exercice publié.",
    "Date de publication des comptes : celle du document correspondant de la BRVM lorsqu'il est connu, sinon le 30 juin de l'année suivant l'exercice.",
    "Synthèse simplifiée : médiane pondérée des valeurs centrales des modèles, sans simulation de Monte-Carlo (temps de calcul).",
    "Rendements avant frais de transaction et impôts ; les cours de titres peu échangés peuvent ne pas être négociables.",
    "Fenêtres de 3 ans qui se chevauchent : les observations ne sont pas indépendantes ; peu de sociétés et peu d'années : la validation reste limitée.",
    "Un résultat passé ne garantit pas les performances futures.",
]


def tr_window(S, d0, d1, today):
    """rendement total entre deux dates (cours + dividendes ordinaires et exceptionnels versés dans la fenêtre), base de la date d0"""
    V0 = C.asof_view(S, d0, today, full=False)
    V1 = C.asof_view(S, d1, today, full=False)
    if not (C.fin(V0["price"]) and C.fin(V1["price"]) and V0["price"] > 0):
        return None
    if V1["pdate"] is None or V1["pdate"] < C.dint(C.ymd(d1) - dt.timedelta(days=92)):  # cours de fin trop ancien (plus de 3 mois)
        return None
    f0 = V0["split_f"]
    p1 = V1["price"] * f0 / V1["split_f"]
    divs = 0.0
    for r in S["drows"]:
        pay = int(str(r.get("pay") or r.get("det") or "0").replace("-", "")[:8] or 0)
        if d0 < pay <= d1:
            divs += r["dps"] * f0
    return (p1 + divs) / V0["price"] - 1


def add_years(d, n):
    return d + n * 10000


def run(I, M, note=print, deadline=None, y0=2012):
    t0 = time.time()
    today = I["today_i"]
    arch_of = {t: S["arch"] for t, S in I["S"].items()}
    obs = []
    years = list(range(y0, I["today"].year))
    for y in years:
        if deadline and time.time() > deadline:
            note(f"validation historique interrompue en {y} (temps imparti)")
            break
        d_mkt = y * 10000 + 630
        Mt = C.market_params(I, I["today"], asof=dt.date(y, 6, 30), series=M["ke_series"])
        Mt["idx"] = M["idx"]
        Mt["beta_prior"], _ = C.beta_prior(I, M["idx"], d_mkt, today)
        Mt["m_pers"], Mt["m_pers_n"] = C.margin_persistence(I, d_mkt)
        Mt["m_pers_raw"] = (I.get("_mp_raw") or {}).get(d_mkt)
        peers = C.peer_table(I, today, d_mkt, arch_of)
        for t, S in I["S"].items():
            pub = (S.get("pub") or {}).get(y - 1)
            d_eval = pub if (pub and y * 10000 + 101 <= pub <= d_mkt) else d_mkt
            try:
                A = C.analyze(t, I, Mt, peers, date=d_eval, mc=False)
            except Exception as e:  # noqa: BLE001
                note(f"validation {t} {y} : {type(e).__name__}: {e}")
                continue
            if not A.get("ok") or not C.fin(A.get("price")) or not C.fin(A.get("central")):
                continue
            if A["fy"] is None or A["fy"] < y - 2:
                continue
            o = {"t": t, "y": y, "d": d_eval, "fy": A["fy"], "p": A["price"], "v": A["central"], "mods": {m: A["mods"][m]["v"] for m in A["mods"]},
                 "arch": arch_of[t], "sf": A.get("split_f") or 1.0}
            for h in (1, 3):
                d1 = add_years(d_eval, h)
                if d1 <= today:
                    o[f"tr{h}"] = tr_window(S, d_eval, d1, today)
            nxt = S["ser"]["ni"].get(A["fy"] + 1)
            if C.fin(nxt) and C.fin(A.get("f_ni")):
                o["ni_act"], o["ni_f"], o["ni_lo"], o["ni_hi"], o["ni0"] = nxt, A["f_ni"], A["f_lo"], A["f_hi"], A["ni0"]
                # chaque méthode de prévision, séparément (mêmes données que la prévision retenue)
                ser = {y: v for y, v in S["ser"]["ni"].items() if y <= A["fy"]}
                ys_ = C._run(ser)
                xs = [ser[y] for y in ys_]
                eq = {y: v for y, v in S["ser"]["eq"].items() if y <= A["fy"]}
                o["fm"] = {m: C._fc_one(m, xs, ys_, eq) for m in C.FC_ORDER} if len(xs) >= 2 else {}
            obs.append(o)
    # rendements relatifs : écart à la moyenne des titres évalués la même année
    for h in (1, 3):
        by = {}
        for o in obs:
            if C.fin(o.get(f"tr{h}")):
                by.setdefault(o["y"], []).append(o[f"tr{h}"])
        for o in obs:
            xs = by.get(o["y"]) or []
            if C.fin(o.get(f"tr{h}")) and len(xs) >= 8:
                o[f"ex{h}"] = o[f"tr{h}"] - sum(xs) / len(xs)
    res = {"ts": dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%SZ"), "n": len(obs), "years": [years[0], years[-1]] if years else None, "lim": LIMITS}

    def ic_block(get_v, h):
        """pouvoir de classement : corrélation de rang, par année, entre log(valeur / cours) et le rendement relatif ultérieur"""
        per_year, all_x, all_y = [], [], []
        for y in sorted(set(o["y"] for o in obs)):
            xs, ys = [], []
            for o in obs:
                v = get_v(o)
                if o["y"] == y and C.fin(v) and v > 0 and C.fin(o.get(f"ex{h}")):
                    xs.append(math.log(v / o["p"]))
                    ys.append(o[f"ex{h}"])
            if len(xs) >= 8:
                r = C.spearman(xs, ys)
                if C.fin(r):
                    per_year.append([y, round(r, 3), len(xs)])
            all_x += xs
            all_y += ys
        if not per_year:
            return None
        ics = [p[1] for p in per_year]
        # écart entre le tiers des titres les plus « sous-évalués » et le tiers les plus « surévalués » (rendement relatif moyen)
        pts = sorted(zip(all_x, all_y))
        k = len(pts) // 3
        spread = (sum(p[1] for p in pts[-k:]) / k - sum(p[1] for p in pts[:k]) / k) if k >= 5 else None
        hit = [1 if ((x > 0) == (yv > 0)) else 0 for x, yv in zip(all_x, all_y) if abs(x) > 0.2]
        mid = len(per_year) // 2
        return {"ic": round(sum(ics) / len(ics), 3), "ic_pos": round(sum(1 for x in ics if x > 0) / len(ics), 3), "n_years": len(per_year),
                "n": len(all_x), "spread": C.rnd(spread, 4), "hit": C.rnd(sum(hit) / len(hit), 3) if len(hit) >= 20 else None, "n_hit": len(hit),
                "ic_p1": round(sum(ics[:mid]) / mid, 3) if mid else None, "ic_p2": round(sum(ics[mid:]) / (len(ics) - mid), 3) if len(ics) - mid else None,
                "p1": [per_year[0][0], per_year[mid - 1][0]] if mid else None, "p2": [per_year[mid][0], per_year[-1][0]] if len(ics) - mid else None,
                "by_year": per_year}
    res["val"] = {}
    for h in (1, 3):
        res["val"][f"h{h}"] = {"syn": ic_block(lambda o: o["v"], h)}
        for m in ("ri", "ddm", "dcf", "mult_own", "mult_peer"):
            res["val"][f"h{h}"][m] = ic_block(lambda o, m=m: o["mods"].get(m), h)
    # prévision du résultat : erreur absolue moyenne contre la prévision naïve, calibration des intervalles à 80 %
    f = [o for o in obs if C.fin(o.get("ni_act"))]
    if f:
        e_m = [abs(o["ni_act"] - o["ni_f"]) for o in f]
        e_n = [abs(o["ni_act"] - o["ni0"]) for o in f if C.fin(o.get("ni0"))]
        cov = [1 if (C.fin(o["ni_lo"]) and C.fin(o["ni_hi"]) and o["ni_lo"] <= o["ni_act"] <= o["ni_hi"]) else 0 for o in f]
        rel = [abs(o["ni_act"] / o["ni_f"] - 1) for o in f if o["ni_f"] and o["ni_f"] > 0]
        res["fc"] = {"n": len(f), "ratio": C.rnd(sum(e_m) / sum(e_n), 3) if sum(e_n) else None, "cover80": C.rnd(sum(cov) / len(cov), 3),
                     "mape_med": C.rnd(C.med(rel), 3), "methods": {}}
        for m in C.FC_ORDER:
            pr = [(abs(o["ni_act"] - o["fm"][m]), abs(o["ni_act"] - o["ni0"])) for o in f if C.fin((o.get("fm") or {}).get(m)) and C.fin(o.get("ni0"))]
            if len(pr) >= 30 and sum(p[1] for p in pr):
                res["fc"]["methods"][m] = {"n": len(pr), "ratio": C.rnd(sum(p[0] for p in pr) / sum(p[1] for p in pr), 3)}
        # facteur d'élargissement des intervalles pour atteindre une couverture de 80 % sur les prévisions passées
        sc = None
        for k in range(10, 61):
            s_ = k / 10
            c_ = 0
            for o in f:
                fv, lo, hi = o["ni_f"], o["ni_lo"], o["ni_hi"]
                if not (C.fin(lo) and C.fin(hi)):
                    continue
                if lo - (fv - lo) * (s_ - 1) <= o["ni_act"] <= hi + (hi - fv) * (s_ - 1):
                    c_ += 1
            if c_ / len(f) >= 0.8:
                sc = s_
                break
        res["fc"]["scale80"] = sc
    # vitesse de convergence du cours vers la valeur estimée (écart log(cours / valeur) d'une année sur l'autre)
    pairs = []
    byk = {(o["t"], o["y"]): o for o in obs}
    for o in obs:
        n_ = byk.get((o["t"], o["y"] + 1))
        if n_ and o["v"] > 0 and n_["v"] > 0:
            pairs.append((math.log(o["p"] / o["v"]), math.log(n_["p"] / n_["v"])))
    if len(pairs) >= 30:
        mx = sum(p[0] for p in pairs) / len(pairs)
        my = sum(p[1] for p in pairs) / len(pairs)
        b = sum((p[0] - mx) * (p[1] - my) for p in pairs) / sum((p[0] - mx) ** 2 for p in pairs)
        res["gap"] = {"n": len(pairs), "b": round(b, 3), "half_life": round(math.log(0.5) / math.log(b), 1) if 0 < b < 1 else None,
                      "med_gap": C.rnd(C.med([abs(p[0]) for p in pairs]), 3)}
    v1 = (res["val"].get("h1") or {}).get("syn") or {}
    v3 = (res["val"].get("h3") or {}).get("syn") or {}
    res["head"] = {"n": len(obs), "years": res["years"], "ic1": v1.get("ic"), "ic3": v3.get("ic"), "spread1": v1.get("spread"), "spread3": v3.get("spread"),
                   "hit1": v1.get("hit"), "fc_ratio": (res.get("fc") or {}).get("ratio"), "cover80": (res.get("fc") or {}).get("cover80"),
                   "half_life": (res.get("gap") or {}).get("half_life"), "scale80": (res.get("fc") or {}).get("scale80")}
    # facteur de performance hors échantillon par modèle (pour la pondération des versions suivantes) : 1 + 2 × moyenne des
    # corrélations de rang à 1 et 3 ans, borné entre 0,6 et 1,4, seulement avec au moins 6 années mesurées
    perf = {}
    for m in ("ri", "ddm", "dcf", "mult_own", "mult_peer"):
        ics = [(res["val"][h].get(m) or {}) for h in ("h1", "h3")]
        ok = [b["ic"] for b in ics if b and b.get("n_years", 0) >= 6]
        if ok:
            perf[m] = {"f": round(C.clamp(1 + 2 * sum(ok) / len(ok), 0.6, 1.4), 3), "ic": round(sum(ok) / len(ok), 3)}
    res["perf"] = perf
    res["obs"] = [{k: (C.rnd(v, 4) if isinstance(v, float) else v) for k, v in o.items() if k not in ("mods", "fm")} for o in obs]
    note(f"validation historique : {len(obs)} évaluations point-in-time ({years[0] if years else '-'}–{years[-1] if years else '-'}) en {time.time() - t0:.0f} s")
    return res
