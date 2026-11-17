# B01 — Fondations locales intégrées à B02

Autorisation : demande utilisateur de corriger l'ordre en implémentant B01,
sans modifier le code B02 ni commencer B03. Plan directeur relu intégralement.

## Préservation et état initial

HEAD `8b9a9cb40faf8617a3a7174e92895543a5c7d03b`, branche `main`, seul README suivi.
README modifié et livrables B00/B02 non suivis. Pas de code B01 préexistant ni PDF.
Avant toute édition : archive vérifiée de 66 fichiers dans
`.local/backups/B01-preimplementation/workspace.zip`, manifest SHA-256, état Git
et diff sauvegardés à côté. Suite B02 initiale : 12 tests réussis.
Aucune restructuration nécessaire : `data/` correspond déjà au monorepo cible.

## Architecture locale retenue pour l'exécution

- FastAPI : uniquement `/health/live` et `/health/ready`. La readiness valide
  le cycle de démarrage et la configuration locale ; aucune dépendance AWS,
  dataset ou modèle nécessaire. Configuration cloud refusée par readiness.
- React/Vite/TypeScript : page d'accueil indiquant l'état de l'API, erreurs et
  relance, lien Grafana ; aucun KPI, contrat RAW, chat ou parcours B07.
- Vite sert le développement local et relaie `/api/health/*` vers FastAPI.
  En Compose, l'image frontend sert les fichiers compilés via nginx et le même
  préfixe API. Grafana est accessible via `/grafana/`, avec authentification.
- Seul le frontend est publié sur `127.0.0.1:18000` par défaut ; API et Grafana
  restent sur le réseau Compose. Aucun port administrateur ouvert au LAN.
  nginx rejoint également un bridge d'entrée pour rendre la publication accessible
  depuis l'hôte ; API et Grafana restent exclusivement sur le réseau interne.
- Grafana OSS : mot de passe local aléatoire conservé dans un fichier ignoré,
  transmis par secret Compose ; aucune valeur secrète dans Git ou dans l'image.
  Volume nommé persistant ; `down` ne supprime pas les volumes.
- Python : environnement uv verrouillé partagé avec pytest et Ruff. Pytest
  collecte `backend/tests` et les tests B02 existants sans les réécrire.
  Le formatage automatique s'applique au nouveau code, pas aux sources B02 gelées.
- npm : versions exactes et lockfile ; ESLint, TypeScript, Vitest/Testing Library,
  Prettier et build Vite. Scripts PowerShell et lanceur Python commun.
- GitHub Actions : événement pull_request, commandes locales et test Compose,
  permissions lecture seule, sans identifiants AWS ni déploiement.

Les choix locaux sont réversibles et consignés dans ADR-011 au statut PROPOSED.
G01–G09 ne sont pas résolus par ce batch. La topologie cloud reste hors périmètre.

## Séquence et preuves attendues

1. Sauvegarde + tests B02 avant changement (faits).
2. Tests API puis implémentation du cycle de santé et de la configuration.
3. Tests React puis page locale et gestion explicite des erreurs.
4. Locks, images, proxy, secrets locaux et scripts compatibles Windows.
5. Workflow PR sans déploiement ; vérifier localement les commandes correspondantes.
6. Tests, lint, format, types, build ; Compose config/up et HTTP réels.
7. Contrôle SHA-256 de tous les fichiers B02 préexistants, revue et rapport B01.

Un déclenchement GitHub sur une PR ne peut pas être attesté par une exécution locale.
Sans événement PR réellement observé, ce critère reste non vérifié et B01 ne sera
pas déclaré PASS global. Aucune publication distante n'est incluse dans la demande.
