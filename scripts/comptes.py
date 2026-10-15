#!/usr/bin/env python3
"""Lecture des états financiers publiés par les sociétés cotées à la BRVM (texte du PDF ou reconnaissance de caractères).

Plan comptable SYSCOHADA (ancien et révisé), plan comptable bancaire de l'UMOA, normes IFRS.
Chaque poste est reconnu par son libellé normalisé (et par sa référence SYSCOHADA quand elle est imprimée) ; chaque montant est
rattaché à son exercice par la colonne sous l'en-tête des années, ou par la structure du tableau (brut / amortissements / net,
colonne de variation). Les montants sont ramenés en millions de FCFA.
Un exercice n'est retenu que si les identités comptables du document se vérifient (total actif = total passif, résultat du
compte de résultat = résultat du bilan, soldes intermédiaires) : rien n'est deviné ni estimé. Bibliothèque standard uniquement.

Utilisation en ligne de commande : comptes.py --dir DOSSIER  (index.json + txt/ produits par fetch_extra.py --only comptes)
-> DOSSIER/comptes.json
"""
import gzip
import json
import os
import re
import sys
import unicodedata

READER_V = 2

# ---------------------------------------------------------------- postes
# clé : (états où le poste peut figurer, motif sur le libellé normalisé : minuscules, sans accents, sans référence ni formule)
S_ACT, S_PAS, S_CR, S_FLX = "actif", "passif", "cr", "flux"
ITEMS = [
    # ---- bilan actif (SYSCOHADA)
    ("charges_immobilisees", (S_ACT,), r"^charges immobilisees$"),
    ("immo_incorp", (S_ACT,), r"^immobilisations incorporelles(?: nettes| brutes)?$"),
    ("immo_corp", (S_ACT,), r"^immobilisations corporelles(?: nettes| brutes)?$"),
    ("immo_fin", (S_ACT,), r"^immobilisations financieres(?: nettes| brutes)?$"),
    ("actif_immobilise", (S_ACT,), r"^(?:total )?actif immobilise(?: net)?$|^total (?:de l.)?actif immobilise(?: net)?$|^total immobilisations(?: nettes)?$"),
    ("actif_circulant_hao", (S_ACT,), r"^actif circulant h\.?a\.?o\.?$"),
    ("stocks", (S_ACT,), r"^stocks?(?: et en.?cours| de marchandises)?$"),
    ("creances", (S_ACT,), r"^creances et emplois assimiles$|^creances$"),
    ("clients", (S_ACT,), r"^clients(?: et comptes rattaches)?$"),
    ("actif_circulant", (S_ACT,), r"^(?:total )?actif circulant$"),
    ("tresorerie_actif", (S_ACT,), r"^(?:total )?tresorerie ?- ?actif$|^(?:total )?tresorerie actif$|^disponibilites$"),
    ("total_actif", (S_ACT, None), r"^total (?:general )?(?:de l.)?actif$|^total general actif$|^total bilan actif$|^total (?:des )?actifs$|^total assets$|^actif total$"),
    # ---- bilan passif (SYSCOHADA)
    ("capital", (S_PAS,), r"^capital(?: social| souscrit(?: appele)?)?$"),
    ("primes_reserves", (S_PAS,), r"^primes et reserves$"),
    ("reserves", (S_PAS,), r"^reserves$"),
    ("report_nouveau", (S_PAS,), r"^report a nouveau"),
    ("capitaux_propres", (S_PAS,), r"^(?:total )?capitaux propres(?: et ressources assimilees| et assimiles)?(?: et)?$|^total des capitaux propres$|^total equity$"),
    ("dettes_financieres", (S_PAS,), r"^(?:total )?dettes financieres(?: et ressources assimilees)?(?: et)?$|^total dettes et res\. assimilees$"),
    ("ressources_stables", (S_PAS,), r"^(?:total )?ressources stables$"),
    ("passif_circulant", (S_PAS,), r"^(?:total )?passif circulant$"),
    ("fournisseurs", (S_PAS,), r"^fournisseurs(?: d.exploitation)?$"),
    ("tresorerie_passif", (S_PAS,), r"^(?:total )?tresorerie ?- ?passif$|^(?:total )?tresorerie passif$"),
    ("total_passif", (S_PAS, None), r"^total (?:general )?(?:du )?passif$|^total general passif$|^total bilan passif$|^total (?:des |du )?(?:capitaux propres et (?:des )?passifs?|passifs? et (?:des )?capitaux propres)$|^total liabilities and (?:shareholders. )?equity$|^passif total$|^total capitaux propres et passifs$"),
    ("actif_non_courant", (S_ACT,), r"^total (?:de l.|des )?actifs? non courants?$"),
    ("actif_courant", (S_ACT,), r"^total (?:de l.|des )?actifs? courants?$"),
    ("passif_non_courant", (S_PAS,), r"^total (?:du |des )?passifs? non courants?$"),
    ("passif_courant", (S_PAS,), r"^total (?:du |des )?passifs? courants?$"),
    # ---- compte de résultat (SYSCOHADA)
    ("ventes_marchandises", (S_CR,), r"^ventes? de marchandises$"),
    ("marge_commerciale", (S_CR,), r"^marge (?:commerciale|brute sur marchandises)$"),
    ("ventes_produits", (S_CR,), r"^ventes? de produits fabriques$"),
    ("travaux_services", (S_CR,), r"^travaux,? services vendus$"),
    ("produits_accessoires", (S_CR,), r"^produits accessoires$"),
    ("chiffre_affaires", (S_CR, None), r"^(?:total )?chiffre d.affaires(?: hors taxes| net| ht| consolide)?$|^revenue$|^revenus$|^produits des activites ordinaires$"),
    ("valeur_ajoutee", (S_CR,), r"^valeur ajoutee$"),
    ("charges_personnel", (S_CR,), r"^charges (?:de|du) personnel$|^frais de personnel$"),
    ("ebe", (S_CR, S_FLX), r"^excedent brut d.exploitation(?: \(?e\.?b\.?e\.?\)?)?$|^ebe$|^ebitda$"),
    ("dotations", (S_CR,), r"^dotations? aux amortissements(?:,? (?:et|aux) (?:aux )?provisions)?(?: et depreciations)?$"),
    ("resultat_exploitation", (S_CR,), r"^resultat d.exploitation$|^resultat operationnel$"),
    ("revenus_financiers", (S_CR,), r"^revenus financiers(?: et assimiles)?$|^produits financiers$"),
    ("frais_financiers", (S_CR,), r"^frais financiers(?: et charges assimilees)?$|^charges financieres$"),
    ("resultat_financier", (S_CR,), r"^resultat financier$"),
    ("rao", (S_CR,), r"^resultat des activites ordinaires$|^resultat activites ordinaires$"),
    ("rhao", (S_CR,), r"^resultat hors activites? ordinaires?$|^resultat h\.? ?a\.? ?o\.?$"),
    ("participation", (S_CR,), r"^participation des travailleurs$"),
    ("impots_resultat", (S_CR,), r"^impots? sur (?:le |les )?(?:resultats?|benefices?|societes)$|^impot sur le resultat$|^charges? d.impots?(?: sur le resultat)?$|^impots? exigibles? et differes?$"),
    ("perte_nette", (S_CR,), r"^perte(?: nette)?(?: de l.exercice)?$"),
    ("resultat_avant_impot", (S_CR,), r"^resultat avant impots?(?: sur le resultat| et participation)?$|^resultat (?:net )?avant impots?$"),
    # « Résultat net » : compte de résultat ou bilan selon l'état où il figure
    ("resultat_net", (S_CR, S_PAS, None), r"^(?:resultat net(?: de l.exercice| de la periode| consolide| comptable| de l.ensemble consolide| total)?|resultat de l.exercice|benefice(?: net)?(?: de l.exercice)?|benefice ou perte|resultat net \(?benefice.*|profit for the (?:year|period))$"),
    ("resultat_net_pg", (S_CR,), r"^resultat net[ ,-]+part (?:du )?groupe$|^resultat net attribuable aux (?:actionnaires|proprietaires) de la (?:societe|maison)? ?mere$|^resultat net attribuable aux (?:actionnaires|proprietaires) de la societe$"),
    # ---- flux de trésorerie (TFT révisé) / TAFIRE
    ("cafg", (S_FLX, None), r"^capacite d.autofinancement globale(?: \(?cafg\)?)?$|^cafg$|^capacite d.autofinancement$"),
    ("flux_operationnels", (S_FLX,), r"^flux de tresorerie (?:nets? )?(?:provenant|provenants|issus?|generes?) (?:des|de l.|par les) ?activites? (?:operationnelles|d.exploitation)$"),
    ("capex_incorp", (S_FLX,), r"^(?:decaissements? lies? aux )?acquisitions? d.immobilisations incorporelles$"),
    ("capex_corp", (S_FLX,), r"^(?:decaissements? lies? aux )?acquisitions? d.immobilisations corporelles$"),
    ("flux_investissement", (S_FLX,), r"^flux de tresorerie (?:nets? )?(?:provenant|provenants|issus?|generes?|lies?) (?:des|de l.|aux) ?(?:activites?|operations) d.investissements?$"),
    ("dividendes_verses", (S_FLX,), r"^dividendes verses$|^distribution de dividendes$"),
    ("flux_financement", (S_FLX,), r"^flux de tresorerie (?:nets? )?(?:provenant|provenants|issus?|generes?|lies?) (?:des|de l.|aux) ?(?:activites?|operations) de financement$"),
    ("variation_tresorerie", (S_FLX,), r"^variation de (?:la )?tresorerie(?: nette)?(?: de la periode)?$"),
    ("tresorerie_fin", (S_FLX,), r"^tresorerie nette (?:au 31 decembre|a la cloture|de cloture|fin de periode|en fin de periode|a la fin de l.exercice)$"),
    # ---- banques (plan comptable bancaire UMOA, ancien et révisé)
    ("b_caisse", (S_ACT,), r"^caisse(?:,? banque centrale(?:,? ccp)?)?$"),
    ("b_creances_interbancaires", (S_ACT,), r"^creances interbancaires(?: et assimilees)?$"),
    ("b_creances_clientele", (S_ACT,), r"^creances sur la clientele$"),
    ("b_effets_publics", (S_ACT,), r"^effets publics et valeurs assimilees$"),
    ("b_titres_placement", (S_ACT,), r"^titres de placement$|^obligations et autres titres a revenu fixe$"),
    ("b_dettes_interbancaires", (S_PAS,), r"^dettes interbancaires(?: et assimilees)?$"),
    ("b_dettes_clientele", (S_PAS,), r"^dettes a l.egard de la clientele$"),
    ("b_capital", (S_PAS,), r"^capital (?:ou dotation|appele)$|^capital souscrit$"),
    ("b_resultat_bilan", (S_PAS,), r"^resultat de l.exercice \(\+/-\)$"),
    ("b_interets_produits", (S_CR,), r"^interets et produits assimilee?s$"),
    ("b_interets_charges", (S_CR,), r"^interets et charges assimilees$"),
    ("b_commissions_produits", (S_CR,), r"^commissions \(?produits\)?$"),
    ("b_commissions_charges", (S_CR,), r"^commissions \(?charges\)?$"),
    ("b_pnb", (S_CR, None), r"^produit net bancaire$|^net banking income$"),
    ("b_charges_generales", (S_CR,), r"^charges generales d.exploitation$|^frais generaux d.exploitation$|^frais generaux$"),
    ("b_rbe", (S_CR,), r"^resultat brut d.exploitation$"),
    ("b_cout_risque", (S_CR,), r"^cout du risque$"),
]
ITEM_RX = [(k, secs, re.compile(p)) for k, secs, p in ITEMS]
SECS = {k: tuple(x for x in secs if x) for k, secs, _ in ITEMS}
SECS["resultat_bilan"] = (S_PAS,)
ITEM_KEYS = [k for k, _, _ in ITEMS] + ["resultat_bilan"]

