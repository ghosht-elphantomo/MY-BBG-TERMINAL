"""QLAB — cœur de calcul du moteur de valorisation des actions de la BRVM (fonctions pures, sans écriture de fichier).

Toutes les grandeurs monétaires des comptes sont en millions de francs CFA (XOF), comme dans les fichiers fa/ du terminal ;
les valeurs par action sont en francs CFA, sur la base du nombre d'actions actuel (dividendes et cours ajustés des
fractionnements). Chaque calcul accepte une date d'évaluation passée (backtest) : seules les données publiées à cette date
sont utilisées.

Les dix familles de modèles du cahier des charges QLAB :
  1 DCF probabiliste (flux disponibles pour l'entreprise, sociétés non financières)   2 simulation de Monte-Carlo
  3 actualisation des dividendes (DDM)   4 multiples prospectifs (historique de la société, comparables)
  5 résultat résiduel (RI)   6 DCF inversé   7 sensibilités multidimensionnelles   8 facteurs de qualité et de risque
  9 prévisions statistiques évaluées hors échantillon   10 régimes économiques
"""
import datetime as dt
import hashlib
import math
import random
import re
import statistics as stx

N_YEARS = 10           # période explicite de projection
N_SIM = 2000           # trajectoires de Monte-Carlo par société
HORIZONS = (1, 3, 5, 10)

# ------------------------------------------------------------------------------------------------------------- archétypes
# phi : part de l'écart de rentabilité (par rapport au coût des fonds propres) encore présente après 10 ans (avantage
# concurrentiel durable) ; win : nombre d'exercices pour la rentabilité normative (plus long pour les activités cycliques)
ARCH = {
    "banque": dict(n="Banque commerciale", fin=True, phi=0.4, win=3,
                   drivers=["Produit net bancaire : marge d'intérêt et commissions", "Croissance des dépôts et des crédits", "Coût du risque",
                            "Coefficient d'exploitation", "Solvabilité et exigences prudentielles"],
                   risks=["Dégradation de la qualité du portefeuille de crédits", "Concentration sur l'État et les titres publics",
                          "Exigences de fonds propres pouvant limiter les dividendes", "Risque souverain du pays d'implantation"]),
    "groupe_bancaire": dict(n="Groupe bancaire multi-pays", fin=True, phi=0.3, win=3,
                            drivers=["Produit net bancaire des filiales", "Coût du risque", "Change dans les pays hors zone franc", "Solvabilité du groupe"],
                            risks=["Change et inflation dans les pays hors zone franc", "Risques souverains multiples",
                                   "Besoins de fonds propres du groupe", "Complexité de gouvernance d'un groupe multi-pays"]),
    "credit_bail": dict(n="Établissement financier spécialisé", fin=True, phi=0.3, win=5,
                        drivers=["Encours de financement", "Coût de refinancement", "Coût du risque"],
                        risks=["Dépendance au refinancement bancaire", "Qualité des créances", "Taille et liquidité réduites"]),
    "telecom": dict(n="Opérateur de télécommunications", phi=0.5, win=3,
                    drivers=["Parc d'abonnés et usage des données mobiles", "Services financiers mobiles", "Investissements de réseau",
                             "Fiscalité sectorielle et redevances"],
                    risks=["Hausse de la fiscalité ou des redevances", "Concurrence et baisse des prix", "Investissements de réseau plus lourds que prévu",
                           "Risque pays des filiales"]),
    "utilite": dict(n="Concession de service public régulée", phi=0.3, win=5,
                    drivers=["Volumes distribués", "Tarifs fixés par l'État", "Investissements de la concession"],
                    risks=["Gel ou retard des révisions tarifaires", "Créances sur l'État et les entités publiques", "Renouvellement de la concession"]),
    "petrole_distribution": dict(n="Distribution de produits pétroliers", phi=0.4, win=5,
                                 drivers=["Volumes vendus", "Marges encadrées par la structure officielle des prix", "Besoin en fonds de roulement"],
                                 risks=["Marges administrées", "Prix du pétrole et fonds de roulement", "Concurrence"]),
    "energie_industrie": dict(n="Industrie de l'énergie", phi=0.3, win=8,
                              drivers=["Commande publique d'infrastructures", "Prix du pétrole brut", "Capacité de production"],
                              risks=["Dépendance aux programmes publics", "Prix des matières premières", "Créances publiques"]),
    "agro_export": dict(n="Agro-industrie exportatrice", phi=0.2, win=8,
                        drivers=["Cours mondiaux de la matière première", "Volumes et rendements des plantations", "Coûts de production", "Dollar contre franc CFA"],
                        risks=["Baisse des cours mondiaux", "Climat et rendements", "Résultats cycliques", "Fiscalité à l'exportation"]),
    "agro_domestique": dict(n="Agro-industrie pour le marché régional", phi=0.3, win=8,
                            drivers=["Volumes produits", "Prix régionaux et protection du marché", "Coûts de production"],
                            risks=["Importations concurrentes", "Climat et rendements", "Prix encadrés"]),
    "biens_conso": dict(n="Biens de consommation de marque", phi=0.5, win=3,
                        drivers=["Volumes et prix de vente", "Coût des intrants importés", "Pouvoir de fixation des prix"],
                        risks=["Fiscalité (droits d'accises)", "Coût des intrants et change", "Pouvoir d'achat des ménages"]),
    "distribution": dict(n="Distribution et négoce", phi=0.3, win=5,
                         drivers=["Volumes de ventes", "Marge commerciale", "Rotation des stocks et crédit client"],
                         risks=["Commande publique et conjoncture", "Change sur les importations", "Besoin en fonds de roulement"]),
    "industrie": dict(n="Industrie manufacturière", phi=0.3, win=5,
                      drivers=["Volumes de production", "Coût des matières premières", "Investissements"],
                      risks=["Coût des intrants importés", "Concurrence des importations", "Demande cyclique"]),
    "btp": dict(n="Bâtiment et travaux publics", phi=0.2, win=8,
                drivers=["Carnet de commandes", "Commande publique", "Délais de paiement"],
                risks=["Dépendance à la commande publique", "Retards de paiement", "Résultats très irréguliers"]),
    "services": dict(n="Services", phi=0.4, win=5,
                     drivers=["Volumes d'activité", "Contrats clés", "Coûts de personnel"],
                     risks=["Perte d'un contrat clé", "Conjoncture", "Taille réduite"]),
}
FIN = {k for k, v in ARCH.items() if v.get("fin")}

# activité réelle de chaque société (faits généraux, sans chiffres) et archétype de modélisation
PROFILES = {
    "ABJC": ("services", "Restauration aérienne (catering) à l'aéroport d'Abidjan", "Activité liée au trafic aérien et aux contrats des compagnies"),
    "BBGC": ("banque", "Banque commerciale en Côte d'Ivoire", ""),
    "BICB": ("banque", "Banque commerciale au Bénin", ""),
    "BICC": ("banque", "Banque commerciale en Côte d'Ivoire", ""),
    "BNBC": ("distribution", "Distribution de quincaillerie, matériaux de construction et équipements", ""),
    "BOAB": ("banque", "Banque commerciale au Bénin, filiale d'un groupe bancaire panafricain", ""),
    "BOABF": ("banque", "Banque commerciale au Burkina Faso, filiale d'un groupe bancaire panafricain", ""),
    "BOAC": ("banque", "Banque commerciale en Côte d'Ivoire, filiale d'un groupe bancaire panafricain", ""),
    "BOAM": ("banque", "Banque commerciale au Mali, filiale d'un groupe bancaire panafricain", ""),
    "BOAN": ("banque", "Banque commerciale au Niger, filiale d'un groupe bancaire panafricain", ""),
    "BOAS": ("banque", "Banque commerciale au Sénégal, filiale d'un groupe bancaire panafricain", ""),
    "CABC": ("industrie", "Fabrication de câbles électriques et téléphoniques", ""),
    "CBIBF": ("banque", "Banque commerciale au Burkina Faso", ""),
    "CFAC": ("distribution", "Distribution de véhicules et services associés", ""),
    "CIEC": ("utilite", "Concession de production, transport et distribution d'électricité en Côte d'Ivoire", "Tarifs de l'électricité fixés par l'État"),
    "ECOC": ("banque", "Banque commerciale en Côte d'Ivoire, filiale d'un groupe bancaire panafricain", ""),
    "ETIT": ("groupe_bancaire", "Holding d'un groupe bancaire panafricain présent dans plus de trente pays",
             "Comptes consolidés ; intérêts minoritaires non isolés dans les données ; filiales hors zone franc exposées aux dévaluations et à "
             "l'inflation, risques que le coût des fonds propres mesuré sur le marché régional ne capte pas entièrement"),
    "FTSC": ("industrie", "Fabrication d'emballages (sacs synthétiques et en jute)", ""),
    "LNBB": ("services", "Loterie et jeux de hasard au Bénin", "Activité exercée sous monopole légal"),
    "NEIC": ("services", "Édition et distribution de livres", "Comptes de la société fusionnée à partir de l'exercice 2011"),
    "NSBC": ("banque", "Banque commerciale en Côte d'Ivoire", ""),
    "NTLC": ("biens_conso", "Produits alimentaires de marque", ""),
    "ONTBF": ("telecom", "Opérateur de télécommunications au Burkina Faso", ""),
    "ORAC": ("telecom", "Opérateur de télécommunications en Côte d'Ivoire", ""),
    "ORGT": ("groupe_bancaire", "Holding d'un groupe bancaire régional", "Comptes consolidés ; intérêts minoritaires non isolés dans les données"),
    "PALC": ("agro_export", "Plantations de palmiers à huile et production d'huile de palme", "Résultats liés aux cours mondiaux de l'huile de palme"),
    "PRSC": ("distribution", "Distribution d'engins, de véhicules et de services associés", ""),
    "SAFC": ("credit_bail", "Crédit-bail et financement d'équipements", ""),
    "SCRC": ("agro_domestique", "Production de sucre", "Marché régional protégé, prix encadrés"),
    "SDCC": ("utilite", "Concession de distribution d'eau potable en Côte d'Ivoire", "Tarifs de l'eau fixés par l'État"),
    "SDSC": ("services", "Logistique, manutention portuaire et transit", ""),
    "SEMC": ("industrie", "Fabrication d'emballages métalliques", ""),
    "SGBC": ("banque", "Banque commerciale en Côte d'Ivoire, filiale d'un groupe bancaire international", ""),
    "SHEC": ("petrole_distribution", "Distribution de carburants et de lubrifiants", ""),
    "SIBC": ("banque", "Banque commerciale en Côte d'Ivoire", ""),
    "SICC": ("agro_export", "Transformation de la noix de coco", ""),
    "SIVC": ("industrie", "Production et distribution de gaz industriels et médicaux", ""),
    "SLBC": ("biens_conso", "Brasserie et boissons", "Droits d'accises sur les boissons"),
    "SMBC": ("energie_industrie", "Production de bitumes et de produits raffinés", ""),
    "SNTS": ("telecom", "Opérateur de télécommunications au Sénégal, avec des filiales au Mali, en Guinée, en Guinée-Bissau et en Sierra Leone",
             "Comptes consolidés ; intérêts minoritaires des filiales non isolés dans les données"),
    "SOGC": ("agro_export", "Plantations d'hévéas et de palmiers à huile", "Résultats liés aux cours mondiaux du caoutchouc et de l'huile de palme"),
    "SPHC": ("agro_export", "Plantations d'hévéas et production de caoutchouc naturel", "Résultats liés aux cours mondiaux du caoutchouc"),
    "STAC": ("btp", "Bâtiment et travaux publics", ""),
    "STBC": ("biens_conso", "Fabrication de cigarettes", "Droits d'accises sur le tabac"),
    "TTLC": ("petrole_distribution", "Distribution de produits pétroliers en Côte d'Ivoire", ""),
    "TTLS": ("petrole_distribution", "Distribution de produits pétroliers au Sénégal", ""),
    "UNLC": ("biens_conso", "Produits d'hygiène et alimentaires de marque", ""),
    "UNXC": ("industrie", "Fabrication de tissus imprimés", ""),
}
GRP_DEFAULT = {"Services financiers": "banque", "Télécoms": "telecom", "Services publics": "utilite", "Énergie": "petrole_distribution",
               "Consommation de base": "biens_conso", "Consommation discrétionnaire": "distribution", "Industriels": "industrie"}

# pertinence de chaque modèle selon l'archétype (0 : inadapté, 1 : pleinement adapté) et raison affichée
APPLIC = {
    "banque": dict(ri=1.0, ddm=0.8, dcf=0.0, mult_own=0.6, mult_peer=0.6),
    "groupe_bancaire": dict(ri=1.0, ddm=0.6, dcf=0.0, mult_own=0.6, mult_peer=0.5),
    "credit_bail": dict(ri=1.0, ddm=0.6, dcf=0.0, mult_own=0.5, mult_peer=0.4),
    "telecom": dict(ri=0.8, ddm=0.8, dcf=1.0, mult_own=0.6, mult_peer=0.5),
    "utilite": dict(ri=0.8, ddm=1.0, dcf=0.8, mult_own=0.5, mult_peer=0.4),
    "petrole_distribution": dict(ri=0.6, ddm=1.0, dcf=0.8, mult_own=0.6, mult_peer=0.6),
    "energie_industrie": dict(ri=0.8, ddm=0.6, dcf=1.0, mult_own=0.5, mult_peer=0.3),
    "agro_export": dict(ri=1.0, ddm=0.6, dcf=0.8, mult_own=0.4, mult_peer=0.5),
    "agro_domestique": dict(ri=1.0, ddm=0.7, dcf=0.8, mult_own=0.5, mult_peer=0.3),
    "biens_conso": dict(ri=0.7, ddm=1.0, dcf=1.0, mult_own=0.6, mult_peer=0.5),
    "distribution": dict(ri=0.8, ddm=0.7, dcf=1.0, mult_own=0.6, mult_peer=0.5),
    "industrie": dict(ri=0.8, ddm=0.7, dcf=1.0, mult_own=0.6, mult_peer=0.5),
    "btp": dict(ri=1.0, ddm=0.5, dcf=0.6, mult_own=0.4, mult_peer=0.3),
    "services": dict(ri=0.8, ddm=0.7, dcf=1.0, mult_own=0.6, mult_peer=0.4),
}
APPLIC_WHY = {
    "ri": {"fin": "modèle de référence pour une banque : la valeur vient des fonds propres et de leur rentabilité au-delà du coût du capital",
           "agro_export": "adapté à une activité cyclique : rentabilité normative sur un cycle complet appliquée aux fonds propres",
           "*": "valorise les fonds propres publiés et la rentabilité au-delà du coût du capital"},
    "ddm": {"petrole_distribution": "distribution régulière de la quasi-totalité du résultat : les dividendes résument bien la valeur",
            "utilite": "société régulée à dividende régulier : les dividendes résument bien la valeur",
            "biens_conso": "dividendes réguliers d'une activité de marque", "*": "valeur des dividendes futurs ; le dividende passé n'est jamais supposé acquis"},
    "dcf": {"fin": "inadapté : les flux de trésorerie d'une banque (dépôts, crédits) ne mesurent pas sa création de valeur",
            "*": "valeur des flux de trésorerie disponibles de l'entreprise après investissements, diminuée de la dette nette"},
    "mult_own": {"*": "méthode relative : prix que le marché a payé pour ce titre dans le passé, appliqué aux résultats attendus"},
    "mult_peer": {"*": "méthode relative : prix payés pour des sociétés comparables de la BRVM ; peu de comparables sur ce marché"},
}
MODEL_NAMES = {"dcf": "DCF probabiliste (flux disponibles)", "ddm": "Actualisation des dividendes (DDM)", "ri": "Résultat résiduel (RI)",
               "mult_own": "Multiples prospectifs : historique de la société", "mult_peer": "Multiples prospectifs : sociétés comparables"}
MODEL_FAM = {"dcf": 1, "ddm": 3, "ri": 5, "mult_own": 4, "mult_peer": 4}

