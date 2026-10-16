# QLAB 2 — Valorisation : méthode

Moteur QLAB-V (scripts/qlab.py, qlab_core.py, qlab_backtest.py), recalculé chaque soir de semaine après la clôture par le passage
« base complète » du terminal. Résultats dans data/qlab/ (une fiche par société, un index, la validation historique) ; copie de
sauvegarde sur la branche raw. Interface : web/pages18.js (onglet « Valorisation » de la fonction QLAB).

## Décisions de RYSO (prioritaires sur le cahier des charges d'origine)

- QLAB ne prédit pas le cours : il présente la valeur selon les modèles d'évaluation les plus connus, comparée au dernier cours.
  Le « rendement implicite au cours actuel » et les rendements du cours des scénarios ont été retirés (16/10/2026).
- Trois sous-onglets seulement : Valorisation (valeur et fourchette de chacun des sept modèles, sans synthèse affichée ni
  poids), Risques et alertes, Qualité et facteurs (16/10/2026, 21 h 40). La synthèse reste calculée en interne pour les contrôles
  (versions, seuils de réévaluation, validation historique) mais n'est plus affichée.
- Pas de recommandation d'achat ou de vente, ni de promesse de performance.
- Fonctionnement entièrement automatique : aucune étape ne demande de contrôle manuel.

## Les sept modèles (sous-onglet Valorisation)

