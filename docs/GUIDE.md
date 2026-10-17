# FQT — terminal de marché (BRVM, US, macro)

> Documentation complète du projet. Elle était dans README.md ; elle est ici pour que la page d'accueil du dépôt reste neutre.
> Règle : ne jamais remettre de description du projet, de nom de site, d'adresse ni de marque dans README.md, LICENSE
> ou la description du dépôt.

Terminal façon Bloomberg : ligne de commande, touches de fonction, tableaux denses, graphiques interactifs. Projet autonome (séparé du screener FOFCO BRVM).

Tapez un ticker ou une fonction puis Entrée : `SNTS GP`, `SNTS QLAB`, `QQQ BTST`, `MACRO`, `EVTS`. Cliquer sur n'importe quel titre ouvre ses écrans. La fonction **HELP** liste toutes les fonctions, leurs onglets et les raccourcis.

## Fonctions (65)

### Fonctions de marché

| Code | Contenu |
|---|---|
| BRIEF | Synthèse du jour — BRVM, portefeuille, alertes, marchés mondiaux, changes, matières, taux, agenda du jour et actualités sur une page |
| BRVM | BRVM — 48 actions, indices, largeur du marché, secteurs ; en option : flottant officiel, valorisation du marché (PER) |
| MOST | Plus actives — Plus fortes hausses et baisses, valeurs les plus échangées sur la séance du jour, largeur du marché |
| LIQ | Liquidité BRVM — Montants échangés, jours cotés, Amihud, délai pour constituer une position |
| DIVC | Calendrier dividendes — BRVM : prochains détachements, classement par rendement, historique |
| EVTS | Événements des sociétés — Avis officiels depuis 2000 : AG, dividendes, états financiers ; en option : suivi des sociétés BRVM, agenda des sociétés (BRVM et résultats US) |
| NOT | Notations financières — Notes de crédit (Bloomfield, WARA, GCR) : sociétés cotées, emprunts obligataires et fonds de titrisation, historique |
| MOTS CLES | Recherche par mots clés — Tous les documents de la BRVM depuis 1998 (états financiers, rapports, avis de la BRVM et du DC/BR, bulletins de la cote, dividendes, notations), obligations, titres, fonctions et actualités |
| SGI | Intervenants du marché — SGI, sociétés de gestion d’OPCVM et de patrimoine, conservateurs, agences de notation, garants : adresses et contacts |
| UEMOA BONDS | Obligations UEMOA — Obligations cotées à la BRVM : coupon, échéance, cours, rendement, duration, sensibilité |
| GC | Courbes souveraines — Courbes des taux zéro-coupon des 8 États de l’UEMOA, écarts, coupons à l’émission |
| UEMOA/DATA | Macro UEMOA — Taux directeurs, inflation, croissance, dette, crédit, titres publics des 8 États ; en option : statistiques économiques mondiales |
| PORTF | Portefeuille — Vos positions BRVM et US : valeur, plus-values, risque (volatilité, VaR, bêta, contributions), performance, dividendes à venir |
| SCREENER | Screener — Filtrer US et BRVM par ratios : FCF, croissance, qualité, valorisation, score |
| ALRT | Alertes — Marges, FCF, dette, révisions, seuils de valorisation, résultats à venir |
| MAP | Carte de chaleur — BRVM, États-Unis, Europe, Royaume-Uni, Asie, Afrique : surface = capitalisation, couleur = variation ; en option : marché US (Nasdaq-100, ETF, facteurs, crypto) |
| INDX | Indices mondiaux — Indices boursiers des Amériques, d’Europe, d’Afrique et d’Asie : niveau, variation, fourchette 52 semaines ; en option : contrats à terme sur indices (indication d’ouverture) |
| FG | Fear & Greed — Indice peur/avidité : États-Unis (CNN, toutes les 15 minutes) et BRVM (calculé par FQT) |
| NEWS ECO | Calendrier éco — Calendrier économique mondial : publications, prévision du consensus, réel, précédent, importance |
| ECWB | Macro US — Courbe des taux, crédit, liquidité, emploi, inflation, récession |
| RATES | Taux : Trésor, monétaire, Fed — Taux directeurs (Fed, BCE, BCEAO), SOFR, bons et emprunts du Trésor, contrats à terme, pentes, inflation anticipée ; en option : anticipations de la Fed (Fed funds), BONDS (taux souverains mondiaux : courbe US, 10 ans, UEMOA) |
| FX | Changes — Franc CFA : USD/XOF, effet de change, simulateur ; en option : changes croisés (G10, Afrique, Asie, Amériques), classement mondial des devises |
| COMMO | Matières premières — Énergie, métaux, agriculture (cacao, café, coton) : contrats à terme du jour |
| BMAP | Carte du pétrole — Flux pétroliers mondiaux, détroits stratégiques, Brent et WTI, stocks US |
| MACRO | Macro & Or — Or depuis 1833, krachs, CAPE, inflation, pétrole, VIX |
| CORR | Corrélations — Matrice BRVM × monde, paire au choix, ACP |
| RRG | Rotation (RRG) — Graphe de rotation relative : secteurs, facteurs, pays, BRVM |
| CORP RESULT | Résultats des sociétés — Calendrier des résultats US (date, consensus, dernière surprise), résultats publiés (surprise, réaction du cours) ; en option : objectifs de cours des analystes |
| HELP | Aide — Toutes les fonctions, leurs onglets et les raccourcis |

