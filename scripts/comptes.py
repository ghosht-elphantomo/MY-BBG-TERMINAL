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
    ("total_actif", (S_ACT, None), r"^total ?(?:general ?)?(?:de ?l.? ?)?actif$|^total general actif$|^total bilan actif$|^total (?:des )?actifs$|^total assets$|^actif total$"),
    # ---- bilan passif (SYSCOHADA)
    ("capital", (S_PAS,), r"^capital(?: social| souscrit(?: appele)?)?$"),
    ("primes_reserves", (S_PAS,), r"^primes et reserves$"),
    ("reserves", (S_PAS,), r"^reserves$"),
    ("report_nouveau", (S_PAS,), r"^report a nouveau"),
    ("capitaux_propres", (S_PAS,), r"^(?:total )?capitaux propres(?: et ressources assimilees| et assimiles)?(?: et)?$|^total des capitaux propres$|^total equity$"),
    ("cp_groupe", (S_PAS,), r"^(?:total )?capitaux propres(?:[ ,-]+part (?:du )?groupe| attribuables aux (?:actionnaires|proprietaires) de la (?:societe|maison)? ?mere| attribuables aux (?:actionnaires|proprietaires) de la societe)$"),
    ("interets_minoritaires", (S_PAS,), r"^(?:capitaux propres attribuables aux |total )?(?:participations|interets) ne donnant pas le controle$|^interets minoritaires$"),
    ("dettes_financieres", (S_PAS,), r"^(?:total )?dettes financieres(?: et ressources assimilees)?(?: et)?$|^total dettes et res\. assimilees$"),
    ("ressources_stables", (S_PAS,), r"^(?:total )?ressources stables$"),
    ("passif_circulant", (S_PAS,), r"^(?:total )?passif circulant$"),
    ("fournisseurs", (S_PAS,), r"^fournisseurs(?: d.exploitation)?$"),
    ("tresorerie_passif", (S_PAS,), r"^(?:total )?tresorerie ?- ?passif$|^(?:total )?tresorerie passif$"),
    ("total_passif", (S_PAS, None), r"^total ?(?:general ?)?(?:du ?)?passif$|^total general passif$|^total bilan passif$|^total (?:des |du )?(?:capitaux propres et (?:des )?passifs?|passifs? et (?:des )?capitaux propres)$|^total liabilities and (?:shareholders. )?equity$|^passif total$|^total capitaux propres et passifs$"),
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
    ("impots_resultat", (S_CR,), r"^impots? [sd]ur (?:le |les )?(?:resultats?|benefices?|societes)$|^impot sur le resultat$|^charges? d.impots?(?: sur le resultat)?$|^impots? exigibles? et differes?$"),
    ("perte_nette", (S_CR,), r"^perte(?: nette)?(?: de l.exercice)?$"),
    ("quote_part_mee", (S_CR,), r"^quote.?part (?:dans |du |des )?(?:le |les )?resultats? (?:net )?(?:des |dans les )?(?:societes|entreprises|entites|participations)(?: mises en(?: equivalence)?| associees| en equivalence)?$"),
    ("resultat_avant_impot", (S_CR,), r"^resultat avant impots?(?: sur le resultat| et participation)?$|^resultat (?:net )?avant impots?$"),
    # « Résultat net » : compte de résultat ou bilan selon l'état où il figure
    ("resultat_net", (S_CR, S_PAS, None), r"^(?:resultat net(?: de l.exercice| l.exercice| de la periode| consolide| comptable| de l.ensemble consolide| total)?|resultat de l.exercice|benefice(?: net)?(?: de l.exercice)?|benefice ou perte|resultat net \(?benefice.*|profit for the (?:year|period))$"),
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
    ("b_resultat_bilan", (S_PAS,), r"^resultat de l.exercice ?\(\+ ?/ ?-\)$"),
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


UNIT_LINE = re.compile(r"(?:\(|\ben\b|montants?|donnees|chiffres|valeurs|unite ?:?)\s*(?:en\s+|de\s+)?(milliards?|millions?|milliers?|mds?|mxof|kxof|mfcfa|kfcfa|"
                       r"francs? cfa|fcfa|f\.? ?cfa|xof)\b")


def line_units(n):
    """Unités annoncées par un en-tête de tableau (« (en millions de FCFA) », « Données en milliers ») : [(position, facteur)].
    Une ligne qui porte des montants n'est pas un en-tête (sauf les années)."""
    rest = re.sub(r"\b(?:19|20)\d\d\b|(?<![\d ,])[12][ ,]0\d\d\b", " ", n)
    if re.search(r"\d{1,3}(?:[ .,]\d{3})+|\b\d{3,}\b|\d,\d", rest) or re.search(r"par action|nominal|dividende|cours", n):
        return []
    out = []
    for m in UNIT_LINE.finditer(n):
        w = m.group(1)
        f = 1e9 if w.startswith("milliard") or w.startswith("md") else 1e6 if w.startswith("million") or w in ("mxof", "mfcfa") \
            else 1e3 if w.startswith("millier") or w in ("kxof", "kfcfa") else 1.0
        out.append((m.start(), f))
    return out