# références SYSCOHADA (ancien et révisé) dont le sens ne change pas d'un plan à l'autre
REF_CODES = {"AZ": "actif_immobilise", "BK": "actif_circulant", "BT": "tresorerie_actif", "BZ": "total_actif", "CA": "capital",
             "CP": "capitaux_propres", "DD": "dettes_financieres", "DF": "ressources_stables", "DP": "passif_circulant",
             "DT": "tresorerie_passif", "DZ": "total_passif", "XA": "marge_commerciale", "XC": "valeur_ajoutee", "XD": "ebe",
             "XE": "resultat_exploitation", "XF": "resultat_financier", "XG": "rao", "XH": "rhao", "XI": "resultat_net"}
# plan révisé (2018 et après) seulement
REF_CODES_REV = {"XB": "chiffre_affaires", "CJ": "resultat_bilan", "RK": "charges_personnel", "RS": "impots_resultat", "RQ": "participation",
                 "TA": "ventes_marchandises", "TB": "ventes_produits", "TC": "travaux_services", "TD": "produits_accessoires",
                 "FA": "cafg", "ZB": "flux_operationnels", "ZC": "flux_investissement", "ZF": "flux_financement", "ZG": "variation_tresorerie",
                 "ZH": "tresorerie_fin", "FF": "capex_incorp", "FG": "capex_corp"}
CODE_SEC = {"A": S_ACT, "B": S_ACT, "C": S_PAS, "D": S_PAS, "T": S_CR, "R": S_CR, "X": S_CR, "F": S_FLX, "Z": S_FLX}

NUM = re.compile(r"\(?[-−–‐‑]?\s?\d{1,3}(?:(?:[    ]|,|\.)\d{3})+(?:,\d{1,3})?\)?|\d{1,2}\.\d{1,2}(?![\d.,])|\(?[-−–‐‑]?\d+(?:,\d{1,3})?\)?")
MOIS = {"janvier": 1, "janv": 1, "jan": 1, "fevrier": 2, "fevr": 2, "fev": 2, "mars": 3, "avril": 4, "avr": 4, "mai": 5, "juin": 6,
        "juillet": 7, "juil": 7, "aout": 8, "septembre": 9, "sept": 9, "sep": 9, "octobre": 10, "oct": 10, "novembre": 11, "nov": 11,
        "decembre": 12, "dec": 12}
# en-têtes de colonnes : 2018, « 31-déc-09 », « 31/12/2010 », « déc-10 », « Exercice N-1 »
HDR_RX = re.compile(r"(?<![\d,.])(?:(?:31|30)[-/. ]?(?:12|06|dec\w*|juin)[-/. ]?)?((?:19[89]\d|20[0-3]\d)|(?<=[-/. ])\d\d)(?![\d,.%])")
SPACE = "   "


def nrm(x):
    x = re.sub(r"[’‘`´ʼ]", "'", x)
    return unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().lower()


_COMMA_K = [False]  # document où la virgule sépare les milliers (« 435,697 » = 435 697)
_NOTE_DOT = [False]  # document à virgule décimale : « 5.3 » est un renvoi de note, pas un montant


def num_val(tok):
    """« 1 400 501 950 », « 1,962,261 », « (26 985) », « -2,579,063 », « 420,3 » -> nombre (None si ce n'est pas un montant)."""
    t = tok.strip()
    neg = t.startswith("(") and t.endswith(")") or t.lstrip("(").startswith(("-", "−", "–", "‐", "‑"))
    t = t.strip("()").lstrip("-−–‐‑").strip()
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+", t) and (_COMMA_K[0] or not re.fullmatch(r"\d{1,3},\d{3}", t)):  # virgules = milliers (1,962,261)
        t = t.replace(",", "")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", t):  # points = milliers
        t = t.replace(".", "")
    else:
        t = re.sub(r"[ " + SPACE + "]", "", t).replace(",", ".")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def unit_of(txt):
    """Unité annoncée des montants : 1 (FCFA), 1e3 (milliers), 1e6 (millions) ; None si rien d'explicite."""
    t = nrm(txt[:40000])
    m = re.search(r"(?:en|donnees en|montants? en|chiffres en|\()\s*(milliards?|millions?|milliers|mxof|kxof|mfcfa|kfcfa|millier|mf|kf|m fcfa|k fcfa|mds?)\b[^\n]{0,25}"
                  r"(?:fcfa|f\.? ?cfa|francs?(?: cfa)?|xof|de francs|de f)", t)
    if m:
        w = m.group(1)
        return 1e9 if w.startswith("milliard") or w.startswith("md") else 1e6 if w.startswith("million") or w in ("mxof", "mfcfa", "mf", "m fcfa") else 1e3
    if re.search(r"\(?en (?:millions|milliers)\)?", t):
        return 1e6 if re.search(r"\(?en millions\)?", t) else 1e3
    if re.search(r"en (?:francs? cfa|fcfa|f\.? ?cfa|xof)\b|montants? en f\.? ?cfa", t):
        return 1.0
    return None