### Fonctions par titre (ticker puis code, ex. SNTS DES)

**Description**

| Code | Contenu |
|---|---|
| DES | Description — Profil, émission, ratios, chiffre d’affaires et BPA, secteur : la fiche d’identité du titre |
| CN | Actualités de la société — Articles qui citent la société, publications officielles, historique des événements |
| HDS | Actionnariat — Principaux actionnaires, répartition du capital et flottant |
| STOCK BONDS | Titres liés — Obligations de l’émetteur cotées à la BRVM, indices, sociétés du même secteur |
| CACS | Opérations sur titres — Dividendes, assemblées, opérations sur le capital, à venir et passées |

**Graphiques et cours**

| Code | Contenu |
|---|---|
| GP | Graphique — Ligne style Bloomberg, bougies, moyennes mobiles, volume, RSI, MACD, comparaison |
| HP | Historique des cours — Cours quotidiens, hebdomadaires, mensuels avec variations et volumes |
| TECH | Analyse technique — Moyennes mobiles, RSI, MACD, stochastique, Bollinger, ATR, pivots, synthèse des signaux |
| TRA | Rendement total — Dividendes réinvestis contre cours seul, par période et par année |
| COMP | Rendements comparés — Performance contre d’autres titres et un indice, dividendes réinvestis |
| HS | Écart historique — Rapport ou écart entre deux titres : moyenne, bandes ±1 et ±2 écarts-types, score z, centile, demi-vie |
| SEAS | Saisonnalité — Rendements années × mois, jour de la semaine, « Sell in May » |
| HVT | Volatilité historique — Volatilité sur 10 à 260 séances, Parkinson, centiles, volatilité glissante |
| VAP | Volume par prix — Échanges par niveau de cours, prix le plus échangé, zone de valeur, VWAP |

**Fondamentaux**

| Code | Contenu |
|---|---|
| FA | Analyse financière — Chiffres clés, compte de résultat, bilan, flux et ratios ; BRVM : états financiers publiés poste par poste et une centaine de ratios sur tout l’historique |
| GF | Graphique des fondamentaux — Chiffre d’affaires, résultat, BPA, FCF, dette par exercice, PER historique |
| RV | Valorisation relative — Multiples contre pairs du secteur et contre son propre historique, juste valeur |
| WACC | Coût du capital — WACC, ROIC et création de valeur (ROIC − WACC) |
| DVD | Dividendes — Historique, rendement, croissance, taux de distribution, couverture par le FCF |
| DDM | Modèle de dividendes — Gordon-Shapiro, croissance implicite, sensibilité |
| MODL | Scénarios bull/base/bear — Simulateur de valorisation : hypothèses modifiables, séparées des données publiées |

**Analystes**

| Code | Contenu |
|---|---|
| ANR | Recommandations — Achat / conserver / vente, objectifs de cours, potentiel, BPA attendu |
| EE | Estimations — Consensus du BPA, révisions, croissance attendue |
| SURP | Surprises de résultats — BPA publié contre consensus, réaction du cours |

**Composition de l’indice**

| Code | Contenu |
|---|---|
| MEMB | Composition de l’indice — Valeurs de l’indice, poids, concentration |
| MOV | Contributions à l’indice — Valeurs qui font monter ou baisser l’indice aujourd’hui, en points |

**Quant**

| Code | Contenu |
|---|---|
| SCOR | Score multifactoriel — Note /100 : value, qualité, croissance, momentum, rendement, faible volatilité |
| LQA | Liquidité et coûts — Échanges 20/60 séances, séances sans échange, coût d’aller-retour, délai de sortie, taille de position |
| ANOM | Anomalies — Alertes statistiques : cours, volume, tendance, résultats, dividendes, données suspectes |
| PEER | Comparateur de sociétés — 2 à 10 sociétés côte à côte, nuage de points sur deux critères |

