# QLAB 3 « Prévisions » — cahier des charges et état d'avancement

Ce fichier conserve l'intégralité du cahier des charges de QLAB 3. Aucune fonctionnalité n'est retirée ou simplifiée par les
évolutions de QLAB 2 « Valorisation ». Une fonctionnalité n'est marquée « faite » qu'une fois réellement implémentée et testée.

## État d'avancement

| Fonctionnalité | État |
|---|---|
| Sous-module « Prévisions » (3e onglet de QLAB), sans toucher Statistiques ni Valorisation | fait (QLAB-P 1.0, 16/10/2026 : scripts/qlab_prev.py, scripts/periodiques.py, web/pages19.js) |
| Prévisions par exercice : chiffre d'affaires (PNB des banques), résultat d'exploitation, résultat net, BPA, marges | fait |
| Prévisions par exercice : flux de trésorerie et indicateurs sectoriels (dépôts, crédits, coût du risque, volumes) | à développer |
| Cumuls intermédiaires (1er trimestre, 1er semestre, 9 mois) publiés et prévus, chaque chiffre lu contrôlé par la variation publiée sur la même ligne | fait (couverture croissante : les rapports d'activité restant à lire sont lus automatiquement) |
| Trimestre isolé (3e trimestre seul, 4e trimestre) | à développer |
| Horizons : exercice en cours, quatre exercices suivants avec incertitude croissante mesurée | fait |
| Choix de méthode propre à chaque société (historique propre, exigence renforcée) et par type d'entreprise (banques / autres) | fait |
| Modèles sectoriels fins (agro-industrie, télécoms, distribution, énergie, services publics) | à développer |
| Facteurs : matières premières, inflation, change, taux, coûts, concurrence, réglementation, fiscalité, climat, macroéconomie, géopolitique | à développer (ne seront intégrés que s'ils réduisent l'erreur hors échantillon) |
| Collecte automatisée : rapports annuels, semestriels, trimestriels, communiqués, avis de la BRVM | fait (lecture automatique de tous les documents déposés à la BRVM) |
| Collecte : données sectorielles, matières premières (caoutchouc, huile de palme, sucre, cacao) | à développer |
| Source (document), date de publication, période, statut de vérification et recoupement de chaque donnée | fait (affichés sans nom de site ni lien) |
| Détection des événements : chaque document publié par la société ou la concernant est examiné (résultats, communiqués, dirigeants, opérations sur le capital, notations, assemblées), intitulés signalant un événement exceptionnel (perte, incendie, grève, cession, sanction…) | fait |
| Détection d'événements extérieurs aux documents de la BRVM (catastrophes, conflits, décisions publiques, ruptures d'approvisionnement) | à développer |
| Analyse d'impact : portée mesurée de chaque nature de document sur le résultat net des exercices passés ; sens défavorable quand l'intitulé l'indique ; pas de double comptage (une publication de résultats remplace les effets estimés) | fait |
| Analyse d'impact par indicateur et par durée (effets ponctuels / durables) au-delà du résultat net | à développer |
| Seuil de matérialité de 5 % du résultat net prévisionnel (configurable, MAT_NI) : déclencheur d'analyse ; cumul des documents de faible portée depuis la dernière version | fait |
| Incertitude : fourchettes à 80 % mesurées sur les erreurs passées, scénarios défavorable / central / favorable | fait |
| Simulation de Monte-Carlo des prévisions de résultats | à développer |
| Révision à chaque publication, mise à jour trimestrielle obligatoire, révisions exceptionnelles, chaque soir sans intervention | fait |
| Historique intégral des prévisions (versions horodatées et chaînées par empreinte, jamais réécrites) | fait |
| Comparaison automatique aux résultats publiés : écarts, biais, couverture, par société, horizon et type d'entreprise | fait (suivi des versions publiées) ; par secteur et périodes de choc : à développer |
| Validation point-in-time à origine glissante, sans information postérieure à la date de prévision | fait |
| Mémoire historique des événements et recherche d'épisodes comparables | partiel (portée par nature de document) ; recherche d'épisodes comparables : à développer |
| Journalisation, erreurs isolées, idempotence, sauvegarde et restauration, alerte de publication en retard | fait |
| Interface : publié (blanc) et prévu (bleu, italique) distingués, facteurs expliqués, révisions, documents examinés, écarts, validation | fait |
| Recalage complet sur tout l'historique et toutes les actualités dès que tous les documents sont lus | programmé (tâche planifiée quotidienne, se désactive après le recalage) |
| Pas de prévision du cours, d'objectif de cours ni de promesse de rendement dans QLAB 3 | règle de conception |

## Séparation des modules