# régimes économiques : (variation de la croissance en points, variation relative de la rentabilité, variation du coût des
# fonds propres en points, durée en années ou None si permanent) — hypothèses de travail affichées comme telles
REGIMES = [
    ("croissance", "Croissance régionale soutenue", "Croissance économique de la zone nettement au-dessus de sa tendance pendant 3 ans"),
    ("ralentissement", "Ralentissement régional", "Croissance économique nettement inférieure à sa tendance pendant 3 ans"),
    ("inflation", "Inflation élevée", "Inflation durablement au-dessus de l'objectif de la banque centrale pendant 3 ans"),
    ("taux", "Hausse durable des taux", "Taux des emprunts d'État et coût des fonds propres en hausse de 2 points"),
    ("change", "Choc de change", "Dollar en hausse de 20 % face au franc CFA (parité fixe avec l'euro) pendant 3 ans"),
    ("matieres", "Choc sur les matières premières", "Cours mondiaux de la matière première du secteur défavorables pendant 3 ans"),
    ("regle", "Changement réglementaire ou fiscal défavorable", "Hausse durable de la fiscalité sectorielle, encadrement des prix ou gel tarifaire"),
]
REG_FX = {
    "croissance": {"*": (1.5, 0.05, 0, 3), "banque": (2, 0.08, 0, 3), "groupe_bancaire": (2, 0.08, 0, 3), "btp": (3, 0.15, 0, 3),
                   "distribution": (2.5, 0.08, 0, 3), "utilite": (1, 0.02, 0, 3), "agro_export": (0.5, 0.0, 0, 3), "telecom": (1.5, 0.04, 0, 3)},
    "ralentissement": {"*": (-3, -0.10, 0.5, 3), "banque": (-3, -0.20, 0.5, 3), "groupe_bancaire": (-3, -0.20, 0.5, 3), "credit_bail": (-3, -0.25, 0.5, 3),
                       "utilite": (-1, -0.05, 0.5, 3), "biens_conso": (-2, -0.08, 0.5, 3), "btp": (-6, -0.35, 0.5, 3), "distribution": (-4, -0.15, 0.5, 3),
                       "telecom": (-1.5, -0.06, 0.5, 3), "agro_export": (-1, -0.05, 0.5, 3), "petrole_distribution": (-2, -0.05, 0.5, 3)},
    "inflation": {"*": (1.5, -0.08, 1, 3), "banque": (2, 0.03, 1, 3), "groupe_bancaire": (2, 0.0, 1.5, 3), "utilite": (1.5, -0.15, 1, 3),
                  "telecom": (1, -0.06, 1, 3), "biens_conso": (2, -0.08, 1, 3), "petrole_distribution": (2, -0.05, 1, 3), "agro_export": (1, 0.03, 1, 3)},
    "taux": {"*": (0, 0.0, 2, None), "banque": (0, 0.05, 2, None), "groupe_bancaire": (0, 0.03, 2, None), "credit_bail": (0, -0.10, 2, None),
             "btp": (-1, -0.05, 2, None)},
    "change": {"*": (0, -0.05, 0, 3), "agro_export": (0, 0.20, 0, 3), "groupe_bancaire": (0, 0.0, 0.5, 3), "petrole_distribution": (0, -0.06, 0, 3),
               "distribution": (-1, -0.10, 0, 3), "biens_conso": (0, -0.08, 0, 3), "industrie": (0, -0.10, 0, 3), "banque": (0, 0.0, 0, 3),
               "utilite": (0, -0.05, 0, 3), "telecom": (0, -0.04, 0, 3), "services": (0, 0.0, 0, 3), "btp": (0, -0.05, 0, 3)},
    "matieres": {"*": (0, 0.0, 0, 3), "agro_export": (-2, -0.40, 0.5, 3), "agro_domestique": (-1, -0.10, 0, 3), "petrole_distribution": (0, -0.05, 0, 3),
                 "energie_industrie": (0, -0.15, 0, 3), "industrie": (0, -0.08, 0, 3), "biens_conso": (0, -0.06, 0, 3)},
    "regle": {"*": (0, -0.05, 0, None), "telecom": (-1, -0.15, 0, None), "utilite": (0, -0.15, 0, None), "banque": (0, -0.08, 0, None),
              "groupe_bancaire": (0, -0.08, 0, None), "biens_conso": (-1, -0.10, 0, None), "petrole_distribution": (0, -0.08, 0, None),
              "services": (0, -0.08, 0, None)},
}
REG_TXT = {  # lecture de l'effet supposé, par régime et archétype (sinon texte générique)
    ("change", "agro_export"): "ventes à l'export libellées en dollars : marges en hausse",
    ("matieres", "agro_export"): "baisse des cours mondiaux : marges fortement réduites",
    ("taux", "banque"): "marge d'intérêt un peu améliorée, mais coût des fonds propres plus élevé",
    ("ralentissement", "banque"): "coût du risque en hausse et crédits moins dynamiques",
    ("inflation", "utilite"): "coûts en hausse avant la révision des tarifs administrés",
    ("regle", "telecom"): "taxes et redevances sectorielles plus lourdes",
    ("regle", "biens_conso"): "droits d'accises relevés",
    ("change", "petrole_distribution"): "produits importés plus chers, marges encadrées",
}

# ------------------------------------------------------------------------------------------------------------- outils
def fin(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def med(xs):
    xs = [x for x in xs if fin(x)]
    return stx.median(xs) if xs else None


def mean(xs):
    xs = [x for x in xs if fin(x)]
    return sum(xs) / len(xs) if xs else None


def sd(xs):
    xs = [x for x in xs if fin(x)]
    return stx.stdev(xs) if len(xs) >= 3 else None


def quant(xs, p):
    xs = sorted(x for x in xs if fin(x))
    if not xs:
        return None
    k = (len(xs) - 1) * p
    i = int(k)
    return xs[i] if i + 1 >= len(xs) else xs[i] + (xs[i + 1] - xs[i]) * (k - i)


def wquant(pts, p):
    """quantile d'un échantillon pondéré [(valeur, poids)]"""
    pts = sorted((v, w) for v, w in pts if fin(v) and w > 0)
    if not pts:
        return None
    tot = sum(w for _, w in pts)
    acc = 0.0
    for v, w in pts:
        acc += w
        if acc >= p * tot - 1e-12:
            return v
    return pts[-1][0]


def fr(s):
    """écriture française des nombres dans un texte : séparateur de milliers, virgule décimale, espace avant %"""
    if not isinstance(s, str):
        return s
    s = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "\u202f", s)
    s = re.sub(r"(?<=\d)\.(?=\d)", ",", s)
    return re.sub(r"(?<=\d) ?%", "\u00a0%", s)


def frall(o, skip=("t", "id", "k", "main", "arch", "fw", "best", "key", "u", "v_id")):
    if isinstance(o, dict):
        return {k: (v if k in skip else frall(v, skip)) for k, v in o.items()}
    if isinstance(o, list):
        return [frall(x, skip) for x in o]
    return fr(o)


def clamp(x, a, b):
    return max(a, min(b, x))


def rnd(x, n=4):
    return round(x, n) if fin(x) else None


def sig(x, n=3):
    """arrondi à n chiffres significatifs (pas de précision artificielle)"""
    if not fin(x) or x == 0:
        return x if fin(x) else None
    d = n - int(math.floor(math.log10(abs(x)))) - 1
    return round(x, d) if d > 0 else float(round(x, d))


def cagr(a, b, n):
    if not (fin(a) and fin(b)) or a <= 0 or b <= 0 or n <= 0:
        return None
    return (b / a) ** (1 / n) - 1


def ymd(d):
    s = str(d or "").replace("-", "")[:8]
    try:
        return dt.date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    except ValueError:
        return None


def dint(d):
    return d.year * 10000 + d.month * 100 + d.day


def spearman(xs, ys):
    pts = [(x, y) for x, y in zip(xs, ys) if fin(x) and fin(y)]
    n = len(pts)
    if n < 5:
        return None

    def rk(v):
        o = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    a, b = rk([p[0] for p in pts]), rk([p[1] for p in pts])
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den else None


def pearson(xs, ys):
    pts = [(x, y) for x, y in zip(xs, ys) if fin(x) and fin(y)]
    n = len(pts)
    if n < 4:
        return None
    mx, my = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    syy = sum((p[1] - my) ** 2 for p in pts)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else None


def px_at(d_, c_, date):
    """dernier cours connu à une date (YYYYMMDD) et date de ce cours"""
    lo, hi = 0, len(d_) - 1
    if hi < 0 or d_[0] > date:
        return None, None
    while lo < hi:
        m = (lo + hi + 1) // 2
        if d_[m] <= date:
            lo = m
        else:
            hi = m - 1
    return c_[lo], d_[lo]


# ------------------------------------------------------------------------------------------------------------- données
def split_factor_after(splits, date, today):
    """produit des facteurs de fractionnement effectifs après une date (et au plus tard aujourd'hui)"""
    f = 1.0
    for d, k in splits or []:
        if date < d <= today and fin(k) and k > 0:
            f *= k
    return f


def company_static(t, I):
    """faits disponibles pour une société (toutes dates) : séries annuelles, cours, dividendes, liquidité, notation"""
    s, f = I["secs"][t], I["fa"].get(t) or {}
    Y = f.get("Y") or {}
    ys = Y.get("y") or []
    ser = {}
    for k in ("rev", "ni", "eq", "ebit", "ebitda", "ocf", "capex", "nd", "cash", "assets", "deposits", "loans", "cor", "solv", "roic", "eps"):
        ser[k] = {y: v for y, v in zip(ys, Y.get(k) or []) if fin(v)}
    verified = set()
    for blk in ("C", "C2"):
        verified |= set((f.get(blk) or {}).get("y") or [])
    prof = PROFILES.get(t)
    arch, act, note = prof if prof else (GRP_DEFAULT.get(s.get("grp"), "services"), s.get("n"), "")
    if s.get("bank") and arch not in FIN:
        arch = "banque"
    first = s.get("first")
    notes = [note] if note else []
    if first and first >= 20150101:
        notes.append(f"Cotée à la BRVM depuis le {str(first)[6:8]}/{str(first)[4:6]}/{str(first)[:4]} : historique boursier court")
    d_, c_ = I["px"].get(t) or ([], [])
    dv, dexc = {}, {}
    drows = []
    for r in I["div"]:
        if r.get("t") != t or not fin(r.get("dps")) or not r.get("ex"):
            continue
        drows.append(r)
        tgt = dexc if r.get("exc") else dv
        tgt[r["ex"]] = tgt.get(r["ex"], 0) + r["dps"]
    rating = None
    for r in I["ratings"]:
        if r.get("t") == t and (not rating or (r.get("d") or "") > (rating.get("d") or "")):
            rating = r
    return {"t": t, "name": s.get("short") or s.get("n"), "full": s.get("n"), "arch": arch, "act": act, "notes": notes,
            "cty": s.get("cty") or "CI", "grp": s.get("grp"), "fin": arch in FIN, "years": ys, "ser": ser, "verified": verified,
            "shares_now": s.get("shares"), "bnpa": s.get("bnpa"), "splits": s.get("split") or [], "liq": I["liq"].get(t) or {},
            "dv": dv, "dexc": dexc, "drows": drows, "rating": rating, "mh": f.get("mh") or {}, "tax": f.get("tax"), "first": first,
            "px": (d_, c_), "last": s.get("last"), "ldt": s.get("dt"), "susp": s.get("susp"), "per_now": s.get("per"),
            "fa_now": {k: f.get(k) for k in ("pe", "pb", "ev_ebitda", "roe", "dy", "nd_ebitda", "fy")}}


def asof_view(S, date, today, full=True):
    """vue « au » d'une date : exercices publiés avant la date, cours et dividendes connus à la date, nombre d'actions de la date.
    date, today : YYYYMMDD (int). Les comptes d'un exercice N sont réputés connus à partir de leur date de publication (index des
    documents de la BRVM), à défaut le 30 juin de N+1 ; à la date du jour, tous les comptes déjà lus sont connus."""
    pub = S.get("pub") or {}
    if date >= today:
        fy_ok = list(S["ser"]["ni"])
    else:
        fy_ok = [y for y in S["ser"]["ni"] if (pub.get(y) or (y + 1) * 10000 + 630) <= date]
    fy = max(fy_ok) if fy_ok else None
    V = {"date": date, "fy": fy}
    f_ = split_factor_after(S["splits"], date, today)
    sh = S["shares_now"] / f_ if S["shares_now"] else None
    V["shares"], V["split_f"] = sh, f_
    d_, c_ = S["px"]
    p, pd_ = px_at(d_, c_, date) if d_ else (None, None)
    if date >= today and fin(S.get("last")) and S.get("ldt") and (pd_ is None or S["ldt"] >= pd_):
        p, pd_ = S["last"], S["ldt"]
    # séries de cours ajustées des fractionnements passés (base actuelle) → base de la date
    V["price"] = p * f_ if fin(p) else None
    V["pdate"] = pd_
    # dividendes ordinaires connus à la date (annonce publiée), en francs par action de la date
    dv = {}
    for r in S["drows"]:
        if r.get("exc"):
            continue
        ann = int(str(r.get("ann") or r.get("det") or f"{r['ex'] + 1}0701").replace("-", "")[:8])
        if ann <= date:
            dv[r["ex"]] = dv.get(r["ex"], 0) + r["dps"] * f_
    V["dv"] = dict(sorted(dv.items()))
    if not full:
        return V
    V["ser"] = {k: {y: v for y, v in d.items() if fy is not None and y <= fy} for k, d in S["ser"].items()}
    V["px_hist"] = [(d, c * f_) for d, c in zip(d_, c_) if d <= date] if d_ else []
    return V


# ------------------------------------------------------------------------------------------------------------- marché
COUNTRY = {"CI": ("Cote d'ivoire", "CIV"), "SN": ("Sénégal", "SEN"), "BJ": ("Bénin", "BEN"), "BF": ("Burkina", "BFA"),
           "ML": ("Mali", "MLI"), "NE": ("Niger", "NER"), "TG": ("Togo", "TGO"), "GW": ("Guinée-Bissau", "GNB")}


def market_dy(I, date, today):
    """rendement du dividende agrégé des actions de la BRVM à une date (dividendes ordinaires du dernier exercice annoncé, au plus
    vieux de deux ans, rapportés à la capitalisation des sociétés cotées à cette date)"""
    dsum = csum = 0.0
    n = 0
    for t, S in I["S"].items():
        V = asof_view(S, date, today, full=False)
        if not fin(V["price"]) or not V["shares"]:
            continue
        cap = V["price"] * V["shares"]
        csum += cap
        n += 1
        if V["dv"]:
            ex = max(V["dv"])
            if ex >= date // 10000 - 2:
                dsum += V["dv"][ex] * V["shares"]
    return (dsum / csum if csum else None), n


def market_params(I, today, asof=None, series=None):
    """taux sans risque par pays (courbe des emprunts d'État la plus récente), croissance nominale de long terme prudente par pays
    (inflation et croissance réelle par habitant médianes sur 15 ans, bornées), coût des fonds propres implicite du marché (rendement
    du dividende agrégé, modèle de Gordon) et sa dispersion historique (annuelle, chaque date avec les seules données de la date).
    asof (date) : paramètres calculés avec les seules données disponibles à cette date (validation historique) ; faute de courbe des
    taux à cette date, la courbe la plus ancienne disponible est utilisée (limite signalée)."""
    curves = I["curves"].get("curves") or {}
    ref = asof or today
    ck = [k for k in curves if k <= ref.isoformat()]
    last = curves[max(ck)] if ck else (curves[min(curves)] if curves else None)
    rf, rf_why = {}, {}
    if last:
        for cty, (cname, _) in COUNTRY.items():
            rows = last["c"].get(cname) or []
            pts = [r[2] for r in rows if r[1] in (5, 7, 10) and fin(r[2])]
            if pts:
                rf[cty] = med(pts)
                rf_why[cty] = f"médiane des taux à 5, 7 et 10 ans de la courbe des emprunts d'État du pays au {last.get('asof')}"
    ind = I["macro"].get("ind") or {}
    gdp = (ind.get("NY.GDP.MKTP.KD.ZG") or {}).get("v") or {}
    cpi = (ind.get("FP.CPI.TOTL.ZG") or {}).get("v") or {}
    popg = (ind.get("SP.POP.GROW") or {}).get("v") or {}
    glt, glt_why = {}, {}
    yrs = [str(y) for y in range(ref.year - 15, ref.year)]
    for cty, (_, iso) in COUNTRY.items():
        g_ = med([gdp.get(iso, {}).get(y) for y in yrs])
        i_ = med([cpi.get(iso, {}).get(y) for y in yrs])
        p_ = med([popg.get(iso, {}).get(y) for y in yrs])
        if fin(g_) and fin(i_) and fin(p_):
            real_pc = clamp((g_ - p_) / 100, 0.0, 0.03)
            infl = clamp(i_ / 100, 0.01, 0.03)
            glt[cty] = clamp(infl + real_pc, 0.02, 0.05)
            glt_why[cty] = (f"inflation médiane {i_:.1f} % (retenue {infl * 100:.1f} %) + croissance réelle par habitant médiane {g_ - p_:.1f} % "
                            f"(retenue {real_pc * 100:.1f} %) sur {yrs[0]}-{yrs[-1]} ; plafond 5 %")
    g_ci, rf_ci = glt.get("CI", 0.04), rf.get("CI")
    tdate = dint(ref)
    dy, n = market_dy(I, tdate, dint(today))
    ke_mkt = dy * (1 + g_ci) + g_ci if dy else None
    # coût des fonds propres implicite du marché : une mesure par an (30 juin), avec les seules données de la date
    if series is None:
        series = []
        for y in range(2010, ref.year + 1):
            d_ = y * 10000 + 630
            if d_ > tdate:
                break
            dy_, n_ = market_dy(I, d_, dint(today))
            if dy_ and n_ >= 15:
                series.append((y, dy_ * (1 + g_ci) + g_ci, dy_))
    else:
        series = [x for x in series if x[0] * 10000 + 630 <= tdate]
    sd_ke = sd([s_[1] for s_ in series])
    ke_lr = med([s_[1] for s_ in series])
    erp = clamp(ke_lr - rf_ci, 0.03, 0.09) if (ke_lr and rf_ci) else 0.05
    return {"rf": rf, "rf_why": rf_why, "glt": glt, "glt_why": glt_why, "dy_mkt": dy, "ke_mkt": ke_mkt, "ke_lr": ke_lr, "erp": erp, "g_ci": g_ci,
            "rf_ci": rf_ci, "ke_series": series, "sd_erp": clamp(sd_ke, 0.005, 0.03) if sd_ke else 0.01,
            "erp_why": (f"rendement exigé médian des actions de la BRVM depuis {series[0][0]} ({ke_lr * 100:.1f} %, mesuré chaque année par le rendement du "
                        f"dividende agrégé + croissance de long terme) − taux sans risque ivoirien ({rf_ci * 100:.2f} %), borné entre 3 et 9 % ; "
                        f"aujourd'hui le rendement exigé implicite du marché est de {ke_mkt * 100:.1f} %")
            if (ke_lr and rf_ci and ke_mkt) else "valeur par défaut de 5 % : données de marché insuffisantes"}


