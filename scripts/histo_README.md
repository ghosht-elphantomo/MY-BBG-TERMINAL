# Base historique BRVM

Archive mise à jour chaque soir. Rien n'y est jamais effacé : une valeur qui change est remplacée
et l'ancienne est conservée dans `corrections.csv`. Aucune donnée n'est estimée ni recalculée.

Fichiers CSV en UTF-8, séparateur virgule, décimales avec un point
(Excel : Données › À partir d'un fichier texte/CSV, origine « UTF-8 », délimiteur « virgule »).

| Fichier | Contenu | Clé |
|---|---|---|
| `cours/AAAA.csv` | Cours des actions tels que publiés dans le bulletin officiel de la cote : précédent, ouverture, clôture, variation %, volume, valeur échangée (FCFA), cours de référence, variation annuelle %, dernier dividende, sa date, rendement %, PER, cours moyen (bulletins 2013-2017) | date, titre |
| `indices.csv` | Clôture des indices BRVM (séances terminées) | date, indice |
| `dividendes.csv` | Dividendes nets par action, d'après les avis (`avis`) et les bulletins de la cote (`bulletin`) ; montant publié, montant ramené au nombre d'actions actuel et facteur d'ajustement ; dates d'annonce, de détachement et de paiement | titre, exercice, origine |
| `fractionnements.csv` | Fractionnements et regroupements (ratio) | titre, date |
| `evenements.csv` | Avis et publications : assemblées, états financiers, opérations sur titres (`operation_sur_titre` = 1), document PDF | date, titre, catégorie, intitulé, document |
| `resultats.csv` | Comptes annuels : chiffre d'affaires, résultat net, capitaux propres, total bilan, trésorerie, EBIT, EBITDA, dette nette, dépôts et crédits clientèle, coût du risque (millions de FCFA) ; BNPA et dividende (FCFA par action) | titre, exercice |
| `etats_financiers.csv` | États financiers publiés par les sociétés, poste par poste (code et libellé du poste ; bilan, compte de résultat, flux ; millions de FCFA), pour les seuls exercices dont les totaux se vérifient dans le document ; périmètre (comptes sociaux ou consolidés), norme (SYSCOHADA ou IFRS) et nombre de documents qui donnent les mêmes montants | titre, exercice, poste |
| `flottant.csv` | Flottant officiel : titres, titres flottants, flottant %, seuil de 15 % | date de l'avis, titre |
| `notations.csv` | Notations financières : agence, notes long et court terme (et précédentes), perspective, échelle, validité | date, document |
| `corrections.csv` | Journal des corrections : date de constat, fichier, clé, champ, ancienne et nouvelle valeur | — |
| `controles.csv` | Contrôles de cohérence du jour (voir ci-dessous) | — |
| `etat.json` | Date de mise à jour, dernière séance, nombre de lignes par fichier, résumé des contrôles | — |

## Contrôles de cohérence

- `variation_incoherente` : la variation publiée ne correspond pas à clôture / cours précédent.
- `precedent_different` : le cours précédent ne reprend pas la clôture de la séance antérieure, sans dividende détaché ni fractionnement pour l'expliquer.
- `variation_hors_seuil` : variation au-delà de ±7,5 % sans opération sur titres connue.
- `prix_moyen_hors_fourchette` : valeur / volume éloigné des cours du jour (montant mal lu, par exemple en milliers).
- `volume_sans_valeur`, `valeur_sans_volume`, `cloture_absente` : séance incomplète pour un titre.
- `seance_incomplete` : bulletin avec nettement moins de titres que d'habitude.
- `avis_different_bulletin` : dividende d'un même exercice différent entre l'avis et le bulletin.
- `dates_incoherentes` : annonce après détachement, ou détachement après paiement.
- `flottant_incoherent`, `bnpa_signe_oppose` : chiffres contradictoires dans une même ligne.

Une alerte signale un point à vérifier, pas une erreur certaine.

## Limites connues

- Cours : bulletins au format actuel depuis fin 2017. Les bulletins plus anciens ont plusieurs mises en page ;
  seules leurs lignes qui se vérifient d'elles-mêmes sont reprises (`etat.json` indique le nombre de lignes non retenues).
- Un bulletin identique à celui de la veille (publié pour un jour férié, ex. 29/10/2020) n'est pas une séance : il est écarté.
- Montants d'un milliard de FCFA et plus imprimés en milliers dans certains bulletins : remis en FCFA (liste dans `etat.json`).
- Les ratios (marges, ROE…) ne sont pas stockés : ils se recalculent à partir de `resultats.csv` et `etats_financiers.csv`.
- Un exercice pas encore clos (comptes semestriels) n'a pas sa place dans `resultats.csv` : une telle ligne est retirée et consignée.
- `etats_financiers.csv` : un exercice provient de ses propres comptes de préférence (définitifs plutôt que provisoires), sinon de la colonne
  « exercice précédent » des comptes de l'année suivante ; un chiffre repris et corrigé par la société dans une publication ultérieure
  l'emporte. Les états lus par reconnaissance de caractères ne gardent que les montants confirmés par deux lectures ou par une
  identité comptable. Un jeu d'états dont un chiffre est faux (unité, année, ordre de grandeur) est écarté en entier ; les
  présentations de résultats et les notations ne servent jamais de source.
- Capitaux propres d'un bilan de synthèse sans ligne de total : somme des composantes publiées (capital, primes, réserves, report à
  nouveau, résultat, autres), retenue seulement si le passif la vérifie (total − dettes financières − passif circulant − trésorerie passif).
- Flux de trésorerie (flux opérationnels, acquisitions d'immobilisations, flux disponible) : uniquement ceux lus dans les états
  financiers publiés et contrôlés par les identités du document. Le fichier de départ `seed/fcf_brvm.json` (lecture sans contrôle,
  31 exercices faux sur 32 recoupés : unités, lignes confondues avec le chiffre d'affaires) a été retiré ; aucun flux n'est estimé.
- Lecture des mises en page particulières : deux pages imprimées côte à côte (bilan et compte de résultat à gauche, TAFIRE à
  droite) sont séparées à leur gouttière avant lecture ; une colonne « 01/01/N » ou « 1er janvier N » (bilan d'ouverture) est
  l'exercice N-1 ; une unité annoncée démentie par le capital social (« montants en milliards » pour des millions) est corrigée ;
  dans un document qui réunit comptes du groupe et comptes de la société (« Sonatel SA », « ONATEL SA »), chaque bloc garde
  son périmètre ; les lignes de contrôle du TAFIRE (variation du FdR, du BFG, de la trésorerie : colonnes emplois / ressources)
  ne sont pas des montants annuels.
- Documents d'émetteurs non cotés déposés sous la page d'une société cotée (BIDC, BOAD…) et états en unités de compte ou en
  dollars (Ecobank Transnational publie en dollars : ses états ne sont pas repris, les chiffres affichés pour ETIT viennent du
  miroir) : jamais retenus.
- Chiffre corrigé après coup : quand la colonne « exercice précédent » des comptes suivants (ou un rapport annuel publié plus
  tard) donne, vérifié par ses identités, un montant différent de celui des comptes de l'exercice, et que la base de recoupement
  (base tierce, archives SikaFinance) le reprend, c'est ce montant corrigé qui est retenu — avec les autres membres de ses
  identités pris dans le même document, jamais un mélange des deux versions (Unilever CI 2021 : résultat retraité ≈ 0 et non
  6 091 ; NSIA Banque 2017 : 10 015 pro forma). Un montant isolé égal à celui d'une autre année dans les autres sources
  (colonne décalée d'un communiqué numérisé) est retiré.