- QLAB 2 « Valorisation » : méthodes d'évaluation reconnues, hypothèses explicites, calculs transparents ; ni recommandation automatique d'achat ou de vente, ni promesse de performance ; aucune projection ni prévision du cours (la valeur estimée est comparée au dernier cours, sans hypothèse sur l'évolution du cours).
- QLAB 3 « Prévisions » : prévisions des résultats financiers et leurs révisions ; aucune prévision du cours, aucun objectif de cours, aucune promesse de rendement.

## Consigne impérative (16/10/2026)

CONSIGNE IMPÉRATIVE — PRÉSERVER INTÉGRALEMENT QLAB 3 « PRÉVISIONS »

La refonte du module QLAB 2 « Valorisation » ne doit entraîner aucune suppression, simplification ou dégradation des fonctionnalités prévues pour QLAB 3 « Prévisions » dans le prompt initial.

Le module 3 doit conserver l’intégralité de son cahier des charges initial, notamment :

* Prévisions financières détaillées : chiffre d’affaires, résultat net, résultat opérationnel, bénéfice par action, marges, flux de trésorerie et autres indicateurs pertinents selon les données disponibles.
* Analyse sectorielle et propre à chaque entreprise : cycles économiques, matières premières, inflation, taux de change, coûts, concurrence, réglementation, fiscalité, conditions météorologiques, évolutions macroéconomiques et géopolitiques, ainsi que tout autre facteur pertinent.
* Détection automatique des événements exceptionnels : catastrophes naturelles, incendies, accidents industriels, conflits, sanctions, décisions gouvernementales, changements réglementaires ou fiscaux, grèves, ruptures d’approvisionnement, problèmes de production, acquisitions, cessions, changements de direction, avertissements sur résultats, publications financières inattendues et tout événement susceptible d’affecter matériellement les résultats d’une entreprise.
* Seuil de matérialité de 5 % : lorsqu’un événement est susceptible de modifier le résultat net prévisionnel de plus de 5 %, le système doit déclencher une analyse exceptionnelle et réévaluer les prévisions concernées. Ce seuil constitue un déclencheur d’analyse, et non une variation automatique de 5 %. Les événements inférieurs à ce seuil ne doivent pas être ignorés s’ils deviennent significatifs par accumulation ou par leur nature.
* Collecte et actualisation automatisées des informations : rapports annuels, semestriels et trimestriels, communiqués des entreprises, publications officielles, données sectorielles, indicateurs macroéconomiques, cours des matières premières, taux de change et autres sources fiables pertinentes. Chaque donnée doit être accompagnée de sa source, de sa date et, lorsque possible, d’un indicateur de fiabilité.
* Analyse de l’impact des événements : déterminer quelles entreprises sont concernées, quels indicateurs financiers peuvent être affectés, dans quelle direction, avec quelle ampleur estimée et pendant combien de temps. Distinguer les effets ponctuels des effets durables et éviter de compter deux fois un même impact.
* Gestion de l’incertitude : lorsque les informations sont incomplètes, contradictoires ou non vérifiées, présenter des hypothèses conditionnelles, des fourchettes et plusieurs scénarios plutôt que d’inventer une estimation précise.
* Modélisation financière adaptée : combiner historiques financiers, facteurs opérationnels, modèles statistiques, séries temporelles et autres méthodes pertinentes, avec validation sur des données passées. Les calculs doivent rester explicables et ne pas reposer uniquement sur une interprétation par IA.
* Scénarios central, favorable et défavorable, avec des prévisions à court terme et, lorsque les données le permettent, sur deux à cinq ans. L’incertitude doit être clairement présentée et augmenter avec l’horizon de prévision.
* Historique intégral des prévisions : conserver chaque version, sa date, les données disponibles à cette date, les hypothèses, le modèle utilisé et les raisons des révisions. Ne jamais écraser les anciennes prévisions.
* Contrôle rétrospectif des performances : comparer automatiquement les prévisions antérieures aux résultats effectivement publiés, mesurer les erreurs et biais de prévision par entreprise, secteur et horizon, et améliorer les modèles sans utiliser d’informations qui n’étaient pas disponibles à la date de prévision.
* Automatisation réelle : mises à jour trimestrielles obligatoires et révisions exceptionnelles déclenchées par les événements pertinents, indépendamment de l’ouverture de la page par un utilisateur. Prévoir journalisation, gestion des erreurs, relances et alertes lorsque les données sont trop anciennes.
* Interface dédiée : distinguer visuellement les résultats historiques publiés des chiffres prévisionnels, expliquer les facteurs qui font évoluer les estimations et afficher l’historique des événements et des révisions.

Séparation stricte entre les modules

QLAB 2 — Valorisation : méthodes reconnues d’évaluation financière, hypothèses explicites et calculs transparents. Pas de recommandations automatiques d’achat ou de vente, ni de promesses de performance.

QLAB 3 — Prévisions : maintien de toutes les fonctionnalités ci-dessus pour prévoir les résultats financiers des entreprises et les réviser en fonction des nouvelles données et des événements exceptionnels. Il ne doit pas prédire le cours futur des actions, produire des objectifs de cours ou promettre des rendements.

Exigence d’implémentation

Avant toute modification, examiner le code existant et le prompt initial. Vérifier explicitement que chaque fonctionnalité de QLAB 3 est préservée. Modifier QLAB 2 de manière isolée, sans réécrire inutilement QLAB 3 ni les autres modules. Si une fonctionnalité initialement prévue n’est pas encore implémentée, la conserver dans le cahier des charges et la signaler comme restant à développer : ne pas prétendre qu’elle fonctionne déjà.

## Cahier des charges initial (16/10/2026)

MISSION — CONSTRUIRE QLAB 3 : MOTEUR INTELLIGENT DE PRÉVISIONS FINANCIÈRES DYNAMIQUES POUR LA BRVM

1. OBJECTIF GÉNÉRAL

Dans le module principal QLAB, il existe actuellement plusieurs sous-modules, notamment :

1. Statistiques
2. Valorisation

Je veux ajouter un troisième sous-module indépendant :

3. Prévisions

Ce nouveau sous-module doit devenir un moteur professionnel de prévisions financières, conçu spécifiquement pour les entreprises cotées à la BRVM.

Son objectif est de produire, pour chaque société, des prévisions actualisables et argumentées de :

* Chiffre d’affaires.
* Résultat opérationnel, lorsque les données le permettent.
* Résultat net.
* Bénéfice par action (BPA/EPS).
* Marges opérationnelles et nettes.
* Principaux facteurs influençant les bénéfices.
* Fourchettes de prévisions et scénarios futurs.
* Risques susceptibles de faire évoluer les prévisions.
* Révisions positives ou négatives par rapport aux prévisions précédentes.

Le système doit couvrir toutes les sociétés cotées pour lesquelles des données suffisamment fiables sont disponibles. Il doit être conçu pour s’enrichir progressivement à mesure que de nouvelles données deviennent accessibles.

Règle absolue : ce module doit être ajouté sans réécrire, supprimer, dégrader ou modifier inutilement les modules Statistiques, Valorisation ou les autres fonctionnalités existantes de QLAB. Il doit également respecter l’architecture actuelle du terminal.

Avant toute modification, inspecte le code existant, identifie l’architecture de QLAB et les composants réutilisables, puis propose une intégration isolée et compatible.

⸻

2. UN MOTEUR QUI NE SE CONTENTE PAS D’EXTRAPOLER LE PASSÉ

Je ne veux pas d’un système qui calcule simplement une croissance moyenne historique et la prolonge sur les cinq ou dix prochaines années.

L’historique financier est indispensable, mais il ne constitue qu’une composante du modèle.

Le moteur doit distinguer :

* Ce que l’entreprise a réalisé historiquement.
* Sa situation économique actuelle.
* Les tendances structurelles de son secteur.
* Les facteurs conjoncturels.
* Les événements récents.
* Les facteurs macroéconomiques et géopolitiques pertinents.
* Les changements réglementaires.
* Les risques propres à l’entreprise.
* Les anticipations et incertitudes concernant le futur.

Il doit rechercher les facteurs réellement explicatifs du chiffre d’affaires et des bénéfices de chaque entreprise.

Il ne doit jamais supposer que les performances passées se reproduiront automatiquement.

Il doit également éviter de confondre corrélation et causalité. Une actualité survenue avant une variation des bénéfices ne doit pas être considérée automatiquement comme la cause de cette variation.

3. UN MODÈLE ADAPTÉ À CHAQUE ENTREPRISE ET À CHAQUE SECTEUR

Le moteur doit identifier l’activité économique réelle de chaque société et adapter ses variables explicatives en conséquence.

Il ne faut pas appliquer exactement le même modèle à toutes les entreprises de la BRVM.

A. Entreprises cycliques : SAPH, SOGB, PALMCI, etc.

Pour les entreprises exposées aux matières premières agricoles, le modèle doit intégrer, selon les données disponibles :

* Les prix mondiaux du caoutchouc naturel et de l’huile de palme.
* Les cours des matières premières pertinentes et leurs perspectives.
* Les volumes de production.
* Les rendements agricoles.
* Les superficies exploitées et leur évolution.
* L’âge des plantations et les cycles de renouvellement.
* Les conditions météorologiques et les risques climatiques.
* Les maladies des cultures et les risques phytosanitaires.
* Les coûts de main-d’œuvre, d’énergie, de transport et d’intrants.
* Les taux de change pertinents.
* Les politiques commerciales, taxes, restrictions et droits de douane.
* Les perturbations logistiques et géopolitiques.
* Les investissements, extensions de capacité et projets annoncés.

Le modèle doit distinguer le cycle de marché de la tendance structurelle de l’entreprise.

Une période exceptionnellement favorable pour les prix des matières premières ne doit pas être extrapolée indéfiniment. De même, une année exceptionnellement mauvaise ne doit pas conduire automatiquement à prévoir une baisse permanente.

Il doit construire des scénarios cohérents concernant les prix, les volumes, les coûts et les marges.

B. Entreprises de télécommunications : SONATEL, ORANGE CI, etc.

Prendre notamment en compte :

* Le nombre d’abonnés.
* Le revenu moyen par utilisateur (ARPU), lorsqu’il est disponible.
* L’évolution du trafic et de la consommation.
* La croissance de l’Internet mobile et des services de données.
* Les investissements dans les infrastructures.
* Les coûts d’interconnexion et d’exploitation.
* La concurrence.
* Les tarifs et les changements réglementaires.
* Les licences et obligations de couverture.
* Les taxes sectorielles.
* Les taux de change et les expositions internationales.
* Les nouveaux services et relais de croissance.

C. Banques et institutions financières

Prendre notamment en compte :

* La croissance des crédits et des dépôts.
* Les marges nettes d’intérêt.
* Le coût du risque.
* Les créances douteuses et leur couverture.
* Les commissions.
* Les exigences de fonds propres.
* Les ratios prudentiels et leur évolution.
* Les taux d’intérêt et la politique monétaire.
* La concentration des expositions.
* Les risques souverains et les risques de crédit.
* Les coûts d’exploitation.
* Les changements réglementaires et fiscaux.

Pour les banques, utiliser des modèles adaptés à leur activité. Ne pas leur appliquer mécaniquement les modèles de flux de trésorerie destinés aux entreprises industrielles.

D. Entreprises de distribution, industrie, énergie, services publics et autres secteurs

Construire des modèles sectoriels adaptés, avec des variables spécifiques à leur activité.

Par exemple, pour une société de distribution, considérer les volumes vendus, les prix, les stocks, les marges commerciales, les coûts logistiques, la concurrence et le pouvoir d’achat.

Pour une société d’eau ou d’électricité, considérer notamment les volumes distribués, les tarifs réglementés, les mécanismes de compensation, les investissements, les pertes techniques, les coûts d’approvisionnement et les obligations de service public.

Pour chaque entreprise, expliquer les principaux facteurs qui déterminent ses revenus, ses coûts et ses bénéfices.

Ne pas inventer de données sectorielles lorsque celles-ci ne sont pas disponibles.

⸻

4. COLLECTE AUTOMATIQUE ET ACTUALISATION DES DONNÉES

Le système doit exploiter automatiquement les sources de données accessibles et autorisées.

Sources à intégrer selon leur disponibilité

* Rapports annuels et états financiers audités.
* Rapports trimestriels et semestriels lorsqu’ils sont publiés.
* Publications de résultats et communiqués officiels.
* Documents de la BRVM.
* Publications des sociétés cotées.
* Documents des régulateurs et autorités publiques.
* Décisions fiscales et réglementaires.
* Statistiques macroéconomiques.
* Données sectorielles.
* Prix des matières premières.
* Taux de change.
* Taux d’intérêt.
* Informations géopolitiques et commerciales pertinentes.
* Annonces de projets, acquisitions, investissements, extensions de capacité ou incidents opérationnels.
* Autres sources fiables ayant un lien économique identifiable avec les sociétés étudiées.

Privilégier les sources primaires : publications des entreprises, BRVM, autorités réglementaires et organismes statistiques.

Les médias économiques et autres sources secondaires peuvent compléter ces informations.

Chaque donnée importante doit comporter, lorsque possible :

* Sa source.
* Sa date de publication.
* Sa période économique de référence.
* Sa date d’intégration dans le système.
* Son unité et sa devise.
* Son statut de vérification.
* Son niveau de fiabilité.

Distinguer impérativement la date à laquelle une information est publiée de la date de la période financière à laquelle elle se rapporte. Éviter toute fuite d’information future dans les simulations historiques.

Le moteur doit pouvoir exploiter les nouvelles données sans nécessiter une modification manuelle du code.

Si une source devient indisponible, le système doit le signaler et éviter de présenter d’anciennes données comme si elles venaient d’être actualisées.

Ne jamais inventer une donnée manquante pour compléter artificiellement un modèle.

⸻

5. DEUX MÉCANISMES OBLIGATOIRES DE MISE À JOUR

A. Actualisation périodique obligatoire

Les prévisions de toutes les sociétés doivent faire l’objet d’une révision automatique au minimum tous les trois mois.

Cette actualisation doit rechercher :

* Les nouvelles publications financières.
* Les nouvelles données sectorielles.
* Les variations des principales variables explicatives.
* Les modifications des hypothèses macroéconomiques.
* Les changements dans les prévisions des années précédentes.
* Les éventuelles dégradations de la qualité des données.

Une actualisation trimestrielle ne signifie pas que le système doit inventer un nouveau chiffre chaque trimestre. Si aucune nouvelle information pertinente n’est disponible, il doit pouvoir conserver ses estimations en indiquant leur date, leur fraîcheur et les raisons pour lesquelles elles n’ont pas changé.

B. Actualisation exceptionnelle déclenchée par un événement

Le système doit surveiller les nouvelles informations pertinentes pour chaque entreprise.

Lorsqu’un événement nouveau est susceptible de modifier le résultat net prévisionnel d’une entreprise de plus de 5 % sur au moins un exercice futur, il doit déclencher une réévaluation exceptionnelle.

Ce seuil de 5 % est un seuil initial obligatoire, mais il doit être configurable.

Le déclenchement doit reposer sur l’impact estimé, et non uniquement sur la présence de mots-clés dans un article.

Exemples :

* Une modification de réglementation affectant les tarifs d’une entreprise.
* Une nouvelle taxe ou une modification fiscale.
* Une variation majeure des prix d’une matière première.
* Une catastrophe naturelle affectant les plantations ou les installations.
* Un incendie, une fermeture d’usine ou une interruption de production.
* Une acquisition ou une cession significative.
* Une perte de contrat important.
* Une nouvelle concession ou un contrat majeur.
* Une augmentation de capital dilutive.
* Une modification importante du taux de change.
* Une décision réglementaire concernant une banque.
* Une modification des coûts d’approvisionnement.
* Une nouvelle information concernant la concurrence ou le marché adressable.

Le système doit estimer si l’événement est susceptible d’améliorer, de détériorer ou de ne pas modifier matériellement les prévisions.

Il doit également estimer l’horizon d’impact : immédiat, prochain trimestre, prochain exercice ou plusieurs exercices.

Un événement peut être temporaire, structurel, récurrent ou incertain. Le moteur doit distinguer ces situations.

Si l’impact estimé dépasse le seuil, les prévisions doivent être recalculées automatiquement, sans attendre la prochaine révision trimestrielle.

Ne pas déclencher de révision majeure sur une simple rumeur non corroborée. Si l’information est incertaine mais potentiellement importante, créer une alerte et, lorsque cela est pertinent, un scénario conditionnel.

⸻

6. QUANTIFIER L’IMPACT DES ÉVÉNEMENTS SUR LES BÉNÉFICES

Le système ne doit pas simplement signaler qu’une actualité est importante. Il doit tenter d’en quantifier les conséquences financières.

Pour chaque événement significatif, analyser :

1. Quelle variable économique est affectée ?
2. Quel est le mécanisme de transmission vers le chiffre d’affaires, les coûts ou les marges ?
3. Quelle est l’ampleur estimée de l’effet ?
4. À partir de quelle période l’effet devrait-il apparaître ?
5. Combien de temps devrait-il durer ?
6. Quels sont les effets directs et indirects ?
7. Quelles hypothèses sont nécessaires ?
8. Quel est le degré d’incertitude ?
9. Quelles autres variables pourraient compenser ou amplifier l’effet ?
10. Quelles prévisions doivent être révisées ?

Exemple illustratif : une réglementation tarifaire pourrait affecter le chiffre d’affaires d’une société de services publics.

Le moteur doit estimer l’effet en tenant compte, si les données le permettent, des volumes, de la date d’entrée en vigueur, des mécanismes de compensation, des coûts et des éventuels effets différés.

Il doit ensuite recalculer le chiffre d’affaires, les marges, le résultat net et le BPA concernés.

Il ne doit pas appliquer arbitrairement une baisse de 5 % à tous les bénéfices dès qu’un événement est détecté.

Le seuil de 5 % sert à déclencher l’analyse et la révision, pas à déterminer automatiquement l’ampleur de l’impact.

Lorsqu’une quantification fiable est impossible, le moteur doit présenter des scénarios ou une fourchette d’impact, plutôt qu’un chiffre artificiellement précis.

⸻

7. MODÈLE DE PRÉVISIONS FINANCIÈRES

Pour chaque entreprise, construire des prévisions par exercice, et par trimestre lorsque les informations disponibles le permettent.

Les horizons doivent inclure :

* Les prochains trimestres.
* Les deux prochains exercices.
* Un horizon de trois à cinq ans lorsque la visibilité et les données sont suffisantes.

Les horizons plus longs peuvent être présentés à titre exploratoire, avec une incertitude explicitement croissante. Ne pas donner l’impression qu’une prévision à dix ans est aussi fiable qu’une prévision à un an.

Pour chaque période, produire au minimum :

* Chiffre d’affaires prévisionnel.
* Croissance du chiffre d’affaires.
* Résultat net prévisionnel.
* Croissance du résultat net.
* BPA prévisionnel.
* Croissance du BPA.
* Marge nette prévisionnelle.
* Principaux facteurs explicatifs.
* Fourchette d’incertitude.
* Date de mise à jour.

Lorsque les données sont disponibles, ajouter le résultat opérationnel, l’EBITDA, les marges opérationnelles, les dépenses d’investissement et les autres indicateurs adaptés au secteur.

Pour le BPA, tenir compte du nombre d’actions et des éventuelles augmentations de capital, réductions de capital, conversions ou autres événements dilutifs.

Ne pas confondre résultat net consolidé et résultat net part du groupe. Utiliser la définition comptable cohérente avec le nombre d’actions retenu.

Toutes les unités doivent être explicites : FCFA, millions de FCFA ou milliards de FCFA, selon le contexte.

⸻

8. SCÉNARIOS ET INCERTITUDE

Pour chaque entreprise, construire au minimum trois scénarios :

* Scénario central.
* Scénario favorable.
* Scénario défavorable.

Ces scénarios doivent être construits à partir de facteurs économiques explicites, et non de simples variations arbitraires du chiffre d’affaires.

Pour une entreprise cyclique, le scénario défavorable peut notamment intégrer une baisse des prix des matières premières, des volumes inférieurs et une compression des marges.

Pour une banque, il peut intégrer une hausse du coût du risque, une croissance plus faible du crédit ou une diminution des marges d’intérêt.

Les scénarios doivent rester cohérents entre eux : les hypothèses de prix, de volumes, de coûts, de fiscalité et de marges doivent correspondre à une histoire économique plausible.

Lorsque les données le permettent, ajouter des simulations probabilistes, notamment Monte Carlo, avec des hypothèses et distributions justifiées.

Ne pas attribuer une probabilité précise à un scénario sans base empirique ou hypothèse explicite.

Afficher les fourchettes de prévisions et leurs principales sources d’incertitude.

⸻

9. MOTEUR INTELLIGENT ET AMÉLIORATION CONTINUE

Je ne veux pas un modèle figé qui applique éternellement la même formule.

Construire une architecture combinant plusieurs méthodes adaptées à la qualité des données :

* Modèles financiers fondés sur les moteurs économiques de l’entreprise.
* Séries temporelles et modèles statistiques lorsque leur utilisation est justifiée.
* Modèles de régression ou autres méthodes prédictives lorsque les données le permettent.
* Analyses sectorielles.
* Analyse structurée des événements et de leur impact financier.
* Scénarios et simulations.
* Agrégation prudente des résultats de plusieurs méthodes lorsque cela améliore les performances.

Les modèles doivent être sélectionnés selon le secteur, la qualité des données et leurs performances hors échantillon.

Ne pas utiliser systématiquement un modèle complexe si un modèle plus simple est plus fiable.

Les méthodes d’IA peuvent servir à extraire des informations des rapports, identifier des événements, classer des nouvelles et proposer des hypothèses. Mais les chiffres financiers doivent être calculés et contrôlés par des mécanismes quantitatifs explicites.

L’IA ne doit jamais inventer des chiffres financiers, des sources, des événements ou des liens de causalité.

Le moteur doit être capable d’ajuster ses modèles à partir des erreurs constatées, mais uniquement selon un processus de validation mesurable.

Il doit comparer les modèles candidats et ne retenir un nouveau modèle que si ses performances hors échantillon sont suffisamment bonnes.

Les mises à jour ne doivent pas dégrader silencieusement les performances. Conserver la version du modèle utilisée, les paramètres, les données de référence et les raisons d’un changement important.

⸻

10. HISTORIQUE DES PRÉVISIONS ET MESURE DES ERREURS

Créer dans le sous-module Prévisions une section dédiée à l’historique des prévisions.

Conserver chaque version des prévisions, avec :

* La date de production.
* L’entreprise concernée.
* L’exercice ou le trimestre visé.
* Les chiffres prévus à cette date.
* Les hypothèses utilisées.
* Les événements ayant entraîné une révision.
* Les données disponibles à la date de prévision.
* La version du modèle.
* Les chiffres réellement publiés ultérieurement.
* L’erreur de prévision constatée.

Ne jamais écraser les anciennes prévisions par les nouvelles. Chaque révision doit être conservée.

Lorsque les résultats réels sont publiés, comparer automatiquement les prévisions antérieures aux résultats réalisés.

Mesurer notamment :

* L’erreur absolue.
* L’erreur absolue en pourcentage lorsque le dénominateur est pertinent.
* Le biais de prévision : tendance à surestimer ou sous-estimer.
* La performance selon l’horizon de prévision.
* La performance par entreprise.
* La performance par secteur.
* La performance par type de modèle.
* La performance lors des périodes normales et des périodes de choc.

Pour les résultats nuls ou proches de zéro, utiliser des métriques qui ne deviennent pas artificiellement infinies.

L’interface doit permettre de comprendre ce qui a été bien anticipé, ce qui a été manqué et quelles hypothèses étaient incorrectes.

Ne pas prétendre que le moteur apprend correctement si les erreurs ne sont pas mesurées et si aucune validation empirique n’est effectuée.

⸻

11. MÉMOIRE HISTORIQUE DES ÉVÉNEMENTS

Je veux que le système exploite l’historique de chaque société depuis sa création, dans la limite des données réellement disponibles.

Constituer progressivement une base historique reliant :

* Les événements économiques.
* Les nouvelles réglementations.
* Les changements de direction.
* Les investissements et expansions.
* Les incidents opérationnels.
* Les chocs de prix.
* Les crises géopolitiques.
* Les évolutions des taux de change.
* Les variations de coûts.
* Les résultats publiés.
* Les révisions de prévisions.
* Les conséquences financières observées.

Pour chaque événement historique, conserver sa date, sa source, les entreprises et secteurs potentiellement concernés, les variables touchées et les effets financiers observés.

Lorsqu’un événement actuel ressemble à un événement historique, le moteur peut rechercher les épisodes comparables et analyser les conséquences passées.

Cependant, il ne doit pas supposer que deux événements similaires produiront nécessairement les mêmes résultats. Il doit comparer le contexte, les conditions initiales et les différences structurelles.

Il doit apprendre des épisodes précédents sans reproduire mécaniquement leurs conséquences.

Si l’historique est incomplet, l’indiquer clairement. Ne pas prétendre disposer de toutes les données depuis la création de la BRVM ou de chaque entreprise sans vérification.

⸻

12. INTERFACE UTILISATEUR

Dans QLAB, ajouter le troisième sous-module « Prévisions », en respectant le design, la navigation et les composants existants du terminal.

Pour chaque entreprise, présenter une interface professionnelle avec :

A. Synthèse des prévisions

* Chiffre d’affaires historique et prévisionnel.
* Résultat net historique et prévisionnel.
* BPA historique et prévisionnel.
* Scénarios central, favorable et défavorable.
* Fourchettes de prévisions.
* Date de la dernière mise à jour.
* Indicateur de qualité et de fraîcheur des données.

B. Graphiques

Afficher l’évolution historique et prévisionnelle des principaux indicateurs.

Distinguer visuellement les résultats réellement publiés des prévisions.

Montrer les anciennes prévisions lorsque cela est utile pour observer les révisions successives.

C. Explication des prévisions

Présenter les principaux facteurs expliquant les résultats attendus.

Pour chaque facteur important, indiquer son effet estimé sur le chiffre d’affaires, le résultat net ou le BPA, son horizon d’impact et le degré d’incertitude.

D. Journal des événements

Afficher les actualités et données qui ont déclenché une révision.

Pour chaque événement, afficher la source, la date, l’impact estimé, les hypothèses et les prévisions avant/après.

E. Historique et performances

Afficher les anciennes prévisions, les résultats réalisés et les erreurs de prévision.

Permettre de comparer les performances du moteur d’une année à l’autre et d’un secteur à l’autre.

L’interface doit rester lisible, rapide et adaptée à un terminal financier professionnel.

⸻

13. FIABILITÉ ET CONTRÔLES

Mettre en place des contrôles automatiques :

* Détection des données manquantes ou incohérentes.
* Contrôle des unités et des devises.
* Vérification de la cohérence entre chiffre d’affaires, marges, résultat net et BPA.
* Détection des doublons dans les publications.
* Contrôle des dates et périodes comptables.
* Identification des données estimées par rapport aux données publiées.
* Détection des ruptures de série et changements de périmètre de consolidation.
* Signalement des sources indisponibles.
* Détection des changements de méthodologie.
* Contrôle des hypothèses anormalement optimistes ou pessimistes.

Une donnée manquante ne doit pas être assimilée à zéro.

Une nouvelle information non vérifiée ne doit pas écraser une donnée officielle.

En cas de données insuffisantes, afficher une prévision limitée, une fourchette plus large ou un avertissement. Ne pas générer artificiellement une prévision précise pour remplir l’interface.

⸻

14. AUTOMATISATION TECHNIQUE

Le système doit fonctionner automatiquement après sa mise en place.

Prévoir des processus distincts pour :

1. La collecte des nouvelles données.
2. La détection des nouvelles publications financières.
3. La surveillance des événements significatifs.
4. L’évaluation de leur pertinence pour chaque entreprise.
5. Le calcul de leur impact potentiel.
6. La révision exceptionnelle des prévisions lorsque le seuil de matérialité est atteint.
7. La révision trimestrielle obligatoire.
8. L’enregistrement des nouvelles versions.
9. La comparaison ultérieure avec les résultats réalisés.
10. Le suivi des performances et des erreurs.

Les tâches doivent être idempotentes : une même publication traitée plusieurs fois ne doit pas produire des révisions en double.

Prévoir une journalisation des opérations, des tentatives, des erreurs et des mises à jour réussies.

Si une source est inaccessible ou si un calcul échoue, conserver les dernières prévisions valides en indiquant qu’elles n’ont pas pu être actualisées.

Les actualisations doivent être déclenchées par des événements ou des tâches planifiées, et non par la seule ouverture de la page par l’utilisateur.

L’automatisation doit être compatible avec l’infrastructure existante du terminal et tenir compte de ses limites de calcul, de stockage, de quotas et de coûts.

Ne pas introduire une dépendance payante à un fournisseur d’IA ou de données sans la signaler et la justifier.

Ne pas supposer que le code actuellement déployé possède déjà un système de base de données, un moteur de tâches en arrière-plan ou des sources de données fiables. Inspecter l’existant avant de choisir la solution.

⸻

15. ARCHITECTURE ET PROTECTION DU CODE

Avant de coder :

* Inspecter l’organisation actuelle du projet.
* Identifier les composants et services de QLAB.
* Identifier les sources de données existantes.
* Identifier les tâches automatiques existantes.
* Vérifier le fonctionnement du terminal et les dépendances.
* Identifier les éventuelles limites de l’infrastructure.

Créer une architecture modulaire séparant la collecte des données, le traitement des événements, les modèles financiers, les calculs, l’historique et l’interface.

Ne pas dupliquer inutilement les données déjà disponibles dans le projet.

Conserver les calculs sensibles côté serveur lorsque l’architecture le permet. Ne jamais exposer de clés secrètes dans le navigateur ou dans le dépôt public.

Si des tables ou des migrations de base de données sont nécessaires, les documenter et préserver les données existantes.

Ne pas réécrire l’ensemble du terminal pour ajouter cette fonctionnalité.

Ne pas modifier les autres modules de QLAB sauf lorsqu’une intégration est indispensable et explicitement justifiée.

⸻

16. MÉTHODE DE DÉVELOPPEMENT

Ne code pas tout le module en une seule opération.

Procède par étapes :

Étape 1 — Audit

Analyse l’architecture existante et indique précisément les composants réutilisables, les données disponibles, les manques techniques et les risques d’intégration.

Étape 2 — Conception

Propose l’architecture du sous-module, les modèles sectoriels, les sources de données, les règles d’actualisation et les structures de stockage.

Étape 3 — Modèle initial

Développe un premier moteur fiable sur un périmètre limité, avec des tests, avant de généraliser à toutes les sociétés.

Étape 4 — Automatisation

Ajoute les actualisations trimestrielles, les déclenchements exceptionnels et le journal des événements.

Étape 5 — Historique et validation

Ajoute le suivi des prévisions, la comparaison aux résultats réalisés et les métriques d’erreur.

Étape 6 — Généralisation

Étends progressivement les modèles aux autres sociétés et secteurs, selon la disponibilité des données.

À chaque étape, fournis un bilan des changements, les tests réalisés, les problèmes restants et les éventuelles dépenses nécessaires.

Ne déclare pas une fonctionnalité terminée tant qu’elle n’a pas été réellement implémentée et testée.

⸻

17. CRITÈRES D’ACCEPTATION

Le module sera considéré comme correctement réalisé lorsque :

* Le sous-module Prévisions apparaît dans QLAB sans casser les fonctionnalités existantes.
* Les prévisions reposent sur des données identifiables et des hypothèses explicites.
* Les modèles sont adaptés aux secteurs et aux entreprises.
* Les rapports trimestriels et annuels sont intégrés lorsqu’ils sont disponibles.
* Une révision trimestrielle automatique est prévue et testée.
* Un événement matériel peut déclencher une révision exceptionnelle.
* Le seuil initial de 5 % du résultat net prévisionnel est appliqué selon une méthodologie documentée.
* Chaque révision conserve son historique.
* Les résultats réels sont comparés aux prévisions antérieures.
* Les erreurs et biais sont mesurés.
* Les limites des données et les incertitudes sont visibles.
* Les tâches automatiques peuvent être surveillées et leurs échecs détectés.
* Les autres fonctionnalités du terminal restent opérationnelles.
* Le coût et les dépendances de l’architecture sont documentés.

Le résultat attendu n’est pas un simple graphique de croissance ni une IA qui invente des chiffres. C’est un moteur de prévisions financières dynamique, traçable, sectoriel et continuellement évalué, capable de réviser ses estimations lorsque de nouvelles informations économiques pertinentes apparaissent.

Priorité absolue : la qualité des prévisions, la traçabilité des données, la capacité à expliquer les révisions et la mesure réelle des erreurs. La complexité algorithmique ne doit jamais être confondue avec la fiabilité.
