"""QLAB — moteur de valorisation des actions de la BRVM (onglet « Valorisation » de la fonction QLAB du terminal).

Lancé par build_terminal.py après la clôture (jamais pendant les relevés de séance), dans un appel protégé : une erreur ici
n'interrompt jamais la construction des autres données du site et laisse en place la dernière estimation valide.

Cycle de vie des estimations :
  - version initiale à la première exécution ;
  - réévaluation complète semestrielle : premier passage du soir à partir du 1er juin (comptes annuels publiés) et du
    1er décembre (comptes semestriels publiés) ;
  - entre deux cycles, chaque document officiel nouveau de la société (états financiers, résultats, dividende, opération sur
    le capital, notation, changement de dirigeant, communiqué) est examiné :
      niveau 1 — vérification : recalcul de contrôle, écarts mesurés, consignés dans le journal ; la prévision officielle ne change pas ;
      niveau 2 — réévaluation exceptionnelle complète, seulement si un seuil de matérialité est franchi (valeur centrale ≥ 10 %,
                 bénéfice attendu ≥ 15 %, nombre d'actions ≥ 5 %, dividende supprimé ou réduit de plus de moitié) ;
      regroupement : au plus une réévaluation exceptionnelle par société sur 30 jours, sauf événement grave (perte, suppression du
      dividende, variation de valeur ≥ 25 %, opération sur le capital) ; aucune dans les 30 jours précédant un cycle semestriel ;
  - chaque version est conservée telle quelle (historique horodaté, empreinte chaînée), jamais réécrite.

Fichiers écrits dans le dossier des données du site (data/) :
  qlab/index.json          tableau de bord (toutes les sociétés)
  qlab/<titre>.json        analyse en vigueur + cours du jour + index des versions + événements de la société
  qlab/hist/<titre>.json   toutes les versions (append-only)
  qlab/events.json         journal de tous les événements examinés et des décisions
  qlab/backtest.json       validation historique (point-in-time)
  qlab/state.json          état du moteur (cycle, documents déjà examinés, journal de la dernière exécution)
Une copie de sauvegarde est gardée dans le dossier des données brutes (branche raw) et restaurée si les données publiées
manquent ou sont plus anciennes.
"""
import datetime as dt
import hashlib
import json
import os
import shutil
import time

import qlab_core as C

ENGINE = "QLAB-V 1.1"  # 1.1 : pondération des modèles selon leur performance mesurée (règle choisie hors échantillon)
CYCLES = ((6, 1), (12, 1))
MAT_VALUE, MAT_EPS, MAT_SHARES, MAT_URGENT = 0.10, 0.15, 0.05, 0.25
GROUP_DAYS = 30
EVENT_KINDS = {"ef": "États financiers", "res": "Résultats", "ra": "Rapport d'activité", "rann": "Rapport annuel", "div": "Dividende",
               "ost": "Opération sur titres", "not": "Notation financière", "dir": "Changement de dirigeant", "com": "Communiqué", "ag": "Assemblée générale"}
TIME_BUDGET = 420  # secondes au plus pour l'ensemble du moteur


# ------------------------------------------------------------------------------------------------------------- fichiers
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


# ------------------------------------------------------------------------------------------------------------- données
def load_inputs(out, today=None):
    today = today or dt.date.today()
    S_ = jload(os.path.join(out, "summary.json"), {}) or {}
    secs = {x["id"]: x for x in S_.get("secs") or [] if x.get("mkt") == "BRVM" and x.get("cls") == "Equity"}
    I = {"out": out, "today": today, "today_i": C.dint(today), "secs": secs,
         "div": jload(os.path.join(out, "dividends.json"), []) or [],
         "liq": {r["id"]: r for r in (jload(os.path.join(out, "liq.json"), {}) or {}).get("rows") or []},
         "curves": jload(os.path.join(out, "umoa_curves.json"), {}) or {},
         "macro": jload(os.path.join(out, "uemoa.json"), {}) or {},
         "ratings": (jload(os.path.join(out, "ratings.json"), {}) or {}).get("rows") or [],
         "fa": {t: jload(os.path.join(out, "fa", f"{t}.json")) for t in secs}, "px": {}}
    for t in secs:
        b = jload(os.path.join(out, "s", f"{t}.json")) or {}
        if b.get("d"):
            I["px"][t] = (b["d"], b["c"])
    ix = jload(os.path.join(out, "s", "BRVMC.json")) or {}
    srch = (jload(os.path.join(out, "search.json"), {}) or {}).get("r") or []
    I["docs"] = srch
    I["S"] = {}
    for t in secs:
        if not I["fa"].get(t):
            continue
        S = C.company_static(t, I)
        # date de publication des comptes annuels de chaque exercice (premier document « états financiers », « résultats » ou
        # « rapport annuel » de l'année suivante, hors semestriels et trimestriels)
        pub = {}
        for r in srch:
            if len(r) >= 7 and r[1] == t and r[0] in ("ef", "res", "rann", "cac") and r[2] and r[3] and "S" not in (r[6] or "") and "T" not in (r[6] or ""):
                if r[3] // 10000 == r[2] + 1:
                    pub[r[2]] = min(pub.get(r[2], 99999999), r[3])
        S["pub"] = pub
        I["S"][t] = S
    M = C.market_params(I, today)
    M["idx"] = list(zip(ix.get("d") or [], ix.get("c") or []))
    M["beta_prior"], M["beta_n"] = C.beta_prior(I, M["idx"], I["today_i"], I["today_i"])
    M["m_pers"], M["m_pers_n"] = C.margin_persistence(I, I["today_i"])
    M["m_pers_raw"] = (I.get("_mp_raw") or {}).get(I["today_i"])
    return I, M