**Risque**

| Code | Contenu |
|---|---|
| BETA | Bêta historique — Bêta sur plusieurs fenêtres, volatilité, corrélation, drawdown, pairs |
| QLAB | Laboratoire quant — Statistiques du cours (distribution, VaR, Hurst, momentum, analogues, probabilité bayésienne) ; valorisation des actions BRVM par sept modèles, risques et alertes, qualité et facteurs |
| BTST | Backtest — 8 stratégies, levier, Monte Carlo, durée des drawdowns |

**Autres**

| Code | Contenu |
|---|---|
| MONITOR | Moniteur de marchés — Tous les titres suivis, signal SMA 200 de QQQ, séance BRVM, carte des capitalisations |
| NEWS | Actualités — Fil d’actualités relié aux titres : BRVM, UEMOA, marchés mondiaux, banques centrales |
| MENU | Menu du titre — Toutes les fonctions disponibles pour ce titre, classées par thème |

## QLAB (laboratoire quant)

| Onglet | Contenu | État |
|---|---|---|
| Statistiques | distribution des rendements, VaR/CVaR, cône de volatilité, autocorrélation, exposant de Hurst, momentum, analogues k-NN + DTW, probabilité bayésienne | en ligne |
| Valorisation (actions BRVM) | **Valorisation** : valeur et fourchette de chacun des sept modèles (DCF probabiliste, simulation Monte-Carlo, actualisation des dividendes, multiples historiques, multiples des comparables, résultat résiduel, DCF inversé), sans synthèse ; **Risques et alertes** : alarmes, sensibilités, régimes économiques, liquidité, révisions et événements ; **Qualité et facteurs** : facteurs de qualité et de risque, qualité des données, comptes et ratios utilisés. Aucune projection du cours. | en ligne (moteur QLAB-V, recalcul chaque soir) |
| Prévisions (actions BRVM) | prévision des résultats annuels (exercice en cours et quatre suivants) et des cumuls intermédiaires (1er trimestre, 1er semestre, 9 mois) : chiffre d'affaires ou PNB, résultat d'exploitation, résultat net, BPA, marges ; méthodes choisies par validation point-in-time, fourchettes mesurées sur les erreurs passées ; révisions à chaque publication, mise à jour trimestrielle, révisions exceptionnelles déclenchées par les documents publiés (seuil de 5 % du résultat net) ; historique des versions et écarts mesurés. Aucune prévision du cours. | en ligne (moteur QLAB-P, recalcul chaque soir) ; fonctions restant à développer listées dans [docs/QLAB3_PREVISIONS.md](QLAB3_PREVISIONS.md) |

Méthode de la valorisation : [docs/QLAB2_VALORISATION.md](QLAB2_VALORISATION.md).

## Données et automatisations

Tout est automatique (GitHub Actions) ; aucune intervention manuelle n'est nécessaire.

| Tâche | Rythme | Rôle | Écrit |
|---|---|---|---|
| Terminal (`terminal.yml`) | toutes les 15 min, jour et nuit ; base complète chaque soir de semaine (22:35 UTC) | cours BRVM, US, crypto, actualités, avis, obligations ; le soir : toute la base, comptes, valorisation QLAB | branches `data`, `raw`, `site` ; archive de la séance sur `main` |
| Métronome (`metronome.yml`) | en continu, relancé chaque heure | déclenche le relevé pile à :00, :15, :30, :45 (la programmation de GitHub est parfois retardée) | — |
| Bulletins officiels (`boc.yml`) | toutes les 2 h | lecture des bulletins officiels de la cote (cours, dividendes, opérations sur le capital) | `boc` |
| Comptes des sociétés cotées (`comptes.yml`) | chaque jour, puis passages enchaînés tant qu'il reste des documents | lecture de tous les documents déposés par les sociétés (états financiers, rapports, communiqués), contrôle des identités comptables | `comptes` |
| Dividendes BRVM (`dividendes.yml`) | chaque jour, passages enchaînés si besoin | avis et calendriers de paiement des dividendes | `dividendes` |
| Base historique (`histo.yml`) | chaque soir | archive cumulative contrôlée (cours, indices, dividendes, événements, états financiers) | `histo` |
| Export complet (`export.yml`) | chaque nuit | copie autonome du site et de ses données, ouvrable sans connexion | `export` |
| Copie de secours (`copie.yml`) | chaque nuit (03:38 UTC) | copie complète de toutes les branches (code et données) vers un dépôt privé hors GitHub ; ne supprime jamais rien côté secours ; alerte un mois avant l'expiration de sa clé (17/10/2027) | dépôt de secours |
| Lien temporaire (`lien.yml`) | à la demande | lien d'accès au terminal qui expire tout seul | — |
| Sonde, Références (`probe.yml`, `refs.yml`) | à la demande (développement) | tests de sources, documents de référence | `probe`, `refs` |