| N° | Modèle | Rôle |
|---|---|---|
| 1 | DCF probabiliste (flux disponibles de l'entreprise) | valeur des flux futurs actualisés, hypothèses tirées dans des lois justifiées par les données ; inadapté aux banques |
| 2 | Simulation Monte-Carlo | 2 000 trajectoires des hypothèses du modèle principal (graine déterministe) : distribution des valeurs et fourchette de la synthèse |
| 3 | Actualisation des dividendes (DDM) | dividendes projetés à partir du taux de distribution et de la rentabilité ; le dividende passé n'est jamais supposé acquis |
| 4 | Multiples historiques de la société | PER, valeur d'entreprise / EBITDA, cours / fonds propres médians sur 5 ans appliqués aux résultats attendus |
| 5 | Multiples des sociétés comparables | multiples médians des comparables de la BRVM (au moins 3), ajustés de l'écart de rentabilité |
| 6 | Résultat résiduel | fonds propres + valeur actuelle des bénéfices au-delà du coût des fonds propres ; modèle de référence des banques |
| 7 | DCF inversé | hypothèses (rentabilité, croissance, rendement exigé) contenues dans le cours ; lecture du cours, hors synthèse |

Synthèse : médiane du mélange pondéré des distributions des modèles 1, 3, 4, 5 et 6 (jamais une moyenne simple). Poids = produit de
la pertinence pour le modèle économique, de la qualité des données, de la robustesse, de la qualité hors échantillon de la prévision
utilisée, de la performance historique mesurée (validation point-in-time 2012-2025, règle de pondération choisie hors échantillon),
de la cohérence avec les résultats publiés et d'une pénalité de redondance, puis normalisation.

Paramètres de marché : taux sans risque tiré des courbes souveraines UEMOA, prime de risque = rendement exigé médian implicite de la
BRVM depuis 2010 moins le taux sans risque, bêta de Dimson rapproché de la moyenne du marché (Vasicek).

## Risques et alertes

Alarmes et alertes recalculées chaque soir (confiance très faible, valeur très éloignée du cours, cours ancien ou titre peu échangé,
réévaluation refusée, comptes attendus manquants, documents examinés) ; sensibilités croisées, hypothèses les plus influentes,
influence globale, seuils où la conclusion change ; régimes économiques ; liquidité et prime d'illiquidité ; historique des versions
et des événements examinés.

## Qualité et facteurs

Facteurs de qualité et de risque définis et classés par rapport aux autres sociétés de la BRVM ; qualité des données (exercices
vérifiés dans les états financiers publiés, données manquantes, ruptures de série) ; comptes et ratios utilisés.

## Versions, événements, garde-fous

- Chaque version est conservée telle quelle (données, hypothèses, résultats), horodatée et chaînée à la précédente (empreinte sha256).
- Réévaluation complète semestrielle (1er juin, 1er décembre) ; réévaluation exceptionnelle si un document nouveau franchit un seuil
  (valeur intrinsèque ≥ 10 %, bénéfice ≥ 15 %, actions ≥ 5 %, dividende réduit de plus de moitié, notation abaissée d'au moins deux crans) ;
  révision de méthode quand le moteur change ; ajustement mécanique en cas de fractionnement.
- Une estimation n'est publiée que si elle passe les contrôles (valeurs finies, fourchette cohérente, poids normalisés, comptes
  récents). Valeur centrale hors de 0,05 à 20 fois le cours : publiée seulement si un contrôle automatique écarte une erreur de
  données (bénéfice par action publié = résultat net ÷ actions, cours fiable), avec une alarme ; sinon la dernière estimation valide
  est conservée et l'essai est refait automatiquement chaque soir.

## Cahier des charges d'origine (conservé tel quel)

Les décisions ci-dessus priment sur ce texte là où elles le modifient (projection du cours, organisation des écrans).

PROMPT GLOBAL — DÉVELOPPEMENT DU MOTEUR QUANTITATIF DE VALORISATION QLAB (BRVM)

1. Mission générale

Tu dois développer un moteur quantitatif avancé d’analyse financière et de prévision boursière, exclusivement consacré aux sociétés cotées à la Bourse Régionale des Valeurs Mobilières (BRVM).

Ce moteur doit être intégré uniquement dans la section QLAB de mon site existant.

L’objectif est de construire un système capable d’analyser chaque société individuellement, d’estimer sa valeur intrinsèque, de produire des prévisions à plusieurs horizons et d’expliquer les facteurs qui pourraient faire évoluer ses résultats, ses dividendes, son cours et son profil de risque.

Le moteur doit utiliser des méthodes financières et quantitatives reconnues, puis développer une logique propriétaire de sélection, de combinaison, de pondération et de validation des modèles adaptée aux spécificités de la BRVM.

Il ne doit jamais prétendre prédire l’avenir avec certitude.

2. Règles impératives de protection du projet existant

Avant toute modification :

1. Inspecte l’architecture actuelle du projet, le fonctionnement de QLAB, les dépendances, les sources de données, les fichiers partagés et les éventuelles fonctions communes.
2. Identifie précisément les fichiers qui devront être créés ou modifiés.
3. Vérifie le fonctionnement actuel de QLAB et repère les risques de régression.
4. Crée un point de restauration fiable avant de modifier le code : sauvegarde du code existant ou commit Git clairement identifiable.
5. Présente un plan d’intervention concis avant les modifications importantes.

Périmètre strict :

* Toutes les nouvelles fonctionnalités doivent appartenir à QLAB.
* Ne reconstruis pas le site.
* Ne refonds pas son architecture générale.
* Ne modifie pas les autres sections, fonctionnalités ou interfaces.
* Privilégie des modules et fichiers autonomes pour limiter les interactions avec l’existant.
* Ne modifie pas un fichier partagé en dehors de QLAB sans expliquer pourquoi et demander mon autorisation préalable.
* Ne supprime aucune fonctionnalité existante pour simplifier ton travail.
* Ne modifie pas la configuration de production, les secrets, les variables d’environnement ou les paramètres de déploiement sans nécessité démontrée et autorisation.

Si une dépendance extérieure à QLAB est indispensable, explique le problème et propose une solution minimale avant de l’appliquer.

Après le développement, exécute les tests possibles, vérifie les éventuelles régressions et fournis un bilan précis des modifications effectuées.

3. Analyse individuelle et spécifique à chaque société

Ne traite jamais toutes les entreprises avec un modèle générique identique.

Pour chaque société, commence par identifier son activité réelle, ses sources de revenus, son marché, sa structure de coûts, ses facteurs de croissance, ses avantages concurrentiels, ses contraintes réglementaires, ses risques et ses particularités comptables.

Adapte ensuite les méthodes de valorisation à son modèle économique.

Par exemple :

* Une banque doit être analysée en tenant compte du risque de crédit, des dépôts, de la solvabilité, du coût du risque et de la qualité des actifs.
* Une entreprise de télécommunications doit être évaluée en tenant compte des investissements réseau, de la croissance des abonnés, des marges, de la dette et des flux de trésorerie.
* Une entreprise agro-industrielle doit être analysée en fonction des prix des matières premières, des volumes, des rendements, des coûts de production et de la cyclicité.
* Une entreprise de distribution doit être étudiée à travers ses volumes, ses marges, ses besoins en fonds de roulement, sa rotation des stocks et son pouvoir de fixation des prix.
* Une entreprise immobilière doit être analysée selon la valeur de ses actifs, ses revenus locatifs, son endettement et la qualité de ses flux de trésorerie.

Ces exemples ne constituent pas une liste fermée. Détermine le modèle approprié à partir des caractéristiques réelles de chaque société.

Ne force jamais un modèle inadapté à une entreprise simplement pour obtenir une estimation.

4. Collecte et contrôle des données

Rassemble, dans la mesure où elles sont disponibles, les données historiques et actuelles nécessaires à une analyse rigoureuse :

* Chiffre d’affaires et croissance annuelle.
* Résultat opérationnel et résultat net.
* Marges opérationnelles et nettes.
* Bénéfice par action et évolution du nombre d’actions.
* Flux de trésorerie opérationnels et flux de trésorerie disponibles.
* Investissements et dépenses en capital.
* Dette, trésorerie et coût de financement.
* Fonds propres, ROE et ROIC lorsque ces indicateurs sont pertinents.
* Dividendes, taux de distribution et historique des paiements.
* Cours historiques, volumes échangés, volatilité et drawdowns.
* Multiples de valorisation historiques et actuels.
* Informations sectorielles, macroéconomiques et réglementaires pertinentes.
* Opérations sur le capital, acquisitions, cessions et autres événements significatifs.

Privilégie les états financiers publiés, les rapports officiels, les publications des sociétés, les informations officielles de la BRVM et les autres sources vérifiables.

Pour chaque donnée importante, conserve sa source, sa date, sa période de référence et son statut de vérification.

Distingue clairement :

* Les données publiées et vérifiées.
* Les données estimées.
* Les hypothèses du modèle.
* Les données manquantes.
* Les données anciennes ou potentiellement obsolètes.

Ne fabrique jamais de chiffres pour compléter une série historique.

Si les données sont insuffisantes, réduis le niveau de confiance, indique les limites et désactive les modèles qui ne peuvent pas être appliqués correctement.

5. Analyse historique approfondie

Avant toute prévision, étudie le comportement passé de l’entreprise.

Analyse notamment :

* Les tendances du chiffre d’affaires, du bénéfice et des flux de trésorerie.
* Les taux de croissance annuels et les CAGR sur les périodes pertinentes.
* La stabilité ou la dégradation des marges.
* La cyclicité des résultats.
* La qualité des bénéfices et leur conversion en trésorerie.
* L’évolution de la dette et de la capacité de remboursement.
* La rentabilité des capitaux investis.
* La politique de dividendes et sa soutenabilité.
* Les changements de structure financière.
* Les crises, anomalies comptables et événements ayant affecté l’activité.
* L’évolution historique de la valorisation et du cours, en tenant compte de la liquidité réelle.

Ne confonds pas croissance historique et croissance future probable. Une forte croissance passée ne justifie pas automatiquement une croissance future élevée.

6. Les dix familles de modèles à étudier

Le moteur doit évaluer les dix familles de méthodes suivantes. Il ne doit pas nécessairement appliquer chacune d’elles à chaque société.

Modèle 1 — DCF probabiliste

Estime la valeur intrinsèque à partir des flux de trésorerie futurs actualisés.

Fais varier les hypothèses pertinentes : croissance, marges, investissements, taux d’actualisation, croissance terminale et autres paramètres propres à l’entreprise.

Utilise des hypothèses cohérentes avec les données historiques, les perspectives économiques et les risques observés.

Modèle 2 — Simulation Monte-Carlo

Simule un grand nombre de trajectoires possibles des variables fondamentales pertinentes.

Les distributions doivent être justifiées par les données, la connaissance de l’activité et des hypothèses documentées.

Intègre les dépendances entre variables lorsqu’elles sont pertinentes. Ne choisis pas arbitrairement des distributions pour produire une apparence de sophistication.

Présente une distribution des valeurs estimées, des intervalles de résultats et les probabilités conditionnelles aux hypothèses retenues.

Modèle 3 — Dividend Discount Model (DDM)

Évalue les sociétés pour lesquelles les dividendes représentent un indicateur pertinent de la valeur économique.

Projette les dividendes, leur croissance, leur taux de distribution et leur soutenabilité.

Ne suppose jamais qu’un dividende historique sera maintenu automatiquement.

Modèle 4 — Multiples prospectifs

Utilise les multiples adaptés à l’entreprise : PER, EV/EBITDA, EV/EBIT, P/B ou autres indicateurs pertinents.

Compare les multiples historiques de la société à ceux d’entreprises comparables lorsque des données fiables existent.

Explique les différences de croissance, de rentabilité, de risque et de liquidité qui justifient une prime ou une décote.

Modèle 5 — Residual Income

Estime la valeur en combinant les fonds propres comptables et les bénéfices futurs excédant le rendement exigé sur les capitaux propres.

Vérifie la pertinence du modèle selon la qualité des comptes et le modèle économique de la société.

Modèle 6 — Reverse DCF

Pars du cours actuel pour déterminer quelles hypothèses de croissance, de rentabilité et de génération de trésorerie semblent déjà intégrées par le marché.

Compare ces attentes implicites aux performances historiques et aux perspectives raisonnablement défendables.

Modèle 7 — Analyse de sensibilité multidimensionnelle

Mesure l’impact combiné de plusieurs hypothèses sur la valeur estimée.

Ne te limite pas à faire varier un seul paramètre à la fois lorsque les variables sont interdépendantes.

Identifie les hypothèses qui influencent le plus la valorisation et les seuils à partir desquels la conclusion change.

Modèle 8 — Facteurs de qualité et de risque

Construis une évaluation structurée portant notamment sur la rentabilité, la qualité des bénéfices, l’endettement, la stabilité des résultats, la gouvernance, la liquidité du titre et les risques sectoriels.

Évite les scores opaques : chaque facteur doit être défini, documenté et interprétable.

Modèle 9 — Modèles statistiques et de prévision

Étudie les modèles statistiques ou séries temporelles adaptés aux données disponibles.

N’utilise pas automatiquement un modèle complexe si l’historique est court, discontinu ou peu informatif.

Compare les résultats à des références simples et mesure les erreurs hors échantillon.

Modèle 10 — Scénarios de régimes économiques

Évalue l’entreprise dans plusieurs environnements économiques cohérents avec son activité : croissance, ralentissement, inflation, hausse des taux, choc de change, variation des matières premières, changement réglementaire ou autres facteurs pertinents.

Ne suppose pas que les mêmes régimes ont le même effet sur toutes les entreprises.

7. Synthèse propriétaire des modèles

La valeur ajoutée de QLAB doit résider dans sa capacité à sélectionner et combiner intelligemment les méthodes disponibles.

Pour chaque société :

1. Détermine les modèles applicables.
2. Évalue la qualité et la quantité des données nécessaires.
3. Mesure la cohérence des résultats avec les fondamentaux.
4. Compare les estimations entre méthodes.
5. Identifie les divergences importantes et cherche à les expliquer.
6. Pondère les modèles selon leur pertinence, leur robustesse et leurs performances historiques hors échantillon lorsque celles-ci peuvent être mesurées.
7. Réduit le poids des modèles fragiles, redondants ou fortement dépendants des mêmes hypothèses.
8. Présente une estimation centrale accompagnée d’une fourchette d’incertitude.

N’effectue pas une simple moyenne arithmétique des dix modèles.

Ne donne pas davantage de poids à un modèle uniquement parce qu’il est sophistiqué. Un modèle simple et robuste peut être préférable à un modèle complexe mal calibré.

Si les méthodes divergent fortement, ne masque pas le désaccord. Explique les raisons, élargis la fourchette d’incertitude et diminue le niveau de confiance.

La méthode de synthèse doit être documentée, testable et améliorable à partir de résultats observés, sans surapprentissage.

8. Prévisions à plusieurs horizons

Pour chaque société, produis des estimations aux horizons suivants :

* 1 an.
* 3 ans.
* 5 ans.
* 10 ans.

Pour chaque horizon, présente trois scénarios :

* Baissier.
* Central.
* Haussier.

Pour chaque scénario, indique :

* Les hypothèses économiques et opérationnelles.
* La croissance anticipée du chiffre d’affaires.
* L’évolution attendue des marges et des bénéfices.
* Les flux de trésorerie et investissements pertinents.
* Les hypothèses de valorisation.
* La valeur estimée par action.
* Le rendement potentiel du cours.
* Les dividendes potentiels, séparément.
* Le rendement total potentiel, dividendes inclus, selon une convention clairement indiquée.
* Les principaux risques et les événements susceptibles d’invalider le scénario.

Précise les dates de référence, la devise et les conventions de calcul.

Pour les horizons longs, augmente explicitement l’incertitude. Ne présente pas une cible à dix ans avec une précision artificielle.

Distingue toujours la valeur intrinsèque estimée du cours futur effectivement observé : le marché peut rester durablement éloigné de la valeur estimée.

9. Particularités de la BRVM

Le moteur doit tenir compte des spécificités du marché régional :

* Faibles volumes ou transactions irrégulières sur certains titres.
* Écarts potentiels entre valeur estimée et prix effectivement négociable.
* Cours anciens ou peu représentatifs du marché actuel.
* Concentration des échanges sur certains titres.
* Nombre parfois limité d’entreprises comparables.
* Informations financières publiées à des fréquences différentes.
* Risques liés aux devises, à la réglementation, à la fiscalité et aux économies des pays concernés.
* Particularités de la distribution des dividendes et du calendrier de publication.

Un cours stable ne signifie pas nécessairement que le titre est peu risqué : il peut simplement être peu échangé.

Ne confonds pas l’incertitude fondamentale et l’incertitude liée à la liquidité.

Si le dernier cours disponible est ancien ou peu représentatif, affiche clairement sa date et déclenche un avertissement. N’utilise pas silencieusement ce cours comme une cotation actuelle.

10. Backtesting et validation

Teste les méthodes sur des données historiques en respectant strictement l’information disponible à chaque date passée.

Évite le look-ahead bias, le survivorship bias et toute fuite d’information future.

Compare, lorsque cela est possible :

* Les prévisions aux résultats effectivement publiés.
* Les valeurs estimées aux prix observés par la suite.
* Les erreurs de prévision entre modèles.
* La calibration des intervalles d’incertitude.
* La performance des méthodes simples et complexes.
* La stabilité des résultats sur différentes périodes.

Distingue les erreurs de valorisation des erreurs de prévision du cours.

Tiens compte des dividendes, des opérations sur titres, de la liquidité et des frais lorsque ceux-ci sont pertinents.

Ne présente pas un backtest comme preuve de performance future. Si l’historique est insuffisant, indique que la validation est limitée.

11. Réévaluation complète semestrielle

Le moteur doit effectuer une réévaluation complète de chaque société tous les six mois.

Lors de chaque cycle, il doit :

1. Actualiser les données financières et boursières disponibles.
2. Vérifier les nouvelles publications et les éventuelles corrections de données.
3. Réexaminer les hypothèses de croissance, de marges, de dette, d’investissements et de dividendes.
4. Recalculer les modèles applicables.
5. Revoir la pondération des modèles selon leur pertinence et leurs performances mesurées.
6. Actualiser les scénarios à 1, 3, 5 et 10 ans.
7. Comparer les nouvelles estimations aux estimations précédentes.
8. Expliquer les principales variations de valorisation et de niveau de confiance.

Le cycle semestriel ne doit pas consister à décaler mécaniquement les anciennes prévisions de six mois. Il doit s’agir d’une nouvelle analyse fondée sur les informations disponibles.

Conserve un historique horodaté et immuable des prévisions successives, des données utilisées, des hypothèses, des résultats des modèles et des synthèses.

Ne remplace pas silencieusement une ancienne prévision par une nouvelle. Chaque version doit rester consultable.

12. Actualisation exceptionnelle : critères stricts et limités

En dehors du cycle semestriel, une actualisation anticipée est autorisée uniquement lorsqu’un événement majeur, suffisamment documenté, est susceptible de modifier matériellement les fondamentaux, la valeur estimée ou le profil de risque de la société.

Le principe est simple : une nouvelle information ne justifie pas automatiquement une nouvelle prévision. Elle doit être susceptible de changer significativement la conclusion de l’analyse.

A. Événements pouvant justifier une actualisation exceptionnelle

1. Résultats très éloignés des attentes

* Résultats annuels ou intermédiaires présentant un écart important et durable par rapport aux hypothèses centrales.
* Révision majeure des perspectives annoncées par l’entreprise.
* Forte dégradation ou amélioration inattendue des marges, des bénéfices ou des flux de trésorerie.
* Découverte d’une anomalie comptable susceptible de remettre en cause les bénéfices historiques.

Un simple écart trimestriel ne suffit pas s’il est ponctuel, explicable et sans effet matériel sur les perspectives à moyen terme.

2. Événement financier ou opérationnel majeur

* Acquisition, cession, fusion ou restructuration importante.
* Augmentation de capital, dilution significative ou changement majeur du nombre d’actions.
* Endettement exceptionnel, refinancement difficile ou risque de défaut.
* Fermeture d’une activité essentielle, perte d’un client majeur ou d’un contrat représentant une part importante des revenus.
* Arrêt de production, sinistre majeur ou interruption prolongée de l’activité.

3. Changement majeur dans les dividendes ou la structure du capital

* Suspension inattendue du dividende.
* Réduction substantielle du dividende pour des raisons structurelles.
* Dividende exceptionnel ou opération sur capital modifiant significativement les paramètres de valorisation.
* Modification importante de la politique financière susceptible d’affecter durablement la valeur par action.

Une hausse ponctuelle du dividende ne doit pas être extrapolée automatiquement aux années suivantes.

4. Changement structurel de l’environnement économique ou réglementaire

* Nouvelle réglementation ayant un effet significatif sur les revenus, les coûts ou la rentabilité.
* Changement fiscal ou tarifaire affectant matériellement l’activité.
* Variation importante et persistante d’une devise, d’un taux, d’un prix de matière première ou d’une variable économique déterminante.
* Modification majeure des conditions d’accès au marché ou des règles sectorielles.

Le changement doit être relié explicitement aux fondamentaux de la société. Une actualité macroéconomique générale ne suffit pas.

5. Dégradation majeure de la solvabilité ou de la gouvernance

* Alerte sur la continuité d’exploitation.
* Risque crédible de défaut ou incapacité de refinancement.
* Perte de licence ou autorisation essentielle.
* Fraude, irrégularité comptable confirmée ou enquête crédible susceptible d’affecter substantiellement l’activité.
* Départ soudain d’un dirigeant clé accompagné d’éléments remettant en cause la stratégie ou la gouvernance.

Distingue les faits confirmés des allégations. Ne déclenche pas une réévaluation complète sur la seule base d’une rumeur non vérifiée.

6. Événement remettant en cause une hypothèse fondamentale du modèle

* Hypothèse de croissance devenue manifestement irréaliste.
* Effondrement structurel d’une marge supposée durable.
* Investissements ou besoins en fonds de roulement bien supérieurs aux prévisions.
* Dégradation importante de la qualité des actifs ou des créances.
* Invalidation d’un avantage concurrentiel ou d’une hypothèse essentielle à la valorisation.

B. Seuils de matérialité

Les critères doivent être adaptés à la société et à son secteur. À titre de règles initiales à calibrer, une alerte peut être examinée lorsqu’un événement entraîne ou risque raisonnablement d’entraîner :

* Une variation estimée d’au moins 10 % de la valeur intrinsèque centrale par action.
* Une révision d’au moins 15 % des bénéfices annuels ou des flux de trésorerie attendus, lorsque ces indicateurs sont pertinents.
* Une modification importante du risque de défaut, de la continuité d’exploitation ou de la soutenabilité du dividende.
* Un changement majeur de structure du capital ou du nombre d’actions.

Ces seuils sont des déclencheurs d’examen, pas des vérités universelles. Ils doivent être adaptés au secteur, à la volatilité fondamentale et à la qualité des données.

Pour les banques, les assurances et les sociétés pour lesquelles les flux de trésorerie classiques sont peu pertinents, utilise les indicateurs propres à leur activité.

Un seuil franchi ne signifie pas nécessairement qu’une nouvelle estimation complète est justifiée. Il déclenche d’abord une vérification de matérialité.

C. Procédure obligatoire avant de déclencher une actualisation

Avant toute réévaluation exceptionnelle :

1. Identifie précisément l’événement et sa date.
2. Vérifie sa source et son degré de fiabilité.
3. Détermine s’il s’agit d’une information nouvelle ou déjà intégrée dans la dernière analyse.
4. Évalue son impact probable sur les fondamentaux, les hypothèses et la valeur estimée.
5. Vérifie si cet impact est suffisamment important et durable.
6. Écarte les événements mineurs, temporaires, redondants ou sans conséquence significative sur la valorisation.
7. Détermine si une réévaluation complète est nécessaire ou si une simple note de suivi suffit.

En cas d’informations contradictoires ou insuffisantes, conserve la dernière prévision validée, signale l’incertitude et indique qu’une vérification est nécessaire.

D. Événements qui ne doivent PAS déclencher une actualisation exceptionnelle

Ne lance pas de nouvelle évaluation complète simplement parce que :

* Le cours monte ou baisse pendant quelques séances.
* Le marché connaît une variation ordinaire.
* Un indicateur technique change de signal.
* Une rumeur non vérifiée circule.
* Une actualité générale n’a pas d’impact matériel identifiable sur l’entreprise.
* Une nouvelle donnée mineure modifie légèrement une hypothèse.
* Le modèle produit une fluctuation de valeur liée uniquement au bruit statistique.
* Un analyste modifie son opinion sans apporter d’information fondamentale nouvelle.

Les mouvements de marché et les signaux techniques peuvent être surveillés séparément, mais ne doivent pas, à eux seuls, provoquer une réévaluation fondamentale complète.

E. Limitation de fréquence et prévention des déclenchements répétés

Pour éviter une actualisation permanente :

* Regroupe les événements liés à une même cause dans un seul dossier d’analyse.
* Ne lance pas plusieurs réévaluations complètes pour le même événement.
* Conserve une trace des événements examinés, acceptés ou rejetés et des raisons de la décision.
* Prévois une période de regroupement des alertes, par défaut de 30 jours, sauf nouvel événement matériel indépendant ou aggravation substantielle.
* Autorise une nouvelle actualisation immédiate en cas de risque grave, d’alerte de continuité d’exploitation, de défaut potentiel ou d’événement pouvant remettre rapidement en cause la survie de l’entreprise.
* Ne bloque jamais une actualisation urgente uniquement parce qu’une autre vient d’avoir lieu.

La règle des 30 jours est une protection contre les répétitions, pas une interdiction d’agir pendant cette période.

F. Deux niveaux d’intervention

Niveau 1 — Vérification exceptionnelle

Une information potentiellement importante est détectée. Le système vérifie sa source, mesure sa matérialité et détermine si elle change réellement les hypothèses.

Cette étape ne modifie pas automatiquement les prévisions officielles.

Niveau 2 — Réévaluation exceptionnelle complète

Elle n’est déclenchée que si l’analyse confirme un changement matériel des fondamentaux, des perspectives, des dividendes, du risque ou de la valeur estimée.

Le système recalcule alors les modèles concernés, réexamine la synthèse, actualise les scénarios et conserve les anciennes prévisions.

Si l’événement n’est pas matériel, il est simplement enregistré pour le prochain cycle semestriel.

G. Traçabilité des actualisations exceptionnelles

Pour chaque événement, conserve :

* La société concernée.
* La date de l’événement et celle de sa détection.
* La source de l’information.
* Le critère de déclenchement.
* L’impact estimé sur les hypothèses et la valeur.
* La décision de déclencher ou non une réévaluation.
* Les anciennes et nouvelles estimations.
* Les modèles affectés.
* L’explication des changements.
* Le niveau de confiance et les limites éventuelles.

L’historique doit permettre de vérifier que le système ne multiplie pas les actualisations inutiles et qu’il ne réécrit pas ses prévisions passées.

13. Interface QLAB

Crée une interface claire et exploitable pour chaque société, sans refondre les autres parties du site.

Elle doit notamment présenter :

* Les données historiques essentielles.
* Les principaux ratios financiers.
* Les hypothèses utilisées.
* Les résultats des modèles applicables.
* La synthèse quantitative.
* Les scénarios à 1, 3, 5 et 10 ans.
* Les valeurs estimées et les fourchettes d’incertitude.
* Les dividendes et rendements potentiels.
* Les risques majeurs et les sensibilités.
* La qualité des données et la date du dernier cours fiable.
* La date de la dernière réévaluation complète.
* La prochaine échéance semestrielle.
* Les actualisations exceptionnelles et leur justification.
* L’historique des prévisions et la comparaison entre versions.

Les informations importantes doivent être lisibles et les hypothèses modifiables uniquement lorsque les permissions et le fonctionnement actuel du projet le permettent.

N’affiche pas une prévision comme actuelle si ses données sont anciennes ou si son cycle de mise à jour a échoué.

14. Automatisation et fiabilité

Vérifie les capacités techniques réelles de l’architecture existante avant de promettre une automatisation.

Si le projet nécessite une tâche planifiée, une source de données supplémentaire ou un service externe, explique les dépendances et les limites avant de les mettre en place.

L’automatisation doit prévoir :

* Des journaux d’exécution.
* La gestion des erreurs.
* La détection des données manquantes ou obsolètes.
* La prévention des exécutions en double.
* La conservation de la dernière estimation valide en cas d’échec.
* Un signalement explicite lorsqu’une mise à jour n’a pas pu être réalisée.
* Une validation des résultats avant leur publication.

Ne prétends jamais que les mises à jour semestrielles ou exceptionnelles sont automatiques tant que le mécanisme correspondant n’a pas été configuré et testé.

Si les nouvelles données ne sont pas disponibles, n’invente pas une actualisation. Conserve la dernière estimation valide, indique son ancienneté et précise les éléments manquants.

15. Amélioration continue et règles de décision

Le système doit conserver les résultats de ses prévisions antérieures et mesurer progressivement les performances des modèles.

Toute modification des poids, des seuils ou des méthodes doit être justifiée par des tests et des résultats observables.

Ne modifie pas les paramètres du moteur simplement parce qu’une prévision a été incorrecte une fois.

Évite le surapprentissage, les changements de méthode opportunistes et l’utilisation des résultats futurs pour calibrer une prévision passée.

Si les données ne permettent pas de valider statistiquement une amélioration, indique-le clairement.

16. Transparence et limites

Les méthodes de valorisation doivent être présentées comme des outils d’analyse, et non comme des prédictions certaines.

Le caractère propriétaire de QLAB doit provenir de son architecture, de ses règles de sélection, de sa synthèse, de ses contrôles de qualité et de son processus de validation, et non de la prétention d’avoir inventé les méthodes financières classiques.

Pour chaque résultat, distingue les faits, les estimations et les hypothèses.

N’affiche jamais une précision artificielle, une probabilité non calibrée ou une performance historique inventée.

Précise que les résultats ne garantissent pas les performances futures et ne constituent pas, à eux seuls, une recommandation personnalisée d’investissement.

17. Livrables et vérifications finales

Une fois le développement terminé :

1. Fournis la liste des fichiers créés et modifiés.
2. Explique brièvement le rôle de chaque module.
3. Indique les modèles réellement implémentés et ceux qui restent partiels ou impossibles à appliquer faute de données.
4. Décris les sources de données effectivement connectées et leurs limites.
5. Présente les tests effectués et leurs résultats.
6. Vérifie que les fonctions existantes hors QLAB n’ont pas été modifiées.
7. Indique les éventuelles limites du backtesting et de l’automatisation.
8. Confirme les mécanismes de sauvegarde et de restauration disponibles.
9. Fournis une procédure de vérification du résultat avant toute publication en production.

Priorité absolue : produire un moteur rigoureux, explicable, adapté aux entreprises réellement cotées à la BRVM, résistant aux données imparfaites et intégré sans régression au site existant. La qualité des analyses prime sur le nombre de fonctionnalités affichées.