def peers_now(I):
    arch_of = {t: S["arch"] for t, S in I["S"].items()}
    return C.peer_table(I, I["today_i"], I["today_i"], arch_of), arch_of


def share_guard(I, log):
    """contrôle du nombre d'actions : après un fractionnement, si le nombre d'actions n'a pas encore été mis à jour alors que le
    bénéfice par action officiel l'a été, le nombre d'actions est corrigé du facteur de fractionnement (et signalé)"""
    for t, S in I["S"].items():
        sh, bnpa = S["shares_now"], S.get("bnpa")
        ni = S["ser"]["ni"]
        if not (sh and C.fin(bnpa) and bnpa > 0 and ni):
            continue
        r = ni[max(ni)] * 1e6 / sh / bnpa
        for d, k in S["splits"]:
            dd = C.ymd(d)
            if dd and dd <= I["today"] and (I["today"] - dd).days <= 120 and C.fin(k) and k > 1 and abs(r / k - 1) < 0.1:
                S["shares_now"] = sh * k
                S["notes"].append(f"nombre d'actions corrigé du fractionnement du {dd.strftime('%d/%m/%Y')} (×{k:g})")
                log(f"QLAB {t} : nombre d'actions non encore mis à jour après le fractionnement, corrigé ×{k:g}")


# ------------------------------------------------------------------------------------------------------------- cycles
def cycle_of(d):
    """cycle semestriel en cours à une date : (identifiant, date de début)"""
    if d >= dt.date(d.year, 12, 1):
        return f"{d.year}-12", dt.date(d.year, 12, 1)
    if d >= dt.date(d.year, 6, 1):
        return f"{d.year}-06", dt.date(d.year, 6, 1)
    return f"{d.year - 1}-12", dt.date(d.year - 1, 12, 1)


def next_cycle(d):
    for y in (d.year, d.year + 1):
        for m, dd in CYCLES:
            c = dt.date(y, m, dd)
            if c > d:
                return c
    return None


# ------------------------------------------------------------------------------------------------------------- contrôles
def validate(A):
    """contrôle d'une analyse avant publication : erreurs bloquantes (la version précédente est alors conservée)"""
    if not A.get("ok"):
        return [A.get("why") or "analyse impossible"]
    e = []
    s = A["syn"]
    for k in ("v", "p10", "p90"):
        if not C.fin(s.get(k)) or s[k] <= 0:
            e.append(f"synthèse : {k} invalide")
    if not e:
        if not (s["p10"] <= s["v"] <= s["p90"]):
            e.append("fourchette incohérente")
        if C.fin(A.get("price")) and A["price"] > 0 and not (0.05 <= s["v"] / A["price"] <= 20):
            e.append("valeur centrale hors de 0,05 à 20 fois le cours : contrôle manuel nécessaire")
    w = sum(m.get("w") or 0 for m in A["models"] if m.get("ok"))
    if abs(w - 1) > 0.01:
        e.append("somme des poids des modèles différente de 1")
    try:
        json.dumps(A, allow_nan=False)
    except ValueError:
        e.append("valeur non finie dans l'analyse")
    return e


def inputs_digest(I, t):
    S = I["S"][t]
    keep = ("rev", "ni", "eq", "ebit", "ebitda", "ocf", "capex", "nd", "roic")
    return digest({"ser": {k: sorted(S["ser"][k].items()) for k in keep}, "dv": sorted(S["dv"].items()), "sh": S["shares_now"],
                   "spl": S["splits"]})[:16]


TYPE_CODE = {"initiale": "I", "semestrielle": "S", "exceptionnelle": "E", "ajustement": "A", "methode": "M"}
TYPE_N = {"initiale": "Version initiale", "semestrielle": "Réévaluation semestrielle", "exceptionnelle": "Réévaluation exceptionnelle",
          "methode": "Révision de méthode",
          "ajustement": "Ajustement mécanique (fractionnement)"}