def doc_kind(txt, title=""):
    """Annuel, semestriel ou trimestriel : d'après le titre de la publication d'abord (« 1er semestre 2026 »), sinon d'après
    les dates de clôture des colonnes (30 juin, 31 mars, 30 septembre). Un document qui joint aux comptes annuels l'activité
    du premier trimestre suivant reste annuel."""
    ti = re.sub(r"[_]+", " ", nrm(title or ""))
    annual_t = re.search(r"exercice\s*\d{4}|etats financiers(?: provisoires?| definitifs?| certifies| approuves| annuels)*\s*\d{4}|annuel", ti)
    if re.search(r"semestr|half.year", ti) and not (annual_t and re.search(r"et (?:le |du )?(?:rapport|activite).*semestr", ti)):
        return "semestre"
    if re.search(r"trimestr|quarter", ti) and not annual_t:
        return "trimestre"
    if annual_t:
        return "annuel"
    t = nrm(txt[:6000])
    if re.search(r"(?:au |clos le |arrete au |situation au )?30 ?(?:juin|/06/|-06-|\.06\.)\s*\d{2,4}|1er semestre|premier semestre|semestriel", t) and not re.search(r"31 ?(?:decembre|/12/|-12-)\s*\d{2,4}", t[:3000]):
        return "semestre"
    if re.search(r"(?:31 ?(?:mars|/03/)|30 ?(?:septembre|/09/))\s*\d{2,4}", t) and not re.search(r"31 ?(?:decembre|/12/|-12-)\s*\d{2,4}", t[:3000]):
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

    # espaces des milliers perdus ou déplacés (« 1673 272 », « 50 701178 », « 2 05 4 491 ») -> groupes recollés quand ils ne
    # forment pas déjà un montant régulier (1 à 3 chiffres puis groupes de 3) ; toujours après reconnaissance de caractères,
    # et dans la couche texte quand le document en compte plusieurs
    def _irr(g):
        return not (len(g[0]) <= 3 and all(len(x) == 3 for x in g[1:]))

    def _run(m):
        g = m.group(0).split(" ")
        if not _irr(g):
            return m.group(0)
        j = "".join(g)
        return j if len(j) <= 13 else m.group(0)
    RUN = r"(?<![\d,.])\d+(?: \d+)+(?![\d,.])"

    if not ocr:
        if sum(1 for m in re.finditer(RUN, txt) if _irr(m.group(0).split(" ")) and len(m.group(0).split(" ")[-1]) < 3) >= 5:
            txt = re.sub(RUN, _run, txt)
        return txt
    txt = re.sub(r"[|\[\]{}¦]", " ", txt)
    txt = re.sub(RUN, _run, txt)
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
    # dates en toutes lettres (« 31 décembre 2021 ») : ni montant ni libellé
    line = re.sub(r"(?i)(?<![\d,.])\d{1,2}(?:er)? ?(?:[-/.] ?)?(?:janv|f[ée]vr|mars|avr|mai|juin|juil|ao[uû]t|sept|oct|nov|d[ée]c)[a-zéû]*\.?"
                  r"(?: ?(?:[-/.] ?)?(?:19|20)?\d\d(?![\d,.]))?(?![a-z])", lambda m_: " " * len(m_.group(0)), line)
    # renvois de notes à plusieurs niveaux (« 6.3.11 ») : ni montant ni libellé
    line = re.sub(r"(?<![\d.,])\d{1,2}(?:\.\d{1,2}){2,}(?![\d.,])", lambda m_: " " * len(m_.group(0)), line)
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
    for m in re.finditer(r"(?<![\d,.])(?:(?:\d{1,2})(?: ?[-/.] ?| {1,2})(?:\d{1,2}|(?:janv?|fevr?|mars|avr|mai|juin|juil|aout|sept?|oct|nov|dec)[a-z]{0,6}\.?)(?: ?[-/.] ?| {1,2}))?((?:19[89]\d|20[0-3]\d)|\d{2})(?![\d%]|[,.]\d)", n):
        y = m.group(1)
        if len(y) == 2:
            if not re.search(r"[-/. ]$", n[:m.start(1)]) or m.start(1) == m.start():
                continue  # « 09 » seul n'est pas une année ; « 31-déc-09 » oui
            y = 2000 + int(y) if int(y) < 50 else 1900 + int(y)
        hs.append((m.end(), m.start(), int(y)))
    for m in re.finditer(r"(?<![a-z])(?:janv?|fevr?|mars|avr|mai|juin|juil|aout|sept?|oct|nov|dec)[a-z]*\.?(?: ?[-/] ?| {1,2})(\d{4}|\d{2})(?![\d%,])", n):
        y = int(m.group(1)) if len(m.group(1)) == 4 else 2000 + int(m.group(1))  # « Dec.-24 », « déc. 2024 »
        if 1990 <= y <= 2039 and not any(s0 <= m.start() < e0 for e0, s0, _ in hs):
            hs.append((m.end(), m.start(), y))
    for m in re.finditer(r"(?<![\d,.])(19[89]|20[0-3]) (\d)(?![\d,.%])", n):  # « 202 4 » (année coupée par la couche texte)
        y = int(m.group(1) + m.group(2))
        if not any(s0 <= m.start() < e0 for e0, s0, _ in hs):
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
    if re.search(r"tableau (?:[a-z]+ )?des flux|flux de tresorerie$|tableau financier|tafire|tableau (?:des )?emplois|^ressources$|^emplois$|tableau de financement", p):
        return S_FLX
    if re.search(r"compte de resultat|comptes? de resultats|compte d.exploitation|compte des resultats|etat du resultat|income statement|pertes et profits|^produits$|^charges$|^produits ?/ ?charges$|^charges ?/ ?produits$|^debit$|^credit$", p):
        return S_CR
    if re.search(r"hors.?bilan|^engagements|affectation du resultat|projet d.affectation|repartition des benefices|^affectation$", p):
        return "hb"
    if re.search(r"^(?:bilan[^a-z]*)?actifs?(?: du bilan)?(?: consolide)?$|^actif ?:?$|^assets$|^actif (?:[-(:] ?)?(?:en|montants?|donnees)\b|^actif -", p):
        return S_ACT
    if re.search(r"^(?:bilan[^a-z]*)?passi ?fs?(?: du bilan)?(?: consolide)?$|^passifs? (?:et )?capitaux propres$|^capitaux propres (?:et )?passifs?$|^liabilities|^passif (?:[-(:] ?)?(?:en|montants?|donnees)\b|^passif -", p):
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
    n_k2 = len(re.findall(r"(?<![\d,.])\d{1,3}(?:,\d{3}){2,}(?![\d,])", txt))
    n_k1 = len(re.findall(r"(?<![\d,.\s])\d{1,3},\d{3}(?![\d,])", txt))
    n_dec = len(re.findall(r"(?<![\d,.])\d+,\d{1,2}(?![\d,])", txt))
    _COMMA_K[0] = (n_k2 >= 5 and n_dec <= n_k2 // 10) or (n_k1 >= 15 and n_dec <= n_k1 // 10 and not re.search(r"\d \d{3},\d", txt))
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
    # vocabulaire propre aux normes IFRS et aux comptes consolidés, quand les titres ne le disent pas
    if std_cur == "syscohada" and not re.search(r"syscohada", nt_) and \
            len(re.findall(r"resultat global|ne donnant pas le controle|actifs? non courants?|passifs? non courants?", nt_)) >= 2:
        std_cur = "ifrs"
    conso_hint = bool(re.search(r"ensemble consolide|ne donnant pas le controle|interets minoritaires|perimetre de consolidation", nt_))
    order_votes = []
    pend = []
    single_hint = []
    unit_side, units_seen, unit_at = [None, None], [], -99
    note_at = -999  # dernière ligne d'en-tête avec une colonne « Note(s) »
    for i, ln in enumerate(lines):
        if "\f" in ln:
            ln = ln.replace("\f", "")
        h = _hdr(ln)
        n_ = nrm(ln).strip()
        if re.search(r"(?:^|\s{2})(?:notes?|ref\.? notes?)(?:\s{2}|$)", n_) and not re.search(r"\d{3}", n_):
            note_at = i
        for pos_u, f_u in line_units(nrm(ln)):  # unité de chaque tableau (de chaque côté quand deux tableaux se font face)
            if split and pos_u >= split[0] - 5:
                unit_side[1] = f_u
            else:
                unit_side[0] = f_u
                if not split:
                    unit_side[1] = f_u
            units_seen.append(f_u)
            unit_at = i
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
            if re.search(r"(?:bilan|comptes?|etats?(?: de synthese| financiers)?|compte de resultat|tableau des flux(?: de tresorerie)?|resultats?|situation financiere|"
                         r"etat du resultat global|flux de tresorerie)\s+(?:[a-z']+\s+){0,3}consolid", n_) and not re.search(r"sociaux|individuel", n_):
                perim = "conso"
            elif re.search(r"(?:bilan|comptes?|etats?(?: de synthese| financiers)?|compte de resultat|tableau des flux)\s+(?:[a-z']+\s+){0,2}(?:sociaux|individuels?|social)\b|"
                           r"comptes sociaux", n_):
                perim = "social"
            if re.search(r"\bifrs\b|normes? internationales?", n_) and not re.search(r"syscohada", n_):
                std_cur = "ifrs"
            elif re.search(r"syscohada", n_) and not re.search(r"\bifrs\b", n_):
                std_cur = "syscohada"
            if re.search(r"\bbruts?\b.*amort|amortissements?.*\bnet|\bbruts?\b.*\bnets?\b", n_):
                brut_tbl = True
            nl = nrm(ln)
            found_s, found_all = [], []
            for mm in re.finditer(r"\S+(?:\s{1,2}\S+)*", nl):
                s_ = head_sec(mm.group(0).strip(" :-"))
                if s_:
                    found_all.append((mm.start(), s_))
                if s_ and (not found_s or found_s[-1][1] != s_):
                    found_s.append((mm.start(), s_))
            if i - unit_at > 4:  # nouvel état sans unité annoncée à côté : unité à déterminer (du côté du titre)
                for pos_h, s_h in found_all:
                    if s_h in (S_ACT, S_PAS, S_CR, S_FLX, "bilan"):
                        if split and pos_h >= split[0] - 5:
                            unit_side[1] = None
                        else:
                            unit_side[0] = None
                            if not split:
                                unit_side[1] = None
            if len(found_all) >= 2 and len({x[1] for x in found_all}) == 1 and found_all[0][1] not in ("bilan", "hb"):
                sec, split = found_all[0][1], None  # même état des deux côtés (« PRODUITS … CHARGES »)
            elif len(found_s) >= 2 and found_s[0][1] != found_s[1][1] and found_s[1][1] != "bilan":
                left = [e for e, _, _ in h if e < found_s[1][0]] if h else []
                s0 = S_ACT if found_s[0][1] == "bilan" else found_s[0][1]
                split = [(max(left) + 1) if left else max(0, found_s[1][0] - 12), s0, found_s[1][1], False]
                sec = s0
            elif found_s:
                s_ = found_s[0][1]
                if s_ == "bilan":
                    sec = S_ACT if sec not in (S_ACT, S_PAS) else sec
                elif split and s_ in (S_CR, S_FLX) and set(split[1:3]) <= {S_ACT, S_PAS}:
                    sec, split = s_, None  # nouvel état après le bilan (titre centré sur la page)
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
                if j + 1 < len(cells) and cells[j][0] == "L" and cells[j + 1][0] in ("N", "D") and \
                        len(re.sub(r"[^A-Za-z]", "", cells[j][1])) <= 3:
                    j += 1  # référence ou bruit de lecture entre le libellé et ses montants (« CHIFFRE D'AFFAIRES  XB  … »)
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
        if split and split[3] and segs and not ocr:
            # « TOTAL ACTIF  x  y   x  y » : les montants au-delà de la limite appartiennent au tableau de droite (sans libellé)
            segs2 = []
            for code_, lab, vals, st_ in segs:
                lv = [x for x in vals if x[1] < split[0]]
                rv = [x for x in vals if x[1] >= split[0] + 8]
                if st_ is not None and st_ < split[0] - 2 and lab and len(lv) >= 1 and len(rv) >= 2 and len(lv) + len(rv) == len(vals):
                    segs2 += [(code_, lab, lv, st_), (None, "", rv, split[0])]
                else:
                    segs2.append((code_, lab, vals, st_))
            segs = segs2
        new_pend = []
        for si, (code_, lab, vals, st_) in enumerate(segs):
            s_here = sec
            side_ = 0
            if split and st_ is not None:
                if si > 0 and segs[si - 1][2] and st_ > 20:  # libellé qui suit des montants : tableau de droite
                    split[0] = min(split[0], st_) if split[3] else st_  # (la 1re mesure remplace l'estimation tirée du titre)
                    split[3] = True  # limite des deux tableaux vérifiée sur une ligne de montants
                    s_here = split[2]
                    side_ = 1
                else:
                    s_here = split[2] if st_ >= split[0] - 2 else split[1]
                    side_ = 1 if st_ >= split[0] - 2 else 0
            if code_ and re.fullmatch(r"[A-Z]{2}", code_) and code_[0] in CODE_SEC:
                s_here = CODE_SEC[code_[0]]
            labn = re.sub(r"\s+", " ", nrm(lab)).strip(" :.-*•")
            labn = re.sub(r"\b([ldnjs])' +", r"\1'", labn)
            labn = re.sub(r"\s*\((?:[a-z]{1,2}|[ivx]+|\d)\)$", "", labn)  # renvoi de note « (1) », « (a) »
            labn = re.sub(r"^(?:[ivx]+|[a-h]|\d{1,2})[-.)] +", "", labn)  # numérotation « I. », « a) »
            labn = re.sub(r"\s*\(?(?:note|notes)\s*\d+[a-z]?\)?$", "", labn)
            labn = re.sub(r"\s+\d{1,2}(?:\.\d)?$", "", labn)  # numéro de note en fin de libellé
            # formule de calcul en fin de libellé (« CHIFFRE D'AFFAIRES (A + B + C + D) », « (somme TK à RN) »)
            labn = re.sub(r"\s*\((?=[^()]*(?:[a-z0-9] ?\+ ?[a-z0-9]|\bsomme\b|\b[a-z]{2} a [a-z]{2}\b))[^)]*\).*$", "", labn)
            if len(vals) == 4 and vals[0][0] is None and vals[1][0] is not None and float(vals[1][0]).is_integer() \
                    and 0 < abs(vals[1][0]) < 100 and vals[2][0] is not None and vals[3][0] is not None:
                vals = vals[2:]  # colonne des signes (« - »), colonne des notes, puis les deux exercices
            nn_ = [v for v, _ in vals if v is not None]
            if len(nn_) >= 2 and vals[0][0] is not None and float(vals[0][0]).is_integer() and 0 < abs(vals[0][0]) < 100 \
                    and ((all(abs(x) >= 10000 for x in nn_[1:]) and (len(nn_) >= 3 or i - note_at < 80 or ocr)) or (len(nn_) >= 3 and all(x == 0 for x in nn_[1:]))
                         or (_NOTE_DOT[0] and all(not float(x).is_integer() for x in nn_[1:3]))):
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
            if key is None and not labn and si > 0 and s_here == S_PAS and \
                    re.fullmatch(r"total ?(?:general ?)?(?:de l.)?actif", re.sub(r"\s+", " ", nrm(segs[si - 1][1])).strip(" :.-*•")):
                key = "total_passif"  # « TOTAL ACTIF  x  y  |  x  y » : montants sans libellé du tableau du passif
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
                        key = {S_ACT: "total_actif", S_PAS: "total_passif"}.get(s_here, None if s_here in (S_CR, S_FLX) else "_total")
                if key is None:
                    if os.environ.get("CPT_DEBUG2"):
                        print("   nokey", i, s_here, cands[:3], [v for v, _ in vals], split, st_)
                    continue
            if key == "resultat_net" and s_here == S_PAS:
                key = "resultat_bilan"
            if key == "b_resultat_bilan":
                key = "resultat_bilan"
            yrs, how = _assign(vals, [] if ocr else heads, i, fy, brut_tbl and s_here == S_ACT)
            if how == "order" and not split and len(vals) > 4:
                continue  # tableau à plusieurs colonnes (par secteur, variation des capitaux propres…) : colonnes inconnues
            if how == "var":
                order_votes.append(yrs)
            if len([v for v, _ in vals if v is not None]) == 1 and not any(v is None for v, _ in vals):
                single_hint.append(1)
            elif len(vals) >= 2:
                single_hint.append(2)
            occ.append((key, s_here, (perim or "_") + ("_ifrs" if std_cur == "ifrs" else ""), i, yrs, how, vals, unit_side[side_]))
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
        basis = "entete"
    else:
        asc = sum(1 for o in order_votes if o.get("asc")) > sum(1 for o in order_votes if o.get("desc"))
        basis = "variation" if order_votes else "defaut"
    guess = set()
    single = single_hint.count(1) > 2 * single_hint.count(2)
    found, alt, ranks = {}, {}, {}
    # unités par tableau : un montant prend l'unité annoncée en tête de son tableau ; un tableau sans unité annoncée prend
    # l'unité qui rend son total de bilan plausible (0,3 à 60 000 milliards de FCFA), de préférence celle du document
    norm = bool(units_seen)
    f_unk = {}
    if norm:
        u_doc = unit_of(txt)
        tots, f_stmt = {}, {}
        for key, s_here, per, i, yrs, how, vals, u_occ in occ:
            if u_occ is None and key in ("total_actif", "total_passif", "_total"):
                for v, _ in vals:
                    if v:
                        tots[per] = max(tots.get(per, 0), abs(v))
            elif u_occ and key in ("total_actif", "total_passif") and s_here in (S_ACT, S_PAS):
                f_stmt.setdefault(per, u_occ)  # unité du bilan de ce périmètre
        for per, f_ in f_stmt.items():
            if per not in tots:
                f_unk[per] = f_
        for per, T in tots.items():
            pl = [f for f in (1.0, 1e3, 1e6, 1e9) if 3e8 <= T * f <= 6e13]
            if f_stmt.get(per) in pl:
                f_unk[per] = f_stmt[per]
                continue
            f_unk[per] = (units_seen[0] if units_seen[0] in pl else u_doc if u_doc in pl else pl[0] if len(pl) == 1 else None)
    for key, s_here, per, i, yrs, how, vals, u_occ in occ:
        if norm:
            f_u = u_occ or f_unk.get(per) or (units_seen[0] if per not in f_unk else None)
            if f_u is None:
                continue  # unité introuvable pour ce tableau : montant non retenu
        else:
            f_u = 1.0
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
                if basis == "defaut":
                    guess.add((per, key))  # sens des colonnes supposé (ni en-tête d'années, ni colonne de variation)
        yrs = {y: v * f_u for y, v in yrs.items() if isinstance(y, int)}
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
    for suf in ("", "_ifrs"):  # périmètre non annoncé : comptes de la société (sociaux), sauf vocabulaire des comptes consolidés
        dflt = ("conso" if conso_hint else "social") + suf
        if "_" + suf in perims:
            if dflt not in perims:
                perims[dflt] = perims.pop("_" + suf)
            else:
                for k, v in perims.pop("_" + suf).items():
                    perims[dflt].setdefault(k, v)
    main = max(perims, key=lambda k: len(perims[k])) if perims else "social"
    items = perims.get(main, {})
    bank = sum(1 for k in items if k.startswith("b_")) >= 3
    unit = 1.0 if norm else unit_of(txt)  # montants déjà ramenés en FCFA par les en-têtes de tableaux
    cap = capital_stated(txt)
    cv = (items.get("capital") or items.get("b_capital") or {})
    cv = cv.get(fy) if fy in cv else (next(iter(cv.values())) if cv else None)
    if cap and cv and not norm:  # le capital du bilan, multiplié par l'unité, doit redonner le capital annoncé
        for u in (1.0, 1e3, 1e6):
            if abs(cv * u / cap - 1) < 0.005:
                unit = u
                break
    nt = nrm(txt[:8000])
    cur = "USD" if re.search(r"(?:milliers|millions) de dollars|en (?:k|m)?usd\b|us\$|\busd ?(?:000|thousand|million)|thousands of us dollars|in thousands of usd", nt) or \
        re.search(r"(?:milliers|millions) de dollars (?:eu|us|americains)|(?:milliers|millions) (?:de )?\$ ?eu\b", nrm(txt)) else "XOF"
    std = "ifrs" if main.endswith("_ifrs") else "syscohada"
    KEYS_G = ("total_actif", "total_passif", "resultat_net", "chiffre_affaires", "b_pnb", "capitaux_propres", "_total")
    dfl_ = "conso" if conso_hint else "social"
    guess_p = sorted({(dfl_ if p_ == "_" else dfl_ + "_ifrs" if p_ == "__ifrs" else p_) for p_, k_ in guess if k_ in KEYS_G})
    return {"guess": guess_p, "items": items, "perims": perims, "main": main, "unit": unit, "cap": cap, "fy": fy, "type": "banque" if bank else "entreprise",
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
    recent = [h for h in heads if 0 <= i - h[0] < 160][-4:]
    out = {}
    if recent:
        # l'en-tête retenu est celui dont les colonnes s'alignent le mieux sur tous les montants de la ligne
        # (plusieurs tableaux se suivent avec des mises en page différentes)
        best_h = None
        cand_h = list(reversed(recent))
        for (l1, h1), (l2, h2) in zip(recent, recent[1:]):
            # en-tête réparti sur deux lignes voisines (« 31 Décembre 2025 » au-dessus de « 2024 ») : colonnes réunies
            if l2 - l1 == 1 and not any(abs(a[0] - b[0]) <= 3 for a in h1 for b in h2):
                cand_h.append((-1, sorted(h1 + h2)))  # (-1 : retenu seulement si toutes les colonnes s'alignent)
        for rk, (l_h, hs) in enumerate(cand_h):
            # montants alignés à droite sous des années centrées : affectation dans l'ordre des colonnes, sur la fenêtre
            # de colonnes d'en-tête la plus proche (tableaux côte à côte : les colonnes de l'autre tableau sont ignorées)
            hs_s = sorted(hs)
            k_ = len(nums)
            if 1 <= k_ <= len(hs_s):
                win = None
                for st_w in range(len(hs_s) - k_ + 1):
                    ds = [abs(hs_s[st_w + j][0] - nums[j][1]) for j in range(k_)]
                    if max(ds) <= 25 and (win is None or sum(ds) < win[0]):
                        win = (sum(ds), st_w)
                if win:
                    got = {}
                    for j in range(k_):
                        yr = hs_s[win[1] + j][2]
                        if isinstance(yr, tuple):
                            yr = fy + yr[1] if fy else None
                        if yr is not None and yr not in got:
                            got[yr] = nums[j][0]
                    if got and len(got) == k_:
                        sc = (k_ + 0.5, -win[0] / k_, -rk)
                        if best_h is None or sc > best_h[0]:
                            best_h = (sc, got)
                        continue
            if l_h == -1:
                continue
            got, dist, dk = {}, [], {}
            for vi_, (v, xe) in enumerate(nums):
                bb = None
                for he, hs_, yr in hs:
                    d = min(abs(he - xe), abs((he + hs_) / 2 - (xe - len(str(abs(int(v)))) * 0.66)))
                    if d <= 12 and (bb is None or d < bb[0]):
                        bb = (d, yr)
                if bb:
                    yr = bb[1]
                    if isinstance(yr, tuple):
                        if not fy:
                            continue
                        yr = fy + yr[1]
                    if yr not in got:
                        got[yr] = v
                        dist.append(bb[0])
                        dk[yr] = (bb[0], len(dist) - 1, vi_)
                    elif bb[0] < dk[yr][0] and vi_ == dk[yr][2] + 1 and float(got[yr]).is_integer() and 0 < abs(got[yr]) < 100 and abs(v) >= 100:
                        got[yr] = v  # renvoi de note juste à gauche du montant : la colonne revient au montant le plus proche
                        dist[dk[yr][1]] = bb[0]
                        dk[yr] = (bb[0], dk[yr][1], vi_)
            if got:
                sc = (len(got), -rk, -sum(dist) / len(dist))  # à nombre égal de colonnes, l'en-tête le plus proche au-dessus
                if best_h is None or sc > best_h[0]:
                    best_h = (sc, got)
        out = best_h[1] if best_h else {}
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
    # résultat net du compte de résultat, ou à défaut celui du bilan (compte de résultat coupé avant sa dernière ligne)
    rn_ = g("resultat_net") if g("resultat_net") is not None else g("resultat_bilan")
    if g("rao") is not None and g("rhao") is not None and rn_ is not None:
        res.append(("RN = RAO + HAO - impôt", rel(g("rao") + g("rhao") - imp, rn_)))
    elif g("resultat_exploitation") is not None and g("resultat_financier") is not None and g("rhao") is not None and rn_ is not None:
        res.append(("RN = RE + RF + HAO - impôt", rel(g("resultat_exploitation") + g("resultat_financier") + g("rhao") - imp, rn_)))
    if g("rao") is not None and g("rhao") is None and g("impots_resultat") is not None and rn_ is not None:
        r_ = rel(g("rao") - imp, rn_)  # comptes sans éléments hors activités ordinaires (IFRS) : retenue si elle se vérifie
        if r_ is not None and r_ <= 0.001:
            res.append(("RN = RAO - impôt", r_))
    if g("rao") is not None and g("resultat_exploitation") is not None and g("resultat_financier") is not None:
        res.append(("RAO = RE + RF", rel(g("resultat_exploitation") + g("resultat_financier"), g("rao"))))
    if g("resultat_avant_impot") is not None and g("impots_resultat") is not None and rn_ is not None:
        # (quote-part des sociétés mises en équivalence après le résultat avant impôt ; impôt positif : charge imprimée
        # sans signe, ou produit d'impôt)
        rai_, it_, mee_ = g("resultat_avant_impot"), g("impots_resultat"), g("quote_part_mee") or 0
        c_ = [rel(rai_ + m_ - abs(it_), rn_) for m_ in {0, mee_}]
        if it_ > 0:
            c_ += [rel(rai_ + m_ + it_, rn_) for m_ in {0, mee_}]
        res.append(("RN = résultat avant impôt - impôt", min(c_)))
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
    allv = [abs(v[y]) for k, v in items.items() if y in v]
    bs_v = [abs(v[y]) for k, v in items.items() if y in v and k not in ("total_actif", "total_passif")
            and set(SECS.get(k, ())) & {S_ACT, S_PAS}]
    if tot and bs_v and abs(tot) < max(bs_v) * 0.9:
        tot = None  # total plus petit qu'un poste du bilan : mal lu
    if tot:
        cands = [u for u in (1.0, 1e3, 1e6, 1e9) if 3e8 <= abs(tot) * u <= 6e13]
    elif ca:
        cands = [u for u in (1.0, 1e3, 1e6, 1e9) if 5e7 <= abs(ca) * u <= 1e13]
    else:
        cands = []
    if allv:  # aucun montant au-delà de 100 000 milliards de FCFA
        cands = [u for u in cands if max(allv) * u <= 1e14]
    if P.get("unit") in cands:
        return P["unit"], cands
    if len(cands) == 1:
        return cands[0], cands
    return None, cands


# lectures par reconnaissance de caractères : français et anglais, page lue comme un bloc (fra, eng) ou ligne par ligne
# (fra4, eng4 : mode « colonne de texte » de tesseract, qui garde mieux les lignes des tableaux numérisés)
OCR_SRC = ("fra", "eng", "fra4", "eng4")


def read_doc(texts, meta):
    """Lecture d'un document (texte, et OCR français / anglais le cas échéant) : exercices vérifiés, montants dans l'unité
    du document (unit = 1, 1e3 ou 1e6 FCFA ; None si l'ordre de grandeur reste à confirmer par une autre source)."""
    fy_hint = meta.get("fy")
    title = meta.get("ti") or ""
    best = None
    parsed = {}
    for src, (txt, ocr) in texts.items():
        if not txt or len(txt.strip()) < 200:
            continue
        try:
            P = parse(txt, fy_hint=fy_hint, title=title, ocr=ocr)
        except Exception:  # noqa: BLE001
            continue
        parsed[src] = P
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
           "cur": P["cur"], "main": P["main"], "n": len(P["items"]), "y": {}, "guess": P.get("guess") or []}
    if P["cur"] != "XOF":
        out["st"] = "devise " + P["cur"]
        return out
    # OCR : un montant n'est gardé que si une autre lecture (autre langue, autre mode) donne le même chiffre,
    # ou s'il entre dans une identité comptable vérifiée
    others = [P_ for s_, P_ in parsed.items() if s_ != src and s_ in OCR_SRC]
    for per, yrs in res.items():
        items = P["perims"][per]
        for y, chk in yrs.items():
            ok_id = {k for n, r in chk if r <= 0.001 for k in IDENT_KEYS.get(n, ())}
            rec = {}
            for k, v in items.items():
                if y not in v:
                    continue
                x = v[y]
                if src in OCR_SRC and k not in ok_id:
                    ovs = [((o_["perims"].get(per) or {}).get(k) or {}).get(y) for o_ in others]
                    if not any(ov is not None and abs(ov - x) <= 0.5 for ov in ovs):
                        continue
                rec[k] = abs(x) if k in CHARGES else x
            unit, cands = unit_choice(P, items, y)
            out["y"].setdefault(per, {})[str(y)] = {"v": rec, "c": chk, "u": unit, "uc": cands, "vk": sorted(k for k in ok_id if k in rec)}
    return out


IDENT_KEYS = {"actif = passif": ("total_actif", "total_passif"), "résultat CR = bilan": ("resultat_net", "resultat_bilan"),
              "RN = RAO + HAO - impôt": ("rao", "rhao", "impots_resultat", "participation", "resultat_net", "resultat_bilan"),
              "RN = RE + RF + HAO - impôt": ("resultat_exploitation", "resultat_financier", "rhao", "impots_resultat", "participation", "resultat_net", "resultat_bilan"),
              "RN = résultat avant impôt - impôt": ("resultat_avant_impot", "impots_resultat", "resultat_net", "resultat_bilan"),
              "RN = RAO - impôt": ("rao", "impots_resultat", "participation", "resultat_net", "resultat_bilan"),
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

    Consolidation poste par poste quand plusieurs documents couvrent un même exercice (comptes de l'exercice, colonne N-1 des
    comptes suivants, versions provisoire et définitive, texte ou reconnaissance de caractères) :
      1. un montant qui entre dans une identité vérifiée de son document l'emporte sur un montant non vérifié ;
      2. puis un montant lu dans la couche texte l'emporte sur une reconnaissance de caractères ;
      3. puis le montant donné par le plus de sources concordantes (documents ; la base de référence ne compte que si elle
         reprend des comptes de même rang : jamais des chiffres provisoires contre des comptes définitifs) ;
      4. puis celui du document le plus probant (comptes de l'exercice, définitifs, le plus récent).
    Un montant décalé d'un facteur 1 000 (ou 1 000 000) par rapport à une autre source est une erreur d'unité : écarté.
    Les états par secteur d'activité ne sont pas des comptes de la société : ignorés."""
    recs = []
    for u, r in (cj.get("docs") or {}).items():
        if not r.get("y") or r.get("per") != "annuel" or r.get("cur", "XOF") != "XOF" or not r.get("t"):
            continue
        if re.search(r"par secteur|sectoriel|segment|par activite|par pays", nrm((r.get("ti") or "") + " " + u)):
            continue
        for per, ys in r["y"].items():
            for y, x in ys.items():
                recs.append({"t": r["t"], "y": int(y), "per": per, "std": "ifrs" if per.endswith("_ifrs") else "syscohada", "u": x.get("u"),
                             "uc": x.get("uc") or [], "v": x.get("v") or {}, "vk": set(x.get("vk") or []), "c": x.get("c"), "doc": u,
                             "rank": _doc_rank(r, int(y)), "d": r.get("d"), "ocr": r.get("src") in OCR_SRC,
                             "guess": per in (r.get("guess") or [])})
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
    for x in recs:
        x["m"] = {k: round(v * x["u"] / 1e6, 3) for k, v in x["v"].items()}
    # erreurs d'unité : un poste qui vaut exactement 1 000 fois (ou un millième) la valeur d'une autre source est écarté
    pool = {}
    for x in recs:
        for k, v in x["m"].items():
            if v:
                pool.setdefault((x["t"], x["y"], k), []).append(v)
    MK = {"chiffre_affaires": "ca", "b_pnb": "ca", "resultat_net": "resultat_net", "total_actif": "total_bilan", "capitaux_propres": "capitaux_propres",
          "resultat_exploitation": "ebit", "ebe": "ebitda"}

    def mirror_v(t, y, k):
        mk = MK.get(k)
        return (((mirror or {}).get(t) or {}).get(mk) or {}).get(str(y)) if mk else None
    for x in recs:
        for k in list(x["m"]):
            v = x["m"][k]
            if not v or k in x["vk"]:
                continue
            others = [o for o in pool.get((x["t"], x["y"], k), []) if o != v]
            mv = mirror_v(x["t"], x["y"], k)
            if mv:
                others.append(mv)
            if any(abs(abs(v / o) - f) <= f * 0.005 for o in others if o for f in (1e3, 1e-3, 1e6, 1e-6)):
                del x["m"][k]
    # année de chaque colonne : un exercice dont les montants sont ceux d'une autre année dans d'autres sources (colonnes inversées)
    # est écarté ; un exercice dont le sens des colonnes a été supposé doit être confirmé par une autre source pour la même année
    KEYC = ("total_actif", "resultat_net", "chiffre_affaires", "b_pnb", "capitaux_propres")
    idx_ty = {}
    for x in recs:
        idx_ty.setdefault((x["t"], x["y"]), []).append(x)

    def same(a_, b_):
        return a_ is not None and b_ is not None and abs(a_ - b_) <= max(0.5, abs(b_) * 0.001)

    def support(x, y, peers=False):
        n_ = 0
        for k in KEYC:
            v = x["m"].get(k)
            if v is None:
                continue
            # (pour juger un décalage d'années, une lecture par reconnaissance de caractères ne contredit pas une couche texte)
            if any(o is not x and o["doc"] != x["doc"] and same(v, o["m"].get(k)) and not (peers and o["ocr"] and not x["ocr"])
                   for o in idx_ty.get((x["t"], y), [])):
                n_ += 1
            elif same(v, mirror_v(x["t"], y, k)) or (mirror_v(x["t"], y, k) is not None and abs(v - mirror_v(x["t"], y, k)) <= abs(mirror_v(x["t"], y, k)) * 0.005):
                n_ += 1
        return n_
    keep = []
    for x in recs:
        s0 = support(x, x["y"])
        sh = max(support(x, x["y"] - 1, True), support(x, x["y"] + 1, True))
        if sh >= 2 and s0 == 0:
            continue  # montants d'une autre année
        if x["guess"] and s0 == 0:
            continue  # sens des colonnes non confirmé
        keep.append(x)
    recs = keep
    out = {}
    by_t = {}
    for x in recs:
        by_t.setdefault(x["t"], []).append(x)
    for t, xs in by_t.items():
        # périmètre et norme : ceux qui concordent le mieux avec la base de référence, sinon ceux qui couvrent le plus d'exercices
        groups = {}
        for x in xs:
            groups.setdefault((x["per"], x["std"]), []).append(x)

        def agree(g):
            ok = n = 0
            for x in g:
                for k in ("chiffre_affaires", "b_pnb", "resultat_net", "total_actif"):
                    mv = mirror_v(t, x["y"], k)
                    if mv and x["m"].get(k) is not None:
                        n += 1
                        ok += abs(x["m"][k] - mv) <= abs(mv) * 0.01 + 0.5
            return (ok / n if n else 0, len({x["y"] for x in g}), g[0]["std"] == "syscohada", n)
        main = max(groups, key=lambda k: agree(groups[k])[:3])
        ag = agree(groups[main])
        res = {}
        for y in sorted({x["y"] for x in groups[main]}):
            cand = sorted([x for x in groups[main] if x["y"] == y], key=lambda x: x["rank"], reverse=True)
            v, nsrc = {}, {}
            for k in sorted({k for x in cand for k in x["m"]}):
                vals = {}
                for x in cand:
                    if k not in x["m"]:
                        continue
                    val = x["m"][k]
                    key_ = next((z for z in vals if abs(z - val) <= max(0.5, abs(z) * 0.001)), val)
                    o = vals.setdefault(key_, {"ver": False, "txt": False, "n": 0, "rank": (0, 0, "")})
                    o["ver"] |= k in x["vk"]
                    o["txt"] |= not x["ocr"]
                    o["n"] += 1
                    o["rank"] = max(o["rank"], x["rank"])
                mv = mirror_v(t, y, k)
                fin_ = max(o["rank"][:2] for o in vals.values())
                for z, o in vals.items():
                    # la base de référence départage des comptes de même rang, mais ne fait préférer ni des comptes
                    # provisoires à des comptes définitifs, ni la colonne N-1 de l'exercice suivant aux comptes de l'exercice
                    o["m"] = 1 if mv and abs(z - mv) <= abs(mv) * 0.005 + 0.5 and o["rank"][:2] >= fin_ else 0
                best_v = max(vals, key=lambda z: (vals[z]["ver"], vals[z]["txt"], vals[z]["n"] + vals[z]["m"], vals[z]["rank"]))
                v[k] = best_v
                nsrc[k] = vals[best_v]["n"]
            best = cand[0]
            res[y] = {"v": v, "n": max(nsrc.get(k, 1) for k in ("total_actif", "resultat_net") if k in nsrc) if any(k in nsrc for k in ("total_actif", "resultat_net")) else 1,
                      "d": best["d"], "own": best["rank"][0], "ns": nsrc}
        # concordance avec la base de référence (même périmètre, mêmes normes ?) : un écart confirmé par au moins deux documents
        # officiels est une erreur de la base, pas un autre périmètre
        a_ok = a_n = rn_ok = rn_n = 0
        for y, r in res.items():
            for k in ("chiffre_affaires", "b_pnb", "resultat_net", "total_actif"):
                mv = mirror_v(t, y, k)
                if not mv or r["v"].get(k) is None:
                    continue  # (un zéro de la base de référence est une donnée manquante)
                ok_ = abs(r["v"][k] - mv) <= abs(mv) * 0.01 + 0.5 or r["ns"].get(k, 1) >= 2
                a_n += 1
                a_ok += ok_
                if k == "resultat_net":
                    rn_n += 1
                    rn_ok += ok_
        for r in res.values():
            r.pop("ns", None)
        ag = (a_ok / a_n if a_n else 0, 0, 0, a_n)
        out[t] = {"y": res, "per": main[0].replace("_ifrs", ""), "std": main[1], "agree": round(ag[0], 3), "ncmp": ag[3],
                  "agree_rn": round(rn_ok / rn_n, 3) if rn_n else None, "n_rn": rn_n}
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
        for src, ocr in (("txt", False),) + tuple((x, True) for x in OCR_SRC):
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
