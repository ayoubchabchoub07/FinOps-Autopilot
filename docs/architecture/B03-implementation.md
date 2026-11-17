# B03 — Contrats et adaptateurs RAW : plan et journal

Date : 2026-11-17. Spec : `FINOPS_IMPLEMENTATION_PLAN.md`, §5 et B03.
Autorisation explicite d'exécuter B03 reçue. Exécution inline avec tests d'abord.
Le plan directeur autorisé fixe le design ; aucune nouvelle approbation de ce
périmètre n'est déduite pour B04 ou AWS.

## Préparation et décisions locales

- Base propre : `d306307`, 82 fichiers suivis sauvegardés avec hashes dans
  `.local/backups/B03-preimplementation/`. Baseline : 20 tests + 15 sous-tests PASS.
- Branche locale `batch/b03-raw-contracts`, checkout existant conservé pour les
  dépendances installées et les artefacts ignorés ; aucune réinitialisation.
- Ruling : réutiliser B02 tel quel. Un manifeste B02 valide fournit les CSV de
  coûts ; les labels restent archivés séparément et jamais collectés comme coûts.
- Ruling : aucun dataset réel ACCEPTED en B02 ; `PublicDatasetAdapter` est
  utilisable avec une fixture locale de forme FOCUS explicitement artificielle.
  Les trois interfaces AWS ne lisent que des fixtures déclarées, aucun SDK/réseau.
- Ruling : G02 matérialisé, non approuvé pour AWS : coût unblended synthétique,
  BilledCost public de démonstration, unblended CUR simulé, allocated_estimate
  OpenCost séparé. USD obligatoire en démo, aucun FX implicite ni mélange de bases.
- Ruling : RAW conserve les octets originaux et leur manifeste source. Métadonnées
  d'ingestion en sidecar : source, fichier, run, heure UTC réelle, hash, rôle,
  version de contrat. Les lignes CLEAN et la déduplication métier restent B04.
- Ruling : objets RAW identifiés par hash + profil + partition + base/devise.
  Réimporter un objet identique réutilise son manifeste initial, même si renommé.
  Un changement d'octets crée une révision ; aucun overwrite. Un dossier incomplet
  ou altéré est refusé explicitement, sans réparation destructrice automatique.

## Tâches et interfaces

1. Contrats versionnés des sept datasets §5 : `data/contracts/`, documentation
   détaillée et validation des valeurs/types/clés. Tests de schémas, crédits,
   manquants, dates UTC, devises, bases et non-facturation OpenCost.
2. Adaptateurs locaux : `collect()`, `validate_manifest()`, `write_raw(root)`.
   Validation de manifestes/hashes/profils, fixtures autorisées, rejets explicites.
3. Stockage immuable et CLI : `data/adapters/`, manifeste comme marqueur de
   complétude ; tests de replay, altération, chemin échappant à la source,
   absence de réseau, conservation d'octets, séparation labels/coûts.
4. Intégration tests/lint B01, runbook, ADR-003 et preuves B03 ; revue finale.

Pre-flight : les champs synthétiques sont déjà en UTC/USD et base unblended ;
les coûts manquants restent absents. Les profils natifs des fixtures sont validés
sans prétendre produire CLEAN ni supporter tous les exports fournisseur.
Le catalogue §5 décrit des contrats futurs ; aucun producteur ML/KPI n'est créé.

## Journal d'exécution

- Préparation : terminée, baseline et sauvegarde vérifiées.
- Contrats, adaptateurs et stockage : terminés ; 45 tests B03 et 20 tests Python
  préexistants passent, plus 15 sous-tests B02 et 4 tests React.
- Revue indépendante : deux corrections intégrées, fixtures stables au checkout
  Windows et contrôle `zero_observed` natif. Test de défaut observé puis corrigé.
- Isolation des tests : nouveaux tests dans `data/tests/b03/` sans `__init__.py`,
  pour conserver la découverte unittest B02 sans dépendance pytest. Vérifié avec
  `python -S -m unittest discover -s data/tests -v` : 12 tests PASS.
- Contrôles finaux, replay CLI, préservation et limites : [rapport B03](../evidence/B03.md).
