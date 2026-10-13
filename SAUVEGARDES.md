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
