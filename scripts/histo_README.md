# Base historique BRVM

Archive mise à jour chaque soir. Rien n'y est jamais effacé : une valeur qui change est remplacée
et l'ancienne est conservée dans `corrections.csv`. Aucune donnée n'est estimée ni recalculée.

Fichiers CSV en UTF-8, séparateur virgule, décimales avec un point
(Excel : Données › À partir d'un fichier texte/CSV, origine « UTF-8 », délimiteur « virgule »).

| Fichier | Contenu | Clé |
|---|---|---|
| `cours/AAAA.csv` | Cours des actions tels que publiés dans le bulletin officiel de la cote : précédent, ouverture, clôture, variation %, volume, valeur échangée (FCFA), cours de référence, variation annuelle %, dernier dividende, sa date, rendement %, PER | date, titre |
| `indices.csv` | Clôture des indices BRVM (séances terminées) | date, indice |
| `dividendes.csv` | Dividendes nets par action, d'après les avis (`avis`) et les bulletins de la cote (`bulletin`) ; montant publié, montant ramené au nombre d'actions actuel et facteur d'ajustement ; dates d'annonce, de détachement et de paiement | titre, exercice, origine |
| `fractionnements.csv` | Fractionnements et regroupements (ratio) | titre, date |
| `evenements.csv` | Avis et publications : assemblées, états financiers, opérations sur titres (`operation_sur_titre` = 1), document PDF | date, titre, catégorie, intitulé, document |
| `resultats.csv` | Comptes annuels : chiffre d'affaires, résultat net, capitaux propres, total bilan, trésorerie, EBIT, EBITDA, dette nette, dépôts et crédits clientèle, coût du risque (millions de FCFA) ; BNPA et dividende (FCFA par action) | titre, exercice |
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
- Les ratios (marges, ROE…) ne sont pas stockés : ils se recalculent à partir de `resultats.csv`.
