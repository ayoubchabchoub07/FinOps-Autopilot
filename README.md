# FinOps-Autopilot
A cloud cost intelligence platform on AWS  FinOps Autopilot helps teams understand, forecast, and reduce their cloud spending. It collects AWS billing data and Kubernetes usage metrics, detects anomalies, predicts future costs, and answers the question “Why are my costs going up?” in plain language.

Cette description expose l'objectif du projet. Au 16 novembre 2026, B00 et B02
sont réalisés et **B01 a été intégré après B02**, sans modifier ses sources ni
ses preuves. FastAPI, React/Vite/TypeScript, Grafana et les contrôles locaux
fonctionnent. **B01 : PARTIAL** (déclenchement réel de CI sur PR non observé) ;
**B02 : PASS** après non-régression. B03–B16 ne sont pas commencés.
Aucun déploiement AWS n'a été effectué.

## B01 — Lancer et vérifier le socle

Prérequis : Python 3.13, uv 0.12.2, Node 22 (>=22.12), npm, Docker Desktop
avec moteur Linux/Compose. Depuis la racine, sous PowerShell :

```powershell
python -m pip install uv==0.12.2
python scripts/tasks.py setup
python scripts/tasks.py dev
python scripts/tasks.py smoke
python scripts/tasks.py test
python scripts/tasks.py lint
python scripts/tasks.py format-check
python scripts/tasks.py typecheck
python scripts/tasks.py build
```

Interface : <http://127.0.0.1:18000/> ; Grafana :
<http://127.0.0.1:18000/grafana/>. Compte `finops-local`, mot de passe généré dans
le fichier privé ignoré `.local/secrets/grafana-admin-password`.
`setup` et `dev` préservent la configuration et le secret existants.
Arrêt sans supprimer les volumes : `python scripts/tasks.py down`.
Des wrappers PowerShell équivalents sont fournis dans `scripts/`.

- [Runbook local et contrat de readiness](docs/operations/local-runbook.md).
- [Preuves B01, résultats et fichiers livrés](docs/evidence/B01.md).
- [Choix locaux et décisions ouvertes — ADR-011](docs/adr/ADR-011-fondations-locales.md).

## B02 — Générer et vérifier les données locales

Python standard uniquement, vérifié avec Python 3.13.5 ; aucune installation ni
connexion AWS nécessaire. Depuis la racine, sous PowerShell :

```powershell
python -m unittest discover -s data/tests -v
python -m data.generators.synthetic --config data/generators/demo_config.json --output data/generated/my-demo
Get-Content data/generated/my-demo/dataset_manifest.json -Encoding UTF8
```

Le dossier de sortie doit être nouveau. Résultat de l'exemple : 2 190 observations
`synthetic`/`DEMO` sur 12 mois, trois partitions chronologiques avec labels séparés
et manifeste SHA-256. Le test utilise une seed distincte mais reste synthétique :
**aucune validation externe réelle n'est disponible** pour les sources auditées.
Les données générées et téléchargements tiers sont ignorés par Git.

- [Audit public et verdicts](docs/data-contracts/public_dataset_audit.md).
- [Stratégie synthétique et contrat B02](docs/data-contracts/synthetic_strategy.md).
- [Preuves et compte rendu B02](docs/evidence/B02.md).

Pour refaire l'audit public (accès HTTPS nécessaire ; objets limités à 2 Mo,
URLs et commits épinglés, aucun appel AWS/BigQuery) :

```powershell
python -m data.audit.public_sources --audit-date 2026-11-16 --output docs/evidence/B02-public-sources.json
```

Adapter `--audit-date` à la date de la nouvelle inspection. Cette commande
remplace le rapport désigné ; les profils ne constituent pas une approbation G01.

## Documents de référence

- [Plan directeur](FINOPS_IMPLEMENTATION_PLAN.md) : exigences et batches.
- [État réel du dépôt](docs/architecture/current-state.md) : inventaire, environnement et blocages.
- [Registre des ADR](docs/adr/README.md) : D01–D15 et gates G01–G09.
- [Preuves B00](docs/evidence/B00.md) et [résultats des sondes locales](docs/evidence/B00-environment.json).
- [Configuration d'exemple](.env.example) : paramètres locaux consommés par Compose et champs réservés aux batches suivants.

Les deux PDF cités dans le plan sont absents du dépôt ; aucune lecture de leur
contenu original n'est revendiquée. Le plan fourni est la source de cadrage disponible.

## Examiner le dépôt sous Windows

Depuis la racine du dépôt, dans PowerShell :

```powershell
Get-Content -LiteralPath 'docs/architecture/current-state.md' -Encoding UTF8
git status --short --branch
git log --all --oneline
git diff --check
python --version
node --version
npm.cmd --version
docker --version
docker compose version
docker version
wsl --version
wsl --status
wsl --list --verbose
```

Ces commandes inspectent l'environnement ; elles ne démarrent pas la plateforme.
Le moteur Docker, indisponible lors de B00, a été démarré et utilisé pour les tests
B01. Les preuves historiques B00 restent conservées. Python 3.13 est vérifié
pour B01/B02 ; la compatibilité PySpark/ML reste à examiner dans les lots concernés.
`npm.cmd` évite de dépendre de la politique d'exécution du wrapper `npm.ps1`.

Le générateur B02 continue de lire son JSON de configuration, pas `.env`.
Les sorties de datasets, caches, sauvegardes, secrets et environnements locaux
sont ignorés par Git. Les fichiers B02 sont intégrés aux tests depuis leur
emplacement d'origine ; ils n'ont pas été déplacés ou réécrits.

CloudFormation reste l'IaC approuvée. Aucun template cloud ni workflow de
déploiement n'est ajouté par B01. AWS exige les gates du plan et une autorisation
explicite. B03 et les batches suivants attendent également cette autorisation.