def capital_stated(txt):
    """Capital social annoncé dans l'en-tête (« au capital de 24 500 000 000 FCFA »), en FCFA."""
    t = nrm(txt[:12000])
    m = re.search(r"capital(?: social)? de\s*(?:f\.?\s?cfa\s*)?([\d][\d ., " + SPACE + r"]{4,}\d)\s*(?:f\.?\s?cfa|francs|fcfa|xof)?", t)
    if not m:
        return None
    v = num_val(re.sub(r"[., " + SPACE + "]", " ", m.group(1)).strip())
    return v if v and v > 1e6 else None


def fiscal_year(txt, hint=None):
    t = nrm(txt[:15000])
    for rx in (r"(?:au|clos le|arrete au|exercice clos le|cloture au|clos au)\s+31[ -/.]+(?:decembre|12)[ -/.]+(20\d\d|19\d\d)",
               r"exercice\s+(20\d\d)", r"(?:bilan|comptes? de resultats?|etats financiers)[^\n]{0,40}?\b(20\d\d)\b"):
        ys = [int(y) for y in re.findall(rx, t)]
        if ys:
            if hint and hint in ys:
                return hint
            return max(set(ys), key=ys.count)
    return hint


def doc_kind(txt, title=""):
    """Annuel ou semestriel / trimestriel, d'après le titre et l'en-tête."""
    t = nrm(title or "") + " " + nrm(txt[:4000])
    if re.search(r"(?:1er|premier|2e|2eme|deuxieme|second|1st|first) semestre|semestriel|30 juin|30/06|30-06|half.year|six mois", t) \
            and not re.search(r"exercice (?:clos le )?31 decembre|annuel|exercice 20\d\d\b(?! *-)", nrm(title or "")):
        return "semestre"
    if re.search(r"trimestr|31 mars|30 septembre|quarter", t) and not re.search(r"31 decembre", t[:2000]):
        return "trimestre"
    return "annuel"


BROKEN = re.compile(r"(?<![\d,.])(\d{1,3}(?: \d{1,3})+) ?,(\d{1,2})(?![\d])")


def _join_broken(m):
    """« 2 3 09 ,1 » -> « 2309,1 » ; « 1 084,1 » reste « 1 084,1 » (groupes de milliers réguliers)."""
    g = m.group(1).split(" ")
    if all(len(x) == 3 for x in g[1:]) and " ," not in m.group(0):
        return m.group(0)
    return "".join(g) + "," + m.group(2)


GLYPH_DIGITS = {chr(0x3EC + d): str(d) for d in range(10)}
GLYPH_DIGITS.update({"\x03": " ", "\u0372": "-"})


def clean(txt, ocr=False):
    """Caractères parasites de la reconnaissance de caractères (barres, crochets) autour des montants ; montants dont la
    couche texte a cassé les chiffres (« 1 19 9 ,2 ») recollés quand le document en compte beaucoup ; chiffres d'une police
    sans table de caractères (codes de glyphes Ϭ…ϵ pour 0…9) remis en chiffres."""
    if sum(1 for ch in txt[:200000] if "\u03ec" <= ch <= "\u03f5") >= 30:
        txt = "".join(GLYPH_DIGITS.get(ch, ch) for ch in txt)
    if len(re.findall(r"\d ,\d|(?<!\d)\d{1,2} \d{1,2} ?,\d", txt)) >= 8:
        txt = BROKEN.sub(_join_broken, txt)
        txt = re.sub(r"(?<=\d) ,(?=\d{1,2}(?!\d))", ",", txt)
    if not ocr:
        return txt
    txt = re.sub(r"[|\[\]{}¦]", " ", txt)
    # reconnaissance de caractères : espaces des milliers perdus ou déplacés (« 1673 272 », « 50 701178 ») ->
    # groupes recollés quand ils ne forment pas déjà un montant régulier (1 à 3 chiffres puis groupes de 3)
    def _run(m):
        g = m.group(0).split(" ")
        if len(g[0]) <= 3 and all(len(x) == 3 for x in g[1:]):
            return m.group(0)
        j = "".join(g)
        return j if len(j) <= 13 else m.group(0)
    txt = re.sub(r"(?<![\d,.])\d+(?: \d+)+(?![\d,.])", _run, txt)
    txt = re.sub(r"(?<=\d)[)](?=\s|$)", " ", txt)
    txt = re.sub(r"(?<=\d) ?[.:;](?=\s{2,}|$)", " ", txt)
    return txt


# ---------------------------------------------------------------- découpage d'une ligne
LINE_CODE = re.compile(r"^(\s*)([A-Z]{2}|[A-Z](?=[0-9A-Z]{0,1}[0-9])[0-9A-Z]{2})(?=\s+\S|\s*$)")
NOT_CODE = {"LE", "LA", "DE", "DU", "ET", "EN", "AU", "OU", "IL", "UN", "NB", "PM", "AG", "CA"}


def _cells(line, skip=()):
    """Découpe une ligne en libellés et montants avec leur position (fin de colonne) ; « - » isolé = case vide.
    Un libellé séparé d'un autre par un grand blanc (deux tableaux côte à côte) forme sa propre cellule.
    Renvoie [(type, valeur, fin, début)] avec type L (libellé), N (montant), D (case vide), C (référence)."""
    out, pos = [], 0
    m = LINE_CODE.match(line)
    if m and (m.group(2) not in NOT_CODE or re.match(r"\s*CA\s+(?:capital|\d)", line, re.I)):
        out.append(("C", m.group(2), m.end(), m.start(2)))
        pos = m.end()

    def labels(gap, start, end):
        parts = [(mm.start(), mm.group(0)) for mm in re.finditer(r"\S+(?:\s{1,4}\S+)*", gap)]
        for k, (st_, part) in enumerate(parts):
            if re.fullmatch(r"[-−–—‐‑]+", part.strip()):
                out.append(("D", None, start + st_ + len(part), start + st_))
                continue
            txt_ = re.sub(r"(?<!\S)[-−–‐‑](?!\S)", " ", part)
            txt_ = re.sub(r"^\s*(?:-?\d+(?:[.,]\d+)?\s*%\s*)+", "", txt_).strip()
            if txt_.startswith("(") or re.search(r"\bsomme\b", txt_, re.I) or re.fullmatch(r"[(+\-/=: ]*(?:[A-Z]{1,2}\b[ +\-à=:]*)+\)?", txt_):
                continue  # formule de calcul (« (XB+RA+RB) », « (somme TK à RN) »), renvoi « (1) »
            if re.fullmatch(r"[+\-/ ]+|notes?|\d+|[a-z]", txt_.strip(), re.I):
                continue
            if re.search(r"[A-Za-zÀ-ÿ]{2}", txt_):
                out.append(("L", txt_, start + st_ + len(part), start + st_))
    for mm in NUM.finditer(line, pos):
        tok = mm.group(0)
        before = line[max(0, mm.start() - 1):mm.start()]
        after = line[mm.end():mm.end() + 2]
        if (before and (before.isalpha() or before in "/")) or (after[:1] and (after[:1].isalpha() or after[:1] in "%/")) \
                or after.strip()[:1] == "%" or mm.end() in skip:
            continue
        gap = line[pos:mm.start()]
        if _NOTE_DOT[0] and re.fullmatch(r"\d{1,2}\.\d{1,2}", tok.strip()):
            labels(gap, pos, mm.start())
            pos = mm.end()
            continue  # renvoi de note « 5.3 » dans un document où la virgule est le séparateur décimal
        if re.search(r"(?:^|\s)notes?\s*$", gap, re.I) and re.fullmatch(r"\d{1,2}(?:[.,]\d{1,2})?[a-z]?", tok.strip()):
            labels(gap[:re.search(r"(?:^|\s)notes?\s*$", gap, re.I).start()], pos, mm.start())
            pos = mm.end()
            continue  # renvoi de note (« Note 23 »)
        sign = 1
        g2 = gap.rstrip()
        if g2.endswith(("-", "−", "–", "‐", "‑")) and (len(g2) < 2 or g2[-2] == " ") and not tok.startswith("("):
            sign = -1
            gap = g2[:-1]
        labels(gap, pos, mm.start())
        v = num_val(tok)
        if v is not None:
            out.append(("N", sign * v, mm.end(), mm.start()))
        pos = mm.end()
    labels(line[pos:], pos, len(line))
    return out