def weekly(px):
    """cours hebdomadaires (dernier cours de chaque semaine ISO)"""
    out, last = [], None
    for d, c in px:
        k = ymd(d).isocalendar()[:2] if ymd(d) else None
        if k != last:
            out.append([d, c])
            last = k
        else:
            out[-1] = [d, c]
    return out


def beta_dimson(px, idx, date, weeks=156):
    """bêta du titre contre l'indice BRVM Composite sur 3 ans de rendements hebdomadaires, corrigé des cotations peu fréquentes
    (Dimson : somme des bêtas sur l'indice contemporain et retardé d'une semaine), avec son erreur type"""
    a = {d: c for d, c in weekly([p for p in px if p[0] <= date])[-weeks - 2:]}
    b = {d: c for d, c in weekly([p for p in idx if p[0] <= date])[-weeks - 3:]}
    dd = sorted(set(a) & set(b))
    if len(dd) < 60:
        return None
    ra, rb, rb1 = [], [], []
    for i in range(2, len(dd)):
        x0, x1 = a[dd[i - 1]], a[dd[i]]
        m0, m1, mm = b[dd[i - 1]], b[dd[i]], b[dd[i - 2]]
        if x0 > 0 and x1 > 0 and m0 > 0 and m1 > 0 and mm > 0:
            ra.append(math.log(x1 / x0))
            rb.append(math.log(m1 / m0))
            rb1.append(math.log(m0 / mm))
    n = len(ra)
    if n < 50:
        return None
    # régression multiple ra = c + b0 rb + b1 rb1 (moindres carrés, 3 paramètres)
    X = [[1.0, u, v] for u, v in zip(rb, rb1)]
    XtX = [[sum(X[k][i] * X[k][j] for k in range(n)) for j in range(3)] for i in range(3)]
    Xty = [sum(X[k][i] * ra[k] for k in range(n)) for i in range(3)]
    inv = inv3(XtX)
    if not inv:
        return None
    bet = [sum(inv[i][j] * Xty[j] for j in range(3)) for i in range(3)]
    res = [ra[k] - sum(bet[i] * X[k][i] for i in range(3)) for k in range(n)]
    s2 = sum(r * r for r in res) / (n - 3)
    var_sum = s2 * (inv[1][1] + inv[2][2] + 2 * inv[1][2])
    return {"b": bet[1] + bet[2], "se": math.sqrt(max(var_sum, 0)), "n": n, "b0": bet[1], "b1": bet[2]}


