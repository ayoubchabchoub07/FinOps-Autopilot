# B02 — Plan d'exécution local

Date : 2026-11-16. Spécification approuvée : `FINOPS_IMPLEMENTATION_PLAN.md`, B02.
La demande utilisateur autorise explicitement B02 ; B01 reste TODO. Ce travail
ne crée ni application, ni Compose, ni CI, ni adaptateur RAW B03.

## Choix d'exécution

Utiliser Python et sa bibliothèque standard, avec `unittest` : aucune installation
ni dépendance externe, donc pas de verrou de dépendances à inventer. Le checkout
contient les livrables B00 non commités ; les préserver et travailler sur les seuls
fichiers B02, sans commit automatique. L'intégration au monorepo B01 reste à faire.

Le repli synthétique est déjà prévu par D03/D04 et G01. Les sources publiques
sont auditées avant sélection ; aucune source n'est acceptée pour un usage non démontré.

## Livrables et contrôles

1. `data/audit/public_sources.py` : URLs HTTPS publiques épinglées à des commits,
   téléchargement borné et explicite, SHA-256, profils CSV et preuves de licence.
   `docs/evidence/B02-public-sources.json` conserve les mesures, sans republier les CSV.
   Auditer FOCUS, Microsoft FinOps Toolkit, Google Borg et le Sandbox FOCUS
   (ce dernier partage la source FOCUS et ne vaut pas validation indépendante).
2. `data/generators/synthetic.py` et `demo_config.json` : coûts quotidiens USD
   sur 12 mois calendaires, deux comptes de démonstration et trois services,
   tendance, cycle hebdomadaire, changement de régime, bruit, crédits, valeurs
   manquantes et pics étiquetés. Nombres décimaux exacts et tirages SHA-256 par
   date/série ; aucune donnée réelle ni prix AWS implicite.
3. Séparer chronologiquement 60 % / 20 % / reste des jours en train/validation/test.
   Utiliser une seed distincte pour le test synthétique réservé. Ce jeu reste
   issu du même simulateur : il n'est PAS une validation externe indépendante.
   Conserver les labels et montants de référence dans des fichiers séparés des
   observations. Aucun feature engineering ou entraînement en B02.
4. `dataset_manifest.json` : origine synthetic/DEMO, version du générateur,
   configuration, schéma, référence temporelle déclarée, licence explicite pour
   les seules données synthétiques, SHA-256 et volumes par fichier/split.
   Refuser un dossier de sortie non vide pour préserver les données existantes.
5. `data/tests/` : écrire et exécuter les tests avant le code ; prouver reproduction,
   calendrier y compris année bissextile, séparation des partitions/labels,
   traçabilité des injections, valeurs manquantes distinctes de zéro, crédits,
   rejet des paramètres invalides et non-écrasement. Profils publics vérifiés sur
   petits exemples contrôlés, sans accès réseau dans les tests.
6. Audit public et stratégie dans `docs/data-contracts/`, mise à jour de G01
   sans approbation inventée, README exécutable et compte rendu `docs/evidence/B02.md`.

## Revue attendue

Vérifier les risques : données tronquées prises pour complètes ; absence prise
pour zéro ; mélange des devises ; fuite des labels dans les observations ; jeu
de test utilisé pour régler des paramètres ; horodatage ou ordre non déterministe ;
écrasement d'une sortie ; licence du code supposée couvrir une source non vérifiée.

Exécuter `python -m unittest discover -s data/tests -v`, deux générations avec la
même configuration et comparaison indépendante des hashes, puis `git diff --check`.
Les commandes et résultats observés seront consignés dans B02.md.