def _hdr(line):
    """Années d'en-tête d'une ligne [(fin, début, année ou ('N', décalage))], si la ligne n'est faite que d'en-têtes."""
    n = nrm(line)
    hs = []
    for m in re.finditer(r"(?<![\d,.])(?:(?:\d{1,2})[-/. ]+(?:\d{1,2}|[a-z]{3,9}\.?)[-/. ]+)?((?:19[89]\d|20[0-3]\d)|\d{2})(?![\d%]|[,.]\d)", n):
        y = m.group(1)
        if len(y) == 2:
            if not re.search(r"[-/. ]$", n[:m.start(1)]) or m.start(1) == m.start():
                continue  # « 09 » seul n'est pas une année ; « 31-déc-09 » oui
            y = 2000 + int(y) if int(y) < 50 else 1900 + int(y)
        hs.append((m.end(), m.start(), int(y)))
    for m in re.finditer(r"(?<![a-z])(?:janv?|fevr?|mars|avr|mai|juin|juil|aout|sept?|oct|nov|dec)[a-z]*\.?[-/ ]+(\d{4}|\d{2})(?![\d%,])", n):
        y = int(m.group(1)) if len(m.group(1)) == 4 else 2000 + int(m.group(1))  # « Dec.-24 », « déc. 2024 »
        if 1990 <= y <= 2039 and not any(s0 <= m.start() < e0 for e0, s0, _ in hs):
            hs.append((m.end(), m.start(), y))
    for m in re.finditer(r"(?<=[\s(])(\d)[, ](\d{3})(?=\s|$)", n):  # « 2,009 », « 2 013 » (année imprimée avec séparateur de milliers)
        y = int(m.group(1) + m.group(2))
        if 1990 <= y <= 2039:
            hs.append((m.end(), m.start(), y))
    hs.sort()
    rest = n
    for e, s, _ in sorted(hs, reverse=True):
        rest = rest[:s] + " " * (e - s) + rest[e:]
    if hs and not re.search(r"\d{3,}", rest) and len(re.findall(r"\d", rest)) <= 4:
        return hs
    hn = [(m.end(), m.start(), ("N", -1 if m.group(1) else 0)) for m in re.finditer(r"(?<![a-z0-9])(?:exercice\s+|annee\s+)?n(\s?-\s?1)?(?![a-z0-9])", n)]
    if len(hn) >= 2 and not re.search(r"\d{3,}", n):
        return hn
    return []


def head_sec(p):
    """État annoncé par un titre (ou un titre de colonne) : actif, passif, compte de résultat, flux, hors bilan, bilan."""
    p = re.sub(r"\s+", " ", p).strip()
    if len(p) > 90 or re.search(r"\d{3}", re.sub(r"(?:19|20)\d\d|\d[ ,.]\d{3}", "", p)):
        return None
    p = re.sub(r"\s+", " ", re.sub(r"[^a-z' /-]|(?<![a-z])[-/](?![a-z])", " ", re.sub(r"(?:19|20)\d\d|\d[ ,.]\d{3}", " ", p))).strip()
    if re.search(r"tableau des flux|flux de tresorerie$|tableau financier|tafire|tableau (?:des )?emplois|^ressources$|^emplois$|tableau de financement", p):
        return S_FLX
    if re.search(r"compte de resultat|comptes? de resultats|compte d.exploitation|compte des resultats|etat du resultat|income statement|pertes et profits|^produits$|^charges$|^produits ?/ ?charges$|^charges ?/ ?produits$", p):
        return S_CR
    if re.search(r"hors.?bilan|^engagements|affectation du resultat|projet d.affectation|repartition des benefices|^affectation$", p):
        return "hb"
    if re.search(r"^(?:bilan[^a-z]*)?actif(?: du bilan)?(?: consolide)?$|^actif ?:?$|^assets$|^actif (?:[-(:] ?)?(?:en|montants?|donnees)\b|^actif -", p):
        return S_ACT
    if re.search(r"^(?:bilan[^a-z]*)?passi ?f(?: du bilan)?(?: consolide)?$|^passif et capitaux propres$|^capitaux propres et passifs$|^liabilities|^passif (?:[-(:] ?)?(?:en|montants?|donnees)\b|^passif -", p):
        return S_PAS
    if re.search(r"^bilan\b|situation financiere|balance sheet", p):
        return "bilan"
    return None


SEC_HEAD = [
    (S_FLX, re.compile(r"tableau des flux|flux de tresorerie$|tableau financier|tafire|tableau emplois|tableau des emplois")),
    (S_CR, re.compile(r"compte de resultat|comptes? de resultats|compte d.exploitation|compte des resultats|etat du resultat|income statement|compte de pertes et profits")),
    (S_ACT, re.compile(r"^(?:bilan[^a-z]*)?actif(?: du bilan)?(?: consolide)?$|^actif ?:?$|^assets$")),
    (S_PAS, re.compile(r"^(?:bilan[^a-z]*)?passif(?: du bilan)?(?: consolide)?$|^passif ?:?$|^passif et capitaux propres$|^capitaux propres et passifs$|^liabilities")),
    ("hb", re.compile(r"^hors.?bilan|^engagements")),
    ("bilan", re.compile(r"^bilan\b|^situation financiere|etat de la situation financiere|balance sheet")),
]


