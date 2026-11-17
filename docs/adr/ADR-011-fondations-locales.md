# ADR-011 — Intégration locale B01 après B02

- Statut : **PROPOSED** ; choix locaux mis en œuvre dans le périmètre autorisé.
- Date : 2026-11-16.
- Approbateur de la décision définitive : utilisateur, validation non enregistrée.
- Autorisation d'exécution : correction B01 et vérification B02 demandées par l'utilisateur.
- Gates G01–G09 : inchangés ; notamment G06 ne détermine pas la topologie locale.

## Contexte et options

B02 existe déjà dans `data/` avec des preuves et des artefacts non committés.
Le déplacer ou le réécrire introduirait un risque sans bénéfice : le chemin
correspond au monorepo prévu. L'option retenue localement ajoute `backend/`,
`frontend/`, `grafana/` et `scripts/` et collecte les tests B02 depuis la racine.
L'archive préalable conserve aussi les fichiers ignorés générés par B02.

## Proposition mise en œuvre

FastAPI expose uniquement les deux routes de santé. React/Vite/TypeScript affiche
l'état local et le lien Grafana. nginx sert React et relaie `/api/` et `/grafana/`.
Python 3.13 et Node 22 sont verrouillés avec uv/npm ; compatibilité des futurs
outils PySpark/ML à évaluer dans leurs batches, sans l'inventer ici.

Compose isole API/Grafana sur un réseau interne. nginx rejoint aussi un réseau
bridge d'entrée et publie seulement `127.0.0.1:18000`. Le réseau entièrement
interne essayé initialement empêchait l'accès depuis l'hôte malgré des sondes
saines. Cette séparation suit l'exemple frontend/backend de la
[documentation Docker](https://docs.docker.com/engine/network/).
Le proxy peut sortir par son réseau d'entrée ; ce n'est pas un pare-feu d'egress.
La plateforme n'initialise aucun client AWS.

Grafana reçoit un secret de fichier généré localement, jamais versionné.
Sous Linux, le répertoire privé 0700 protège l'accès sur l'hôte ; le fichier 0644
reste lisible dans le conteneur sous UID 472, car Compose ne remappe pas le
propriétaire de ce montage. Sous Windows, les ACL du profil hôte s'appliquent.
Le volume Grafana persiste lors de `down`, et le secret existant n'est jamais remplacé.

L'override npm `@typescript-eslint/typescript-estree > minimatch=11.0.1`
corrige l'avis [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249).
Lint/types/tests/build ont été exécutés avec ce verrouillage ; conserver le lock
et réexaminer l'override lors d'une mise à jour du parent. Aucun audit npm n'est
assimilé à une garantie générale de sécurité.

## Alternatives et impacts

Recréation du dépôt et déplacement B02 écartés pour préserver les fichiers.
Publication directe de Grafana/API et écoute sur toutes les interfaces écartées.
Le port 8080 essayé a été refusé par Windows ; 18000 a été vérifié réellement.
Un mot de passe hardcodé et l'accès anonyme Grafana sont exclus.
Le lint B02 historique n'est pas ajouté rétroactivement ; ses tests sont intégrés.

## Décisions restant ouvertes

La matrice Python des batches data/ML et la topologie cloud demeurent à valider
dans les lots concernés. La CI est configurée sur `pull_request` mais son
déclenchement réel reste à observer lors d'une publication/PR autorisée séparément.
Ces limites empêchent un PASS global B01, sans bloquer les contrôles locaux.
Aucune décision G01–G09 ni autorisation AWS n'est déduite de cet ADR.

Preuves : [B01](../evidence/B01.md), [plan d'intégration](../architecture/B01-implementation.md),
[runbook](../operations/local-runbook.md).