def inv3(m):
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-18:
        return None
    return [[(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
            [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
            [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det]]


def beta_prior(I, idx, date, today):
    """moyenne et dispersion réelle des bêtas des actions de la BRVM à une date (a priori de Vasicek : dispersion observée moins
    la part due à l'erreur de mesure)"""
    bs = []
    for t, S in I["S"].items():
        d_, c_ = S["px"]
        if not d_:
            continue
        px = [(d, c) for d, c in zip(d_, c_) if d <= date]
        bd = beta_dimson(px, idx, date)
        if bd and bd["n"] >= 100 and fin(bd["b"]):
            bs.append(bd)
    if len(bs) < 8:
        return (1.0, 0.4), 0
    m = mean([b["b"] for b in bs])
    var = (sd([b["b"] for b in bs]) or 0.4) ** 2 - mean([b["se"] ** 2 for b in bs])
    return (m, math.sqrt(max(var, 0.04))), len(bs)


def margin_persistence(I, date):
    """part de l'écart entre la marge nette d'une année et la marge médiane de la société qui subsiste l'année suivante, mesurée
    sur l'ensemble des sociétés non financières de la BRVM (exercices publiés à la date, au moins 8 exercices par société,
    écarts bornés à ±30 points)"""
    pts = []
    for S in I["S"].values():
        if S["fin"]:
            continue
        rev, ni = S["ser"]["rev"], S["ser"]["ni"]
        br = rev_breaks(rev)
        y0 = max(br) if br else -1
        pub = S.get("pub") or {}
        nm = {y: ni[y] / rev[y] for y in rev if y >= y0 and y in ni and rev[y] > 0 and (pub.get(y) or (y + 1) * 10000 + 630) <= date}
        if len(nm) < 8:
            continue
        mdn = med(list(nm.values()))
        for y in nm:
            if y + 1 in nm:
                pts.append((clamp(nm[y] - mdn, -0.3, 0.3), clamp(nm[y + 1] - mdn, -0.3, 0.3)))
    sxx = sum(x * x for x, _ in pts)
    if len(pts) < 50 or not sxx:
        return 0.7, len(pts)
    b = sum(x * y for x, y in pts) / sxx
    I.setdefault("_mp_raw", {})[date] = b
    return clamp(b, 0.3, 0.95), len(pts)



# ------------------------------------------------------------------------------------------------------------- historique
def rev_breaks(rev):
    """ruptures de série du chiffre d'affaires (changement de périmètre ou de présentation) : variation d'un an supérieure à ×2,5
    ou inférieure à ×0,5"""
    ys = sorted(rev)
    return [b for a, b in zip(ys, ys[1:]) if b == a + 1 and rev[a] > 0 and rev[b] > 0 and not (0.5 <= rev[b] / rev[a] <= 2.5)]


def history(S, V):
    ser = V["ser"]
    ni, rev, eq = ser["ni"], ser["rev"], ser["eq"]
    H = {"fy": V["fy"]}
    br = rev_breaks(rev)
    H["breaks"] = br
    y0 = max(br) if br else -1
    rev_pb = {y: v for y, v in rev.items() if y >= y0}
    H["rev_pb"] = rev_pb

    def c_(d, n):
        if not d:
            return None
        y1 = max(d)
        return cagr(d.get(y1 - n), d.get(y1), n) if (y1 - n) in d else None
    for k, d in (("rev", rev_pb), ("ni", ni), ("eq", eq)):
        for n in (3, 5, 10):
            H[f"cagr_{k}_{n}"] = c_(d, n)
    H["g_rev"] = {y: rev_pb[y] / rev_pb[y - 1] - 1 for y in sorted(rev_pb) if (y - 1) in rev_pb and rev_pb[y - 1] > 0}
    roe = {}
    for y in sorted(ni):
        b0, b1 = eq.get(y - 1), eq.get(y)
        base = (b0 + b1) / 2 if fin(b0) and fin(b1) else b1
        if fin(base) and base > 0:
            roe[y] = ni[y] / base
    H["roe"] = roe
    H["nm"] = {y: ni[y] / rev_pb[y] for y in ni if rev_pb.get(y)}
    H["om"] = {y: ser["ebit"][y] / rev_pb[y] for y in ser["ebit"] if rev_pb.get(y)}
    H["conv"] = {y: ser["ocf"][y] / ni[y] for y in ser["ocf"] if ni.get(y) and ni[y] > 0}
    H["capex_s"] = {y: abs(ser["capex"][y]) / rev_pb[y] for y in ser["capex"] if rev_pb.get(y)}
    H["losses5"] = sum(1 for y in sorted(ni)[-5:] if ni[y] < 0)
    last5 = [ni[y] for y in sorted(ni)[-5:]]
    mu = mean(last5)
    H["cv_ni"] = (sd(last5) / abs(mu)) if (len(last5) >= 3 and mu) else None
    sh = V["shares"]
    pay = {}
    for y, d in V["dv"].items():
        if ni.get(y) and ni[y] > 0 and sh:
            pay[y] = d * sh / (ni[y] * 1e6)
    H["payout"] = pay
    fy = V["fy"] or 0
    H["div_years10"] = sum(1 for y in range(fy - 9, fy + 1) if V["dv"].get(y))
    ds = [V["dv"][y] for y in sorted(V["dv"]) if fy - 9 <= y <= fy]
    H["div_cuts"] = sum(1 for a, b in zip(ds, ds[1:]) if b < a * 0.9)
    # multiples historiques hebdomadaires (5 dernières années avant la date)
    mh = S["mh"]
    if mh.get("d"):
        idx = [i for i, d in enumerate(mh["d"]) if d <= V["date"]][-260:]
        H["mh_pe"] = [mh["pe"][i] for i in idx if fin((mh.get("pe") or [None] * (i + 1))[i]) and 0 < mh["pe"][i] < 60]
        H["mh_pb"] = [mh["pb"][i] for i in idx if fin((mh.get("pb") or [None] * (i + 1))[i]) and 0 < mh["pb"][i] < 20]
        H["mh_eve"] = [mh["ev_ebitda"][i] for i in idx if fin((mh.get("ev_ebitda") or [None] * (i + 1))[i]) and 0 < mh["ev_ebitda"][i] < 40]
    # cours : volatilité annualisée sur 3 ans, plus forte baisse sur 5 ans, ancienneté du dernier cours
    px = V["px_hist"]
    if len(px) > 120:
        c = [p[1] for p in px[-756:]]
        r = [math.log(c[i] / c[i - 1]) for i in range(1, len(c)) if c[i - 1] > 0 and c[i] > 0]
        v_ = sd(r)
        H["vol3"] = v_ * math.sqrt(252) if v_ else None
        pk, mdd = 0, 0
        for _, x in px[-1260:]:
            pk = max(pk, x)
            mdd = min(mdd, x / pk - 1) if pk else mdd
        H["mdd5"] = mdd
    return H


# ------------------------------------------------------------------------------------------------------------- prévisions (modèle 9)
def _run(series):
    """plus longue suite d'exercices consécutifs se terminant au dernier exercice"""
    ys = sorted(series)
    if not ys:
        return []
    out = [ys[-1]]
    for y in reversed(ys[:-1]):
        if y == out[-1] - 1:
            out.append(y)
        else:
            break
    return sorted(out)


def _ols(X, y):
    k = len(X[0])
    n = len(X)
    if n <= k + 1:
        return None
    XtX = [[sum(X[r][i] * X[r][j] for r in range(n)) for j in range(k)] for i in range(k)]
    Xty = [sum(X[r][i] * y[r] for r in range(n)) for i in range(k)]
    if k == 3:
        inv = inv3(XtX)
        if not inv:
            return None
        return [sum(inv[i][j] * Xty[j] for j in range(3)) for i in range(3)]
    return None


FC_ORDER = ["naive", "moy3", "derive", "roe", "ar1"]
# une méthode plus élaborée que la prévision naïve n'est retenue pour une société que si elle a fait au moins 20 % d'erreur en
# moins sur au moins 8 exercices testés (la validation historique montre qu'une sélection moins exigeante dégrade la prévision)
FC_SEL_RATIO, FC_SEL_K = 0.8, 8
FC_NAMES = {"naive": "Naïve (dernier exercice reconduit)", "moy3": "Moyenne des 3 derniers exercices", "derive": "Tendance (croissance médiane récente)",
            "roe": "Retour de la rentabilité vers sa médiane", "ar1": "Autorégressif avec tendance (AR(1))"}


def _fc_one(m, xs, ys_, eq):
    """prévision de l'exercice suivant le dernier de xs (valeurs) / ys_ (années) avec la méthode m ; None si impossible"""
    x = xs[-1]
    if m == "naive":
        return x
    if m == "moy3":
        return sum(xs[-3:]) / 3 if len(xs) >= 3 else None
    if m == "derive":
        g = [xs[i] / xs[i - 1] - 1 for i in range(max(1, len(xs) - 5), len(xs)) if xs[i - 1] > 0 and xs[i] > 0]
        return x * (1 + clamp(med(g), -0.3, 0.3)) if (len(g) >= 3 and x > 0) else None
    if m == "roe":
        if not eq:
            return None
        rs = [xs[i] / eq[ys_[i - 1]] for i in range(1, len(xs)) if eq.get(ys_[i - 1]) and eq[ys_[i - 1]] > 0]
        b = eq.get(ys_[-1])
        if len(rs) < 3 or not b or b <= 0:
            return None
        r0, rm = rs[-1], med(rs[-8:])
        return b * (r0 + 0.35 * (rm - r0))
    if m == "ar1":
        if len(xs) < 8:
            return None
        X = [[1.0, float(i), xs[i - 1]] for i in range(1, len(xs))]
        bet = _ols(X, xs[1:])
        if not bet:
            return None
        return bet[0] + bet[1] * len(xs) + bet[2] * x
    return None


def forecast(series, eq=None, min_hist=5, scale=1.0):
    """prévision statistique de l'exercice suivant, comparée hors échantillon (origine glissante) à la prévision naïve.
    Renvoie les erreurs de chaque méthode, la méthode retenue, la prévision et un intervalle empirique."""
    ys_ = _run(series)
    xs = [series[y] for y in ys_]
    res = {"n_hist": len(xs), "models": [], "best": "naive", "why": ""}
    if len(xs) < 2:
        res.update(f=xs[-1] if xs else None, lo=None, hi=None, ok=False, why="historique insuffisant")
        return res
    errs = {m: [] for m in FC_ORDER}
    rel = {m: [] for m in FC_ORDER}  # erreurs normalisées : (réalisé − prévu) / médiane des valeurs absolues des 5 derniers exercices

    def nscale(xs_):
        return med([abs(x) for x in xs_[-5:]]) or None
    cover = []
    for o in range(min_hist, len(xs)):
        act = xs[o]
        sc0 = nscale(xs[:o])
        for m in FC_ORDER:
            f_ = _fc_one(m, xs[:o], ys_[:o], eq)
            if fin(f_):
                errs[m].append(abs(act - f_))
                if sc0:
                    rel[m].append((act - f_) / sc0)
    mae_n = mean(errs["naive"])
    for m in FC_ORDER:
        n = len(errs[m])
        mae = mean(errs[m])
        res["models"].append({"id": m, "n": FC_NAMES[m], "k": n, "mae": rnd(mae, 1), "ratio": rnd(mae / mae_n, 3) if (mae is not None and mae_n) else None})
    ok_models = [r for r in res["models"] if r["k"] >= 4 and r["ratio"] is not None]
    best = "naive"
    if ok_models:
        rb = min(ok_models, key=lambda r: r["ratio"])
        if rb["id"] != "naive" and rb["ratio"] < FC_SEL_RATIO and rb["k"] >= FC_SEL_K:
            best = rb["id"]
        res["why"] = (f"{FC_NAMES[best]} : erreur moyenne hors échantillon {'%.0f' % ((rb['ratio'] if best != 'naive' else 1) * 100)} % de celle de la "
                      f"prévision naïve sur {rb['k']} exercices testés") if best != "naive" else \
            "aucune méthode ne fait nettement mieux que la prévision naïve (au moins 20 % d'erreur en moins sur 8 exercices) : la prévision naïve est retenue"
        res["ok"] = True
    else:
        res["why"] = "validation hors échantillon impossible (historique trop court) : prévision naïve retenue"
        res["ok"] = False
    res["best"] = best
    f_ = _fc_one(best, xs, ys_, eq)
    if not fin(f_):
        best, f_ = "naive", xs[-1]
        res["best"] = best
    res["f"] = f_
    r_ = rel[best] if len(rel[best]) >= 4 else rel["naive"]
    if len(r_) >= 6:
        lo, hi = quant(r_, 0.1), quant(r_, 0.9)
    else:
        s_ = max(sd(r_) or 0.0, 0.25) * 1.28
        lo, hi = -s_, s_
    sc_now = nscale(xs) or abs(f_) or 1.0
    lo, hi = lo * scale, hi * scale
    res["lo"], res["hi"] = f_ + lo * sc_now, f_ + hi * sc_now
    res["rel"] = (lo, hi)
    res["scale"] = scale
    # calibration : chaque intervalle construit avec les seules erreurs antérieures, comparé à l'exercice suivant
    for o in range(min_hist + 3, len(xs)):
        prev = []
        for oo in range(min_hist, o):
            ff = _fc_one(best, xs[:oo], ys_[:oo], eq)
            sc0 = nscale(xs[:oo])
            if fin(ff) and sc0:
                prev.append((xs[oo] - ff) / sc0)
        ff = _fc_one(best, xs[:o], ys_[:o], eq)
        sc0 = nscale(xs[:o])
        if len(prev) >= 3 and fin(ff) and sc0:
            if len(prev) >= 6:
                l_, h_ = quant(prev, 0.1), quant(prev, 0.9)
            else:
                s_ = max(sd(prev) or 0.0, 0.25) * 1.28
                l_, h_ = -s_, s_
            cover.append(1 if ff + l_ * scale * sc0 <= xs[o] <= ff + h_ * scale * sc0 else 0)
    res["cover"] = (sum(cover) / len(cover), len(cover)) if cover else None
    res["ratio_best"] = next((r["ratio"] for r in res["models"] if r["id"] == best), None) if res["ok"] else None
    return res


def oos_factor(ratio):
    """poids lié à la performance hors échantillon : 1 pour une méthode qui fait moitié moins d'erreur que la prévision naïve,
    0,8 pour la prévision naïve, 0,5 au plus bas ; 0,8 si non mesurable"""
    return clamp(1.2 - 0.4 * ratio, 0.5, 1.1) if fin(ratio) else 0.8


# ------------------------------------------------------------------------------------------------------------- hypothèses
def build_params(S, V, H, M, F):
    """hypothèses centrales (avec justification et statut) et paramètres de calcul"""
    hyp = []

    def add(k, n, v, kind, why, fmt="pct"):
        hyp.append({"k": k, "n": n, "v": rnd(v, 5) if fin(v) else v, "kind": kind, "why": why, "fmt": fmt})
    arch = S["arch"]
    A = ARCH[arch]
    cty = S["cty"]
    fix = M.get("fix") or {}
    rf = fix.get("rf") or M["rf"].get(cty) or M["rf"].get("CI") or 0.072
    add("rf", "Taux sans risque", rf, "fait", M["rf_why"].get(cty, "taux ivoirien utilisé faute de courbe du pays"))
    bd = beta_dimson(V["px_hist"], M["idx"], V["date"])
    bp_m, bp_s = M.get("beta_prior") or (1.0, 0.4)
    if fix.get("beta"):
        b_adj, se_b = fix["beta"], fix.get("se_beta", 0.2)
        add("beta", "Bêta", b_adj, "estimation", "bêta de la version en vigueur (paramètres de marché figés pour mesurer l'effet des seules informations nouvelles)", "num")
    elif bd and fin(bd["b"]) and bd["se"] > 0:
        b_raw, se_b = bd["b"], bd["se"]
        wv = bp_s ** 2 / (bp_s ** 2 + se_b ** 2)
        b_adj = clamp(wv * b_raw + (1 - wv) * bp_m, 0.4, 1.8)
        se_b = math.sqrt(wv) * se_b
        add("beta", "Bêta", b_adj, "estimation",
            f"bêta mesuré {b_raw:.2f} (erreur type {bd['se']:.2f}) sur {bd['n']} semaines contre l'indice BRVM Composite, corrigé des cotations peu fréquentes, "
            f"puis rapproché de la moyenne des actions de la BRVM ({bp_m:.2f}) d'autant plus que la mesure est imprécise (poids de la mesure {wv:.0%})", "num")
    else:
        b_adj, se_b = bp_m, bp_s
        add("beta", "Bêta", bp_m, "hypothèse", f"historique de cours insuffisant pour mesurer le bêta : moyenne des actions de la BRVM ({bp_m:.2f})", "num")
    erp = fix.get("erp") or M["erp"]
    add("erp", "Prime de risque du marché", erp, "estimation", M["erp_why"])
    ke = rf + b_adj * erp
    add("ke", "Coût des fonds propres", ke, "estimation", "taux sans risque + bêta × prime de risque du marché")
    glt = min(fix.get("glt") or M["glt"].get(cty) or M["glt"].get("CI") or 0.04, ke - 0.04)
    add("glt", "Croissance de long terme (au-delà de 10 ans)", glt, "hypothèse",
        (M["glt_why"].get(cty) or "4 % par défaut") + " ; au plus coût des fonds propres − 4 points")
    sig_ke = math.sqrt((se_b * erp) ** 2 + (b_adj * M["sd_erp"]) ** 2)
    P = {"ke": ke, "glt": glt, "rf": rf, "beta": b_adj, "se_beta": se_b, "sig_ke": fix.get("sig_ke") or clamp(sig_ke, 0.005, 0.03), "phi": A["phi"],
         "shares": V["shares"], "fw": None, "px_w": fix.get("price")}
    add("phi", "Persistance de la rentabilité excédentaire à 10 ans", A["phi"], "hypothèse",
        f"part de l'écart entre rentabilité et coût des fonds propres encore présente dans 10 ans pour un(e) {A['n'].lower()} "
        "(concurrence et régulation la réduisent progressivement)")
    ser = V["ser"]
    fy = V["fy"]
    win = A["win"]
    # base : fonds propres publiés du dernier exercice
    B0 = ser["eq"].get(fy)
    P["B0"] = B0
    NI0 = ser["ni"].get(fy)
    P["NI0"] = NI0
    # cadre de projection
    rev_pb = H["rev_pb"]
    yrs_rev = [y for y in sorted(rev_pb) if y in ser["ni"]]
    if S["fin"]:
        fw = "roe" if (fin(B0) and B0 > 0 and len(H["roe"]) >= 3) else None
    else:
        fw = "marge" if (len(yrs_rev) >= 5 and fy in rev_pb) else ("roe" if (fin(B0) and B0 > 0 and len(H["roe"]) >= 3) else None)
    P["fw"] = fw
    if fw == "roe":
        rs = [H["roe"][y] for y in sorted(H["roe"])[-win:]]
        roe0 = med(rs)
        P["roe0"] = roe0
        P["sig_roe"] = clamp((sd([H["roe"][y] for y in sorted(H["roe"])[-8:]]) or 0.03) * 0.7, 0.01, 0.08)
        add("roe0", "Rentabilité des fonds propres de départ", roe0, "estimation",
            f"médiane des {len(rs)} derniers exercices publiés (résultat net / fonds propres moyens)" + (" : rentabilité normative sur un cycle" if win >= 8 else ""))
        if F["ni"] and F["ni"].get("f") is not None and fin(B0) and B0 > 0:
            P["roe1"] = F["ni"]["f"] / B0
            add("roe1", "Rentabilité de l'exercice à venir", P["roe1"], "estimation",
                f"prévision statistique du résultat net : {F['ni']['why']}")
        P["rev0"] = rev_pb.get(fy)
    elif fw == "marge":
        P["rev0"] = rev_pb[fy]
        nms = [H["nm"][y] for y in sorted(H["nm"])[-win:]]
        m0 = med(nms)
        anchor = med([H["nm"][y] for y in sorted(H["nm"])[-10:]])
        P["m0"], P["m_anchor"] = m0, anchor
        P["sig_m"] = clamp((sd([H["nm"][y] for y in sorted(H["nm"])[-8:]]) or 0.02) * 0.7, 0.005, 0.06)
        P["b_m"] = M.get("m_pers") or 0.7
        add("m0", "Marge nette de départ", m0, "estimation", f"médiane des {len(nms)} derniers exercices publiés (résultat net / chiffre d'affaires)")
        add("m_lt", "Marge nette normative", anchor, "hypothèse",
            f"médiane des {min(len(H['nm']), 10)} derniers exercices publiés ; la marge s'en rapproche chaque année : {P['b_m']:.0%} de l'écart subsiste d'une année "
            f"sur l'autre, rythme mesuré sur l'ensemble des sociétés non financières de la BRVM ({M.get('m_pers_n', 0)} observations"
            + (f", mesure {M['m_pers_raw']:.0%} bornée à {P['b_m']:.0%}" if fin(M.get("m_pers_raw")) and abs(M["m_pers_raw"] - P["b_m"]) > 0.005 else "") + ")")
        gh = med([H.get("cagr_rev_5"), H.get("cagr_rev_10")])
        if not fin(gh):
            gh = H.get("cagr_rev_3")
        g_mid = 0.5 * clamp(gh, -0.05, 0.15) + 0.5 * glt if fin(gh) else glt
        P["g_mid"] = g_mid
        gs = [H["g_rev"][y] for y in sorted(H["g_rev"])[-10:]]
        P["sig_g"] = clamp((sd(gs) or 0.08) / math.sqrt(5) + 0.01, 0.01, 0.06)
        add("g_hist", "Croissance historique du chiffre d'affaires", gh, "fait",
            "taux annuels composés sur 5 et 10 ans (médiane)" + (f" ; série reprise après la rupture de {max(H['breaks'])}" if H["breaks"] else ""))
        add("g_mid", "Croissance du chiffre d'affaires (années 2 à 10)", g_mid, "hypothèse",
            "moitié de la croissance historique (bornée entre −5 % et +15 %), moitié de la croissance de long terme, puis convergence vers celle-ci")
        if F["rev"] and F["rev"].get("best") != "naive" and fin(F["rev"].get("f")) and rev_pb.get(fy):
            P["g1"] = clamp(F["rev"]["f"] / rev_pb[fy] - 1, -0.3, 0.4)
            add("g1", "Croissance du chiffre d'affaires de l'exercice à venir", P["g1"], "estimation", f"prévision statistique : {F['rev']['why']}")
        # corrélation empirique entre croissance du chiffre d'affaires et variation de la marge nette (≥ 8 observations)
        pairs = [(H["g_rev"][y], H["nm"][y] - H["nm"][y - 1]) for y in H["g_rev"] if y in H["nm"] and (y - 1) in H["nm"]]
        rho = pearson([p[0] for p in pairs], [p[1] for p in pairs]) if len(pairs) >= 8 else None
        P["rho_gm"] = clamp(0.5 * rho, -0.6, 0.6) if fin(rho) else 0.0
        P["rho_n"] = len(pairs)
        if fin(B0) and B0 > 0 and fin(NI0):
            P["roe_cur"] = med([H["roe"][y] for y in sorted(H["roe"])[-win:]])
        # rentabilité marginale observée : croissance du résultat sur 10 ans rapportée au taux de rétention médian (une société qui
        # a longtemps grandi en distribuant presque tout son bénéfice n'a pas besoin de retenir autant que le suppose la formule)
        pays10 = [H["payout"][y] for y in sorted(H["payout"])[-10:]]
        g_ni = H.get("cagr_ni_10")
        if len(pays10) >= 7 and fin(g_ni) and g_ni > 0 and win < 8:
            ret = 1 - med(pays10)
            P["r_hist"] = min(g_ni / ret, 1.0) if ret > 0.02 else 1.0
            add("r_hist", "Rentabilité marginale observée du bénéfice retenu", P["r_hist"], "estimation",
                f"croissance annuelle du résultat sur 10 ans ({g_ni:.1%}) / part du bénéfice retenue (médiane {ret:.0%}), plafonnée à 100 % ; "
                "sert à fixer le taux de distribution de long terme compatible avec la croissance")
    # distribution
    pays = [H["payout"][y] for y in sorted(H["payout"])[-5:]]
    pay0 = med(pays)
    if fin(pay0):
        P["pay0"] = clamp(pay0, 0.0, 1.2)
        P["sig_pay"] = clamp(sd(pays) or 0.1, 0.03, 0.25)
        add("pay0", "Taux de distribution de départ", P["pay0"], "estimation",
            f"médiane des {len(pays)} derniers taux de distribution publiés (dividende ordinaire / bénéfice par action) ; le dividende passé n'est pas supposé acquis")
    else:
        P["pay0"], P["sig_pay"] = 0.0, 0.05
        add("pay0", "Taux de distribution de départ", 0.0, "fait", "aucun dividende ordinaire récent")
    # DCF : marge opérationnelle, rentabilité des capitaux investis, dette nette, impôt
    if not S["fin"] and fw == "marge":
        oms = [H["om"][y] for y in sorted(H["om"])[-win:]]
        ro = [ser["roic"][y] for y in sorted(ser["roic"])[-5:]]
        nd0 = ser["nd"].get(fy)
        tax = S.get("tax")
        if len(H["om"]) >= 5 and len(ro) >= 3 and fin(nd0) and fin(tax):
            P["om0"] = med(oms)
            P["om_anchor"] = med([H["om"][y] for y in sorted(H["om"])[-10:]])
            P["sig_om"] = clamp((sd([H["om"][y] for y in sorted(H["om"])[-8:]]) or 0.02) * 0.7, 0.005, 0.08)
            P["roic0"] = med(ro)
            P["sig_roic"] = clamp((sd(ro) or 0.03) * 0.7, 0.01, 0.1)
            P["nd0"], P["tax"] = nd0, tax
            P["kd"] = rf + 0.02
            # taux de réinvestissement observé : 1 − (flux d'exploitation − investissements) / résultat d'exploitation après impôt
            rr = []
            y_br = max(H["breaks"]) if H["breaks"] else -1
            for y in ser["ocf"]:
                if y >= y_br and y in ser["capex"] and ser["ebit"].get(y) and ser["ebit"][y] > 0:
                    rr.append(clamp(1 - (ser["ocf"][y] - abs(ser["capex"][y])) / (ser["ebit"][y] * (1 - tax)), -0.5, 1.0))
            if len(rr) >= 5:
                P["rr_hist"] = clamp(med(rr), 0.0, 1.0)
            add("om0", "Marge opérationnelle de départ", P["om0"], "estimation", f"médiane des {len(oms)} derniers exercices (résultat d'exploitation / chiffre d'affaires)")
            add("roic0", "Rentabilité des capitaux investis", P["roic0"], "estimation", f"médiane des {len(ro)} derniers exercices publiés")
            add("tax", "Taux d'impôt sur les sociétés", tax, "fait", "taux de l'impôt sur les sociétés du pays")
            add("nd0", "Dette nette (millions FCFA)", nd0, "fait", f"dernier bilan publié (exercice {fy}) ; négative = trésorerie nette", "m")
            add("kd", "Coût de la dette", P["kd"], "hypothèse", "taux sans risque du pays + 2 points (coût d'emprunt des sociétés non publié)")
            if fin(P.get("rr_hist")):
                add("rr_hist", "Taux de réinvestissement observé", P["rr_hist"], "estimation",
                    f"médiane sur {len(rr)} exercices de 1 − (flux de trésorerie d'exploitation − investissements) / résultat d'exploitation après impôt, "
                    "bornée entre 0 et 100 % ; "
                    "converge en 10 ans vers le réinvestissement nécessaire à la croissance (croissance / rentabilité des nouveaux investissements)")
    return P, hyp


def roe_lt(P, ke):
    base = P.get("roe0") if P["fw"] == "roe" else P.get("roe_cur")
    if not fin(base):
        return None
    return ke + P["phi"] * (base - ke)


# ------------------------------------------------------------------------------------------------------------- projection
def project(P, ke, glt, shock=None, N=N_YEARS):
    """projection annuelle sur N+1 exercices : chiffre d'affaires, résultat, dividendes, fonds propres, flux disponibles.
    shock : (dg en points, variation relative de la rentabilité, durée en années ou None)."""
    fw = P["fw"]
    dg, dprof, dur = (shock[0] / 100, shock[1], shock[2]) if shock else (0.0, 0.0, None)
    rlt = roe_lt(P, ke)
    R = max(rlt if fin(rlt) else 0.0, P.get("r_hist") or 0.0) if fw == "marge" else rlt
    if fin(R) and R > glt + 0.005:
        pay_lt = clamp(1 - glt / R, 0.2, 1.0)
    else:
        pay_lt = clamp(P["pay0"], 0.0, 1.0)
    rows = []
    B = P.get("B0")
    rev = P.get("rev0")
    nd = P.get("nd0")
    dcf = "om0" in P
    if dcf:
        ronic = ke + P["phi"] * (P["roic0"] - ke)
        ronic = max(ronic, glt + 0.02)
    b_m = P.get("b_m", 0.7)
    for k in range(1, N + 2):
        w = min((k - 1) / (N - 1), 1.0)
        fade = 1.0 if (dur is None or k <= dur) else (max(0.0, 1 - (k - dur) / 2))
        s_g = dg * fade
        s_p = dprof * fade
        if fw == "roe":
            roe = P["roe0"] + (rlt - P["roe0"]) * w if not (k == 1 and fin(P.get("roe1"))) else P["roe1"]
            roe *= (1 + s_p)
            ni = roe * B
            g = None
        else:
            if k == 1 and fin(P.get("g1")):
                g = P["g1"]
            elif k > N:
                g = glt
            else:
                g = P["g_mid"] + (glt - P["g_mid"]) * min((k - 2) / (N - 2), 1.0) if k >= 2 else P["g_mid"]
            g += s_g
            rev = rev * (1 + g)
            m = P["m_anchor"] + (P["m0"] - P["m_anchor"]) * b_m ** k
            ni = rev * m * (1 + s_p)
        pay = P["pay0"] + (pay_lt - P["pay0"]) * w if k <= N else pay_lt
        div = max(0.0, pay * ni) if ni > 0 else 0.0
        if fw == "roe":
            g = (ni - div) / B if B else None
            if fin(rev) and fin(g):
                rev = rev * (1 + g)
        r = {"k": k, "ni": ni, "div": div, "pay": pay, "g": g, "B": B, "rev": rev}
        if dcf:
            om = (P["om_anchor"] + (P["om0"] - P["om_anchor"]) * b_m ** k) * (1 + s_p)
            gn = glt if k > N else (g if g is not None else glt)
            nopat = rev * om * (1 - P["tax"])
            reinv = clamp(gn / ronic, -0.3, 1.0) if ronic > 0 else 0.0
            if fin(P.get("rr_hist")) and k <= N:
                reinv = P["rr_hist"] + (reinv - P["rr_hist"]) * w
            fcff = nopat * (1 - reinv)
            r["om"], r["fcff"], r["nopat"] = om, fcff, nopat
            if fin(nd):
                interest = P["kd"] * (1 - P["tax"]) * max(nd, 0)
                nd = nd - (fcff - interest - div)
                r["nd"] = nd
        if B is not None:
            B = B + ni - div
        r["B1"] = B
        rows.append(r)
    return rows, pay_lt


def v_ri(P, rows, ke, glt):
    if not fin(P.get("B0")) or P["B0"] <= 0:
        return None
    N = len(rows) - 1
    v = P["B0"]
    for r in rows[:N]:
        v += (r["ni"] - ke * r["B"]) / (1 + ke) ** r["k"]
    last = rows[N]
    tv = (last["ni"] - ke * last["B"]) / (ke - glt) / (1 + ke) ** N
    return v + tv, tv / (v + tv) if (v + tv) else None


def v_ddm(P, rows, ke, glt):
    N = len(rows) - 1
    v = sum(r["div"] / (1 + ke) ** r["k"] for r in rows[:N])
    tv = rows[N]["div"] / (ke - glt) / (1 + ke) ** N
    return v + tv, tv / (v + tv) if (v + tv) else None


def wacc_of(P, ke, price):
    price = P.get("px_w") or price
    if not (fin(price) and P.get("shares")):
        return ke
    E = price * P["shares"] / 1e6
    D = max(P["nd0"], 0.0)
    return (E * ke + D * P["kd"] * (1 - P["tax"])) / (E + D) if (E + D) > 0 else ke


def v_dcf(P, rows, ke, glt, price):
    if "om0" not in P:
        return None
    w = wacc_of(P, ke, price)
    if w <= glt + 0.01:
        return None
    N = len(rows) - 1
    ev = sum(r["fcff"] / (1 + w) ** r["k"] for r in rows[:N])
    tv = rows[N]["fcff"] / (w - glt) / (1 + w) ** N
    eqv = ev + tv - P["nd0"]
    return eqv, (tv / (ev + tv) if (ev + tv) else None), w


def values(P, ke, glt, price, shock=None, dke=0.0):
    """valeur par action de chaque modèle intrinsèque pour un jeu de paramètres"""
    ke_ = ke + dke
    glt_ = min(glt, ke_ - 0.03)
    rows, pay_lt = project(P, ke_, glt_, shock)
    sh = P["shares"]
    out = {}
    if P["fw"] and sh:
        r = v_ri(P, rows, ke_, glt_)
        if r:
            out["ri"] = (r[0] * 1e6 / sh, r[1])
        r = v_ddm(P, rows, ke_, glt_)
        if r and P["pay0"] > 0.05:
            out["ddm"] = (r[0] * 1e6 / sh, r[1])
        r = v_dcf(P, rows, ke_, glt_, price)
        if r:
            out["dcf"] = (r[0] * 1e6 / sh, r[1])
    return out, rows


def value_at(P, rows, ke, glt, h, model, price):
    """valeur par action à l'horizon h (années) selon le modèle, à partir de la trajectoire projetée"""
    sh = P["shares"]
    N = len(rows) - 1
    glt = min(glt, ke - 0.03)
    if model == "ddm":
        v = sum(r["div"] / (1 + ke) ** (r["k"] - h) for r in rows[:N] if r["k"] > h)
        v += rows[N]["div"] / (ke - glt) / (1 + ke) ** (N - h)
    elif model == "ri":
        Bh = rows[h - 1]["B1"] if h >= 1 else P["B0"]
        v = Bh + sum((r["ni"] - ke * r["B"]) / (1 + ke) ** (r["k"] - h) for r in rows[:N] if r["k"] > h)
        v += (rows[N]["ni"] - ke * rows[N]["B"]) / (ke - glt) / (1 + ke) ** (N - h)
    else:
        w = wacc_of(P, ke, price)
        ev = sum(r["fcff"] / (1 + w) ** (r["k"] - h) for r in rows[:N] if r["k"] > h)
        ev += rows[N]["fcff"] / (w - glt) / (1 + w) ** (N - h)
        ndh = rows[h - 1].get("nd", P["nd0"]) if h >= 1 else P["nd0"]
        v = ev - ndh
    return v * 1e6 / sh


# ------------------------------------------------------------------------------------------------------------- Monte-Carlo (modèle 2)
MC_KEYS = ("ke", "glt", "phi", "pay0", "roe0", "m0", "g_mid", "om0", "roic0")


def sample_params(P, rng, ops_only=False):
    """un tirage des paramètres incertains (distributions justifiées par l'historique de la société et du marché) ; ops_only :
    seules les hypothèses d'exploitation varient (rendement exigé et croissance de long terme fixés), pour construire les scénarios"""
    Q = dict(P)
    z1, z2, z3, z4, z5 = (rng.gauss(0, 1) for _ in range(5))
    u_glt = rng.uniform(P["glt"] - 0.01, P["glt"] + 0.005)
    if not ops_only:
        Q["ke"] = clamp(P["ke"] + P["sig_ke"] * z1, P["rf"] + 0.01, 0.3)
        Q["glt"] = u_glt
    Q["phi"] = clamp(rng.uniform(P["phi"] - 0.15, P["phi"] + 0.15), 0.0, 0.9)
    Q["pay0"] = clamp(P["pay0"] + P["sig_pay"] * z5, 0.0, 1.2)
    if P["fw"] == "roe":
        Q["roe0"] = P["roe0"] + P["sig_roe"] * z3
        if fin(P.get("roe1")):
            Q["roe1"] = P["roe1"] + P["sig_roe"] * z3 * 0.5
    elif P["fw"] == "marge":
        rho = P.get("rho_gm", 0.0)
        zg = rho * z3 + math.sqrt(1 - rho * rho) * z2
        Q["g_mid"] = P["g_mid"] + P["sig_g"] * zg
        Q["m0"] = P["m0"] + P["sig_m"] * z3
        if fin(P.get("roe_cur")):
            Q["roe_cur"] = P["roe_cur"] * (Q["m0"] / P["m0"]) if P["m0"] else P["roe_cur"]
        if "om0" in P:
            Q["om0"] = P["om0"] + P["sig_om"] * z3
            Q["roic0"] = P["roic0"] + P["sig_roic"] * z4
    return Q


def monte_carlo(P, price, seed, n=N_SIM, keep_paths=True, ops_only=False):
    rng = random.Random(seed)
    out = {"ri": [], "ddm": [], "dcf": []}
    paths = []
    hv = {m: {h: [] for h in HORIZONS} for m in out}
    for _ in range(n):
        Q = sample_params(P, rng, ops_only)
        glt = min(Q["glt"], Q["ke"] - 0.03)
        vals, rows = values(Q, Q["ke"], glt, price)
        rec = {k: Q.get(k) for k in MC_KEYS}
        for m in out:
            v = vals.get(m)
            out[m].append(v[0] if v else None)
            rec[m] = v[0] if v else None
            if v and keep_paths:
                for h in HORIZONS:
                    hv[m][h].append(value_at(Q, rows, Q["ke"], glt, h, m, price))
        if keep_paths:
            paths.append(rec)
    return out, paths, hv


# ------------------------------------------------------------------------------------------------------------- multiples (modèle 4)
def multiples(S, V, H, P, F, peers):
    """valeur par les multiples : historiques de la société (5 ans) et comparables (même archétype), appliqués aux résultats attendus
    de l'exercice à venir (prévision statistique). Échantillons pour la synthèse : multiples historiques tirés dans la distribution
    observée, résultat tiré dans l'intervalle de prévision."""
    sh = V["shares"]
    res = {}
    if not sh or not F["ni"] or not fin(F["ni"].get("f")):
        return res
    ni1, lo, hi = F["ni"]["f"], F["ni"]["lo"], F["ni"]["hi"]
    eps1 = ni1 * 1e6 / sh
    B0 = V["ser"]["eq"].get(V["fy"])
    div1 = max(0.0, P["pay0"] * ni1) if ni1 > 0 else 0.0
    bv1 = (B0 + ni1 - div1) * 1e6 / sh if fin(B0) else None
    rng = random.Random(int(hashlib.sha256(f"{S['t']}{V['date']}mult".encode()).hexdigest()[:8], 16))  # graine reproductible

    def ni_draw():
        return rng.triangular(lo, hi, ni1) if (fin(lo) and fin(hi) and lo <= ni1 <= hi) else ni1
    # historique de la société ; si le résultat attendu est négatif ou inférieur au tiers du résultat normatif (médiane sur 10 ans),
    # les multiples de résultat ne sont pas utilisés (résultat déprimé) : multiple de fonds propres à la place
    subs, samp, txt = [], [], []
    pe_h, pb_h, eve_h = H.get("mh_pe") or [], H.get("mh_pb") or [], H.get("mh_eve") or []
    ni10 = med([V["ser"]["ni"][y] for y in sorted(V["ser"]["ni"])[-10:]])
    depressed = not (ni1 > 0 and fin(ni10) and ni10 > 0 and ni1 >= ni10 / 3)
    if len(pe_h) >= 52 and not depressed:
        subs.append(("PER", med(pe_h) * eps1))
        txt.append(f"PER médian sur 5 ans {med(pe_h):.1f} × bénéfice par action attendu {eps1:,.0f} FCFA")
    if (S["fin"] or depressed) and len(pb_h) >= 52 and fin(bv1) and bv1 > 0:
        subs.append(("P/B", med(pb_h) * bv1))
        txt.append(f"cours / fonds propres médian sur 5 ans {med(pb_h):.2f} × fonds propres par action attendus {bv1:,.0f} FCFA"
                   + (" (résultat attendu trop faible pour un multiple de résultat)" if depressed and not S["fin"] else ""))
    ebitda0 = V["ser"]["ebitda"].get(V["fy"])
    nd0 = V["ser"]["nd"].get(V["fy"])
    if not S["fin"] and not depressed and len(eve_h) >= 52 and fin(ebitda0) and ebitda0 > 0 and fin(nd0):
        g1 = (F["rev"]["f"] / V["ser"]["rev"][V["fy"]] - 1) if (F.get("rev") and fin(F["rev"].get("f")) and V["ser"]["rev"].get(V["fy"])) else 0.0
        e1 = ebitda0 * (1 + clamp(g1, -0.3, 0.4))
        subs.append(("VE/EBITDA", (med(eve_h) * e1 - nd0) * 1e6 / sh))
        txt.append(f"valeur d'entreprise / EBITDA médian sur 5 ans {med(eve_h):.1f} × EBITDA attendu, moins la dette nette")
    if subs:
        for _ in range(N_SIM):
            k = rng.randrange(len(subs))
            nm = subs[k][0]
            n_ = ni_draw()
            if nm == "PER":
                samp.append(rng.choice(pe_h) * n_ * 1e6 / sh)
            elif nm == "P/B":
                samp.append(rng.choice(pb_h) * (B0 + n_ - max(0.0, P["pay0"] * n_)) * 1e6 / sh)
            else:
                samp.append((rng.choice(eve_h) * e1 * (n_ / ni1 if ni1 else 1) - nd0) * 1e6 / sh)
        res["mult_own"] = {"v": med([s_[1] for s_ in subs]), "samp": samp, "subs": subs, "txt": txt, "n_obs": len(pe_h)}
    # comparables
    pl = [p for p in peers if p["t"] != S["t"]]
    key = "pb" if (S["fin"] or depressed) else "pe"
    vals = [p[key] for p in pl if fin(p.get(key)) and (0 < p[key] < (8 if key == "pb" else 40))]
    if len(vals) >= 3:
        mm = med(vals)
        base = bv1 if key == "pb" else eps1
        adj, adj_txt = 1.0, ""
        if key == "pb":
            # un multiple de fonds propres dépend de la rentabilité : ajustement par (ROE normative − g) / (ROE médiane des comparables − g)
            roe_c = med([H["roe"][y] for y in sorted(H["roe"])[-10:]])
            roe_p = med([p.get("roe") for p in pl])
            g_ = P["glt"]
            if fin(roe_c) and fin(roe_p) and roe_p > g_ + 0.01:
                adj = clamp((roe_c - g_) / (roe_p - g_), 0.2, 3.0)
                adj_txt = f", ajusté de la rentabilité (ROE médiane sur 10 ans {roe_c:.1%} contre {roe_p:.1%} pour les comparables : ×{adj:.2f})"
        if fin(base) and base > 0:
            samp = []
            for _ in range(N_SIM):
                n_ = ni_draw()
                b_ = ((B0 + n_ - max(0.0, P["pay0"] * n_)) * 1e6 / sh) if key == "pb" else n_ * 1e6 / sh
                samp.append(rng.choice(vals) * adj * b_)
            res["mult_peer"] = {"v": mm * adj * base, "samp": samp, "n_peers": len(vals), "mult": mm, "adj": adj, "key": key,
                                "peers": [p["t"] for p in pl if fin(p.get(key))],
                                "txt": [f"{'cours / fonds propres' if key == 'pb' else 'PER'} médian de {len(vals)} sociétés comparables {mm:.2f}{adj_txt} × "
                                        f"{'fonds propres par action attendus' if key == 'pb' else 'bénéfice par action attendu'} {base:,.0f} FCFA"]}
    return res


def peer_table(I, today_i, date, arch_of):
    """multiples des sociétés de la BRVM à une date (PER, cours / fonds propres), groupés par archétype"""
    rows = []
    for t, S in I["S"].items():
        V = asof_view(S, date, today_i)
        if not fin(V["price"]) or not V["shares"] or V["fy"] is None:
            continue
        ni = V["ser"]["ni"].get(V["fy"])
        eq = V["ser"]["eq"].get(V["fy"])
        cap = V["price"] * V["shares"] / 1e6
        rows.append({"t": t, "arch": arch_of[t], "pe": cap / ni if (fin(ni) and ni > 0) else None, "pb": cap / eq if (fin(eq) and eq > 0) else None,
                     "roe": (ni / eq) if (fin(ni) and fin(eq) and eq > 0) else None})
    return rows


PEER_GROUPS = [({"banque", "groupe_bancaire", "credit_bail"}, "banques et établissements financiers"),
               ({"telecom"}, "opérateurs de télécommunications"), ({"utilite"}, "concessions de service public"),
               ({"petrole_distribution", "energie_industrie"}, "sociétés de l'énergie"), ({"agro_export", "agro_domestique"}, "agro-industries"),
               ({"biens_conso"}, "biens de consommation de marque"), ({"distribution", "industrie", "btp", "services"}, "industrie, distribution et services")]


def peers_for(arch, table):
    """sociétés comparables : même groupe d'activité (au moins trois en plus de la société, sinon le modèle n'est pas appliqué)"""
    for grp, lbl in PEER_GROUPS:
        if arch in grp:
            return [r for r in table if r["arch"] in grp], lbl
    return [], ""


# ------------------------------------------------------------------------------------------------------------- facteurs (modèle 8)
FACTORS = [
    ("F1", "Rentabilité", "rentabilité des fonds propres (médiane 3 ans)", 1),
    ("F2", "Stabilité des résultats", "coefficient de variation du résultat net sur 5 ans (plus faible = plus stable)", -1),
    ("F3", "Croissance", "croissance annuelle composée du chiffre d'affaires sur 5 ans", 1),
    ("F4", "Qualité des bénéfices", "flux de trésorerie d'exploitation / résultat net (médiane), sociétés non financières", 1),
    ("F5", "Solidité du bilan", "dette nette / EBITDA (non financières, plus faible = plus solide) ; fonds propres / total du bilan (banques)", 0),
    ("F6", "Régularité du dividende", "nombre d'exercices avec dividende sur 10 ans, moins les baisses de plus de 10 %", 1),
    ("F7", "Liquidité du titre", "part des séances sans échange sur un an (plus faible = plus liquide)", -1),
    ("F8", "Risque de marché", "volatilité annualisée sur 3 ans (plus faible = moins risqué)", -1),
    ("F9", "Qualité des données", "part des 5 derniers exercices vérifiés dans les états financiers publiés et longueur de l'historique", 1),
    ("F10", "Notation financière", "notation de long terme d'une agence agréée, lorsqu'elle existe", 1),
]
RATING_SC = {"AAA": 100, "AA+": 95, "AA": 90, "AA-": 85, "A+": 80, "A": 75, "A-": 70, "BBB+": 62, "BBB": 55, "BBB-": 48, "BB+": 40, "BB": 33,
             "BB-": 27, "B+": 20, "B": 15, "B-": 10}


def factor_raw(S, V, H):
    r = {}
    r["F1"] = med([H["roe"][y] for y in sorted(H["roe"])[-3:]])
    r["F2"] = H.get("cv_ni")
    r["F3"] = H.get("cagr_rev_5")
    r["F4"] = med([H["conv"][y] for y in sorted(H["conv"])[-5:]]) if not S["fin"] else None
    fy = V["fy"]
    if S["fin"]:
        a, e = V["ser"]["assets"].get(fy), V["ser"]["eq"].get(fy)
        r["F5"] = e / a if (fin(a) and fin(e) and a > 0) else None
    else:
        nd, eb = V["ser"]["nd"].get(fy), V["ser"]["ebitda"].get(fy)
        r["F5"] = -(nd / eb) if (fin(nd) and fin(eb) and eb > 0) else None
    r["F6"] = H["div_years10"] - H["div_cuts"]
    z = (S["liq"] or {}).get("zero")
    r["F7"] = z
    r["F8"] = H.get("vol3")
    last5 = [y for y in sorted(V["ser"]["ni"])[-5:]]
    vs = sum(1 for y in last5 if y in S["verified"]) / len(last5) if last5 else 0
    r["F9"] = vs * 0.7 + min(len(V["ser"]["ni"]), 15) / 15 * 0.3
    rt = S.get("rating")
    lt = (rt or {}).get("lt") or ""
    base = lt.split("(")[0].strip().upper()
    r["F10"] = RATING_SC.get(base)
    r["F10_txt"] = f"{lt} ({rt.get('ag')}, perspective {rt.get('out') or 'non précisée'})" if rt else "non notée"
    return r


def factor_scores(raws, is_fin):
    """rang centile de chaque facteur parmi les sociétés de la BRVM (0 = le moins favorable, 100 = le plus favorable) ; la solidité
    du bilan est classée séparément chez les banques et chez les sociétés non financières (indicateurs différents)"""
    out = {}
    for fid, _, _, sign in FACTORS:
        vals = {t: r.get(fid) for t, r in raws.items() if fin(r.get(fid))}
        for t, v in vals.items():
            if fid == "F10":
                out.setdefault(t, {})[fid] = v
                continue
            pool = [x for u, x in vals.items() if fid != "F5" or is_fin.get(u) == is_fin.get(t)]
            if len(pool) < 3:
                continue
            below = sum(1 for x in pool if (x < v if sign >= 0 else x > v))
            eq_ = sum(1 for x in pool if x == v) - 1
            out.setdefault(t, {})[fid] = round(100 * (below + 0.5 * eq_) / max(len(pool) - 1, 1))
    return out


# ------------------------------------------------------------------------------------------------------------- synthèse
def synth_weights(S, V, H, P, F, mods, mc, perf=None):
    """poids de chaque modèle : pertinence × données × robustesse × performance hors échantillon × cohérence × redondance"""
    arch = S["arch"]
    ap = APPLIC[arch]
    fy = V["fy"]
    last5 = sorted(V["ser"]["ni"])[-5:]
    vshare = sum(1 for y in last5 if y in S["verified"]) / len(last5) if last5 else 0.0
    sh = V["shares"]
    ni10 = med([V["ser"]["ni"][y] for y in sorted(V["ser"]["ni"])[-10:]])
    eps0 = ni10 * 1e6 / sh if (sh and fin(ni10)) else None
    bv0 = V["ser"]["eq"].get(fy) * 1e6 / sh if (sh and fin(V["ser"]["eq"].get(fy))) else None
    nyears = {"ri": min(len(V["ser"]["eq"]), len(V["ser"]["ni"])), "ddm": H["div_years10"], "dcf": min(len(H["om"]), len(V["ser"]["roic"]) + 5),
              "mult_own": len(H.get("mh_pe") or []) // 52, "mult_peer": 5}
    # performance hors échantillon de la grandeur dont dépend chaque modèle : résultat par retour de la rentabilité (RI),
    # dividende (DDM), chiffre d'affaires (DCF), résultat de l'exercice suivant (multiples)
    oos = {"ri": F.get("ri_ratio"), "ddm": F.get("dps_ratio"), "dcf": (F.get("rev") or {}).get("ratio_best"),
           "mult_own": (F.get("ni") or {}).get("ratio_best"), "mult_peer": (F.get("ni") or {}).get("ratio_best")}
    W = {}
    for m, d in mods.items():
        a = ap.get(m, 0.0)
        q = clamp(0.3 + 0.1 * min(nyears.get(m, 0), 7), 0.4, 1.0) * (0.75 + 0.25 * vshare)
        p10, p50, p90 = d["p10"], d["p50"], d["p90"]
        rob = 1 / (1 + (p90 - p10) / (2 * p50)) if (fin(p50) and p50 > 0 and fin(p10) and fin(p90)) else 0.2
        if fin(d.get("tv")) and d["tv"] > 0.75:
            rob *= 0.85
        o = oos_factor(oos.get(m))
        coh, cnote = 1.0, None
        v = d["v"]
        if fin(eps0) and eps0 > 0 and fin(v):
            pe_i = v / eps0
            if not (3 <= pe_i <= 40):
                coh, cnote = (0.3 if not (1.5 <= pe_i <= 80) else 0.5), f"PER implicite {pe_i:.1f} (sur le résultat médian de 10 ans) hors de la plage 3-40 : valeur peu cohérente avec les résultats publiés"
        if fin(bv0) and bv0 > 0 and fin(v):
            pb_i = v / bv0
            if not (0.2 <= pb_i <= 10):
                coh, cnote = min(coh, 0.3 if not (0.1 <= pb_i <= 20) else 0.5), f"cours / fonds propres implicite {pb_i:.2f} hors de la plage 0,2-10"
        pf = ((perf or {}).get(m) or {}).get("f", 1.0)
        W[m] = {"a": a, "q": round(q, 3), "r": round(rob, 3), "o": round(o, 3), "p": pf, "coh": coh, "red": 1.0, "cnote": cnote}
    # redondance : modèles dont les valeurs simulées évoluent ensemble (corrélation > 0,85) ; les deux multiples partagent le même résultat attendu
    ms = [m for m in W if W[m]["a"] > 0]
    raw = {m: W[m]["a"] * W[m]["q"] * W[m]["r"] * W[m]["o"] * W[m]["p"] * W[m]["coh"] for m in ms}
    for i, a in enumerate(ms):
        for b in ms[i + 1:]:
            if a in mc and b in mc:
                xs = [(x, y) for x, y in zip(mc[a], mc[b]) if fin(x) and fin(y)]
                rho = pearson([p[0] for p in xs], [p[1] for p in xs]) if len(xs) > 50 else None
                if fin(rho) and rho > 0.85:
                    lo_ = a if raw[a] < raw[b] else b
                    W[lo_]["red"] = round(W[lo_]["red"] * 0.75, 3)
                    W[lo_].setdefault("rnote", []).append(f"corrélé à {MODEL_NAMES[b if lo_ == a else a]} ({rho:.2f})")
    if "mult_own" in W and "mult_peer" in W:
        W["mult_own"]["red"] *= 0.85
        W["mult_peer"]["red"] *= 0.85
    tot = 0.0
    for m in W:
        W[m]["raw"] = W[m]["a"] * W[m]["q"] * W[m]["r"] * W[m]["o"] * W[m]["p"] * W[m]["coh"] * W[m]["red"]
        tot += W[m]["raw"]
    for m in W:
        W[m]["w"] = W[m]["raw"] / tot if tot else 0.0
    return W, vshare


def synthesize(mods, W, n_draw=6000, seed=0):
    """mélange pondéré des distributions des modèles : médiane = valeur centrale, quantiles = fourchette"""
    pts = []
    for m, d in mods.items():
        w = W[m]["w"]
        s = [x for x in d["samp"] if fin(x) and x > 0]
        if w <= 0 or not s:
            continue
        pw = w / len(s)
        pts.extend((x, pw) for x in s)
    if not pts:
        return None
    q = {p: wquant(pts, p) for p in (0.05, 0.1, 0.2, 0.25, 0.5, 0.75, 0.8, 0.9, 0.95)}
    return q, pts


def confidence(S, V, H, P, F, mods, W, Q, vshare, n_models):
    parts = []

    def pen(lbl, v):
        if v > 0.5:
            parts.append([lbl, -round(v)])
    pen("exercices récents non vérifiés dans les états financiers publiés", (1 - vshare) * 15)
    pen("historique de résultats court", max(0, 8 - len(V["ser"]["ni"])) * 2)
    cen = [mods[m]["p50"] for m in mods if W[m]["w"] >= 0.08 and fin(mods[m]["p50"])]
    div = (max(cen) - min(cen)) / med(cen) if len(cen) >= 2 and med(cen) else 0.0
    pen("désaccord entre modèles", min(25, max(0, div - 0.25) * 40))
    spread = (Q[0.9] - Q[0.1]) / Q[0.5] if Q[0.5] else 9
    pen("largeur de la fourchette d'incertitude", min(50, max(0, spread - 0.5) * 40))
    pen("rupture de série comptable récente", 5 * sum(1 for b in H["breaks"] if b >= (V["fy"] or 0) - 7))
    pen("pertes récentes", min(12, 4 * H["losses5"]))
    pen("un seul modèle applicable", 10 if n_models <= 1 else 0)
    if any("minoritaires" in n for n in S["notes"]):
        pen("intérêts minoritaires non isolés dans les données", 5)
    if ARCH[S["arch"]]["win"] >= 8:
        pen("activité cyclique", 5)
    if fin(H.get("cv_ni")):
        pen("résultats très variables", min(15, max(0, H["cv_ni"] - 0.3) * 20))
    if not (F.get("ni") or {}).get("ok"):
        pen("prévisions non validées hors échantillon (historique trop court)", 5)
    price = V["price"]
    if fin(price) and price > 0 and Q[0.5] > 0:
        gap = abs(math.log(Q[0.5] / price))
        pen("écart important avec le cours : le marché intègre peut-être des perspectives absentes des comptes publiés", min(15, max(0, gap - 0.4) * 30))
    score = clamp(100 + sum(p[1] for p in parts), 5, 100)
    lbl = "élevée" if score >= 75 else "moyenne" if score >= 55 else "faible" if score >= 35 else "très faible"
    return round(score), lbl, parts, div, spread


def price_reliability(S, V, today):
    """fiabilité du dernier cours (distincte de l'incertitude sur la valeur)"""
    out = {"warn": []}
    pd_ = ymd(V["pdate"]) if V["pdate"] else None
    if not pd_:
        out.update(lvl="absent", txt="aucun cours disponible")
        return out
    sess = sum(1 for k in range((today - pd_).days) if (pd_ + dt.timedelta(days=k + 1)).weekday() < 5)
    out["sessions"] = sess
    z = (S["liq"] or {}).get("zero")
    lvl = "fiable"
    if S.get("susp"):
        lvl = "suspendu"
        out["warn"].append("cotation suspendue : le dernier cours n'est pas négociable")
    if sess > 20:
        lvl = "ancien"
        out["warn"].append(f"dernier cours du {pd_.strftime('%d/%m/%Y')}, il y a {sess} séances : il n'est pas représentatif d'une cotation actuelle")
    elif sess > 5:
        lvl = "prudence" if lvl == "fiable" else lvl
        out["warn"].append(f"dernier cours du {pd_.strftime('%d/%m/%Y')}, il y a {sess} séances")
    if fin(z) and z > 0.5:
        lvl = "prudence" if lvl == "fiable" else lvl
        out["warn"].append(f"titre peu échangé : aucune transaction lors de {z * 100:.0f} % des séances de l'année")
    out["lvl"] = lvl
    return out


# ------------------------------------------------------------------------------------------------------------- sensibilités (modèles 6 et 7)
def bisect(f, lo, hi, target, it=50):
    flo, fhi = f(lo) - target, f(hi) - target
    if not (fin(flo) and fin(fhi)) or flo * fhi > 0:
        return None
    for _ in range(it):
        mid = (lo + hi) / 2
        fm = f(mid) - target
        if not fin(fm):
            return None
        if fm * flo > 0:
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def with_shift(P, key, val):
    Q = dict(P)
    if key == "prof":
        if P["fw"] == "roe":
            Q["roe0"] = P["roe0"] * (1 + val)
            if fin(P.get("roe1")):
                Q["roe1"] = P["roe1"] * (1 + val)
        else:
            Q["m0"] = P["m0"] * (1 + val)
            Q["m_anchor"] = P["m_anchor"] * (1 + val)
            if fin(P.get("roe_cur")):
                Q["roe_cur"] = P["roe_cur"] * (1 + val)
            if "om0" in P:
                Q["om0"] = P["om0"] * (1 + val)
                Q["om_anchor"] = P["om_anchor"] * (1 + val)
    elif key == "g":
        if P["fw"] == "marge":
            Q["g_mid"] = P["g_mid"] + val
            if fin(P.get("g1")):
                Q["g1"] = P["g1"] + val
    else:
        Q[key] = P[key] + val
    return Q


def sensitivities(P, main, price):
    def v(Q, dke=0.0, glt=None):
        vals, _ = values(Q, Q["ke"], Q["glt"] if glt is None else glt, price, dke=dke)
        x = vals.get(main)
        return x[0] if x else None
    base = v(P)
    out = {"main": main, "base": base}
    # grille coût des fonds propres × croissance (ou × rentabilité pour les banques)
    kes = [-0.02, -0.01, 0.0, 0.01, 0.02]
    if P["fw"] == "marge":
        ax2, vals2, lbl2 = "g", [-0.02, -0.01, 0.0, 0.01, 0.02], "croissance du chiffre d'affaires (écart en points)"
    else:
        ax2, vals2, lbl2 = "prof", [-0.2, -0.1, 0.0, 0.1, 0.2], "rentabilité des fonds propres (écart relatif)"
    grid = [[rnd(v(with_shift(P, ax2, b), dke=a), 0) for b in vals2] for a in kes]
    out["grid"] = {"ke": kes, "x": vals2, "xlbl": lbl2, "v": grid}
    grid2 = [[rnd(v(with_shift(P, "prof", b), dke=0.0, glt=P["glt"] + a), 0) for b in [-0.2, -0.1, 0.0, 0.1, 0.2]] for a in [-0.01, -0.005, 0.0, 0.005]]
    out["grid2"] = {"glt": [-0.01, -0.005, 0.0, 0.005], "x": [-0.2, -0.1, 0.0, 0.1, 0.2], "v": grid2}
    # tornade : chaque hypothèse à son 10e et 90e centile (distributions de la simulation)
    torn = []
    for k, lbl, lo, hi in (("ke", "Coût des fonds propres", -1.28 * P["sig_ke"], 1.28 * P["sig_ke"]),
                           ("glt", "Croissance de long terme", -0.008, 0.004),
                           ("phi", "Persistance de la rentabilité", -0.12, 0.12),
                           ("pay0", "Taux de distribution", -1.28 * P["sig_pay"], 1.28 * P["sig_pay"]),
                           ("prof", "Rentabilité de départ", -1.28 * ((P.get("sig_roe") or 0.02) / (P.get("roe0") or 1) if P["fw"] == "roe" else (P.get("sig_m") or 0.01) / (P.get("m0") or 1)),
                            1.28 * ((P.get("sig_roe") or 0.02) / (P.get("roe0") or 1) if P["fw"] == "roe" else (P.get("sig_m") or 0.01) / (P.get("m0") or 1))),
                           ("g", "Croissance à moyen terme", -1.28 * (P.get("sig_g") or 0), 1.28 * (P.get("sig_g") or 0))):
        if k == "g" and P["fw"] != "marge":
            continue
        if k in ("ke",):
            a, b = v(P, dke=lo), v(P, dke=hi)
        elif k == "glt":
            a, b = v(P, glt=P["glt"] + lo), v(P, glt=P["glt"] + hi)
        elif k == "phi":
            a, b = v(with_shift(P, "phi", lo)), v(with_shift(P, "phi", hi))
        elif k == "pay0":
            Q1, Q2 = dict(P), dict(P)
            Q1["pay0"], Q2["pay0"] = clamp(P["pay0"] + lo, 0, 1.2), clamp(P["pay0"] + hi, 0, 1.2)
            a, b = v(Q1), v(Q2)
        else:
            a, b = v(with_shift(P, k, lo)), v(with_shift(P, k, hi))
        if fin(a) and fin(b) and fin(base):
            torn.append({"k": k, "n": lbl, "lo": rnd(min(a, b), 0), "hi": rnd(max(a, b), 0), "sw": rnd(abs(b - a) / base, 4)})
    out["tornado"] = sorted(torn, key=lambda r: -r["sw"])
    # seuils : valeur de chaque hypothèse pour laquelle la valeur estimée égale le cours
    thr = []
    if fin(price) and fin(base):
        x = bisect(lambda d: v(P, dke=d), -0.06, 0.15, price)
        if x is not None:
            thr.append({"k": "ke", "n": "Coût des fonds propres implicite (rendement exigé par le cours actuel)", "v": rnd(P["ke"] + x, 4)})
        if P["fw"] == "marge":
            x = bisect(lambda d: v(with_shift(P, "g", d)), -0.15, 0.25, price)
            if x is not None:
                thr.append({"k": "g", "n": "Croissance annuelle du chiffre d'affaires (années 2 à 10) implicite dans le cours", "v": rnd(P["g_mid"] + x, 4)})
        x = bisect(lambda d: v(with_shift(P, "prof", d)), -0.9, 3.0, price)
        if x is not None:
            base_p = P["roe0"] if P["fw"] == "roe" else P["m0"]
            thr.append({"k": "prof", "n": ("Rentabilité des fonds propres" if P["fw"] == "roe" else "Marge nette") + " implicite dans le cours",
                        "v": rnd(base_p * (1 + x), 4)})
    out["thr"] = thr
    return out


def global_sens(paths, main):
    """corrélation de rang entre chaque hypothèse simulée et la valeur (prend en compte les interactions entre hypothèses)"""
    vals = [p.get(main) for p in paths]
    out = []
    names = {"ke": "Coût des fonds propres", "glt": "Croissance de long terme", "phi": "Persistance de la rentabilité", "pay0": "Taux de distribution",
             "roe0": "Rentabilité des fonds propres de départ", "m0": "Marge nette de départ", "g_mid": "Croissance à moyen terme",
             "om0": "Marge opérationnelle", "roic0": "Rentabilité des capitaux investis"}
    for k in MC_KEYS:
        xs = [p.get(k) for p in paths]
        if sum(1 for x in xs if fin(x)) < 100 or len(set(round(x, 6) for x in xs if fin(x))) < 10:
            continue
        r = spearman(xs, vals)
        if fin(r):
            out.append({"k": k, "n": names[k], "rho": rnd(r, 3)})
    return sorted(out, key=lambda r: -abs(r["rho"]))


# ------------------------------------------------------------------------------------------------------------- régimes (modèle 10)
def regimes(S, P, main, price, central):
    out = []
    vals0, _ = values(P, P["ke"], P["glt"], price)
    b = vals0.get(main)
    if not b:
        return out
    for rid, nm, desc in REGIMES:
        fx = REG_FX[rid].get(S["arch"], REG_FX[rid]["*"])
        dg, dp, dke, dur = fx
        vals, _ = values(P, P["ke"], P["glt"], price, shock=(dg, dp, dur), dke=dke / 100)
        v = vals.get(main)
        if not v:
            continue
        d = v[0] / b[0] - 1
        out.append({"id": rid, "n": nm, "desc": desc, "eff": REG_TXT.get((rid, S["arch"]), ""),
                    "hyp": {"dg": dg, "dprof": dp, "dke": dke, "dur": dur}, "dv": rnd(d, 4), "v": rnd(central * (1 + d), 0) if fin(central) else None})
    return out


# ------------------------------------------------------------------------------------------------------------- scénarios
def scenarios(S, V, P, main, ops_paths, hv, Q, price, mods):
    """scénarios baissier / central / haussier à 1, 3, 5 et 10 ans.
    Hypothèses d'exploitation : central = hypothèses centrales ; baissier et haussier = médiane des hypothèses des simulations
    « exploitation seule » (rendement exigé fixé) dont la valeur se situe entre les 15e et 25e centiles, ou entre les 75e et 85e.
    Valeur aujourd'hui : valeur centrale de la synthèse × (valeur du modèle principal avec les hypothèses du scénario / avec les
    hypothèses centrales). Valeur à l'horizon : modèle principal recalculé à cette date sur la trajectoire du scénario, au même niveau.
    La fourchette du scénario central à chaque horizon vient de la simulation complète (rendement exigé compris)."""
    vals_main = [(p.get(main), i) for i, p in enumerate(ops_paths) if fin(p.get(main))]
    vals_main.sort()
    n = len(vals_main)
    if n < 100:
        return None

    def band(lo, hi):
        idx = [i for _, i in vals_main[int(lo * n):int(hi * n)]]
        Pq = dict(P)
        for k in MC_KEYS:
            if k in ("ke", "glt"):
                continue
            xs = [ops_paths[i].get(k) for i in idx if fin(ops_paths[i].get(k))]
            if xs and k in P:
                Pq[k] = med(xs)
        if "roe0" in Pq and P["fw"] == "roe" and fin(P.get("roe1")):
            Pq["roe1"] = P["roe1"] + (Pq["roe0"] - P["roe0"]) * 0.5
        if P["fw"] == "marge" and fin(P.get("roe_cur")) and P["m0"]:
            Pq["roe_cur"] = P["roe_cur"] * Pq["m0"] / P["m0"]
        return Pq
    v_c, _ = values(P, P["ke"], P["glt"], price)
    base_v = v_c.get(main, (None,))[0]
    sets = {}
    for sc, Pq in (("bear", band(0.15, 0.25)), ("base", dict(P)), ("bull", band(0.75, 0.85))):
        vq, _ = values(Pq, Pq["ke"], Pq["glt"], price)
        sets[sc] = (Pq, Q[0.5] * vq[main][0] / base_v if (vq.get(main) and base_v) else None)
    sh = V["shares"]
    out = {"conv": ("Valeurs par action en francs CFA, base du nombre d'actions actuel ; date de référence : date d'évaluation. "
                    "Dividendes : somme des dividendes ordinaires projetés sur la période, non réinvestis. "
                    "Les scénarios portent sur la valeur estimée, les résultats et les dividendes : aucune projection du cours n'est faite, "
                    "le marché pouvant rester durablement éloigné de la valeur estimée."),
           "rows": {}}
    for sc, (Pq, v0syn) in sets.items():
        ke, glt = Pq["ke"], min(Pq["glt"], Pq["ke"] - 0.03)
        vals, rows = values(Pq, ke, glt, price)
        vm = vals.get(main)
        if not vm or not fin(v0syn):
            continue
        ratio = v0syn / vm[0] if vm[0] > 0 else 1.0
        rs = []
        for h in HORIZONS:
            vh = value_at(Pq, rows, ke, glt, h, main, price) * ratio
            divs = sum(r["div"] for r in rows[:h]) * 1e6 / sh
            r_h = rows[h - 1]
            rev0 = Pq.get("rev0")
            g_rev = ((r_h["rev"] / rev0) ** (1 / h) - 1) if (fin(r_h.get("rev")) and fin(rev0) and rev0 > 0) else None
            nd = 3 if h <= 3 else 2
            row = {"h": h, "v": sig(vh, nd), "eps": sig(r_h["ni"] * 1e6 / sh, nd), "dps": sig(r_h["div"] * 1e6 / sh, nd),
                   "bvps": sig(r_h["B1"] * 1e6 / sh, nd) if fin(r_h.get("B1")) else None, "divs": sig(divs, nd), "g_rev": rnd(g_rev, 4),
                   "nm": rnd(r_h["ni"] / r_h["rev"], 4) if (fin(r_h.get("rev")) and r_h["rev"]) else None,
                   "roe": rnd(r_h["ni"] / r_h["B"], 4) if (fin(r_h.get("B")) and r_h["B"] > 0) else None,
                   "fcff": sig(r_h["fcff"] * 1e6 / sh, nd) if fin(r_h.get("fcff")) else None, "om": rnd(r_h.get("om"), 4)}
            # (aucune projection du cours : seuls les dividendes projetés sont rapportés au dernier cours)
            if fin(price) and price > 0:
                row["dy"] = rnd(divs / price / h, 4)
            # fourchette de la simulation à cet horizon (modèle principal ramené au niveau de la synthèse), qui s'élargit avec l'horizon
            hs = [x for x in hv[main][h] if fin(x)]
            if sc == "base" and len(hs) > 100:
                scale = Q[0.5] / med(mods[main]["samp"]) if med(mods[main]["samp"]) else 1.0
                row["p10"], row["p90"] = sig(quant(hs, 0.1) * scale, 2), sig(quant(hs, 0.9) * scale, 2)
            rs.append(row)
        hyp = {"ke": rnd(ke, 4), "glt": rnd(glt, 4), "pay0": rnd(Pq["pay0"], 4), "phi": rnd(Pq["phi"], 3)}
        if P["fw"] == "roe":
            hyp["roe0"] = rnd(Pq["roe0"], 4)
            rl = roe_lt(Pq, ke)
            hyp["roe_lt"] = rnd(rl, 4)
        else:
            hyp["g_mid"] = rnd(Pq["g_mid"], 4)
            hyp["m0"] = rnd(Pq["m0"], 4)
            hyp["m_lt"] = rnd(Pq["m_anchor"], 4)
            if "om0" in Pq:
                hyp["om0"] = rnd(Pq["om0"], 4)
                hyp["roic0"] = rnd(Pq["roic0"], 4)
        out["rows"][sc] = {"v0": sig(v0syn, 3), "hyp": hyp, "h": rs}
    # risques et événements susceptibles d'invalider chaque scénario
    A = ARCH[S["arch"]]
    out["risks"] = {"bear": A["risks"], "base": [], "bull": []}
    return out


# ------------------------------------------------------------------------------------------------------------- analyse complète
def dps_eval(V, best):
    """performance hors échantillon de la prévision du dividende utilisée par le DDM (taux de distribution médian × résultat prévu)
    contre la prévision naïve (dividende reconduit)"""
    ni, dv, sh = V["ser"]["ni"], V["dv"], V["shares"]
    ys_ = _run(ni)
    xs = [ni[y] for y in ys_]
    e_m, e_n = [], []
    for o in range(5, len(xs)):
        y_o, y_n = ys_[o - 1], ys_[o]
        if y_n not in dv or y_o not in dv or not sh:
            continue
        pays = [dv[y] * sh / (ni[y] * 1e6) for y in ys_[max(0, o - 5):o] if y in dv and ni.get(y, 0) > 0]
        if len(pays) < 3:
            continue
        f_ = _fc_one(best, xs[:o], ys_[:o], V["ser"]["eq"])
        if not fin(f_):
            continue
        e_m.append(abs(dv[y_n] - max(0.0, med(pays) * f_ * 1e6 / sh)))
        e_n.append(abs(dv[y_n] - dv[y_o]))
    if len(e_m) >= 4 and mean(e_n):
        return mean(e_m) / mean(e_n), len(e_m)
    return None, len(e_m)


DIV_WHY = {
    "ddm": "le DDM ne valorise que les dividendes projetés (taux de distribution de départ {pay:.0%}) : il pèse moins quand la société retient une grande partie de ses bénéfices",
    "ri": "le RI part des fonds propres publiés ({bv:,.0f} FCFA par action) et d'une rentabilité de {roe:.1%} contre un coût des fonds propres de {ke:.1%}",
    "dcf": "le DCF dépend de la marge d'exploitation ({om:.1%}), de la rentabilité des nouveaux investissements ({roic:.1%}) et de la dette nette",
    "mult_own": "les multiples historiques reflètent les prix que le marché a payés pour ce titre ces cinq dernières années",
    "mult_peer": "les multiples des comparables reflètent les prix payés pour d'autres sociétés, dont la rentabilité, la croissance et la liquidité diffèrent",
}


def _txt(fmt, **kw):
    try:
        return fmt.format(**kw)
    except (KeyError, ValueError, TypeError):
        return fmt.split(" (")[0]


def analyze(t, I, M, peers_tbl, date=None, mc=True, light=False, fix=None, seed_date=None):
    """analyse complète d'une société à une date (par défaut aujourd'hui).
    fix : paramètres de marché figés (bêta, prime de risque, taux sans risque, croissance de long terme, cours de pondération) pour
    mesurer l'effet des seules informations nouvelles ; seed_date : date servant de graine à la simulation (mêmes tirages)."""
    if fix:
        M = dict(M, fix=fix)
    S = I["S"][t]
    today = I["today_i"]
    date = date or today
    V = asof_view(S, date, today)
    out = {"t": t, "name": S["name"], "date": date, "ok": False}
    if V["fy"] is None:
        out["why"] = "aucun exercice publié à cette date"
        return out
    if not V["shares"]:
        out["why"] = "nombre d'actions inconnu : aucune valeur par action ne peut être calculée"
        return out
    price = V["price"]
    td = I["today"] if date >= today else ymd(date)
    exp_fy = td.year - 1 if td.month >= 7 else td.year - 2
    if V["fy"] < exp_fy - 1:
        out["why"] = f"derniers comptes annuels publiés trop anciens (exercice {V['fy']}, alors que l'exercice {exp_fy} devrait être disponible)"
        return out
    H = history(S, V)
    sc_ = M.get("fc_scale") or 1.0
    F = {"ni": forecast(V["ser"]["ni"], eq=V["ser"]["eq"], scale=sc_), "rev": forecast(H["rev_pb"], scale=sc_) if len(H["rev_pb"]) >= 3 else None}
    rr = next((m for m in F["ni"]["models"] if m["id"] == "roe"), None)
    F["ri_ratio"] = rr["ratio"] if (rr and rr["k"] >= 4) else None
    F["dps_ratio"], F["dps_n"] = dps_eval(V, F["ni"]["best"])
    P, hyp = build_params(S, V, H, M, F)
    arch = S["arch"]
    ap = APPLIC[arch]
    vals0, rows0 = values(P, P["ke"], P["glt"], price) if P["fw"] else ({}, [])
    mods, notapp = {}, []
    mcv, paths, hv = ({}, [], {})
    if mc and P["fw"]:
        seed = int(hashlib.sha256(f"{t}{seed_date or date}".encode()).hexdigest()[:8], 16)
        mcv, paths, hv = monte_carlo(P, price, seed, keep_paths=not light)
    for m in ("ri", "ddm", "dcf"):
        why_app = APPLIC_WHY[m].get("fin" if (S["fin"] and "fin" in APPLIC_WHY[m]) else arch, APPLIC_WHY[m]["*"])
        if ap.get(m, 0) <= 0:
            notapp.append({"id": m, "why": why_app})
            continue
        if m not in vals0:
            why = {"ri": "fonds propres du dernier exercice non publiés ou historique de rentabilité trop court",
                   "ddm": "pas de dividende ordinaire régulier : le DDM supposerait des dividendes que la société ne verse pas",
                   "dcf": "données insuffisantes : il faut au moins 5 exercices de résultat d'exploitation, la rentabilité des capitaux investis et la dette nette publiée"}[m]
            if not P["fw"]:
                why = "historique insuffisant pour projeter les résultats"
            notapp.append({"id": m, "why": why})
            continue
        v, tv = vals0[m]
        samp = [x for x in (mcv.get(m) or []) if fin(x)] or [v]
        if not fin(v) or v <= 0 or med(samp) <= 0:
            notapp.append({"id": m, "why": "valeur négative ou nulle avec les hypothèses centrales : modèle écarté"})
            continue
        mods[m] = {"v": v, "tv": tv, "samp": samp, "why": why_app}
    peers, peer_src = peers_for(arch, peers_tbl)
    mu = multiples(S, V, H, P, F, peers)
    for m in ("mult_own", "mult_peer"):
        if m in mu and fin(mu[m]["v"]) and mu[m]["v"] > 0:
            mods[m] = {"v": mu[m]["v"], "tv": None, "samp": [x for x in mu[m]["samp"] if fin(x)] or [mu[m]["v"]], "why": APPLIC_WHY[m]["*"],
                       "txt": mu[m].get("txt"), "extra": {k: mu[m].get(k) for k in ("n_peers", "mult", "key", "peers", "n_obs")}}
        else:
            notapp.append({"id": m, "why": "historique de multiples trop court" if m == "mult_own" else "moins de trois sociétés comparables avec un multiple significatif"})
    for m, d in mods.items():
        d["p10"], d["p50"], d["p90"] = quant(d["samp"], 0.1), quant(d["samp"], 0.5), quant(d["samp"], 0.9)
    if not mods:
        out["why"] = "aucun modèle applicable avec les données disponibles"
        out["notapp"] = notapp
        return out
    W, vshare = synth_weights(S, V, H, P, F, mods, {m: mcv[m] for m in mcv}, perf=M.get("perf"))
    if not mc:
        # backtest : synthèse sur les valeurs centrales (médiane pondérée), sans simulation
        pts = [(mods[m]["v"], W[m]["w"]) for m in mods]
        central = wquant(pts, 0.5)
        out.update(ok=True, fy=V["fy"], price=price, pdate=V["pdate"], shares=V["shares"], split_f=V["split_f"], ke=P["ke"], central=central,
                   mods={m: {"v": mods[m]["v"], "w": W[m]["w"]} for m in mods}, f_ni=F["ni"].get("f"), f_lo=F["ni"].get("lo"), f_hi=F["ni"].get("hi"),
                   f_best=F["ni"]["best"], f_models=F["ni"]["models"], ni0=V["ser"]["ni"].get(V["fy"]))
        return out
    syn = synthesize(mods, W)
    if not syn:
        out["why"] = "synthèse impossible"
        return out
    Q, pool = syn
    n_models = sum(1 for m in W if W[m]["w"] >= 0.05)
    score, lbl, parts, div, spread = confidence(S, V, H, P, F, mods, W, Q, vshare, n_models)
    intr = [m for m in ("ri", "ddm", "dcf") if m in mods and len(mods[m]["samp"]) > 100]
    main = max(intr, key=lambda m: W[m]["w"]) if intr else None
    # explication des écarts entre modèles
    div_txt = []
    for m in mods:
        if W[m]["w"] <= 0 or not fin(mods[m]["p50"]):
            continue
        e = mods[m]["p50"] / Q[0.5] - 1
        if abs(e) >= 0.25:
            bv = (V["ser"]["eq"].get(V["fy"]) or 0) * 1e6 / V["shares"]
            div_txt.append(f"{MODEL_NAMES[m]} {'au-dessus' if e > 0 else 'en dessous'} de la synthèse ({e:+.0%}) : "
                           + _txt(DIV_WHY[m], pay=P["pay0"], bv=bv, roe=P.get("roe0") or P.get("roe_cur") or 0, ke=P["ke"], om=P.get("om0") or 0,
                                  roic=P.get("roic0") or 0))
    # DCF inversé et sensibilités
    sens = sensitivities(P, main, price) if main else None
    if sens and fin(sens.get("base")) and sens["base"] > 0:
        # valeurs ramenées au niveau de la synthèse (rapport synthèse / modèle principal), pour être comparables à la valeur affichée
        r_ = Q[0.5] / sens["base"]
        for g_ in ("grid", "grid2"):
            sens[g_]["v"] = [[sig(x * r_, 3) if fin(x) else None for x in row] for row in sens[g_]["v"]]
        for t_ in sens["tornado"]:
            t_["lo"], t_["hi"] = sig(t_["lo"] * r_, 3), sig(t_["hi"] * r_, 3)
    glob = global_sens(paths, main) if (main and paths) else []
    reg = regimes(S, P, main, price, Q[0.5]) if main else []
    sc = None
    if main:
        _, ops_paths, _ = monte_carlo(P, price, seed + 1, n=800, keep_paths=True, ops_only=True) if mc else (None, [], None)
        sc = scenarios(S, V, P, main, ops_paths, hv, Q, price, mods)
    rev_txt = []
    if sens:
        for th in sens["thr"]:
            if th["k"] == "ke":
                rev_txt.append(f"Le cours actuel correspond à un rendement annuel exigé de {th['v']:.1%}, contre un coût des fonds propres estimé à {P['ke']:.1%}.")
            elif th["k"] == "g":
                gh = next((h["v"] for h in hyp if h["k"] == "g_hist"), None)
                rev_txt.append(f"Avec les autres hypothèses inchangées, le cours suppose une croissance annuelle du chiffre d'affaires de {th['v']:.1%} sur 10 ans"
                               + (f" (historique : {gh:.1%})." if fin(gh) else "."))
            elif th["k"] == "prof":
                cur = P.get("roe0") if P["fw"] == "roe" else P.get("m0")
                rev_txt.append(f"Ou bien une {'rentabilité des fonds propres' if P['fw'] == 'roe' else 'marge nette'} de départ de {th['v']:.1%} (retenue : {cur:.1%}).")
    # liquidité : distincte de l'incertitude fondamentale
    lq = S["liq"] or {}
    z, am = lq.get("zero"), lq.get("amihud")
    lp = clamp(0.025 * (z or 0) + 0.01 * min(am, 1.0) if fin(am) else 0.025 * (z or 0), 0.0, 0.02)
    liq = {"zero": z, "adv1y": lq.get("adv1y"), "med": lq.get("med"), "amihud": am, "turn": lq.get("turn"), "lp": rnd(lp, 4),
           "d": {k: lq.get(k) for k in ("d10", "d50", "d100", "d500")}}
    if main and lp > 0.0005:
        vl, _ = values(P, P["ke"], P["glt"], price, dke=lp)
        if vl.get(main) and vals0.get(main):
            liq["v_adj"] = sig(Q[0.5] * vl[main][0] / vals0[main][0], 3)
    pr = price_reliability(S, V, I["today"])
    # lecture alternative : valeur au rendement exigé implicite actuel du marché (hors synthèse)
    alt = None
    if main and fin(M.get("ke_mkt")) and fin(M.get("rf_ci")) and not M.get("fix"):
        erp_now = max(M["ke_mkt"] - M["rf_ci"], 0.005)
        dke = P["beta"] * (erp_now - M["erp"])
        va, _ = values(P, P["ke"], P["glt"], price, dke=dke)
        if va.get(main) and vals0.get(main) and vals0[main][0] > 0:
            alt = {"ke": rnd(P["ke"] + dke, 4), "v": sig(Q[0.5] * va[main][0] / vals0[main][0], 3), "ke_mkt": rnd(M["ke_mkt"], 4)}
    # qualité des données
    fy = V["fy"]
    yrs = sorted(set(V["ser"]["ni"]) | set(V["ser"]["rev"]) | set(V["ser"]["eq"]))
    dq = {"fy": fy, "years": len(V["ser"]["ni"]), "vshare": rnd(vshare, 3), "verified": sorted(y for y in yrs if y in S["verified"]),
          "missing": [], "warn": [], "breaks": H["breaks"]}
    for k, lbl_ in (("eq", "fonds propres"), ("ocf", "flux de trésorerie d'exploitation"), ("capex", "investissements"), ("nd", "dette nette"),
                    ("ebit", "résultat d'exploitation")):
        if fy not in V["ser"][k] and not (S["fin"] and k in ("ocf", "capex", "nd", "ebit")):
            dq["missing"].append(f"{lbl_} {fy}")
    if fy < I["today"].year - 1 or (fy == I["today"].year - 2 + 0 and I["today"].month >= 7):
        dq["warn"].append(f"derniers comptes annuels disponibles : exercice {fy}")
    if H["breaks"]:
        dq["warn"].append("rupture de série du chiffre d'affaires en " + ", ".join(str(b) for b in H["breaks"]) + " (changement de périmètre ou de présentation) : croissance mesurée après la rupture")
    # historique affiché
    hist = {"y": yrs}
    for k in ("rev", "ni", "eq", "ebit", "ebitda", "ocf", "capex", "nd", "deposits", "loans", "cor"):
        hist[k] = [V["ser"][k].get(y) for y in yrs]
    hist["roe"] = [rnd(H["roe"].get(y), 4) for y in yrs]
    hist["nm"] = [rnd(H["nm"].get(y), 4) for y in yrs]
    hist["om"] = [rnd(H["om"].get(y), 4) for y in yrs]
    hist["dps"] = [rnd(V["dv"].get(y), 2) for y in yrs]
    hist["pay"] = [rnd(H["payout"].get(y), 4) for y in yrs]
    hist["ver"] = [1 if y in S["verified"] else 0 for y in yrs]
    sh = V["shares"]
    ni0 = V["ser"]["ni"].get(fy)
    eq0 = V["ser"]["eq"].get(fy)
    ratios = {"pe": rnd(price * sh / (ni0 * 1e6), 2) if (fin(price) and fin(ni0) and ni0 > 0) else None,
              "pb": rnd(price * sh / (eq0 * 1e6), 3) if (fin(price) and fin(eq0) and eq0 > 0) else None,
              "dy": rnd(V["dv"][max(V["dv"])] / price, 4) if (V["dv"] and fin(price) and price > 0) else None,
              "roe3": rnd(med([H["roe"][y] for y in sorted(H["roe"])[-3:]]), 4), "nm3": rnd(med([H["nm"][y] for y in sorted(H["nm"])[-3:]]), 4),
              "cagr_rev5": rnd(H.get("cagr_rev_5"), 4), "cagr_ni5": rnd(H.get("cagr_ni_5"), 4), "cagr_rev10": rnd(H.get("cagr_rev_10"), 4),
              "vol3": rnd(H.get("vol3"), 4), "mdd5": rnd(H.get("mdd5"), 4), "cv_ni": rnd(H.get("cv_ni"), 3),
              "conv": rnd(med([H["conv"][y] for y in sorted(H["conv"])[-5:]]), 3), "pay5": rnd(med([H["payout"][y] for y in sorted(H["payout"])[-5:]]), 4),
              "div10": H["div_years10"], "cuts": H["div_cuts"], "eps0": rnd(ni0 * 1e6 / sh, 1) if fin(ni0) else None,
              "bvps0": rnd(eq0 * 1e6 / sh, 1) if fin(eq0) else None}
    # multiples : prime ou décote expliquée
    mexp = []
    if "mult_peer" in mods:
        ex = mods["mult_peer"]["extra"]
        own = ratios["pb"] if ex["key"] == "pb" else ratios["pe"]
        pr_ = [p for p in peers if p["t"] != t]
        roe_p = med([p.get("roe") for p in pr_])
        if fin(own) and fin(ex["mult"]):
            d_ = own / ex["mult"] - 1
            mexp.append(f"{'Cours / fonds propres' if ex['key'] == 'pb' else 'PER'} actuel {own:.2f} contre {ex['mult']:.2f} pour la médiane des comparables "
                        f"({peer_src}, {ex['n_peers']} sociétés) : {'prime' if d_ > 0 else 'décote'} de {abs(d_):.0%}.")
        if fin(roe_p) and fin(ratios["roe3"]):
            mexp.append(f"Rentabilité des fonds propres {ratios['roe3']:.1%} contre {roe_p:.1%} pour les comparables : "
                        + ("une rentabilité supérieure justifie un multiple plus élevé." if ratios["roe3"] > roe_p else "une rentabilité inférieure justifie un multiple plus faible."))
        if fin(z):
            mexp.append(f"Liquidité : aucune transaction lors de {z:.0%} des séances de l'année ; une faible liquidité justifie en général une décote.")
    mlist = []
    for m in ("dcf", "ddm", "ri", "mult_own", "mult_peer"):
        if m in mods:
            d = mods[m]
            w = W[m]
            mlist.append({"id": m, "n": MODEL_NAMES[m], "fam": MODEL_FAM[m], "ok": True, "why": d["why"], "v": sig(d["v"], 3), "p10": sig(d["p10"], 3),
                          "p50": sig(d["p50"], 3), "p90": sig(d["p90"], 3), "tv": rnd(d.get("tv"), 3), "w": rnd(w["w"], 4),
                          "wd": {k: w.get(k) for k in ("a", "q", "r", "o", "p", "coh", "red")}, "notes": [x for x in ([w.get("cnote")] + (w.get("rnote") or [])) if x],
                          "txt": d.get("txt"), "extra": d.get("extra")})
        else:
            na = next((x for x in notapp if x["id"] == m), None)
            mlist.append({"id": m, "n": MODEL_NAMES[m], "fam": MODEL_FAM[m], "ok": False, "why": na["why"] if na else "non applicable"})
    # Monte-Carlo : présentation
    mcd = None
    if main:
        s_ = [x for x in mods[main]["samp"] if fin(x)]
        lo_, hi_ = quant(s_, 0.01), quant(s_, 0.99)
        bins = []
        if lo_ is not None and hi_ is not None and hi_ > lo_:
            nb = 30
            step = (hi_ - lo_) / nb
            cnt = [0] * nb
            for x in s_:
                if lo_ <= x <= hi_:
                    cnt[min(nb - 1, int((x - lo_) / step))] += 1
            bins = {"lo": rnd(lo_, 1), "step": rnd(step, 2), "c": cnt}
        pv = [(x, w_) for x, w_ in pool]
        share_above = (sum(w_ for x, w_ in pv if fin(price) and x > price) / sum(w_ for _, w_ in pv)) if (pv and fin(price)) else None
        prm = [{"k": "ke", "n": "Coût des fonds propres", "dist": f"normale, écart type {P['sig_ke']:.2%}",
                "why": "erreur type du bêta mesuré et dispersion historique du coût des fonds propres implicite du marché"},
               {"k": "glt", "n": "Croissance de long terme", "dist": "uniforme de −1 point à +0,5 point", "why": "incertitude asymétrique : prudence à la hausse"},
               {"k": "phi", "n": "Persistance de la rentabilité", "dist": "uniforme ±0,15", "why": "hypothèse d'archétype, incertaine"},
               {"k": "pay0", "n": "Taux de distribution", "dist": f"normale, écart type {P['sig_pay']:.1%}", "why": "dispersion des 5 derniers taux publiés"}]
        if P["fw"] == "roe":
            prm.append({"k": "roe0", "n": "Rentabilité des fonds propres de départ", "dist": f"normale, écart type {P['sig_roe']:.1%}",
                        "why": "70 % de la dispersion des rentabilités publiées sur 8 ans au plus"})
        else:
            prm.append({"k": "m0", "n": "Marge nette de départ", "dist": f"normale, écart type {P['sig_m']:.2%}", "why": "70 % de la dispersion des marges publiées sur 8 ans au plus"})
            prm.append({"k": "g_mid", "n": "Croissance à moyen terme", "dist": f"normale, écart type {P['sig_g']:.2%}",
                        "why": "volatilité de la croissance annuelle publiée divisée par √5, plus 1 point d'incertitude de modèle"})
            if "om0" in P:
                prm.append({"k": "om0", "n": "Marge d'exploitation", "dist": "liée à la marge nette (même tirage)", "why": "les deux marges évoluent ensemble"})
                prm.append({"k": "roic0", "n": "Rentabilité des capitaux investis", "dist": f"normale, écart type {P['sig_roic']:.1%}", "why": "dispersion des rentabilités publiées"})
        mcd = {"n": len(s_), "main": main, "bins": bins, "share_above": rnd(share_above, 3), "params": prm,
               "corr": ({"rho": rnd(P.get("rho_gm"), 3), "n": P.get("rho_n"),
                         "why": "corrélation empirique entre croissance du chiffre d'affaires et variation de la marge nette, divisée par deux (prudence)"}
                        if P["fw"] == "marge" and P.get("rho_n", 0) >= 8 else
                        {"rho": 0, "n": P.get("rho_n", 0), "why": "moins de 8 observations : variables tirées indépendamment"}),
               "p": {str(k): sig(v, 3) for k, v in Q.items()}}
    raw_f = factor_raw(S, V, H)
    out.update(ok=True, fy=fy, price=price, pdate=V["pdate"], shares=sh, split_f=V["split_f"],
               mp={"rf": rnd(P["rf"], 5), "beta": rnd(P["beta"], 4), "se_beta": rnd(P["se_beta"], 4), "erp": rnd(M.get("fix", {}).get("erp") or M["erp"], 5),
                   "glt": rnd(P["glt"], 5), "sig_ke": rnd(P["sig_ke"], 5), "price": price, "ke": rnd(P["ke"], 5)},
               profile={"arch": arch, "arch_n": ARCH[arch]["n"], "act": S["act"], "notes": S["notes"], "drivers": ARCH[arch]["drivers"],
                        "risks": ARCH[arch]["risks"], "fw": P["fw"], "cty": S["cty"],
                        "fw_txt": {"roe": "projection par la rentabilité des fonds propres (adaptée aux banques et aux sociétés sans chiffre d'affaires exploitable)",
                                   "marge": "projection par le chiffre d'affaires et la marge nette"}.get(P["fw"], "projection impossible")},
               hist=hist, ratios=ratios, hyp=hyp, models=mlist, main=main,
               syn={"v": sig(Q[0.5], 3), "p10": sig(Q[0.1], 3), "p25": sig(Q[0.25], 3), "p75": sig(Q[0.75], 3), "p90": sig(Q[0.9], 3),
                    "p20": sig(Q[0.2], 3), "p80": sig(Q[0.8], 3), "conf": score, "conf_lbl": lbl, "conf_parts": parts, "div": rnd(div, 3),
                    "spread": rnd(spread, 3), "div_txt": div_txt, "up": rnd(Q[0.5] / price - 1, 4) if (fin(price) and price > 0) else None},
               mc=mcd, rev={"txt": rev_txt, "thr": sens["thr"] if sens else []},
               sens={k: sens[k] for k in ("grid", "grid2", "tornado")} if sens else None, glob=glob, reg=reg, scen=sc,
               fc={"ni": {k: F["ni"].get(k) for k in ("models", "best", "why", "f", "lo", "hi", "cover", "n_hist", "ok")},
                   "rev": {k: F["rev"].get(k) for k in ("models", "best", "why", "f", "lo", "hi", "cover", "n_hist", "ok")} if F["rev"] else None,
                   "dps_ratio": rnd(F["dps_ratio"], 3), "dps_n": F["dps_n"]},
               fac_raw=raw_f, liq=liq, pr=pr, dq=dq, mexp=mexp, alt=alt,
               divs={"hist": {str(y): rnd(v, 2) for y, v in V["dv"].items()}, "exc": {str(y): rnd(v * V["split_f"], 2) for y, v in S["dexc"].items()}})
    return frall(out)