def parse(txt, fy_hint=None, title="", ocr=False):
    """{postes: {poste: {exercice: montant (unité du document)}}, unité, exercice, type, norme, périmètre, période…}"""
    txt = clean(txt, ocr)
    _COMMA_K[0] = len(re.findall(r"(?<![\d,.])\d{1,3}(?:,\d{3}){2,}(?![\d,])", txt)) >= 5 and \
        len(re.findall(r"(?<![\d,.])\d+,\d{1,2}(?![\d,])", txt)) <= len(re.findall(r"(?<![\d,.])\d{1,3}(?:,\d{3}){2,}(?![\d,])", txt)) // 10
    _NOTE_DOT[0] = not _COMMA_K[0] and len(re.findall(r"(?<![\d.,])\d{1,3},\d{1,2}(?![\d,.])", txt)) >= 20 and \
        len(re.findall(r"(?<![\d.,])\d{1,2}\.\d{1,2}(?![\d,.])", txt)) < len(re.findall(r"(?<![\d.,])\d{1,3},\d{1,2}(?![\d,.])", txt)) / 2
    fy = fiscal_year(txt, fy_hint)
    lines = txt.splitlines()
    nt_ = nrm(txt)
    revised = bool(re.search(r"^\s*xb\s+chiffre d.affaires|^\s*xi\s+resultat net \(xg", nt_, re.M))
    brut_tbl = False
    occ = []  # (poste, état, périmètre, ligne, {année: valeur}, ordre déduit ?)
    heads = []  # [(ligne, [(fin, début, année)])]
    sec, split, perim = None, None, None
    tt_ = nrm(title or "") + " " + nrm(txt[:3000])
    std_cur = "ifrs" if re.search(r"\bifrs\b|normes? internationales?", tt_) and not re.search(r"syscohada", nrm(title or "")) else "syscohada"
    order_votes = []
    pend = []
    single_hint = []
    for i, ln in enumerate(lines):
        if "\f" in ln:
            ln = ln.replace("\f", "")
        h = _hdr(ln)
        n_ = nrm(ln).strip()
        if h:
            # en-tête sur deux lignes (« EXERCICE 2025 » / « EXERCICE 2024 ») : regroupé avec la précédente
            if len(h) == 1 and heads and i - heads[-1][0] <= 3 and len(heads[-1][1]) == 1 and heads[-1][1][0][2] != h[0][2]:
                heads[-1] = (i, sorted(heads[-1][1] + h))
            else:
                heads.append((i, h))
            if re.search(r"\bbrut\b|amortissements?|amort\.|depreciations", n_):
                brut_tbl = True
        nb_ = nrm(ln)
        for e_, s0_, _ in (h or []):
            nb_ = nb_[:s0_] + " " * (e_ - s0_) + nb_[e_:]
        if not re.search(r"\d{3}", re.sub(r"(?:19|20)\d\d", "", nb_)):
            # titres d'états et sous-titres (actif / passif côte à côte, consolidé / social)
            titre_ = len(n_) <= 110 and re.search(r"bilan|compte|etat|tableau|resultat|flux|situation financiere", n_)
            if titre_ and re.search(r"consolid", n_) and not re.search(r"sociaux|individuel", n_):
                perim = "conso"
            elif titre_ and re.search(r"comptes? sociaux|etats financiers sociaux|individuels?|bilan social|compte de resultat social|societe mere", n_):
                perim = "social"
            if re.search(r"\bifrs\b|normes? internationales?", n_) and not re.search(r"syscohada", n_):
                std_cur = "ifrs"
            elif re.search(r"syscohada", n_) and not re.search(r"\bifrs\b", n_):
                std_cur = "syscohada"
            if re.search(r"\bbrut\b.*amort|amortissements?.*\bnet|\bbrut\b.*\bnet\b", n_):
                brut_tbl = True
            nl = nrm(ln)
            found_s, found_all = [], []
            for mm in re.finditer(r"\S+(?:\s{1,2}\S+)*", nl):
                s_ = head_sec(mm.group(0).strip(" :-"))
                if s_:
                    found_all.append((mm.start(), s_))
                if s_ and (not found_s or found_s[-1][1] != s_):
                    found_s.append((mm.start(), s_))
            if len(found_all) >= 2 and len({x[1] for x in found_all}) == 1 and found_all[0][1] not in ("bilan", "hb"):
                sec, split = found_all[0][1], None  # même état des deux côtés (« PRODUITS … CHARGES »)
            elif len(found_s) >= 2 and found_s[0][1] != found_s[1][1] and found_s[1][1] != "bilan":
                left = [e for e, _, _ in h if e < found_s[1][0]] if h else []
                s0 = S_ACT if found_s[0][1] == "bilan" else found_s[0][1]
                split = [(max(left) + 1) if left else max(0, found_s[1][0] - 12), s0, found_s[1][1]]
                sec = s0
            elif found_s:
                s_ = found_s[0][1]
                if s_ == "bilan":
                    sec = S_ACT if sec not in (S_ACT, S_PAS) else sec
                elif split:  # deux tableaux côte à côte : seul le côté du titre change d'état
                    if found_s[0][0] < split[0] - 5:
                        split[1] = sec = s_
                    else:
                        split[2] = s_
                elif s_ != sec or split:
                    sec, split = s_, None
                if s_ == S_PAS:
                    brut_tbl = False
        cells = _cells(ln, skip={e for e, _, _ in h} if h else set())
        code = cells[0][1] if cells and cells[0][0] == "C" else None
        segs = []  # [(code, libellé, [(valeur, fin)], début)]
        k = 0
        while k < len(cells):
            c = cells[k]
            if c[0] == "C":
                k += 1
                continue
            if c[0] == "L":
                lab = c[1]
                st_ = c[3]
                j = k + 1
                vals = []
                while j < len(cells) and cells[j][0] in ("N", "D"):
                    vals.append((cells[j][1], cells[j][2]))
                    j += 1
                segs.append((code if not segs else None, lab, vals, st_))
                k = j
                continue
            # montants sans libellé sur la ligne (libellé sur la ligne précédente ou référence seule)
            j = k
            vals = []
            while j < len(cells) and cells[j][0] in ("N", "D"):
                vals.append((cells[j][1], cells[j][2]))
                j += 1
            segs.append((code if not segs else None, "", vals, c[3]))
            k = j
        new_pend = []
        for si, (code_, lab, vals, st_) in enumerate(segs):
            s_here = sec
            if split and st_ is not None:
                if si > 0 and segs[si - 1][2] and st_ > 20:  # libellé qui suit des montants : tableau de droite
                    split[0] = min(split[0], st_)
                    s_here = split[2]
                else:
                    s_here = split[2] if st_ >= split[0] - 2 else split[1]
            if code_ and re.fullmatch(r"[A-Z]{2}", code_) and code_[0] in CODE_SEC:
                s_here = CODE_SEC[code_[0]]
            labn = re.sub(r"\s+", " ", nrm(lab)).strip(" :.-*•")
            labn = re.sub(r"\b([ldnjs])' +", r"\1'", labn)
            labn = re.sub(r"\s*\((?:[a-z]{1,2}|[ivx]+|\d)\)$", "", labn)  # renvoi de note « (1) », « (a) »
            labn = re.sub(r"^(?:[ivx]+|[a-h]|\d{1,2})[-.)] +", "", labn)  # numérotation « I. », « a) »
            labn = re.sub(r"\s*\(?(?:note|notes)\s*\d+[a-z]?\)?$", "", labn)
            labn = re.sub(r"\s+\d{1,2}(?:\.\d)?$", "", labn)  # numéro de note en fin de libellé
            nn_ = [v for v, _ in vals if v is not None]
            if len(nn_) >= 2 and vals[0][0] is not None and float(vals[0][0]).is_integer() and 0 < vals[0][0] < 100 \
                    and (all(abs(x) >= 10000 for x in nn_[1:]) or (_NOTE_DOT[0] and all(not float(x).is_integer() for x in nn_[1:3]))):
                vals = vals[1:]  # colonne des notes
            if not any(v is not None for v, _ in vals):
                if labn:
                    new_pend.append((labn, s_here))
                continue
            cands = []
            if labn:
                cands.append(labn)
            for p_, _ in pend[-2:][::-1]:
                cands.append((p_ + " " + labn).strip())
                if not labn:
                    cands.append(p_)
            key = None
            if code_ and re.fullmatch(r"[A-Z]{2}", code_):
                key = REF_CODES.get(code_) or (REF_CODES_REV.get(code_) if revised else None)
                if key == "resultat_net" and s_here == S_PAS:
                    key = "resultat_bilan"
            if key is None:
                for lab_ in cands:
                    for kk, secs, rx in ITEM_RX:
                        if rx.search(lab_) and (s_here in secs or s_here is None or None in secs or (s_here == "hb" and None in secs)):
                            key = kk
                            break
                    if key:
                        break
                if key is None and cands:
                    t0 = cands[0]
                    if re.fullmatch(r"total(?: general| bilan)?|total general \(?[ivx0-9 +]+\)?", t0):
                        key = {S_ACT: "total_actif", S_PAS: "total_passif"}.get(s_here, "_total")
                if key is None:
                    continue
            if key == "resultat_net" and s_here == S_PAS:
                key = "resultat_bilan"
            if key == "b_resultat_bilan":
                key = "resultat_bilan"
            yrs, how = _assign(vals, [] if ocr else heads, i, fy, brut_tbl and s_here == S_ACT)
            if how == "var":
                order_votes.append(yrs)
            if len([v for v, _ in vals if v is not None]) == 1 and not any(v is None for v, _ in vals):
                single_hint.append(1)
            elif len(vals) >= 2:
                single_hint.append(2)
            occ.append((key, s_here, (perim or "_") + ("_ifrs" if std_cur == "ifrs" else ""), i, yrs, how, vals))
            if os.environ.get("CPT_DEBUG"):
                print("   occ", i, key, s_here, perim, how, yrs, [v for v, _ in vals], repr(labn[:40]), code_)
        pend = new_pend[-2:] if new_pend else ([] if segs else pend)
    # sens des colonnes sans en-tête : d'après les colonnes de variation ; sinon N puis N-1
    # sens des colonnes : années d'en-tête qui se suivent (N puis N-1, ou l'inverse), sinon colonnes de variation
    hv = [0, 0]
    for _, hs in heads:
        seq = [y for _, _, y in hs if isinstance(y, int) and fy and y in (fy, fy - 1)]
        if len(seq) >= 2 and seq[0] != seq[1]:
            hv[seq[0] == fy - 1] += 1
    if hv[0] or hv[1]:
        asc = hv[1] > hv[0]
    else:
        asc = sum(1 for o in order_votes if o.get("asc")) > sum(1 for o in order_votes if o.get("desc"))
    single = single_hint.count(1) > 2 * single_hint.count(2)
    found, alt, ranks = {}, {}, {}
    for key, s_here, per, i, yrs, how, vals in occ:
        if how in ("order", "single"):
            nums = [v for v, _ in vals if v is not None]
            if how == "single" and not single:
                continue
            if fy is None:
                continue
            if how == "single":
                yrs = {fy: nums[0]}
            else:
                pair = (nums[0], nums[1])
                yrs = {fy: pair[1], fy - 1: pair[0]} if asc else {fy: pair[0], fy - 1: pair[1]}
        yrs = {y: v for y, v in yrs.items() if isinstance(y, int)}
        if not yrs:
            continue
        pk = per
        d = found.setdefault(pk, {})
        if key in ("total_actif", "total_passif", "_total"):
            alt.setdefault(pk, {}).setdefault(key, []).append(yrs)
            continue
        rank = 0 if s_here in SECS.get(key, ()) else 1
        if key not in d:
            d[key] = yrs
            ranks[(pk, key)] = rank
        elif key == "resultat_net" and "resultat_bilan" not in d and s_here is None:
            d["resultat_bilan"] = yrs
            ranks[(pk, "resultat_bilan")] = 1
        elif rank < ranks.get((pk, key), 1):  # le poste figure dans son état : cette occurrence l'emporte
            d[key] = yrs
            ranks[(pk, key)] = rank
        elif rank == ranks.get((pk, key), 1) and all(abs(d[key][y] - v) <= 0.5 for y, v in yrs.items() if y in d[key]) and any(y in d[key] for y in yrs):
            for y, v in yrs.items():  # même poste, mêmes montants : exercices complétés
                d[key].setdefault(y, v)
    for pk, d in found.items():  # « PERTE » (compte de résultat bancaire) : résultat négatif
        for y, v in (d.pop("perte_nette", None) or {}).items():
            if v and not (d.get("resultat_net") or {}).get(y):
                d.setdefault("resultat_net", {})[y] = -abs(v)
    for pk, a in alt.items():  # totaux : le plus grand de l'état (les sous-totaux sont plus petits)
        d = found.setdefault(pk, {})
        tots = a.get("_total", [])
        for key in ("total_actif", "total_passif"):
            cand = a.get(key, [])
            if not cand and len(tots) >= 2:  # « TOTAL » sans état connu : 1re occurrence = actif, 2e = passif
                cand = [tots[0]] if key == "total_actif" else [tots[1]]
            if cand:
                ys = {}
                for c in cand:
                    for y, v in c.items():
                        if y not in ys or abs(v) > abs(ys[y]):
                            ys[y] = v
                d[key] = ys
    items = found.get("conso") or {}
    perims = {k: v for k, v in found.items() if v}
    for suf in ("", "_ifrs"):  # périmètre non annoncé : comptes de la société (sociaux)
        if "_" + suf in perims:
            if "social" + suf not in perims:
                perims["social" + suf] = perims.pop("_" + suf)
            else:
                for k, v in perims.pop("_" + suf).items():
                    perims["social" + suf].setdefault(k, v)
    main = max(perims, key=lambda k: len(perims[k])) if perims else "social"
    items = perims.get(main, {})
    bank = sum(1 for k in items if k.startswith("b_")) >= 3
    unit = unit_of(txt)
    cap = capital_stated(txt)
    cv = (items.get("capital") or items.get("b_capital") or {})
    cv = cv.get(fy) if fy in cv else (next(iter(cv.values())) if cv else None)
    if cap and cv:  # le capital du bilan, multiplié par l'unité, doit redonner le capital annoncé
        for u in (1.0, 1e3, 1e6):
            if abs(cv * u / cap - 1) < 0.005:
                unit = u
                break
    nt = nrm(txt[:8000])
    cur = "USD" if re.search(r"(?:milliers|millions) de dollars|en (?:k|m)?usd\b|us\$|\busd ?(?:000|thousand|million)|thousands of us dollars|in thousands of usd", nt) else "XOF"
    std = "ifrs" if main.endswith("_ifrs") else "syscohada"
    return {"items": items, "perims": perims, "main": main, "unit": unit, "cap": cap, "fy": fy, "type": "banque" if bank else "entreprise",
            "cur": cur, "per": doc_kind(txt, title), "std": std, "revised": revised}