def make_version(A, t, vtype, reason, now, prev, inputs, extra=None):
    rec = {"id": f"{t}-{A['date']}-{TYPE_CODE[vtype]}", "t": t, "type": vtype, "type_n": TYPE_N[vtype], "reason": reason,
           "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "engine": ENGINE, "inputs": inputs, "prev": prev.get("hash") if prev else None, "a": A}
    if extra:
        rec.update(extra)
    rec["hash"] = digest(rec)
    return rec


def vsum(rec):
    a = rec["a"]
    s = a["syn"]
    return {"id": rec["id"], "type": rec["type"], "type_n": rec["type_n"], "ts": rec["ts"], "date": a["date"], "fy": a["fy"], "v": s["v"], "p10": s["p10"],
            "p90": s["p90"], "conf": s["conf"], "conf_lbl": s["conf_lbl"], "price": a["price"], "shares": a["shares"], "reason": rec["reason"],
            "chg": rec.get("chg"), "main": a.get("main")}


def per_share_ratio(old, new):
    """rapport des nombres d'actions (pour comparer des valeurs par action de part et d'autre d'un fractionnement)"""
    return (old["shares"] / new["shares"]) if (old.get("shares") and new.get("shares")) else 1.0


def model_v(A, m):
    x = next((r for r in A.get("models") or [] if r["id"] == m and r.get("ok")), None)
    return x["v"] if x else None


def explain_change(t, I, M, peers, old, new):
    """décomposition de la variation de la valeur centrale entre deux versions : effet des informations nouvelles (données et
    comptes, paramètres de marché de l'ancienne version) et effet des paramètres de marché"""
    k = per_share_ratio(old, new)
    v_old = old["syn"]["v"] * k
    out = {"dv": C.rnd(new["syn"]["v"] / v_old - 1, 4) if v_old else None, "dconf": new["syn"]["conf"] - old["syn"]["conf"], "lines": []}
    try:
        fx = dict(old["mp"], price=(old["mp"].get("price") or 0) * k or None)
        mix = C.analyze(t, I, M, peers, fix=fx, seed_date=new["date"])
        if mix.get("ok") and v_old:
            out["d_data"] = C.rnd(mix["syn"]["v"] / v_old - 1, 4)
            out["d_mkt"] = C.rnd(new["syn"]["v"] / mix["syn"]["v"] - 1, 4)
    except Exception as e:  # noqa: BLE001
        out["lines"].append(f"décomposition impossible ({e})")
    if new.get("fy") != old.get("fy"):
        out["lines"].append(f"nouveaux comptes annuels intégrés : exercice {new['fy']} (contre {old['fy']})")
    ho = {h["k"]: h for h in old.get("hyp") or []}
    for h in new.get("hyp") or []:
        o = ho.get(h["k"])
        if not o or not C.fin(h.get("v")) or not C.fin(o.get("v")):
            continue
        if h.get("fmt") == "pct" and abs(h["v"] - o["v"]) >= 0.005:
            out["lines"].append(C.fr(f"{h['n']} : {o['v'] * 100:.1f} % → {h['v'] * 100:.1f} %"))
        elif h.get("fmt") == "num" and abs(h["v"] - o["v"]) >= 0.05:
            out["lines"].append(C.fr(f"{h['n']} : {o['v']:.2f} → {h['v']:.2f}"))
    wo = {m["id"]: m.get("w") for m in old.get("models") or [] if m.get("ok")}
    for m in new.get("models") or []:
        if m.get("ok") and abs((m.get("w") or 0) - (wo.get(m["id"]) or 0)) >= 0.05:
            out["lines"].append(C.fr(f"poids {m['n']} : {(wo.get(m['id']) or 0) * 100:.0f} % → {m['w'] * 100:.0f} %"))
    if out["dconf"]:
        out["lines"].append(f"confiance : {old['syn']['conf']} → {new['syn']['conf']}")
    return out


# ------------------------------------------------------------------------------------------------------------- événements
def new_docs(I, t, seen):
    out = []
    for r in I["docs"]:
        if len(r) >= 7 and r[1] == t and r[0] in EVENT_KINDS and r[5] and r[5] not in seen and r[3]:
            out.append({"id": r[5], "kind": r[0], "kind_n": EVENT_KINDS[r[0]], "title": r[4], "d": r[3], "y": r[2], "u": r[5]})
    return sorted(out, key=lambda e: e["d"])


def examine(t, evs, I, M, peers, cur, st, today):
    """niveau 1 : vérification de matérialité. Recalcul de contrôle avec les paramètres de marché de la version en vigueur (même
    graine de simulation) : seules les informations nouvelles (comptes, dividendes, nombre d'actions, notation) font varier le résultat."""
    A0 = cur["a"]
    S = I["S"][t]
    k_split = C.split_factor_after(S["splits"], A0["date"], I["today_i"])
    fx = dict(A0["mp"])
    if fx.get("price"):
        fx["price"] = fx["price"] / k_split
    A1 = C.analyze(t, I, M, peers, fix=fx, seed_date=A0["date"])
    res = {"crit": [], "material": False, "urgent": False, "split": k_split if k_split > 1 else None}
    if not A1.get("ok"):
        res["dec"] = "vérification impossible (" + (A1.get("why") or "erreur") + ") : dernière prévision validée conservée, vérification nécessaire"
        return res, None

    def crit(name, val, thr, hit, txt):
        res["crit"].append({"n": name, "v": C.rnd(val, 4) if C.fin(val) else val, "thr": thr, "hit": bool(hit), "txt": C.fr(txt)})
    # nombre d'actions hors fractionnement
    if A0.get("shares") and A1.get("shares"):
        chg = A1["shares"] / (A0["shares"] * k_split) - 1
        crit("Nombre d'actions (hors fractionnement)", chg, MAT_SHARES, abs(chg) >= MAT_SHARES, f"variation de {chg:+.1%}")
        if abs(chg) >= MAT_SHARES:
            res["material"] = res["urgent"] = True
    if k_split > 1:
        crit("Fractionnement", k_split, None, False, f"division du nominal ×{k_split:g} : ajustement mécanique des valeurs par action, sans effet économique")
    # valeur intrinsèque du modèle principal (calcul déterministe, valeur des fonds propres)
    m = A0.get("main")
    v0, v1 = model_v(A0, m), model_v(A1, m)
    if C.fin(v0) and C.fin(v1) and v0 > 0:
        dv = (v1 * A1["shares"]) / (v0 * A0["shares"]) - 1
        crit("Valeur intrinsèque centrale (" + C.MODEL_NAMES.get(m, m) + ")", dv, MAT_VALUE, abs(dv) >= MAT_VALUE, f"variation de {dv:+.1%}")
        res["dv"] = dv
        if abs(dv) >= MAT_VALUE:
            res["material"] = True
        if abs(dv) >= MAT_URGENT:
            res["urgent"] = True
    # bénéfice : résultat publié contre prévision, ou révision de la prévision
    f0 = (A0.get("fc") or {}).get("ni", {}).get("f")
    ni_new = None
    if A1["fy"] and A1.get("hist"):
        ys = A1["hist"]["y"]
        ni_new = A1["hist"]["ni"][ys.index(A1["fy"])] if A1["fy"] in ys else None
    if A1["fy"] != A0["fy"] and C.fin(f0) and f0 > 0 and C.fin(ni_new):
        de = ni_new / f0 - 1
        crit(f"Résultat net publié {A1['fy']} contre la prévision", de, MAT_EPS, abs(de) >= MAT_EPS, f"écart de {de:+.1%}")
    else:
        f1 = (A1.get("fc") or {}).get("ni", {}).get("f")
        de = (f1 / f0 - 1) if (C.fin(f0) and f0 > 0 and C.fin(f1)) else None
        if de is not None:
            crit("Bénéfice attendu de l'exercice à venir", de, MAT_EPS, abs(de) >= MAT_EPS, f"révision de {de:+.1%}")
    if de is not None and abs(de) >= MAT_EPS:
        res["material"] = True
    ys0 = A0["hist"]["y"]
    ni_old = A0["hist"]["ni"][ys0.index(A0["fy"])] if A0["fy"] in ys0 else None
    if C.fin(ni_new) and ni_new < 0 and C.fin(ni_old) and ni_old >= 0:
        crit("Passage en perte", ni_new, 0, True, "résultat net négatif après un exercice bénéficiaire")
        res["material"] = res["urgent"] = True
    # dividende annoncé contre dividende projeté
    exy = str((A0["fy"] or 0) + 1)
    d_new = (A1.get("divs") or {}).get("hist", {}).get(exy)
    try:
        d_proj = A0["scen"]["rows"]["base"]["h"][0]["dps"] / k_split
    except (KeyError, IndexError, TypeError):
        d_proj = None
    if C.fin(d_new) and C.fin(d_proj) and d_proj > 0:
        dd = d_new / d_proj - 1
        hit = d_new < 0.5 * d_proj
        crit(f"Dividende de l'exercice {exy} contre le dividende projeté", dd, -0.5, hit, f"écart de {dd:+.1%}" + (" : réduction de plus de moitié" if hit else ""))
        if hit:
            res["material"] = res["urgent"] = True
    # notation financière
    r0, r1 = (A0.get("fac_raw") or {}).get("F10"), (A1.get("fac_raw") or {}).get("F10")
    if C.fin(r0) and C.fin(r1) and r1 < r0:
        hit = r0 - r1 >= 10
        crit("Notation financière", r1 - r0, -10, hit, f"dégradation : {(A0.get('fac_raw') or {}).get('F10_txt')} → {(A1.get('fac_raw') or {}).get('F10_txt')}")
        if hit:
            res["material"] = True
    return res, A1


def decide(t, res, st, today, cur):
    """niveau 2 seulement si matériel ; regroupement sur 30 jours sauf urgence ; pas d'exceptionnelle juste avant un cycle"""
    if res.get("dec"):
        return 1, res["dec"]
    if not res["material"]:
        if res.get("split"):
            return 2, "fractionnement : ajustement mécanique des valeurs par action"
        return 1, "non matériel : aucun seuil franchi ; consigné pour le prochain cycle semestriel"
    last = st.get("last_exc", {}).get(t)
    nc = next_cycle(today)
    if not res["urgent"]:
        if last and (today - dt.date.fromisoformat(last)).days < GROUP_DAYS:
            return 1, f"matériel mais regroupé : une réévaluation exceptionnelle a eu lieu le {dt.date.fromisoformat(last).strftime('%d/%m/%Y')} (période de {GROUP_DAYS} jours) ; réexamen à l'issue de la période"
        if nc and (nc - today).days <= GROUP_DAYS:
            return 1, f"matériel mais intégré à la réévaluation semestrielle du {nc.strftime('%d/%m/%Y')}, dans moins de {GROUP_DAYS} jours"
    return 2, ("urgent : " if res["urgent"] else "") + "seuil de matérialité franchi : réévaluation exceptionnelle complète"


# ------------------------------------------------------------------------------------------------------------- sauvegarde
def restore_if_needed(Q, extra, log):
    """restaure le dossier QLAB depuis la copie de sauvegarde (données brutes) s'il manque ou s'il est plus ancien"""
    if not extra:
        return
    B = os.path.join(extra, "qlab")
    sq = (jload(os.path.join(Q, "state.json"), {}) or {}).get("seq", -1)
    sb = (jload(os.path.join(B, "state.json"), {}) or {}).get("seq", -1)
    if sb > sq and os.path.isdir(B):
        if os.path.isdir(Q):
            shutil.rmtree(Q)
        shutil.copytree(B, Q)
        log(f"QLAB : dossier restauré depuis la sauvegarde (exécution n° {sb}, publiée : n° {sq})")


def backup(Q, extra, log):
    if not extra:
        return
    B = os.path.join(extra, "qlab")
    tmp = B + ".tmp"
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    shutil.copytree(Q, tmp)
    if os.path.isdir(B):
        shutil.rmtree(B)
    os.replace(tmp, B)


# ------------------------------------------------------------------------------------------------------------- exécution
def company_status(I, t, rec, cyc_start, today):
    """état de la prévision en vigueur : à jour, cycle non réalisé, comptes attendus manquants"""
    a = rec["a"]
    st = {"ok": True, "warn": []}
    if a["date"] < C.dint(cyc_start):
        st["ok"] = False
        st["warn"].append(f"la réévaluation semestrielle du {cyc_start.strftime('%d/%m/%Y')} n'a pas pu être réalisée : estimation du "
                          f"{C.ymd(a['date']).strftime('%d/%m/%Y')} conservée (dernière estimation valide)")
    exp_fy = today.year - 1 if today.month >= 6 else today.year - 2
    if (a.get("fy") or 0) < exp_fy:
        st["warn"].append(f"comptes annuels de l'exercice {exp_fy} non disponibles : l'estimation repose sur l'exercice {a.get('fy')}")
    return st


def market_block(I, t, rec):
    """cours du jour face à la valeur estimée de la version en vigueur (valeurs par action ajustées d'un éventuel fractionnement)"""
    S = I["S"][t]
    V = C.asof_view(S, I["today_i"], I["today_i"], full=False)
    a = rec["a"]
    k = (a["shares"] / V["shares"]) if (a.get("shares") and V.get("shares")) else 1.0
    v, lo, hi = (a["syn"][x] * k for x in ("v", "p10", "p90"))
    pr = C.price_reliability(S, V, I["today"])
    p = V["price"]
    return {"price": p, "pdate": V["pdate"], "v": C.sig(v, 3), "p10": C.sig(lo, 3), "p90": C.sig(hi, 3), "k": C.rnd(k, 6),
            "up": C.rnd(v / p - 1, 4) if (C.fin(p) and p > 0) else None, "pos": C.rnd((p - lo) / (hi - lo), 3) if (C.fin(p) and hi > lo) else None,
            "pr": pr}


def run(out, extra=None, log=print, today=None, now=None, budget=TIME_BUDGET, do_backtest=True):
    t0 = time.time()
    now = now or dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    today = today or dt.date.today()
    Q = os.path.join(out, "qlab")
    os.makedirs(os.path.join(Q, "hist"), exist_ok=True)
    restore_if_needed(Q, extra, log)
    sp = os.path.join(Q, "state.json")
    st = jload(sp, {}) or {}
    lk = st.get("lock")
    if lk and (now - dt.datetime.strptime(lk, "%Y-%m-%dT%H:%M:%SZ")).total_seconds() < 7200:
        log("QLAB : une autre exécution est en cours (verrou de moins de 2 h) : rien n'est fait")
        return {"skipped": True}
    st["lock"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    jdump(st, sp)
    msgs = []

    def note(m):
        msgs.append(m)
        log("QLAB " + m)
    try:
        return _run(out, extra, Q, st, sp, today, now, t0, budget, note, do_backtest)
    finally:
        st.pop("lock", None)
        st["log"] = msgs[-200:]
        jdump(st, sp)
        try:
            backup(Q, extra, log)
        except Exception as e:  # noqa: BLE001
            log("QLAB : sauvegarde impossible :", e)


def _run(out, extra, Q, st, sp, today, now, t0, budget, note, do_backtest):
    I, M = load_inputs(out, today)
    share_guard(I, note)
    peers, _ = peers_now(I)
    cyc_id, cyc_start = cycle_of(today)
    first = not st.get("cycle")
    seen = set(st.get("seen") or [])
    pending = st.get("pending") or {}
    st.setdefault("last_exc", {})
    ev_all = (jload(os.path.join(Q, "events.json"), {}) or {}).get("ev") or []
    # validation historique (point-in-time) : à la version initiale, à chaque cycle semestriel, ou si elle manque ; ses mesures
    # (performance de chaque modèle, calibration des intervalles) servent aux versions publiées ensuite
    bt_p = os.path.join(Q, "backtest.json")
    bt = jload(bt_p)
    due_cycle = any((jload(os.path.join(Q, f"{t}.json")) or {}).get("cur", {}).get("a", {}).get("date", 0) < C.dint(cyc_start) for t in list(I["S"])[:5])
    if do_backtest and (first or not bt or bt.get("cycle") != cyc_id or due_cycle or bt.get("engine") != ENGINE):
        try:
            import qlab_backtest
            bt = qlab_backtest.run(I, M, note, deadline=t0 + budget * 0.4)
            bt["cycle"], bt["engine"] = cyc_id, ENGINE
            jdump(bt, bt_p)
        except Exception as e:  # noqa: BLE001
            note(f"validation historique non refaite ({type(e).__name__}: {e})")
    if bt:
        M["perf"] = bt.get("perf") or {}
        if (bt.get("fc") or {}).get("n", 0) >= 100 and bt["fc"].get("scale80"):
            M["fc_scale"] = bt["fc"]["scale80"]
    n_new = {"initiale": 0, "semestrielle": 0, "exceptionnelle": 0, "ajustement": 0, "methode": 0}
    n_fail, n_l1, skipped = 0, 0, []
    files, nofile = {}, []
    for t in sorted(I["S"]):
        if time.time() - t0 > budget:
            skipped.append(t)
            continue
        cf = os.path.join(Q, f"{t}.json")
        comp = jload(cf) or {"t": t, "vers": [], "events": []}
        cur = comp.get("cur")
        docs = new_docs(I, t, seen)
        dig = inputs_digest(I, t)
        vtype, reason, A, extra_v = None, None, None, {}
        try:
            if not cur:
                vtype = "initiale"
                reason = "première évaluation complète de la société par le moteur QLAB"
            elif cur["a"]["date"] < C.dint(cyc_start):
                vtype = "semestrielle"
                reason = f"réévaluation complète du cycle semestriel du {cyc_start.strftime('%d/%m/%Y')}"
            elif cur.get("engine") != ENGINE:
                vtype = "methode"
                reason = (f"nouvelle méthode du moteur ({cur.get('engine')} → {ENGINE}) : modèles pondérés selon leur performance mesurée par la "
                          "validation historique, règle choisie par comparaison hors échantillon ; données inchangées")
            else:
                trig = list(docs)
                if dig != (comp.get("inputs_seen") or cur.get("inputs")) and not docs:
                    trig.append({"id": f"data:{t}:{today.isoformat()}", "kind": "data", "kind_n": "Révision des données", "title":
                                 "données financières ou boursières modifiées (comptes relus, dividende ou nombre d'actions)", "d": C.dint(today), "u": None})
                if pending.get(t) and not trig:
                    trig.append({"id": f"pend:{t}:{today.isoformat()}", "kind": "pending", "kind_n": "Réexamen d'un dossier en attente",
                                 "title": pending[t].get("why") or "dossier matériel regroupé", "d": C.dint(today), "u": None})
                if trig:
                    res, A1 = examine(t, trig, I, M, peers, cur, st, today)
                    lvl, dec = decide(t, res, st, today, cur)
                    dossier = f"{t}-{today.isoformat()}"
                    entry_base = {"t": t, "dossier": dossier, "d_detect": C.dint(today), "lvl": lvl, "dec": C.fr(dec), "crit": res["crit"],
                                  "old": {"id": cur["id"], "v": cur["a"]["syn"]["v"], "p10": cur["a"]["syn"]["p10"], "p90": cur["a"]["syn"]["p90"]},
                                  "src": "documents officiels publiés par la société ou la bourse"}
                    if lvl == 2:
                        vtype = "ajustement" if (res.get("split") and not res["material"]) else "exceptionnelle"
                        reason = C.fr(dec + " — " + "; ".join(e["kind_n"] + " : " + (e["title"] or "") for e in trig[:4]))
                        extra_v = {"dossier": dossier}
                        pending.pop(t, None)
                    else:
                        n_l1 += 1
                        if res["material"]:
                            pending[t] = {"since": today.isoformat(), "why": C.fr(dec)}
                        else:
                            pending.pop(t, None)
                    for e in trig:
                        ev_all.append(dict(entry_base, id=e["id"], kind=e["kind"], kind_n=e["kind_n"], title=e["title"], d_event=e["d"], u=e.get("u")))
                    comp["events"] = (comp.get("events") or []) + [dict(entry_base, n=len(trig), titles=[e["title"] for e in trig][:6])]
                    if lvl == 1:
                        comp["inputs_seen"] = dig  # une révision examinée n'est réexaminée que si les données changent encore
            if vtype:
                A = C.analyze(t, I, M, peers)
                err = validate(A)
                if err:
                    n_fail += 1
                    note(f"{t} : {TYPE_N[vtype].lower()} non publiée ({'; '.join(err)}) — dernière estimation valide conservée")
                    comp.setdefault("fail", []).append({"d": C.dint(today), "type": vtype, "err": err})
                    vtype = None
        except Exception as e:  # noqa: BLE001
            n_fail += 1
            note(f"{t} : erreur de calcul ({type(e).__name__}: {e}) — dernière estimation valide conservée")
            comp.setdefault("fail", []).append({"d": C.dint(today), "err": [f"{type(e).__name__}: {e}"]})
            vtype = None
        if vtype:
            chg = explain_change(t, I, M, peers, cur["a"], A) if cur else None
            if chg is not None and vtype == "methode":
                chg["method"] = True
            rec = make_version(A, t, vtype, reason, now, cur, dig, dict(extra_v, chg=chg))
            hp = os.path.join(Q, "hist", f"{t}.json")
            hist = jload(hp) or {"t": t, "v": []}
            if hist["v"] and hist["v"][-1]["id"] == rec["id"]:
                note(f"{t} : version {rec['id']} déjà enregistrée (exécution en double ignorée)")
            else:
                hist["v"].append(rec)
                jdump(hist, hp)
                comp["cur"] = rec
                comp["inputs_seen"] = dig
                comp["vers"] = (comp.get("vers") or []) + [vsum(rec)]
                n_new[vtype] += 1
                if vtype == "exceptionnelle":
                    st["last_exc"][t] = today.isoformat()
                    ev_all.append({"t": t, "dossier": extra_v.get("dossier"), "d_detect": C.dint(today), "lvl": 2, "kind": "version", "kind_n": "Nouvelle version",
                                   "dec": f"version {rec['id']} publiée", "old": {"id": cur["id"], "v": cur["a"]["syn"]["v"]} if cur else None,
                                   "new": {"id": rec["id"], "v": A["syn"]["v"], "p10": A["syn"]["p10"], "p90": A["syn"]["p90"], "conf": A["syn"]["conf"]},
                                   "models": [m["id"] for m in A["models"] if m.get("ok")], "expl": chg})
        for e in docs:
            seen.add(e["id"])
        comp["name"] = I["S"][t]["name"]
        comp["fail"] = (comp.get("fail") or [])[-20:]
        if comp.get("cur"):
            comp["mkt"] = market_block(I, t, comp["cur"])
            comp["status"] = company_status(I, t, comp["cur"], cyc_start, today)
            comp["events"] = (comp.get("events") or [])[-60:]
            files[t] = comp
        else:
            jdump(comp, cf)
            nofile.append({"t": t, "n": comp["name"], "why": (comp["fail"][-1]["err"] if comp["fail"] else ["aucune estimation"])})
    # facteurs de qualité et de risque : rangs parmi les sociétés (valeurs des versions en vigueur)
    raws = {t: c["cur"]["a"].get("fac_raw") or {} for t, c in files.items()}
    sc = C.factor_scores(raws, {t: I["S"][t]["fin"] for t in files})
    for t, c in files.items():
        c["fac"] = {"scores": sc.get(t, {}), "raw": raws[t], "def": [{"id": f[0], "n": f[1], "d": f[2]} for f in C.FACTORS],
                    "gov": "gouvernance : non mesurée, faute de données structurées et vérifiables pour toutes les sociétés"}
        jdump(c, os.path.join(Q, f"{t}.json"))
    if first:
        for r in I["docs"]:
            if len(r) >= 7 and r[1] and r[5]:
                seen.add(r[5])
        note(f"version initiale : {len(seen)} documents déjà publiés considérés comme intégrés")
    st.update(cycle=cyc_id, cycle_start=cyc_start.isoformat(), next_cycle=next_cycle(today).isoformat(), seen=sorted(seen), pending=pending,
              last_run=now.strftime("%Y-%m-%dT%H:%M:%SZ"), run_date=today.isoformat(), seq=int(st.get("seq", 0)) + 1, engine=ENGINE)
    jdump({"ev": ev_all[-5000:]}, os.path.join(Q, "events.json"))
    # tableau de bord
    rows = []
    for t, c in sorted(files.items()):
        a = c["cur"]["a"]
        rows.append({"t": t, "n": c["name"], "arch": a["profile"]["arch_n"], "v": c["mkt"]["v"], "p10": c["mkt"]["p10"], "p90": c["mkt"]["p90"],
                     "price": c["mkt"]["price"], "pdate": c["mkt"]["pdate"], "up": c["mkt"]["up"], "pos": c["mkt"]["pos"], "pr": c["mkt"]["pr"].get("lvl"),
                     "conf": a["syn"]["conf"], "conf_lbl": a["syn"]["conf_lbl"], "ver": c["cur"]["id"], "vtype": c["cur"]["type"], "vdate": a["date"],
                     "fy": a["fy"], "main": a.get("main"), "ok": c["status"]["ok"], "warn": len(c["status"]["warn"]), "nev": len(c.get("events") or [])})
    idx = {"engine": ENGINE, "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "date": C.dint(today), "cycle": cyc_id, "cycle_start": cyc_start.isoformat(),
           "next_cycle": next_cycle(today).isoformat(), "rows": rows,
           "mkt": {"erp": C.rnd(M["erp"], 4), "ke_lr": C.rnd(M.get("ke_lr"), 4), "ke_now": C.rnd(M.get("ke_mkt"), 4), "dy": C.rnd(M.get("dy_mkt"), 4),
                   "rf": {k: C.rnd(v, 4) for k, v in M["rf"].items()}, "glt": {k: C.rnd(v, 4) for k, v in M["glt"].items()},
                   "beta_prior": [C.rnd(x, 3) for x in M["beta_prior"]], "erp_why": C.fr(M["erp_why"]),
                   "ke_series": [[y, C.rnd(k, 4)] for y, k, _ in M["ke_series"]]},
           "bt": (bt or {}).get("head"), "perf": (bt or {}).get("perf"), "wrule": {k: (bt or {}).get("wrule", {}).get(k) for k in ("chosen", "table", "why")}, "fc_scale": M.get("fc_scale"), "skipped": skipped, "fails": n_fail, "none": nofile,
           "m_pers": [C.rnd(M.get("m_pers"), 3), M.get("m_pers_n")]}
    jdump(idx, os.path.join(Q, "index.json"))
    note(f"{len(files)} sociétés ; versions : {n_new['initiale']} initiales, {n_new['semestrielle']} semestrielles, {n_new['exceptionnelle']} exceptionnelles, "
         f"{n_new['ajustement']} ajustements, {n_new['methode']} révisions de méthode ; {n_l1} vérifications de niveau 1 ; {n_fail} échecs ; {len(skipped)} non traitées (temps) ; {time.time() - t0:.0f} s")
    return {"files": len(files), "new": n_new, "fail": n_fail, "l1": n_l1}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--extra", default=None)
    ap.add_argument("--today", default=None)
    ap.add_argument("--no-backtest", action="store_true")
    a = ap.parse_args()
    run(a.out, a.extra, print, today=dt.date.fromisoformat(a.today) if a.today else None, do_backtest=not a.no_backtest)