Le site publié lit ses données en direct sur la branche `data` (`api/data.js`) ; la branche `site` ne contient que la page et n'est redéployée que si le code change. Les branches de données ne sont jamais déployées (`vercel.json`).

**Documents** : le site n'affiche jamais l'adresse d'origine d'un document. Le relais remplace les adresses dans les données par des adresses du site, et `vercel.json` les sert à la volée (rien n'est stocké) :

| Adresse du site | Document servi |
|---|---|
| `/doc/b/<fichier>` | documents publiés (états financiers, rapports, avis) |
| `/doc/f/<fichier>` | bulletins de la cote du jour |
| `/doc/a/<horodatage>/<chemin>` | anciens documents (archive web, copie à la date indiquée) |
| `/doc/c/<horodatage>/<chemin>` | anciens bulletins (même archive) |
| `/doc/r/<chemin>` | quelques documents d'un site d'information boursière |

La recherche MOTS CLES contrôle chaque ligne contre le nom de son fichier (`fix_by_file` dans `scripts/build_search.py`) : un fichier d'une autre société ou d'un autre type que l'intitulé est rattaché à la bonne société, avec un intitulé refait d'après le fichier.

### Secours si GitHub ne répond plus

- **Copie** : `copie.yml` envoie chaque nuit tout le dépôt vers un dépôt privé hors GitHub (secret GitHub `GITLAB_TOKEN`, droits lecture et écriture du dépôt uniquement).
- **Lecture par le site** : si GitHub ne répond plus (ou ne connaît plus le dépôt), `api/data.js` lit les données dans la copie (variable Vercel partagée `GITLAB_READ_TOKEN`, lecture seule, reliée au projet). Le site reste alors utilisable avec des données d'au plus un jour. Essai du secours seul : `/api/data?p=qlabp/index.json&via=2`.
- **Clés** : les deux clés expirent le 17/10/2027 ; en créer de nouvelles (ou « Rotate ») et remplacer le secret GitHub et la variable Vercel avant cette date.
- **Page du dépôt** : le champ « site web » du dépôt doit rester rempli avec l'adresse du dépôt lui-même — s'il est vide, Vercel y remet automatiquement l'adresse du site à chaque mise en ligne.
- **Plan B complet** (à préparer) : kit d'installation d'un serveur qui reprendrait les automatisations et écrirait dans la copie.

## Fichiers

```
index.html                 page générée : python3 build.py (assemble web/ ; code compacté sans commentaires par terser, obligatoire)
web/                       style.css, body.html, core.js (fonctions, navigation), engine.js (moteur quant), chart.js, pages*.js
api/data.js                lecture des données publiées (branche data) ; adresses des documents remplacées par /doc/… et
                           libellés de provenance retirés au passage ; alias de certains fichiers (ALIAS)
scripts/scrape.py          relevé de séance
scripts/fetch_extra.py     sources complémentaires, avis, comptes et documents de la BRVM
scripts/build_terminal.py  construction de toute la base data/ (puis QLAB le soir)
scripts/build_search.py    index de la recherche MOTS CLES
scripts/comptes.py         lecture et contrôle des états financiers publiés
scripts/dividendes.py      avis et calendriers de dividendes
scripts/qlab.py, qlab_core.py, qlab_backtest.py   moteur de valorisation QLAB (versions, événements, validation)
scripts/qlab_prev.py, periodiques.py               moteur de prévisions QLAB 3 et lecture des publications intermédiaires
docs/                      cahiers des charges et méthodes de QLAB
SAUVEGARDES.md             points de restauration (retour arrière possible à chaque étape)
```

## En local

```bash
npm install -g terser@5.36.0                        # une fois : build.py s'arrête sans lui
python3 build.py                                    # assemble index.html
git fetch origin data && git archive origin/data | tar -x -C /tmp/qsite
cp index.html /tmp/qsite/ && python3 -m http.server -d /tmp/qsite 8000   # http://localhost:8000
# (en local, les données ne passent pas par le relais : adresses d'origine et noms de fichiers réels)
```

Outil d'analyse personnel, pas un conseil en investissement. Les données de marché restent la propriété de leurs émetteurs.