def _assign(vals, heads, i, fy, brut):
    """Montants d'une ligne -> {exercice: montant}, et la règle employée."""
    nums = [(v, e) for v, e in vals if v is not None]
    if not nums:
        return {}, None
    if brut and len(vals) >= 3:
        # actif : brut, amortissements, net N, net N-1 (le net se vérifie : brut - amortissements = net)
        v = [x for x, _ in vals]
        z = [0 if x is None else x for x in v]
        if len(v) >= 4 and v[2] is not None and abs(z[0] - abs(z[1]) - z[2]) <= max(2, abs(z[0]) * 1e-6) and fy:
            return ({fy: v[2], fy - 1: v[3]} if v[3] is not None else {fy: v[2]}), "brut"
        if len(v) == 3 and v[2] is not None and abs(z[0] - abs(z[1]) - z[2]) <= max(2, abs(z[0]) * 1e-6) and fy:
            return {fy: v[2]}, "brut"
    recent = [h for h in heads if 0 <= i - h[0] < 160][-3:]
    out = {}
    if recent:
        for v, xe in nums:
            best = None
            for _, hs in reversed(recent):
                for he, hs_, yr in hs:
                    d = min(abs(he - xe), abs((he + hs_) / 2 - (xe - len(str(abs(int(v)))) * 0.66)))
                    if d <= 12 and (best is None or d < best[0]):
                        best = (d, yr)
                if best:
                    break
            if best:
                yr = best[1]
                if isinstance(yr, tuple):
                    if not fy:
                        continue
                    yr = fy + yr[1]
                if yr not in out:
                    out[yr] = v
        if out:
            if fy and not any(y in (fy, fy - 1) for y in out):
                return {}, None
            return out, "hdr"
    if len(nums) >= 3:
        a, b, c = nums[0][0], nums[1][0], nums[2][0]
        if abs(a - b - c) <= max(2, abs(a) * 1e-5) and abs(c) > 0:
            return {"desc": 1}, "var"
        if abs(b - a - c) <= max(2, abs(b) * 1e-5) and abs(c) > 0:
            return {"asc": 1}, "var"
    if len(nums) == 2 or (len(nums) >= 2 and len(vals) >= 2):
        return {}, "order"
    if len(nums) == 1 and len(vals) == 1:
        return {}, "single"
    return {}, None


# ---------------------------------------------------------------- contrôle : identités comptables
ACT_PARTS = ("charges_immobilisees", "immo_incorp", "immo_corp", "immo_fin", "actif_circulant_hao", "stocks", "creances", "tresorerie_actif")
STRONG = ("actif = passif", "résultat CR = bilan", "RN = RAO + HAO - impôt", "RN = résultat avant impôt - impôt", "RN = RE + RF + HAO - impôt", "RN = RAO - impôt")


