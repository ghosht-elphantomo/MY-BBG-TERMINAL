# Points de restauration

Chaque version du terminal reste dans l'historique du dépôt (la branche main n'est jamais réécrite).
Un point de restauration est noté ici avant chaque modification importante. Pour revenir en arrière :
demander « reviens au point de restauration du … » ; le code de ce point est remis en place par un nouveau commit
(rien n'est effacé, on peut donc aussi annuler le retour). Le site publié peut aussi être remis instantanément
à une version précédente depuis le tableau de bord Vercel (Deployments → Promote / Instant Rollback).

| Date (Paris) | Point | Code (main) | Site publié (branche site) |
|---|---|---|---|
| 13/10/2026 matin | Avant les modifications de la journée | `1fa9307b3358e3554d6164e1adc4cf6af01c866c` | — |
| 13/10/2026 17 h 30 | Avant le retour du libellé « MAJ … GMT » | `f60e34a99b86a6f6d18820342759fb670e0f0551` | `d554488d00a08eddf059b1d486049934efd7c63f` |
| 13/10/2026 17 h 45 | Avant le passage des fondamentaux BRVM aux sources officielles (bulletins, états financiers, brvm.org) | `2b02b603df86481d8f4102baeec5b25168380032` | `242be614e62156ba4fcd053e8768be382ce62545` |
| 13/10/2026 18 h 00 | Avant le regroupement des écrans en double : CF dans EVTS, WCRS dans FX, WB dans RATES (ex-WIRP), EQS renommé SCREN | `b530ef2a350c393a128fc7e3f90dc7727a4769d7` | `18f930c6cd316d087e5daca558e507832edfa12a` |
| 13/10/2026 18 h 15 | Avant le déplacement du classement des devises de FX vers FXC et la mise à jour de HELP | `b6c5fa071ee62e820f6fe4d958043e626a8bbf56` | `35da078f0ae558cddcdb26f9835cc9246c795b03` |
| 13/10/2026 18 h 20 | Avant le retrait de la touche TOP (écran renommé NEWS) | `840afad90721c1224de4843e5f2009f7c20bb515` | `35da078f0ae558cddcdb26f9835cc9246c795b03` |
| 13/10/2026 18 h 25 | Avant le retrait de la touche MON (écran renommé MONITOR, touche placée en premier) | `cf363916bb73890ebdc8b2211eeef10d7b73946d` | `feb30b29ca036637ebe98a916d45a385153046d6` |
| 13/10/2026 18 h 30 | Avant le renommage de GLCO en COMMO | `f02ad6691b0f5d6df9bc43724ac94c94ffade2ab` | `feb30b29ca036637ebe98a916d45a385153046d6` |
| 13/10/2026 18 h 30 | Avant la mise à jour automatique des pages ouvertes, la garde contre la republication d'un site plus ancien et la lecture des avis sur brvm.org | `0723e6acdffec4654db40ef8f649ff2fccdb29e7` | `6d0c64ea6fc518b955778e8b6af13a856a5142c3` |
| 13/10/2026 18 h 50 | Avant l'arrêt des publications « aperçu » de la branche site sur Vercel (vercel.json : "site": false) | `258ab64f779aa84875e61e0d0560af7e7f0127e1` | `fc271f4437d1417c63adaa182255a69cb7f4f62b` |
| 13/10/2026 19 h 05 | Avant le regroupement de BTMM, WIRP et WB dans RATES (onglets : marché monétaire, Fed, BONDS) | `e8b640d15f5b49ecd349d7bf9b130e84d7989d8c` | `a3023a41c82da4316dcf4b2b3b4a4f6bc1df15eb` |
| 13/10/2026 22 h 25 | Avant : avis d'un même document réunis en une ligne, MONITOR sans colonnes cachées, ECO, fichier eco_lite, alias d'actualités | `6001f989dafe53d335df3a8e4ec351e585f7161d` | `b85bbf3cfdff19fe446bbdf2c6df7ec79b0d05ff` |
| 13/10/2026 22 h 55 | Avant : capitalisations US unifiées (fractionnements, ADR), montants officiels BRVM, mises en page FA/RV | `0ff9e279d5788e2e595e56005a0a435def131710` | `efeeb31268e3bc8a1da51d956ee47deccf48f1e3` |
| 13/10/2026 22 h 45 | Avant le déplacement des objectifs des analystes US de EVTS vers EA (doublon) | `a4add8b93210866cf80c9549d20f4b6a2ee99768` | `efeeb31268e3bc8a1da51d956ee47deccf48f1e3` |
| 14/10/2026 09 h 30 | Avant : dividendes d'après les avis officiels lus dans les PDF (rectificatifs compris), retrait du contrôle par le calendrier | `3fdabbc4627b8deed913fc3f62798804834d179f` | `87d76c1096abb5467fbfdd045ecb89a77d3973eb` |
| 15/10/2026 14 h 30 | Avant l'audit de sécurité, le flottant officiel, STOCK BONDS, BTST dividendes réinvestis, NOT et SGI | `823c9534a7646909de5481face94097c070921e4` | `87d76c1096abb5467fbfdd045ecb89a77d3973eb` |