def checks(items, year, bank=False):
    """Identités vérifiées pour un exercice : liste de (nom, écart relatif)."""
    g = lambda k: (items.get(k) or {}).get(year)  # noqa: E731
    res = []

    def rel(a, b):
        if a is None or b is None:
            return None
        den = max(abs(a), abs(b), 1.0)
        return abs(a - b) / den
    for nm, a, b in (("actif = passif", g("total_actif"), g("total_passif")), ("résultat CR = bilan", g("resultat_net"), g("resultat_bilan"))):
        r = rel(a, b)
        if r is not None:
            res.append((nm, r))
    if g("valeur_ajoutee") is not None and g("charges_personnel") is not None and g("ebe") is not None:
        res.append(("EBE = VA - personnel", rel(g("valeur_ajoutee") - abs(g("charges_personnel")), g("ebe"))))
    imp = abs(g("impots_resultat") or 0) + abs(g("participation") or 0)
    if g("rao") is not None and g("rhao") is not None and g("resultat_net") is not None:
        res.append(("RN = RAO + HAO - impôt", rel(g("rao") + g("rhao") - imp, g("resultat_net"))))
    elif g("resultat_exploitation") is not None and g("resultat_financier") is not None and g("rhao") is not None and g("resultat_net") is not None:
        res.append(("RN = RE + RF + HAO - impôt", rel(g("resultat_exploitation") + g("resultat_financier") + g("rhao") - imp, g("resultat_net"))))
    if g("rao") is not None and g("rhao") is None and g("impots_resultat") is not None and g("resultat_net") is not None:
        r_ = rel(g("rao") - imp, g("resultat_net"))  # comptes sans éléments hors activités ordinaires (IFRS) : retenue si elle se vérifie
        if r_ is not None and r_ <= 0.001:
            res.append(("RN = RAO - impôt", r_))
    if g("rao") is not None and g("resultat_exploitation") is not None and g("resultat_financier") is not None:
        res.append(("RAO = RE + RF", rel(g("resultat_exploitation") + g("resultat_financier"), g("rao"))))
    if g("resultat_avant_impot") is not None and g("impots_resultat") is not None and g("resultat_net") is not None:
        res.append(("RN = résultat avant impôt - impôt", rel(g("resultat_avant_impot") - abs(g("impots_resultat")), g("resultat_net"))))
    # sommes des postes du bilan : retenues seulement quand elles se vérifient (elles confirment alors chaque poste lu)
    for nm, tot, parts, need in (("actif = somme des postes", "total_actif", ACT_PARTS, ("immo_corp", "tresorerie_actif")),
                                 ("actif = somme des masses", "total_actif", ("actif_immobilise", "actif_circulant", "tresorerie_actif"), ("actif_immobilise", "actif_circulant", "tresorerie_actif")),
                                 ("passif = somme des masses", "total_passif", ("capitaux_propres", "dettes_financieres", "passif_circulant", "tresorerie_passif"), ("capitaux_propres", "dettes_financieres", "passif_circulant", "tresorerie_passif")),
                                 ("passif = ressources stables + dettes", "total_passif", ("ressources_stables", "passif_circulant", "tresorerie_passif"), ("ressources_stables", "passif_circulant", "tresorerie_passif"))):
        if g(tot) is not None and all(g(k) is not None for k in need):
            r_ = rel(sum(g(k) or 0 for k in parts), g(tot))
            if r_ is not None and r_ <= 0.0005:
                res.append((nm, r_))
    if g("b_pnb") is not None and g("b_charges_generales") is not None and g("b_rbe") is not None:
        res.append(("RBE ≤ PNB", 0.0 if abs(g("b_rbe")) <= abs(g("b_pnb")) else 1.0))
    if g("capitaux_propres") is not None and g("total_passif") is not None:
        res.append(("capitaux propres ≤ total", 0.0 if abs(g("capitaux_propres")) <= abs(g("total_passif")) * 1.0001 else 1.0))
    if g("chiffre_affaires") is not None and g("ventes_marchandises") is not None and g("ventes_produits") is not None and g("travaux_services") is not None:
        s_ = g("ventes_marchandises") + g("ventes_produits") + g("travaux_services") + (g("produits_accessoires") or 0)
        res.append(("CA = somme des ventes", rel(s_, g("chiffre_affaires"))))
    return res


def validate(parsed, year, items=None):
    """Exercice retenu si au moins une identité forte se vérifie à 0,1 % et qu'aucune ne s'écarte de plus de 1 %."""
    c = checks(items if items is not None else parsed["items"], year, parsed.get("type") == "banque")
    strong = [r for n, r in c if n in STRONG]
    ok = bool(strong) and min(strong) <= 0.001 and all(r <= 0.01 for _, r in c)
    return ok, c


# ---------------------------------------------------------------- consolidation des documents
CHARGES = {"charges_personnel", "dotations", "frais_financiers", "impots_resultat", "participation", "capex_corp", "capex_incorp",
           "dividendes_verses", "b_interets_charges", "b_commissions_charges", "b_charges_generales"}


def unit_choice(P, items, y):
    """Unité des montants : annoncée ou déduite du capital, si l'ordre de grandeur du total du bilan la confirme ;
    sinon la seule unité plausible (total du bilan entre 0,3 et 60 000 milliards de FCFA). None si plusieurs restent possibles."""
    tot = (items.get("total_actif") or {}).get(y) or (items.get("total_passif") or {}).get(y)
    ca = (items.get("chiffre_affaires") or items.get("b_pnb") or {}).get(y)
    if tot:
        cands = [u for u in (1.0, 1e3, 1e6, 1e9) if 3e8 <= abs(tot) * u <= 6e13]
    elif ca:
        cands = [u for u in (1.0, 1e3, 1e6, 1e9) if 5e7 <= abs(ca) * u <= 1e13]
    else:
        cands = []
    if P.get("unit") in cands:
        return P["unit"], cands
    if len(cands) == 1:
        return cands[0], cands
    return None, cands


def read_doc(texts, meta):
    """Lecture d'un document (texte, et OCR français / anglais le cas échéant) : exercices vérifiés, montants dans l'unité
    du document (unit = 1, 1e3 ou 1e6 FCFA ; None si l'ordre de grandeur reste à confirmer par une autre source)."""
    fy_hint = meta.get("fy")
    title = meta.get("ti") or ""
    best = None
    for src, (txt, ocr) in texts.items():
        if not txt or len(txt.strip()) < 200:
            continue
        try:
            P = parse(txt, fy_hint=fy_hint, title=title, ocr=ocr)
        except Exception:  # noqa: BLE001
            continue
        res = {}
        for per, items in P["perims"].items():
            yrs = sorted({y for v in items.values() for y in v}, reverse=True)
            for y in yrs[:2]:
                ok, c = validate(P, y, items)
                if ok:
                    res.setdefault(per, {})[y] = [(n, round(r, 5)) for n, r in c]
        score = sum(len(v) for v in res.values()) * 100 + len(P["items"])
        if best is None or score > best[0]:
            best = (score, src, P, res)
    if not best:
        return {"st": "illisible"}
    _, src, P, res = best
    out = {"st": "ok" if res else "non vérifié", "src": src, "fy": P["fy"], "per": P["per"], "std": P["std"], "type": P["type"],
           "cur": P["cur"], "main": P["main"], "n": len(P["items"]), "y": {}}
    if P["cur"] != "XOF":
        out["st"] = "devise " + P["cur"]
        return out
    # OCR : un montant n'est gardé que si les deux lectures (français, anglais) donnent le même chiffre,
    # ou s'il entre dans une identité comptable vérifiée
    other = None
    alt_src = "eng" if src == "fra" else "fra"
    if src in ("fra", "eng") and texts.get(alt_src, (None,))[0]:
        try:
            other = parse(texts[alt_src][0], fy_hint=fy_hint, title=title, ocr=True)
        except Exception:  # noqa: BLE001
            other = None
    for per, yrs in res.items():
        items = P["perims"][per]
        for y, chk in yrs.items():
            ok_id = {k for n, r in chk if r <= 0.001 for k in IDENT_KEYS.get(n, ())}
            rec = {}
            for k, v in items.items():
                if y not in v:
                    continue
                x = v[y]
                if src in ("fra", "eng"):
                    ov = ((other["perims"].get(per) or {}).get(k) or {}).get(y) if other else None
                    if k not in ok_id and (ov is None or abs(ov - x) > 0.5):
                        continue
                rec[k] = abs(x) if k in CHARGES else x
            unit, cands = unit_choice(P, items, y)
            out["y"].setdefault(per, {})[str(y)] = {"v": rec, "c": chk, "u": unit, "uc": cands}
    return out


IDENT_KEYS = {"actif = passif": ("total_actif", "total_passif"), "résultat CR = bilan": ("resultat_net", "resultat_bilan"),
              "RN = RAO + HAO - impôt": ("rao", "rhao", "impots_resultat", "participation", "resultat_net"),
              "RN = RE + RF + HAO - impôt": ("resultat_exploitation", "resultat_financier", "rhao", "impots_resultat", "participation", "resultat_net"),
              "RN = résultat avant impôt - impôt": ("resultat_avant_impot", "impots_resultat", "resultat_net"),
              "RN = RAO - impôt": ("rao", "impots_resultat", "participation", "resultat_net"),
              "actif = somme des postes": ("total_actif",) + ACT_PARTS,
              "actif = somme des masses": ("total_actif", "actif_immobilise", "actif_circulant", "tresorerie_actif"),
              "passif = somme des masses": ("total_passif", "capitaux_propres", "dettes_financieres", "passif_circulant", "tresorerie_passif"),
              "passif = ressources stables + dettes": ("total_passif", "ressources_stables", "passif_circulant", "tresorerie_passif"),
              "EBE = VA - personnel": ("valeur_ajoutee", "charges_personnel", "ebe"), "RAO = RE + RF": ("rao", "resultat_exploitation", "resultat_financier"),
              "CA = somme des ventes": ("chiffre_affaires", "ventes_marchandises", "ventes_produits", "travaux_services", "produits_accessoires")}


# ---------------------------------------------------------------- consolidation : un jeu de comptes par société et par exercice
def _doc_rank(r, y):
    """Préférence entre documents pour un exercice : comptes de l'exercice lui-même (plutôt que la colonne N-1 du suivant),
    définitifs (certifiés, approuvés) plutôt que provisoires, puis le plus récent (un document qui « annule et remplace »)."""
    ti = nrm(r.get("ti") or "")
    own = 1 if r.get("fy") == y else 0
    final = 0 if re.search(r"provisoire|non audite|efp\b|_efp_|- efp -", ti) else 1
    if re.search(r"certifi|approuv|audite|definiti|efa\b|_efa_|- efa -|annule et remplace", ti):
        final = 2
    return (own, final, r.get("d") or "")


def consolidate(cj, mirror=None):
    """comptes.json (documents lus) -> {titre: {"y": {exercice: {"v": {poste: millions de FCFA}, "n", "d", "own"}}, "per", "std",
    "agree" (part des montants communs égaux à ceux de la base de référence), "ncmp" (nombre de montants comparés)}}.
    Unité : celle du document quand elle est sûre, sinon celle qui fait concorder ses montants avec un autre document de la
    même société (même exercice), sinon avec la base de référence (mirror : {titre: {série: {exercice: millions}}})."""
    recs = []
    for u, r in (cj.get("docs") or {}).items():
        if not r.get("y") or r.get("per") != "annuel" or r.get("cur", "XOF") != "XOF" or not r.get("t"):
            continue
        for per, ys in r["y"].items():
            for y, x in ys.items():
                recs.append({"t": r["t"], "y": int(y), "per": per, "std": "ifrs" if per.endswith("_ifrs") else "syscohada", "u": x.get("u"), "uc": x.get("uc") or [],
                             "v": x.get("v") or {}, "c": x.get("c"), "doc": u, "rank": _doc_rank(r, int(y)), "d": r.get("d")})
    known = {}
    for x in recs:
        if x["u"]:
            for k in ("total_actif", "resultat_net", "chiffre_affaires", "b_pnb", "capitaux_propres"):
                if x["v"].get(k):
                    known.setdefault((x["t"], x["y"], x["per"], x["std"], k), []).append(x["v"][k] * x["u"])
    MS = {"total_actif": "total_bilan", "resultat_net": "resultat_net", "chiffre_affaires": "ca", "b_pnb": "ca", "capitaux_propres": "capitaux_propres"}
    for x in recs:
        if x["u"]:
            continue
        for cand in x["uc"]:
            hit = 0
            for k, mk in MS.items():
                v = x["v"].get(k)
                if not v:
                    continue
                for kv in known.get((x["t"], x["y"], x["per"], x["std"], k), []):
                    if abs(v * cand - kv) <= abs(kv) * 0.002:
                        hit += 1
                mv = (((mirror or {}).get(x["t"]) or {}).get(mk) or {}).get(str(x["y"]))
                if mv and abs(v * cand / 1e6 - mv) <= abs(mv) * 0.01 + 0.5:
                    hit += 1
            if hit:
                x["u"] = cand
                break
    recs = [x for x in recs if x["u"]]
    out = {}
    by_t = {}
    for x in recs:
        x["m"] = {k: round(v * x["u"] / 1e6, 3) for k, v in x["v"].items()}
        by_t.setdefault(x["t"], []).append(x)
    for t, xs in by_t.items():
        # périmètre et norme : ceux qui concordent le mieux avec la base de référence, sinon ceux qui couvrent le plus d'exercices
        groups = {}
        for x in xs:
            groups.setdefault((x["per"], x["std"]), []).append(x)

        def agree(g):
            ok = n = 0
            for x in g:
                for k, mk in (("chiffre_affaires", "ca"), ("b_pnb", "ca"), ("resultat_net", "resultat_net"), ("total_actif", "total_bilan")):
                    mv = (((mirror or {}).get(t) or {}).get(mk) or {}).get(str(x["y"]))
                    if mv and x["m"].get(k) is not None:
                        n += 1
                        ok += abs(x["m"][k] - mv) <= abs(mv) * 0.01 + 0.5
            return (ok / n if n else 0, len({x["y"] for x in g}), g[0]["std"] == "syscohada", n)
        main = max(groups, key=lambda k: agree(groups[k])[:3])
        ag = agree(groups[main])
        res = {}
        for y in sorted({x["y"] for x in groups[main]}):
            cand = sorted([x for x in groups[main] if x["y"] == y], key=lambda x: x["rank"], reverse=True)
            best = cand[0]
            v = dict(best["m"])
            n_ok = 1
            for o in cand[1:]:  # autres documents : confirmation, et postes complétés s'ils donnent les mêmes montants communs
                com = [k for k in ("total_actif", "resultat_net", "chiffre_affaires", "b_pnb", "capitaux_propres") if k in v and k in o["m"]]
                if com and all(abs(v[k] - o["m"][k]) <= max(0.5, abs(v[k]) * 0.001) for k in com):
                    n_ok += 1
                    for k, val in o["m"].items():
                        v.setdefault(k, val)
            res[y] = {"v": v, "n": n_ok, "d": best["d"], "own": best["rank"][0]}
        out[t] = {"y": res, "per": main[0].replace("_ifrs", ""), "std": main[1], "agree": round(ag[0], 3), "ncmp": ag[3]}
    return out


def run_dir(d):
    """Relit tous les textes en cache (index.json, txt/) et écrit comptes.json : documents lus et exercices validés."""
    ip = os.path.join(d, "index.json")
    idx = json.load(open(ip, encoding="utf8")) if os.path.exists(ip) else {"docs": {}}
    docs = {}
    for u, m in idx.get("docs", {}).items():
        h = m.get("h")
        if not h:
            continue
        texts = {}
        for src, ocr in (("txt", False), ("fra", True), ("eng", True)):
            p_ = os.path.join(d, "txt", f"{h}.{src}.gz" if src != "txt" else f"{h}.txt.gz")
            if os.path.exists(p_):
                texts[src] = (gzip.open(p_, "rt", encoding="utf8").read(), ocr)
        if not texts:
            continue
        r = read_doc(texts, m)
        r.update({"t": m.get("t"), "d": m.get("d"), "ti": m.get("ti"), "cat": m.get("cat")})
        docs[u] = r
    out = {"v": READER_V, "docs": docs}
    with open(os.path.join(d, "comptes.json"), "w", encoding="utf8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    n_ok = sum(1 for r in docs.values() if r.get("st") == "ok")
    print(f"[comptes] {len(docs)} documents relus, {n_ok} avec au moins un exercice vérifié", flush=True)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    run_dir(ap.parse_args().dir)
    sys.exit(0)
