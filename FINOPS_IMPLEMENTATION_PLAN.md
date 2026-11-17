# FINOPS_IMPLEMENTATION_PLAN.md

> **FinOps Autopilot — Plan directeur d'implémentation pour Codex**  
> Version : `1.0` — 11 novembre 2026  
> Statut : **B00, B02 et B03 PASS ; B01 PARTIAL (local vérifié, CI sur PR non observée) ; B04–B16 non commencés**
> Langue des rapports, tickets et documentations : français ; noms techniques, code, API et tests : anglais.  
> **Instruction importante :** ce fichier est une spécification d'exécution. Il ne constitue pas la preuve qu'une fonctionnalité est déjà implémentée.

## 0. Instructions impératives pour Codex

Tu es l'agent d'implémentation du projet académique **FinOps Autopilot**. Lis **entièrement** ce fichier, les PDF de référence s'ils sont présents, puis inspecte le dépôt avant de modifier quoi que ce soit.

### 0.1. Règles non négociables

1. **Ne pas remplacer CloudFormation par Terraform.** Aucun workflow de déploiement Terraform, aucun `terraform apply`, aucun générateur de Terraform. AWS CloudFormation (YAML) est l'IaC approuvée ; `cfn-lint`, `cfn-guard` et **Change Sets** sont les contrôles associés.
2. **Développement local d'abord**, intégration AWS sur autorisation ; les services de calcul AWS seront activés à la demande. Ne crée aucune ressource facturable, ne lance aucun job SageMaker/Glue/ECS/Bedrock, n'exécute aucun Change Set ni aucune suppression AWS sans approbation explicite de l'utilisateur et sans revue des coûts prévisionnels.
3. **Aucune modification AWS automatique proposée par un LLM.** Un futur agent peut préparer une PR et un Change Set, mais l'exécution nécessite une approbation humaine distincte. V1 : interdiction des actions destructives (notamment suppression de volumes EBS) et des modifications de ressources non gérées par le mécanisme IaC autorisé.
4. **Ne pas inventer de dataset, de benchmark, de modèle validé, de métrique, de coût AWS réel, de résultat de test, de performance ni d'autorisation.** Tout résultat artificiel est explicitement marqué `synthetic`/`demo`; toute validation sur données réelles est justifiée par l'origine du dataset.
5. **Ne pas confondre AWS CUR facturé et coûts OpenCost alloués.** Ne jamais additionner directement ces deux valeurs dans un KPI de dépense totale.
6. **Séparer travaux et livrables.** À chaque batch : créer le code, les tests, la documentation de lancement, puis exécuter localement les contrôles disponibles ; rapporter ce qui fonctionne réellement, ce qui échoue et les dépendances manquantes.
7. **Ne pas s'arrêter à un plan générique.** Exécute uniquement le batch demandé par l'utilisateur ; si le dépôt est vide, commence par B00/B01. N'implémente pas silencieusement les batches suivants.
8. **Ne jamais bloquer l'avancement local** à cause d'une décision AWS future. Utilise des interfaces/configurations/mocks explicites et ouvre un point de décision (ADR). En revanche, bloque l'action concernée lorsque l'autorisation ou la donnée est essentielle.
9. **Sécurité par défaut :** pas de secrets dans le repo ; permissions IAM minimales ; aucune requête Athena produite par le LLM sans contrôles ; aucun endpoint ou dashboard administratif exposé sans protection.
10. Conserve la traçabilité des décisions (`docs/adr/`), des contrats (`docs/data-contracts/`), des exécutions et des tests (`docs/evidence/`).

### 0.2. Compte rendu obligatoire après chaque batch

Utiliser la forme :

```text
BATCH: Bxx - <titre>
STATUS: PASS | PARTIAL | BLOCKED
CHANGES: chemins de fichiers créés/modifiés
TESTS: commandes exactes + résultats observés
DELIVERABLES: fichiers + mode d'exécution
DECISIONS: ADR approuvées / propositions en attente
RISKS: sécurité, coût, dépendances, limites
NEXT: prochain batch autorisé, sans l'exécuter
```

Ne jamais déclarer `PASS` si les tests obligatoires ou le critère de sortie n'ont pas été démontrés.

---

## 1. Sources et provenance des exigences

### 1.1. Documents utilisateur

- **`FinOps Autopilot Period 2 Project Spec.pdf`** — 6 pages. Référence de périmètre : pipeline S3/Glue/Athena, modèles ML SageMaker, architecture cloud, assistant Bedrock, extension d'optimisation et données.
- **`FinOps_Autopilot_FR.pdf`** — 14 slides. Référence des schémas : architecture globale (slide 4), pipeline (5), zones RAW/CLEAN/CURATED (6), ML/MLOps (8–9), assistant Bedrock (10), sécurité (11), agent GitOps (12), livrables (13).

### 1.2. Décisions explicitement validées lors des huit parties

| ID | Décision validée | Impact de mise en œuvre |
|---|---|---|
| D01 | Plateforme principale d'abord, agent d'optimisation ensuite | Aucun automatisme GitOps tant que le cœur n'est pas validé |
| D02 | **AWS CloudFormation remplace Terraform** | Toutes les stacks, change sets et processus de PR sont en CloudFormation |
| D03 | ML : entraînement sur données synthétiques ou publiques **si adaptées et gratuites** | Priorité à l'audit de datasets ; générateur synthétique reproductible en secours |
| D04 | Validation externe sur données publiques indépendantes **si compatibles** | Rapporter honnêtement les limites si aucune validation externe faisable |
| D05 | Données AWS réelles à la fin, lors du déploiement | Contrats et adaptateurs conçus en amont, activation seulement dans la phase cloud |
| D06 | Data pipeline RAW → CLEAN → CURATED ; PySpark local puis Glue, S3, Athena | Transformation testable localement, même logique sur AWS |
| D07 | Orchestration AWS EventBridge + Step Functions | Exécutions batch quotidiennes, redémarrables et idempotentes |
| D08 | Forecast : baseline + Prophet + XGBoost, horizon de 30 jours | Comparaison temporelle, model selection selon métriques |
| D09 | Anomalies : résidus de prévision puis comparaison Isolation Forest | Precision/Recall/F1, résultats expliqués |
| D10 | SageMaker Training Jobs, Model Registry et batch quotidien | Aucun endpoint de prédiction permanent ; réentraînement initialement mensuel |
| D11 | Dashboard : **Grafana OSS + React + FastAPI** | Grafana pour KPIs, React pour navigation/chat, FastAPI pour API |
| D12 | Assistant : **Bedrock** avec SQL prédéfini + Text-to-SQL contrôlé | Trois outils, validation SQL rigoureuse, read-only |
| D13 | Développement local + infrastructure AWS à la demande | Docker Compose, tests hors cloud, activation et nettoyage AWS documentés |
| D14 | GitHub Actions + OIDC, IAM least privilege, Budgets, CloudWatch | Déploiement contrôlé et traçable |
| D15 | Agent **semi-automatique** : détection, risque, OPA/Guard, PR, Change Set, approbation humaine | Aucune modification effective avant validation ; pas de suppression destructrice en V1 |

### 1.3. Éléments présents dans les PDF mais **non décidés définitivement**

- Source/version/licence des données publiques et possibilité réelle de validation indépendante.
- Région et compte AWS, quotas et budget maximum de déploiement.
- Modèle Bedrock précis (les PDF citent Claude ou Llama ; comparer les modèles accessibles et compatibles avec Converse/tool use).
- Source des budgets FinOps (fichier local, table dédiée, éventuelle synchronisation AWS).
- Topologie exacte ECS (Web/API/Grafana, gestion HTTPS/authentification, ALB éventuel, DNS et réseau).
- Rapport mensuel avec RAG / Bedrock Knowledge Bases : **extension facultative dans la spec**, non validée comme livrable obligatoire pendant la discussion.

Ces points suivent la procédure `ADR` (§3), sans modifier les décisions D01–D15.

---

## 2. Objectifs, livrables et non-objectifs

### 2.1. Objectif produit

Construire une plateforme FinOps AWS permettant de :

1. Ingérer et préparer les coûts de facturation, les métriques Kubernetes et les inventaires de ressources.
2. Explorer les coûts par période, service, compte, région et équipe (si les tags sont disponibles).
3. Prévoir les coûts quotidiens à 30 jours, avec évaluation et traçabilité du modèle.
4. Identifier et expliquer les dépenses anormales.
5. Interroger les données en langage naturel par un assistant Bedrock sécurisé.
6. En extension, identifier le gaspillage et proposer des changements d'infrastructure revus par un humain.

### 2.2. Jalons de livraison

| Milestone | Contenu | Précondition |
|---|---|---|
| M0 — Foundations | Dépôt, conventions, ADR, tests, Compose minimal, contrats de données | aucune |
| M1 — Data local | Ingestion public/synthétique, RAW/CLEAN/CURATED, contrôle qualité, agrégats | M0 |
| M2 — ML local | Forecast + anomalies, backtesting, modèle et artefacts tracés | M1 |
| M3 — Application locale | Grafana OSS + React/FastAPI, KPIs, modèle et anomalies | M1, M2 |
| M4 — Assistant local/API | Outils, SQL sécurisé, mock ; intégration Bedrock approuvée | M3, accès Bedrock pour l'intégration |
| M5 — AWS Cloud Platform | Data/ML/AI/App + CI/CD, CloudFormation, test réel | M1–M4 + approbation AWS |
| M6 — Optimization Agent | Waste, risk, OPA/Guard, PR et Change Sets, tests sécurisés | M5 et jeu de cas validé |
| M7 — Defense & Documentation | Rapport, vidéo/demo/script, preuves, coûts et limites | M5 ; M6 si réalisée |

### 2.3. Non-objectifs de la V1

- Déploiement multi-cloud, multi-tenant SaaS ou optimisation autonome de production.
- Prédiction garantie sur coûts réels à partir d'un compte étudiant peu actif.
- Refonte/recréation automatique de ressources AWS existantes non gérées par CloudFormation.
- Modification de factures, suppression automatique de volumes, redimensionnement autonome en production.
- Kubernetes/EKS permanent uniquement pour héberger FastAPI/Grafana ; utiliser `kind` + OpenCost localement pour la démonstration technique.
- Prétendre à une analyse de causalité si les métriques ne fournissent que des corrélations ou décompositions.

---

## 3. Points de décision, ADR et gates obligatoires

Ne jamais inventer une réponse. Pour chaque décision ouverte, créer `docs/adr/ADR-NNN-<slug>.md` avec : contexte, options, contraintes, décision, impacts, approbateur, date, alternatives rejetées, preuve/documentation. Un ADR non approuvé reste `PROPOSED`.

| Gate | Moment | Décision / vérification requise | Default de développement tant qu'elle est ouverte |
|---|---|---|---|
| G01 | B02 | Dataset(s) publics : licence gratuite et autorisant usage académique, historique, coût comparable, granularité, provenance | Générateur synthétique, validation externe = `NOT_AVAILABLE` |
| G02 | B03 | Coût de référence (ex. unblended/non amorti) + devise et conversion FX | Tout en USD dans le jeu de test, `cost_basis` explicite, refuser mélanges |
| G03 | B06 | Suffisance des séries temporelles par service/compte ; granularité du modèle | Repli au niveau service/global, sans fuite de données |
| G04 | B10–B12 | Région AWS, compte, accès aux exports CUR 2.0, quotas et budget maximal | Aucun provisionnement ; tests locaux |
| G05 | B11 | Modèle Bedrock, droits d'accès, coût et disponibilité Converse/tool use | Mock déterministe local |
| G06 | B12 | Topologie ECS Fargate, HTTPS, AuthN/AuthZ, accès Grafana et budget réseau | Compose local ; infrastructure CloudFormation paramétrable |
| G07 | B08 | Règles et saisie budgets mensuels | Table `finops_budgets` à partir d'un fichier de config versionné sans données sensibles |
| G08 | B15 | Périmètre exact des ressources CloudFormation optimisables, politiques et approbateurs | DRY-RUN / PR sans apply ; ressources non gérées = recommandations uniquement |
| G09 | Backlog | Rapport mensuel RAG/Knowledge Bases | Facultatif, pas une condition de sortie du cœur |

### 3.1. Gate avant tout déploiement AWS

L'utilisateur doit confirmer **explicitement** : compte (sans exposer son numéro publiquement), région, plafonnement souhaité, services à lancer, coûts estimés (inclure ECS, ALB/NAT/VPC endpoints, Bedrock, SageMaker, Athena, logs), durée prévue d'activation, nettoyage/rollback. Un **AWS Budget alerte** ne représente pas un arrêt automatique ou un plafond garanti.

### 3.2. Politique d'autorisation GitOps

Deux approbations distinctes :

- Revue et fusion du code/PR ;
- Revue d'un Change Set identifié, lié à un commit immuable, puis autorisation explicite de son exécution.

Les rôles de génération de Change Set et d'exécution doivent être distincts, et les contrôles relancés si le commit, les paramètres ou la stack ont changé.

---

## 4. Architecture cible et flux

```text
SOURCES
  |-- DEV: synthetic generator + audited public datasets
  |-- AWS DEPLOY: CUR 2.0 + OpenCost/Prometheus + boto3 inventory
  v
DATA LAKE S3 (raw/, clean/, curated/, quarantine/)
  |-- Glue (PySpark shared transforms) --> Glue Data Catalog
  |-- Athena workgroups (read only for apps, dedicated query result bucket)
  |-- EventBridge Scheduler --> Step Functions --> batch ETL + checks
  v
ML (SageMaker training, Model Registry, batch inference)
  |-- forecast / anomalies / evaluation outputs -> S3 + Athena
  v
SERVING (on-demand ECS Fargate)
  |-- React UI + FastAPI backend
  |-- Grafana OSS dashboards (Athena datasource)
  |-- Bedrock Converse + approved tools
  v
EXTENSION (after core)
  |-- deterministic waste detector + savings estimator + risk score
  |-- LLM explanation (no unilateral execution)
  |-- OPA/Rego + cfn-guard --> GitHub PR --> Change Set
  `-- Human reviews --> separately authorized execute --> verify / rollback

CROSS-CUTTING: CloudFormation | GitHub Actions/OIDC | IAM | CloudWatch | Budgets
```

### 4.1. Règles d'architecture

- **Séparer** l'infrastructure (CloudFormation) du code applicatif et des données.
- Un seul jeu de **contrats de données**, plusieurs adaptateurs de sources.
- Codes de transformation communs entre PySpark local et Glue ; ne pas maintenir deux ETL divergents.
- Mécanismes de traitement **rejouables et idempotents** ; les coûts AWS peuvent être corrigés rétroactivement.
- Historique des prévisions conservé par `run_id`, `generated_at`, `target_date`, `model_version`, non écrasé par le run suivant.
- Source unique du coût réel pour le KPI global : jeu CUR normalisé, jamais `CUR + OpenCost`.
- Séparer sources `synthetic`, `public`, `aws_real` par colonnes de provenance ET espaces de travail/environnements. Les résultats locaux de démonstration restent étiquetés `DEMO`.
- Ne pas présenter le CUR comme temps réel : noter la dernière ingestion et la période de facturation connue.
- Préparer un mode `local`, un mode `aws-demo` et une configuration `aws-real` approuvée. Les secrets ne figurent dans aucun fichier de configuration versionné.

---

## 5. Contrats de données et calcul des métriques

### 5.1. Datasets logiques

**`cloud_costs` (transactionnel, source du KPI de dépense)** :

| Champ | Type logique | Remarques |
|---|---|---|
| `usage_start_time` | timestamp UTC | Date de consommation originale |
| `usage_date` | date | Jour UTC standardisé |
| `account_id` | string | Pas de déduction à partir des noms affichés |
| `service_name` | string | Mapping fournisseur -> nomenclature interne |
| `region` | string nullable | Peut être absente |
| `resource_id` | string nullable | Existant si source/granularité le permettent |
| `team` | string nullable | Déduit uniquement de tags validés |
| `cost_amount` | decimal | Montant dans la devise et base déclarées |
| `currency` | string ISO | Au départ USD uniquement pour comparaisons |
| `cost_basis` | string | `unblended`, `amortized`... **choix G02** |
| `charge_type` | string nullable | Usage, crédit, remboursement, etc. |
| `source_record_id` | string | Clé d'idempotence définie par adaptateur |
| `data_source` | enum | synthetic/public/aws_real |
| `source_file` | string | Chemin/URI source |
| `ingestion_run_id` | string | Identifiant de batch |
| `ingested_at` | timestamp UTC | Horodatage d'ingestion |

**`k8s_usage` (allocation des ressources et coûts, pas nouvelle facture)** :
`observation_time`, `cluster_id`, `namespace`, `workload`, `container`, `cpu_request_cores`, `cpu_usage_cores`, `memory_request_bytes`, `memory_usage_bytes`, `allocated_cost_amount`, `currency`, `cost_basis=allocated_estimate`, `data_source`, `run_id`, `quality_flags`.

**`resource_inventory` (snapshots)** :
`snapshot_at`, `account_id`, `region`, `resource_type`, `resource_id`, `state`, `tags`, `attachment_state`, `cloudformation_stack_id`, `metrics_coverage`, `data_source`, `run_id`. Ne pas inventer une métrique CPU, mémoire ou trafic si AWS ne l'expose pas.

**`finops_budgets`** : `period_month`, `scope_type`, `scope_id`, `budget_amount`, `currency`, `owner`, `source`, `effective_at`.

**`ml_forecast`** : `generated_at`, `target_date`, `account_id`, `service_name`, `predicted_cost`, `prediction_lower`, `prediction_upper`, `model_version`, `training_dataset_version`, `run_id`, `data_source`.

**`ml_anomalies`** : `event_id`, `usage_date`, `account_id`, `service_name`, `actual_cost`, `expected_cost`, `deviation`, `deviation_pct`, `anomaly_score`, `severity`, `model_version`, `status`, `evidence`, `run_id`.

**`optimization_recommendations`** : `recommendation_id`, `resource_id`, `resource_type`, `finding_type`, `evidence`, `current_cost_estimate`, `proposed_cost_estimate`, `expected_monthly_savings`, `risk_score`, `risk_reasons`, `policy_result`, `proposal_status`, `stack_id`, `pull_request_url`, `change_set_arn`, `approval_status`, `execution_status`.

### 5.2. Zones et partitionnement

```text
raw/cloud_costs/{synthetic,public,aws_cur}/...       # immuable, octets originaux
raw/k8s_usage/{synthetic,public,opencost}/...
raw/resource_inventory/{synthetic,aws_boto3}/...
clean/cloud_costs/year=YYYY/month=MM/part-*.parquet
clean/k8s_usage/year=YYYY/month=MM/part-*.parquet
clean/resource_inventory/year=YYYY/month=MM/part-*.parquet
curated/daily_cost_by_service/year=YYYY/month=MM/...
curated/daily_cost_by_account/year=YYYY/month=MM/...
curated/daily_cost_by_team/year=YYYY/month=MM/...
curated/daily_k8s_usage/year=YYYY/month=MM/...
curated/resource_inventory_snapshot/year=YYYY/month=MM/...
curated/finops_budgets/...
ml/features/... | ml/models/... | ml/predictions/... | ml/evaluation/...
quarantine/<dataset>/run_id=<id>/...
```

Les chemins exacts S3 sont paramétrables ; les chemins RAW CUR AWS ne doivent pas altérer la structure native exportée (manifeste et révisions). Partitionnement année/mois d'abord, à reconsidérer si le volume justifie des partitions journalières. Parquet pour CLEAN/CURATED.

### 5.3. Qualité et anti-double comptage

- Schéma validé avec versions explicites, champ source obligatoire.
- `cost_amount` peut être négatif (crédits, remboursements) et n'est donc pas rejeté par défaut.
- Tout montant doit avoir une devise ; aucune addition inter-devises sans taux daté/documenté.
- Ne pas mélanger mesures amorties et non amorties dans un même total.
- Déduplication selon clé source ; rejouer un batch ne doit jamais doubler les agrégats.
- Recalculer les partitions impactées par des révisions de facturation CUR.
- Des dates sans ligne ne valent pas automatiquement 0 ; distinguer `absence`, `zero_observed`, `missing`.
- Vérifier l'égalité `SUM(clean.cost_amount) == SUM(curated.cost_amount)` **sur une même fenêtre, même devise, même base, même périmètre**, avec règles d'arrondi documentées.
- Enregistrer en quarantine les lignes invalides avec motif, source, run_id ; produire un rapport `quality_report.json`.

### 5.4. KPI contractuels

| KPI | Formule contrôlée | Guardrail |
|---|---|---|
| MTD spend | somme des coûts facturés depuis le 1er jour du mois **jusqu'à la dernière date de coût observée** | source et coût de référence affichés |
| Forecast EOM | coûts réels acquis du mois + prévisions du reste du mois | différent du `next 30 days` |
| Budget variance | forecast EOM − budget mensuel comparable | même devise, même périmètre |
| Top services | coût par service décroissant | ne pas additionner namespaces OpenCost |
| Anomaly count | nombre d'événements distincts à statut ouvert | déduplication des alertes |
| CPU request utilization | CPU utilisé / CPU demandé sur fenêtre définie | CPU=0 ou métriques manquantes -> `N/A` |
| Potential savings | coût mensuel actuel estimé − coût mensuel proposé estimé | estimation, pas économie réalisée |

Pour les économies, conserver la convention `estimated_current_cost - estimated_proposed_cost` et documenter remises, réservations et frais de migration avant de qualifier une estimation de réaliste.

---

## 6. Structure cible du dépôt

```text
finops-autopilot/
  FINOPS_IMPLEMENTATION_PLAN.md
  README.md
  .env.example
  .gitignore
  pyproject.toml                    # outillage Python partagé, si pertinent
  Makefile | scripts/               # commandes de dev documentées, compatibles Windows
  docker-compose.yml
  backend/
    app/{api,core,auth,models,services,providers,tools}/
    tests/
    Dockerfile
  frontend/
    src/{pages,components,api,types}/
    tests/
    Dockerfile
  grafana/
    provisioning/{datasources,dashboards}/
    dashboards/
    Dockerfile
  data/
    contracts/
    adapters/{synthetic,public,aws_cur,opencost,inventory}/
    generators/
    etl/{raw_to_clean,clean_to_curated}/
    quality/
    tests/
  ml/
    features/
    forecasting/{baseline,prophet,xgboost}/
    anomalies/
    backtesting/
    training/
    inference/
    tests/
  agent/
    detection/
    pricing/
    risk/
    policies/opa/
    proposals/
    tests/
  infrastructure/
    cloudformation/{foundation,data,pipeline,ml,ai,app}.yaml
    parameters/{dev,demo}.example.json
    guard/
    README.md
  .github/workflows/{ci,preview-infra,deploy-manual}.yml
  docs/
    adr/
    architecture/
    data-contracts/
    evidence/
    operations/{local-runbook,aws-runbook,cleanup,rollback}.md
    security/
    ml-evaluation/
    demo/
  tests/{integration,e2e,security}/
```

Créer les dossiers au fil des batches, pas des coquilles vides pour simuler l'achèvement. Utiliser un gestionnaire Python reproductible (`uv` ou `pip` locké) et `npm` lockfile. Sous Windows, documenter PowerShell et Docker Desktop/WSL2. Fixer les versions de dépendances importantes dans les fichiers de lock.

---

## 7. Carte des dépendances entre batches

```text
B00 --> B01 --> B02 --> B03 --> B04 --> B05 --> B06 --> B07
                                              |            |
                                              +-----+------+----> B08 --> B09
                                                               |
                                                               v
                                                        B10 --> B11 --> B12 --> B13
                                                                         |
                                                                         v
                                                                B14 --> B15 --> B16
```

**Détails :**
- B05 (Data Lake local) dépend de B02–B04 ; B06 (ML) dépend de B05.
- B07 (Grafana/React/API) dépend de B05 et B06 ; B08 (LLM & tools) dépend de B07 et de contrats Data/ML ; B09 (tests intégrés locaux) dépend de B07/B08.
- B10 (sécurité/IaC préflight) peut être préparé en parallèle de B07/B08, sans créer de ressources AWS.
- B11–B13 impliquent une autorisation AWS explicite, avec G04/G05/G06 résolus.
- B14–B15 (agent) ne commencent qu'après la validation de la plateforme principale ; B16 (documentation et soutenance) consolide les preuves.

La numérotation est l'ordre d'exécution par défaut ; une optimisation en parallèle est autorisée uniquement si les dépendances, tests et contrats sont déjà stables.

## 8. Plan exécutable détaillé — batches B00 à B16

**Chaque batch comporte :** objectif, tâches, tests, critères d'acceptation et sorties. **Ne jamais** se contenter de créer des dossiers ou du code non exécuté. Conserver les commandes des tests et leurs traces dans `docs/evidence/Bxx.md`.

### B00 — Audit du dépôt et cadrage technique

**Objectif :** connaître l'état réel du projet avant d'écrire du code.

**Tâches**
- [ ] Inspecter les fichiers existants, l'historique Git, les dépendances, la documentation et les tests.
- [ ] Vérifier présence des PDF, clarifier ce qui est projet/documentation vs code réellement produit.
- [ ] Créer `docs/architecture/current-state.md` : ce qui existe, ce qui manque, risques de régression.
- [ ] Documenter environnement Windows + Docker Desktop/WSL2 + Python + Node + Git + AWS CLI (sans exiger de compte AWS pour le mode local).
- [ ] Ajouter le registre d'ADR et reprendre les décisions D01–D15.
- [ ] Définir un ensemble de commandes standard (voir §9) et un fichier de configuration d'exemple.

**Tests :** dépôt lisible, status Git connu, linter de base s'il existe, commande de démarrage préexistante si applicable.

**DONE :** audit écrit, aucun code utilisateur écrasé ; décisions retrouvables ; blockers clairement identifiés.

**Livrables :** `docs/architecture/current-state.md`, ADR initial, `README.md` de démarrage mis à jour.

### B01 — Monorepo, outillage et skeleton local

**Objectif :** créer une base exécutable, testable et automatisable.

**Tâches**
- [x] Mettre en place FastAPI (`/health/live`, `/health/ready`), React/Vite/TypeScript et Grafana OSS avec `docker-compose.yml`.
- [x] Configurer le reverse proxy/local dev et les URLs de services sans secrets hardcodés.
- [x] Mettre en place pytest, Ruff, lint/typecheck frontend, tests de base API et React.
- [x] Écrire un Makefile ou scripts `dev`, `test`, `lint`, `format-check`, `down`; fournir les équivalents PowerShell.
- [x] Fournir `.env.example` et `.gitignore` (secrets, outputs de datasets, tokens, logs volumineux exclus).
- [x] Créer le workflow CI GitHub Actions **sans** déploiement AWS ni secrets.
- [x] Définir le contrat de readiness : services démarrés, erreurs lisibles, aucune dépendance cloud obligatoire.

**Tests**
- [x] `docker compose config` réussit.
- [x] `docker compose up --build` démarre les services sur machine cible.
- [x] FastAPI health renvoie HTTP 200 ; frontend charge ; Grafana est accessible en local. HTTP et rendu React jsdom vérifiés ; contrôle visuel navigateur indisponible.
- [ ] Tests backend et frontend passent ; CI se déclenche sur PR. Tests locaux PASS ; événement PR distant non observé.

**DONE :** développement local reproductible après clone ; README avec commandes Windows ; secrets absents du Git.

### B02 — Audit datasets publics, stratégie synthétique, traçabilité

**Objectif :** constituer une base de données **défendable** pour l'entraînement et l'évaluation.

**Tâches**
- [ ] Rechercher au moins 3 sources candidates, puis vérifier pour chacune : URL, licence, coût d'accès, droit d'usage académique/publication, granularité temporelle, champs coût/devise/service, taille, période couverte, taux de trous, possibilité de split temporel, compatibilité AWS/FinOps.
- [ ] Documenter le résultat dans `docs/data-contracts/public_dataset_audit.md` avec verdict `ACCEPTED`, `LIMITED`, `REJECTED` et preuve.
- [ ] Candidats à auditer, **non considérés comme datasets validés** : exemples FOCUS et FOCUS Sandbox de la FinOps Foundation ; traces cluster Google (usage mais pas nécessairement prix AWS) ; autres données avec historique de coûts si trouvées.
- [ ] Construire un générateur déterministe `seed`, version, paramètres : 12 mois initiaux de coûts quotidiens par service/compte, tendance, saisonnalité hebdomadaire, changements de régime, bruit, valeurs manquantes, crédits, anomalies injectées et labels.
- [ ] Conserver `dataset_manifest.json` : provenance, licence, version, hash, date, schéma, période, méthode de génération ; ne jamais publier un dataset tiers dont la licence l'interdit.
- [ ] Séparer *train*, *validation temporelle* et *test indépendant*. Éviter d'utiliser un dataset public de validation pour régler des hyperparamètres.
- [ ] Si aucun jeu de données public de coûts n'est adapté, documenter `PUBLIC_VALIDATION_NOT_FEASIBLE` et planifier tests synthétiques/backtesting sans prétendre à une validation externe réelle.

**Tests**
- [ ] Deux générations avec la même seed produisent des artefacts identiques (hashs ou égalité des lignes).
- [ ] Les volumes, dates, devises et étiquettes générés respectent le contrat.
- [ ] Les anomalies injectées sont traçables ; aucune donnée de test ne fuit dans l'entraînement.
- [ ] L'audit ne déclare aucun dataset `ACCEPTED` sans vérification de la licence et du contenu réel.

**DONE :** G01 documentée ; générateur fonctionnel ; audit public et limites explicités ; aucun téléchargement opaque.

### B03 — Contrats et adaptateurs RAW

**Objectif :** permettre aux différentes sources d'alimenter le même pipeline, sans préjuger du déploiement AWS.

**Tâches**
- [x] Écrire contrats détaillés des datasets du §5 : champs obligatoires, types, unités, clés et règles de qualité.
- [x] Trancher ou matérialiser G02 : base de coûts de référence (source + méthode + champ), devise USD par défaut en mode démonstration ; ne pas convertir silencieusement les devises. Repli local matérialisé ; décision réelle PROPOSED dans ADR-003.
- [x] Implémenter `SyntheticAdapter` et `PublicDatasetAdapter` derrière une interface commune `collect()` / `validate_manifest()` / `write_raw()`.
- [x] Concevoir mais **ne pas connecter** `Cur2Adapter`, `OpenCostAdapter`, `AwsInventoryAdapter` : interfaces, schémas, tests avec fixtures.
- [x] Conserver les données RAW immuables ; gestion des recharges, manifeste d'ingestion et hash des sources.
- [x] Prévoir `data_source`, `source_file`, `ingestion_run_id`, `ingested_at` dès RAW/clean. Sidecars RAW ; propagation CLEAN prévue par contrat, réservée à B04.

**Tests**
- [x] Chaque adaptateur accepte les fixtures autorisées et rejette les schémas incompatibles avec message explicite.
- [x] Ingérer deux fois un fichier ne le duplique pas logiquement.
- [x] Les fichiers source restent identiques octet par octet.

**DONE :** contrats versionnés ; au moins deux adaptateurs utilisables si dataset public retenu, sinon synthétique + fixtures publiques ; interfaces AWS testées avec mocks.

### B04 — ETL RAW → CLEAN (PySpark local)

**Objectif :** nettoyer, normaliser et tracer les données sans en perdre silencieusement.

**Tâches**
- [ ] Implémenter un job PySpark partagé local/Glue, avec mapping spécifique par adaptateur.
- [ ] Normaliser UTC, types, noms de service, dates, devise explicite, coût de référence, tags/équipe et valeurs nulles.
- [ ] Dédupliquer sur la clé métier/source ; gérer corrections et versions de fichier CUR.
- [ ] Définir `quarantine/` pour les lignes invalides + raison ; `quality_report.json` et seuils de refus du job.
- [ ] Ne pas supprimer par défaut les coûts négatifs ou arrondir prématurément les montants.
- [ ] Écrire les sorties CLEAN en Parquet, partitions temporelles raisonnables et schéma stable.

**Tests**
- [ ] Unit tests sur valeurs négatives, doublons, champs manquants, noms et devises incohérents.
- [ ] Test d'idempotence : reprocesser le même batch et obtenir le même résultat.
- [ ] Test de correction rétroactive : remplacement d'une ligne déjà ingérée sans coût doublé.
- [ ] Test de comptabilité des lignes : RAW = acceptées + rejetées, sous règles de déduplication documentées.

**DONE :** tests PySpark locaux passent ; rapport qualité ; aucun record perdu sans justification ; même fonction transférable à Glue.

### B05 — ETL CLEAN → CURATED, catalogue logique et requêtes

**Objectif :** produire les tables métier du dashboard et du ML.

**Tâches**
- [ ] Implémenter les agrégats `daily_cost_by_service`, `daily_cost_by_account`, `daily_cost_by_team`, `daily_k8s_usage`, `resource_inventory_snapshot`.
- [ ] Calculer les budgets et KPIs du §5 dans une couche métier commune ; ne pas coder des formules contradictoires dans plusieurs dashboards.
- [ ] Écrire Parquet CURATED ; gérer le recalcul des partitions affectées et la conservation des périodes.
- [ ] Développer un **catalogue local** des schémas SQL pour DuckDB et un mapping Glue/Athena.
- [ ] Produire des vues SQL réutilisables, avec contrôle de périmètre/devises et documentation des dimensions.
- [ ] Ajouter un jeu de fixtures avec sommes manuelles attendues pour vérifier chaque agrégation.

**Tests**
- [ ] Réconciliation coûts CLEAN/CURATED sur même période/périmètre/base/devise.
- [ ] Nulls, équipes sans tags, dates absentes et crédits correctement pris en compte.
- [ ] Requête DuckDB sur Parquet reproduit un total attendu.
- [ ] K8s n'est pas ajouté à la facture totale AWS ; double comptage détecté en test.

**DONE :** Data Lake local reproductible ; vues analytiques stables ; `docs/data-contracts/kpis.md` contient SQL et formules.

### B06 — ML forecasting, anomalies et évaluation locale

**Objectif :** mettre en place les deux modèles avec évaluation scientifique reproductible.

**Tâches forecasting**
- [ ] Construire séries quotidiennes par service/compte : dates manquantes vs vrais zéros, niveau d'agrégation adapté à la densité des données (G03).
- [ ] Créer features sans leakage : lags 1/7/30, rolling means **strictement passées**, calendrier, service/compte ; usage CPU/RAM seulement si connu au moment de la prévision.
- [ ] Implémenter baseline naïve / moving average ; Prophet ; XGBoost (stratégie multi-horizon explicite ou récursive sans utiliser les futurs réels).
- [ ] Split chronologique initial train/test ~80/20 puis backtesting multi-fenêtres avec horizon 30 jours ; ne pas choisir le modèle sur le test final.
- [ ] Calculer MAE, RMSE, MAPE avec gestion des zéros, WAPE ; métriques par service et globales ; comparaison baseline et intervalles d'incertitude s'ils sont calibrables.
- [ ] Réaliser un test public indépendant si G01 l'autorise et si schémas/périodes comparables ; sinon écrire la limite sans masquer l'échec de disponibilité.
- [ ] Archiver configurations, seed, données/version, métriques, artefacts, courbes forecast-vs-actual et JSON de synthèse.

**Tâches anomalies**
- [ ] Implémenter détecteur basé sur résidus du forecasting avec seuil calibré sur données d'entraînement/validation.
- [ ] Comparer Isolation Forest sur features non fuyantes.
- [ ] Évaluer avec anomalies injectées **dans un jeu de test séparé** : precision/recall/F1 et faux positifs ; rappeler que les labels synthétiques ne valident pas les incidents réels.
- [ ] Produire résultats structurés `ml_forecast` et `ml_anomalies` avec `run_id`/`model_version`/origine.

**Tests**
- [ ] Tests des features et découpage temporel (aucune date future en entrée d'une prédiction passée).
- [ ] Test `next 30 days` : précisément 30 dates cibles par service/configuration éligible.
- [ ] Métriques recomputées par script indépendant à partir du fichier `predictions.csv/parquet`.
- [ ] Rejouer une expérience avec seed/config fixés reproduit le résultat dans les tolérances documentées.
- [ ] Si Prophet/XGBoost ne surpasse pas baseline, conserver baseline gagnante et **ne pas prétendre au contraire**.

**DONE :** tableau de comparaison, backtesting, figures, modèles et anomalies versionnés ; limites de généralisation documentées.

### B07 — Plateforme React/FastAPI/Grafana locale

**Objectif :** offrir une interface fonctionnelle connectée aux vraies tables CURATED locales et aux résultats ML.

**Tâches**
- [ ] FastAPI : endpoints `GET /api/kpis/overview`, `/api/costs`, `/api/forecast`, `/api/anomalies`, `/api/resources`, `/api/budgets`, `/health/*` ; pagination, filtres, date, source.
- [ ] React : navigation `Overview`, `Cost Explorer`, `Forecast & Budgets`, `Anomalies`, `Resources & Optimization` ; états loading/empty/error ; filtres cohérents ; version démonstration visible.
- [ ] Grafana OSS : dashboards versionnés en JSON + provisioning datasource local ; requêtes source local/dev ou service adapter, aucune dépendance silencieuse à Athena en local.
- [ ] Unifier les définitions de KPI ; afficher timestamp de fraîcheur, unité/devise, provenance et différence observé/prévu.
- [ ] `finops_budgets` via config/fichier ou API minimal ; aucune valeur de budget inventée dans l'application.
- [ ] Installer le plugin `grafana-athena-datasource` dans l'image AWS prévue ; provisionner workgroup et role IAM à l'intégration.
- [ ] Concevoir une séparation authentification backend et accès Grafana ; ne pas publier une instance Grafana admin ouverte. Établir G06 avant hébergement public.

**Tests**
- [ ] API contract/integration contre fixtures déterministes.
- [ ] End-to-end : filtre de période/service change correctement le coût total et les détails.
- [ ] Forecast fin de mois = réalisé MTD + prévisions des jours restants ; non confondu avec 30-day forecast.
- [ ] Affichage correct données vides, anomalies sans résultats, source synthétique et erreur pipeline.
- [ ] Démarrage local via Docker Compose reproductible.

**DONE :** parcours complet local de cinq pages ; chiffres contrôlés ; aucun mock de coût réel présenté comme observation AWS.

### B08 — Assistant LLM : API, outils, SQL sécurisé, Bedrock adapter

**Objectif :** rendre l'assistant fiable, vérifiable et compatible avec Bedrock.

**Tâches**
- [ ] Définir `LLMProvider` et `MockLLMProvider`; `BedrockConverseProvider` configuré sans supposer un modèle précis (G05).
- [ ] Implémenter `POST /api/chat` : session, identifiant, limites de tokens/round-trips/outils, timeouts et erreurs.
- [ ] Outils typés Pydantic : `run_athena_query`, `get_forecast`, `get_anomalies` ; chaque retour indique période, provenance, source et éventuelle limite de résultats.
- [ ] **Chemin A préconstruit** : templates SQL paramétrés pour top service, total, évolution, service/compte, budgets ; aucune concaténation non contrôlée d'identifiants/tables.
- [ ] **Chemin B génératif** : générer un SQL candidat à partir d'un catalogue métier **allowlist** (tables/champs/vues); validation avec SQLGlot pour dialecte Athena ; refuser DDL/DML, requêtes multiples, cross-schema, fonctions non permises, références externes, accès secrets et contournements ; imposer périodes et limites.
- [ ] Appliquer au backend des filtres d'autorisation du demandeur **en plus** de l'IAM ; l'authentification et l'accès aux datasets ne dépendent jamais uniquement du prompt.
- [ ] Athena en lecture seule, workgroup dédié, plafonnement bytes scanned, bucket de résultats privé et TTL, budgets/cap des appels. Ne pas affirmer que le seul IAM garantit syntaxiquement `SELECT-only`.
- [ ] Prévoir l'échec sûr : `insufficient_data`, `unauthorized`, `query_rejected`, `tool_failed`, `model_unavailable` ; pas de valeurs inventées.
- [ ] Ajouter Bedrock Guardrails en défense complémentaire et **non** en remplacement du validateur SQL.
- [ ] UI chat React avec indicateurs de provenance et distinction résultat calculé vs explication LLM ; pas de dump de prompts/secrets dans les logs.

**Tests**
- [ ] Préparer environ 20 questions canoniques avec résultat attendu pour les datasets fixtures.
- [ ] Tester top-N, périodes relatives, budgets, forecasts, anomalies, données vides, périodes sans données.
- [ ] Tester tentatives `DROP`, `DELETE`, `INSERT`, `UNLOAD`, multi-statements, accès table interdite, exfiltration et prompt injection.
- [ ] Comparer **résultat effectif SQL** aux valeurs de référence, pas seulement syntaxe.
- [ ] Détecter/alerter les hallucinations numériques ; imposer timeout/nombre d'outils bornés.
- [ ] Les tests locaux fonctionnent avec MockLLM/DuckDB ; Bedrock+Athena nécessite un gate AWS séparé.

**DONE :** assistant local fonctionnel sur fixtures, outils et contrôles testés, jeu d'évaluation reproductible, intégration Bedrock préparée.

### B09 — Test d'intégration locale de la plateforme principale

**Objectif :** créer un premier livrable exploitable **sans AWS**.

**Tâches**
- [ ] Pipeline `generate/download-audited → RAW → CLEAN → CURATED → local query → ML → dashboards → assistant` exécuté de bout en bout.
- [ ] Préparer 3 scénarios de démonstration : hausse de coût par service ; dépassement budgétaire prédit ; anomalie expliquée avec provenance.
- [ ] Vérifier Docker Compose, provenance, prévisions historisées, erreurs de fraîcheur, KPI et confidentialité.
- [ ] Effectuer une revue qualité : dépendances, tests, logs, accessibilité UI basique, résilience en absence de données.
- [ ] Marquer les données et visuels `SYNTHETIC/DEMO` si non réels ; archiver captures et commandes d'exécution.

**Tests**
- [ ] `test`, `lint`, `typecheck`, tests intégration et E2E passent.
- [ ] Rejouer le pipeline deux fois conserve les mêmes totaux.
- [ ] Assistant ne répond pas avec des coûts fabriqués sur un dataset vide.
- [ ] La procédure `docs/operations/local-runbook.md` fonctionne depuis un clone propre.

**DONE :** M1–M4 locaux démontrés ; note de validation `docs/evidence/local-acceptance.md` signée/revue avant AWS.

### B10 — Préparation CloudFormation, sécurité et coûts (sans déployer)

**Objectif :** produire une infrastructure vérifiable et éviter les surprises facturables.

**Tâches**
- [ ] CloudFormation YAML modulaire : `foundation`, `data`, `pipeline`, `ml`, `ai`, `app`, paramètres par environnement et outputs minimaux.
- [ ] Ressources candidates : S3 buckets data/query-results, Glue Catalog/Jobs, Athena workgroup, EventBridge Scheduler, Step Functions, Lambda, ECR, ECS Fargate, CloudWatch, IAM, Budgets. Pour CUR 2.0, vérifier compatibilité et prérequis `AWS::BCMDataExports::Export` avant usage.
- [ ] Séparer stockage persistant (données, modèles, logs selon rétention) et compute éphémère ; définir politique de suppression (`DeletionPolicy`, `UpdateReplacePolicy`) adaptée aux données.
- [ ] Réseau : décision NAT vs VPC endpoints vs autre architecture, contrôle ALB/HTTPS, pas d'accès public direct aux services administratifs.
- [ ] Configurer roles IAM par usage : Glue, SageMaker, inventory Lambda, Grafana Athena, FastAPI Bedrock, CI/CD preview/deploy ; identités OIDC restreintes à dépôt/branches/environnements.
- [ ] Définir budgets 50/80/100 % avec notifications, **sans les présenter comme arrêt automatique**, tags `Project`, `Environment`, `Owner`, `CostCenter`, CloudWatch retention.
- [ ] Ajouter `cfn-lint`, `cfn-guard` et politiques sécurité à CI ; ne pas générer de clés d'accès AWS permanentes.
- [ ] Rédiger `docs/operations/aws-runbook.md`, `cleanup.md`, `rollback.md`, estimation et inventaire des ressources susceptibles de générer des frais à l'arrêt (ALB, NAT, logs, IP, stockage, ECR etc.).

**Tests**
- [ ] Tous les templates passent validation locale `cfn-lint` et règles `cfn-guard`.
- [ ] Tests de policy : bucket sans chiffrement, port public dangereux, IAM wildcard critique, ressource destructive -> FAIL.
- [ ] CI sur PR ne lance **aucun** déploiement ; preview Change Set uniquement sur autorisation et rôle contrôlé.

**DONE :** stacks et runbooks vérifiés localement ; G04/G06 restent ouverts tant que l'utilisateur n'a pas fourni les éléments requis.

### B11 — Intégration AWS : Data Lake, ETL, Athena et SageMaker

**Objectif :** prouver les quatre premières exigences sur AWS à coût maîtrisé.

**Précondition obligatoire :** G04 approuvé ; budget/quotas/permission vérifiés ; contrat public/synthétique local stable.

**Tâches**
- [ ] Déployer `foundation`, `data`, puis `pipeline` via Change Sets et approbation ; préserver les ressources de données selon la politique retenue.
- [ ] Charger d'abord le dataset d'essai dans S3, puis lancer Glue PySpark/Step Functions à la demande ; contrôler Catalogue et Athena.
- [ ] Capturer run IDs, durées, scans Athena, qualité et coûts observables.
- [ ] Déployer `ml` puis lancer **un** Training Job SageMaker sur données autorisées ; versionner le modèle, exécuter batch inference sans endpoint permanent.
- [ ] Écrire les prédictions dans S3, exposer à Athena, vérifier cohérence avec résultats locaux.
- [ ] Étudier contraintes CUR 2.0 (compte payeur, autorisations facturation, livraison/rétrocorrections) ; préparer export **sans supposer immédiatement une facture exploitable**.
- [ ] Optionnel pour démonstration : OpenCost/Prometheus sur `kind` local ; n'activer EKS que si bénéfice démontré et coût approuvé.

**Tests**
- [ ] Glue lit RAW et écrit CLEAN/CURATED conformes ; Athena renvoie les totaux attendus.
- [ ] Step Functions gère succès/échec et relance idempotente.
- [ ] SageMaker Training Job termine ; Model Registry contient une version traçable ; batch inference donne 30 dates de prévision.
- [ ] Chiffrement, IAM et logs vérifiés ; ressources facturables arrêtées après test si prévu.

**DONE :** preuves AWS `docs/evidence/aws-data-ml.md` ; aucune affirmation de validation sur coûts réels sans observations réelles disponibles.

### B12 — Intégration AWS : Bedrock + Grafana OSS + FastAPI/React sur ECS

**Objectif :** démontrer l'assistant et le dashboard sur l'infrastructure AWS.

**Préconditions :** G04/G05/G06 tranchés et approuvés, B11 terminé.

**Tâches**
- [ ] Comparer modèles Bedrock disponibles dans la région choisie sur sous-ensemble du banc de test : qualité d'outils, SQL, coût estimé/token, latence.
- [ ] Sélectionner le modèle conforme et versionner son identifiant/config ; exécuter tests Converse & tool-calling réels.
- [ ] Construire/publier images Web/API/Grafana vers ECR ; faire fonctionner Grafana Athena datasource avec permissions S3/Glue/Athena minimales.
- [ ] Déployer l'app ECS Fargate via CloudFormation ; démarrage/arrêt contrôlé (`desiredCount=0` pour arrêt des tâches si service), sans confondre l'arrêt de tâches et absence totale de coûts fixes.
- [ ] Assurer HTTPS, authentification applicative, protection Grafana ; s'assurer que le backend n'expose pas de credentials AWS au navigateur.
- [ ] Valider les dashboards, le chat, la taille des requêtes et logs CloudWatch.

**Tests**
- [ ] Parcours utilisateur complet : connexion autorisée → dashboard → filtre → forecast → chat → requête Athena validée.
- [ ] Requêtes interdites rejetées en AWS ; coût de la requête et des appels Bedrock mesurés.
- [ ] Arrêt et redémarrage ECS fonctionnels ; dashboards reprovisionnés ; aucun secret exposé.
- [ ] Absence de données CUR réelles gérée proprement, sans les remplacer silencieusement par de fausses données réelles.

**DONE :** application cloud de démonstration utilisable, sécurisée et documentée ; captures et mesures d'exécution conservées.

### B13 — CI/CD, opérations AWS réelles et nettoyage

**Objectif :** rendre les déploiements traçables et répétables.

**Tâches**
- [ ] CI GitHub Actions : lint, test, typecheck, sécurité, validation CloudFormation, build d'images.
- [ ] Workflow `preview-infra` : OIDC restreint, créer Change Set et publier résumé sans exécution.
- [ ] Workflow `deploy-manual` : environnement GitHub protégé + revue approbateur + liaison commit SHA / Change Set / stack, exécuter uniquement avec consentement explicite.
- [ ] Intégrer smoke tests post-déploiement, vérifications CloudWatch et procédure de rollback versionnée.
- [ ] Scripts d'activation/désactivation à la demande ; inventaire des coûts persistants ; suppression contrôlée des ressources temporaires.
- [ ] Ajouter `cost-and-cleanup-checklist.md` : budgets, facturation prévisible, ressources arrêtées/supprimées, ressources conservées et justification.

**Tests**
- [ ] PR défectueuse bloque CI ; PR sans approbation ne peut pas lancer apply.
- [ ] Test de déploiement piloté, smoke tests puis arrêt contrôlé.
- [ ] Dans le rollback, vérifier séparation applicatif/infra/données : aucune suppression accidentelle de la couche RAW ou des modèles sauvegardés.

**DONE :** CI/CD fonctionnelle et sécurisée ; preuve d'un déploiement et d'un arrêt contrôlés.

### B14 — Agent v1 : waste detection, savings, risk scoring (sans changement AWS)

**Objectif :** transformer l'inventaire et les usages en recommandations vérifiables.

**Tâches**
- [ ] Conception d'une structure `OptimizationFinding` avec source, fenêtre d'observation, métriques et incertitudes.
- [ ] Détecteurs déterministes : EC2 sous-utilisée (CPU/mémoire/pics si disponibles) ; EBS détaché ; NAT suspect ; requests Kubernetes disproportionnées.
- [ ] Ne pas confondre `unused` et `safe to delete`; absence de métriques ou capacité critique doit relever le risque ou annuler l'action.
- [ ] Estimation d'économies sur hypothèses tarifaires documentées ; séparer coûts observés, coûts estimés, économies prédites et **économies réalisées**.
- [ ] Risk score déterministe 0–100 sur prod/dev, impact, risque de données, métriques manquantes, réversibilité ; conserver raisons et appliquer overrides absolus.
- [ ] Intégrer les recommandations dans API/Grafana/React, statuts `new`, `needs_review`, `blocked`, `approved`, `executed`, `verified`, `rejected`.

**Tests**
- [ ] Fixtures pour quatre types de gaspillage, faux positifs, prod critique, métriques absentes.
- [ ] Économies calculées selon formule `current - proposed`, en devise/base comparable.
- [ ] Production et ressources inconnues ne reçoivent aucune proposition auto-applicable.
- [ ] Mode dry-run sans droits AWS d'écriture passe tous les tests.

**DONE :** recommandations explicables et chiffrées **sans effet de bord**, moteur de détection testé.

### B15 — Agent v2 : OPA/Rego, CloudFormation Guard, PR, Change Sets et humains

**Objectif :** proposer des modifications révisables et **ne jamais** les appliquer sans humain.

**Précondition :** B14 validé ; G08 approuvé ; création d'une stack de démonstration CloudFormation gérée explicitement.

**Tâches**
- [ ] Écrire politiques OPA/Rego sur des objets structurés : env prod, données, limites minimales, métriques insuffisantes, stack non gérée, score élevé, autorisation manquante.
- [ ] Générateur de modifications CloudFormation **contraint par un allowlist de changements** (par ex. type EC2 dans paramètres autorisés). Ne jamais laisser le LLM produire librement du YAML exécutable sans validation.
- [ ] `cfn-lint` et `cfn-guard` sur le template ; OPA sur recommandation et impact ; vérifications métier complètes.
- [ ] Associer `resource_id` à un `stack_id`; ressource non gérée par une stack compatible => recommandation seulement, pas de Change Set.
- [ ] Générer branche et PR GitHub avec diff, preuves, estimation, score et résultat des politiques. Séparer le rôle de création de PR, celui de preview et celui d'exécution.
- [ ] À l'approbation requise, créer Change Set pour la version de template correspondant à un commit SHA immuable ; publier son ARN et le résumé du diff (create/update/delete/replace).
- [ ] Mettre un contrôle **fail closed** : tout `Remove`/`Replace` inattendu, absence de métriques, politique en échec, approbation absente, changement de commit/paramètres = BLOCK.
- [ ] Exécution uniquement après revue de la PR **et** approbation explicite du Change Set ; vérifier état final, suivi des métriques, retour arrière documenté.
- [ ] **EBS :** recommandation de vérification uniquement dans la V1 ; pas de suppression automatique. **Kubernetes :** si sources gérées par manifests/Helm, PR sur ces manifests, sans les déguiser en CloudFormation.
- [ ] Bedrock aide à **expliquer** le changement, sans pouvoir approuver ni contourner les garde-fous.

**Tests**
- [ ] Tests unitaires OPA : cas autorisé et tous les scénarios de rejet.
- [ ] Mock GitHub/CloudFormation : PR créée uniquement pour type autorisé, Change Set lié au SHA exact ; suppression/replacement critique bloqué.
- [ ] Test de sécurité : personne autre que l'approbateur autorisé ne peut exécuter un Change Set.
- [ ] Demo AWS uniquement avec une stack **non critique** approuvée, revue d'un Change Set, exécution contrôlée, vérification et rollback simulé/testé si possible sans danger.

**DONE :** cycle de recommandation → PR → politiques → Change Set → approbation → déploiement contrôlé validé sur cas autorisé, avec preuve qu'un refus bloque réellement l'action.

### B16 — Validation finale, rapport et soutenance

**Objectif :** fournir une démonstration honnête et reproductible des exigences du Project Spec.

**Tâches**
- [ ] Mettre à jour schéma de l'architecture réelle (ne pas afficher des services non déployés comme opérationnels).
- [ ] Produire dossier d'évaluation ML : source données, licence, baseline/Prophet/XGBoost, backtesting, métriques et limites de validation externe ; anomalies et F1 sur injections.
- [ ] Produire rapport pipeline : volumes, déduplication, qualité, réconciliation, exécution AWS ; preuves Glue/Athena/Step Functions.
- [ ] Documenter tests assistant ~20 questions, requêtes Athena, exactitude, rejets SQL, budget, sécurité.
- [ ] Documenter workflow CloudFormation, PR, Change Sets, GitHub OIDC, risques, budgets et coûts de démonstration (valeurs mesurées, pas estimées comme facturées).
- [ ] Préparer un script de soutenance de 8–12 minutes (durée adaptable) et un parcours de secours local si les services AWS sont indisponibles.
- [ ] Lister les fonctionnalités effectivement réalisées, les extensions reportées, les limites et les résultats observés.
- [ ] Vérifier README, instructions Windows, déploiement AWS, nettoyage, secrets et licences des jeux de données.

**Tests / acceptance finale**
- [ ] Clone propre → setup local → tests → E2E.
- [ ] Pipeline cloud démontré (ou blocker explicitement documenté sans faux succès).
- [ ] Modèles comparés et expérimentations reproductibles.
- [ ] KPI dashboard cohérents avec tables de référence.
- [ ] Assistant répond avec outils, sources et refus sûrs.
- [ ] Agent semi-automatique démontré si extension terminée.
- [ ] AWS coûts persistants contrôlés/nettoyés ; aucune clé/secrets dans le dépôt.

**DONE :** présentation défendable, journal de preuves, architecture et limitations fidèles au code.

---

## 9. Commandes de validation et conventions de développement

Les exemples ci-dessous constituent des **interfaces de commandes à implémenter**, non la preuve qu'elles fonctionnent déjà :

```bash
# Developpement local
 docker compose config
 docker compose up --build -d
 docker compose ps
 docker compose down

# Python (a adapter au gestionnaire choisi)
 python -m pytest -q
 ruff check .
 ruff format --check .

# Frontend (dans frontend/)
 npm ci
 npm run lint
 npm run typecheck
 npm run test -- --run
 npm run build

# CloudFormation (une fois les fichiers crees)
 cfn-lint infrastructure/cloudformation/*.yaml
 cfn-guard validate --rules infrastructure/guard/ --data infrastructure/cloudformation/data.yaml --type CFNTemplate

# AWS : commandes de lecture uniquement, apres validation du compte et region
 aws sts get-caller-identity
 aws cloudformation describe-stacks --stack-name finops-data-demo
```

Ne jamais coller dans README une commande `aws cloudformation execute-change-set`, `create-stack`, `delete-stack` ou `aws ecs update-service` qui pourrait être lancée aveuglément. Les placer dans le runbook **avec préconditions, paramètres, revue et confirmation explicite**. Les scripts cloud utiliseront par défaut `dry-run`/`preview` quand techniquement possible.

### 9.1. Qualité de livraison de chaque batch

- Tests automatisés et résultat réel enregistrés.
- Paramètres d'environnement dans `.env.example`, sans valeurs sensibles.
- Logs structurés et erreurs explicites.
- Datasets petits pour les tests rapides ; datasets volumineux conservés hors du repo.
- Code métier séparé des API et des adaptateurs AWS.
- Modules Python avec typing et erreurs explicites ; SQL centralisé et testé.
- Versions/lockfiles documentés, migrations contrôlées si stockage applicatif ajouté.
- Pas de dépendance cachée à un compte AWS pour lancer la suite de tests locale.
- Un README par sous-module uniquement s'il améliore réellement le lancement ; éviter la documentation dupliquée.

---

## 10. Matrice de tests globale

| Domaine | Test essentiel | Condition PASS |
|---|---|---|
| RAW | intégrité fichiers, manifeste, provenance | original préservé + hash cohérent |
| CLEAN | normalisation + dedup + quarantine | lignes rejouées sans doublons |
| CURATED | réconciliation coût par dimensions | totaux égaux sur périmètre identique |
| ML | leakage + backtesting + baseline | métriques vérifiables et chronologie valide |
| Anomalies | précision/rappel/F1 sur injections | scores calculés, limites documentées |
| Dashboard | filtres/périodes/budgets | valeurs cohérentes avec la couche CURATED |
| API | validation input, erreurs, authentification | requêtes non autorisées bloquées |
| SQL LLM | SELECT autorisé seulement + allowlist + tenant/scope | requêtes dangereuses et contournements rejetés |
| CloudFormation | syntaxe + policies | `cfn-lint` + `cfn-guard` PASS |
| OPA | deny policies | refus d'une action interdite observé |
| Change Set | preview lié à commit et stack | pas de `execute` avant approbation dédiée |
| CI/CD | tests PR + OIDC restreint | aucune PR non approuvée ne déploie |
| AWS coûts | activation/arrêt + persistance | ressources coûteuses identifiées et nettoyées |

**Tests de non-régression incontournables :**
1. Une seconde ingestion n'augmente pas le coût total.
2. L'ajout des coûts alloués OpenCost ne double pas la facture AWS.
3. Une prévision datée ne voit pas les observations réelles postérieures à sa date de génération.
4. Un `missing` n'est pas converti en zéro arbitrairement.
5. Un utilisateur non autorisé ne lit pas un compte tiers, même par SQL généré.
6. Une demande « supprime toutes les données » ne produit aucune action d'écriture.
7. Une ressource `prod` sensible ne peut pas être modifiée par l'agent.
8. Un Change Set avec suppression/remplacement imprévu bloque le workflow.
9. Les dashboards fonctionnent après redémarrage/reprovisionnement Grafana.
10. Sans données publiques compatibles, le rapport d'évaluation ne prétend pas à une validation sur données publiques réelles.

---

## 11. Risques, arbitrages et plans de repli

| Risque | Déclencheur | Réponse à implémenter |
|---|---|---|
| Dataset public insuffisant | moins de fenêtres d'évaluation 30j, autre granularité | synthétique pour train/test + rapport de limites ; ne pas affirmer externe |
| Historique AWS trop court | CUR réel activé tard | valider pipeline réel, pas « modèle validé sur AWS » ; évaluer lorsque données arrivent |
| Données altérées ou partielles | retards CUR, crédits, révisions | fraîcheur visible, idempotence, partitions rejouables |
| Coût AWS trop élevé | jobs/SageMaker/NAT/ALB/ECS actifs | développement local, budget gate, batch éphémère, arrêt/nettoyage |
| Coûts fixes malgré ECS arrêté | ALB/NAT/endpoints/stockage facturés | inventaire des coûts résiduels + suppression contrôlée si nécessaire |
| LLM indisponible | accès modèle/région/quota | mock local + autre modèle après G05 ; pas d'appel caché |
| SQL dangereux | prompt injection/SQL libre | allowlist, parse, IAM, workgroup, budgets, bloque sur erreur |
| Performance ML trompeuse | fuites temporelles / validation synthétique | backtesting, test public si possible, baselines, provenance |
| CloudFormation ne gère pas la ressource | inventaire seulement via boto3 | recommandation sans proposition de modification IaC |
| Déploiement en échec | services/quota/réseau | Change Set, smoke tests, rollback/rétention des données |
| Perte de config Grafana | redémarrage conteneur | provisionner datasources + dashboards depuis Git, sauvegarde si besoin |
| Fausses économies | coût alloué vs facture, réservations | qualifier estimation, formules et hypothèses, suivi post-action |

---

## 12. Guide de décision pour Codex : que faire lorsque quelque chose manque ?

- **Ne pas demander à chaque petite incertitude.** Choisir une valeur de développement sûre et réversible, documentée comme hypothèse, et continuer.
- **Ne pas inventer les décisions G01–G09.** Créer ADR `PROPOSED`, exposer alternatives/recommandation, obtenir approbation avant l'action dépendante.
- **Ne pas créer de ressource payante sans gate.** Même pour « tester vite ».
- **Ne jamais supprimer, remplacer ou modifier une ressource cloud de production à partir d'un simple signal d'usage.**
- **Tout service absent dans la région/compte choisi** : proposer une alternative de même finalité, comparer les coûts et les impacts ; attendre validation si cela change une décision approuvée.
- **Échecs de tests** : corriger dans le batch ; si un blocage externe subsiste, statut `PARTIAL`/`BLOCKED` + commande/reproduction + prochaine décision.

---

## 13. Critères globaux de fin de projet

### Cœur de plateforme — obligatoire

- [ ] Pipeline RAW/CLEAN/CURATED fonctionnel avec données synthétiques ou publiques auditées, et traitement AWS réel démontré.
- [ ] Coûts quotidiens par service/compte interrogables dans Athena.
- [ ] Modèle forecasting 30 jours entraîné, comparé à baseline, évalué temporellement et déployé en batch sur SageMaker.
- [ ] Anomalies détectées et expliquées avec métriques et limites.
- [ ] Grafana OSS, React et FastAPI utilisables localement et sur AWS à la demande.
- [ ] Assistant Bedrock avec 3 outils, Text-to-SQL hybride, autorisations et tests de sécurité.
- [ ] CloudFormation uniquement pour l'IaC ; CI/CD GitHub Actions/OIDC, IAM, CloudWatch et Budgets.
- [ ] Test d'ingestion des coûts AWS réels à la fin **si les exports CUR sont effectivement disponibles**, sans falsifier leur disponibilité.

### Extension agent — après le cœur

- [ ] Détection EC2/EBS/NAT/K8s et recommandations de coûts justifiables.
- [ ] Risk scoring déterministe avec refus absolus.
- [ ] OPA/Rego + CloudFormation Guard.
- [ ] PR GitHub, Change Set CloudFormation et double validation humaine.
- [ ] Démonstration d'une modification autorisée sur stack non critique ; aucun accès effectif sur ressource non gérée.

### Option facultative non bloquante

- [ ] Rapport mensuel LLM et RAG des rapports historiques avec Bedrock Knowledge Bases si G09 est approuvé, avec contrôles documentaires et données validées.

---

## 14. Prompt à donner à Codex pour démarrer

Copier ce texte dans Codex **après avoir placé ce fichier à la racine du dépôt** :

> Tu es l'agent développeur de FinOps Autopilot. Lis entièrement `FINOPS_IMPLEMENTATION_PLAN.md` et inspecte le dépôt, puis travaille **uniquement sur le batch B00**. Respecte toutes les décisions D01–D15, surtout **CloudFormation (jamais Terraform)**, développement local avant AWS, aucune dépense ni modification cloud sans approbation explicite, données synthétiques étiquetées, contrôles de qualité et GitOps à approbation humaine. Ne fais aucune hypothèse de réussite. Produis les livrables/tests du batch B00 et un compte rendu structuré selon §0.2. Attends mon feu vert avant B01.

Pour lancer un batch suivant :

> Lis `FINOPS_IMPLEMENTATION_PLAN.md` et les ADR existantes. Réalise uniquement le batch **Bxx**, en respectant ses dépendances, tâches, tests et critères DONE. N'exécute aucune opération AWS sans mon accord explicite. Donne le résultat réel des tests, le diff des fichiers et les décisions bloquantes, puis arrête-toi.

---

## 15. Références techniques (à revérifier à l'implémentation)

Les liens ci-dessous sont des **sources de documentation**, pas des preuves de service déjà configuré. Vérifier les spécifications au moment du batch et les contraintes régionales/compte :

- CloudFormation stacks et Change Sets : https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacks.html ; https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets-create.html
- CUR 2.0 Data Exports pour CloudFormation : https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bcmdataexports-export.html
- SageMaker batch inference : https://docs.aws.amazon.com/sagemaker/latest/dg/batch-transform.html
- Grafana OSS Athena datasource : https://grafana.com/docs/plugins/grafana-athena-datasource/latest/
- CloudFormation Guard : https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-guard.html
- AWS IAM GitHub OIDC : https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html
- AWS Budgets CloudFormation : https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-budgets-budget.html
- ECS desiredCount et services : https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service_definition_parameters.html
- Amazon Bedrock Converse / tool use : https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-call.html
- FOCUS open cost data specification : https://focus.finops.org/
- FOCUS sample datasets : https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS-Sample-Data
- Google cluster traces : https://github.com/google/cluster-data

---

## 16. Checklist de gouvernance et progression

Mettre à jour ce tableau après **exécution réelle** de chaque batch, pas simplement parce que les décisions conceptuelles ont été validées.

| Batch | Statut initial | Preuve attendue |
|---|---|---|
| B00 | PASS | [audit / ADR / preuves](docs/evidence/B00.md) |
| B01 | PARTIAL | [Socle local et tests vérifiés](docs/evidence/B01.md) ; déclenchement réel CI sur PR non observé |
| B02 | PASS | [audit datasets + générateur + preuves](docs/evidence/B02.md) ; [non-régression après B01](docs/evidence/B01.md), fichiers B02 préservés |
| B03 | PASS | [Contrats 1.0, adaptateurs RAW locaux et preuves](docs/evidence/B03.md) ; G02 matérialisé, aucun connecteur réel |
| B04 | TODO | PySpark CLEAN + quarantine |
| B05 | TODO | CURATED + KPIs + réconciliation |
| B06 | TODO | modèles ML + évaluation |
| B07 | TODO | dashboards + frontend + API |
| B08 | TODO | assistant hybride + tests SQL |
| B09 | TODO | tests E2E locaux |
| B10 | TODO | CloudFormation + préflight |
| B11 | TODO | Data + ML AWS intégrés |
| B12 | TODO | app + Bedrock sur AWS |
| B13 | TODO | CI/CD déploiement + cleanup |
| B14 | TODO | agent lecture seule |
| B15 | TODO | agent PR + Change Set + humain |
| B16 | TODO | rapport final + soutenance |

**Fin du plan v1.0.** Les huit parties fonctionnelles ont été discutées et validées avec l'utilisateur. **Cela ne signifie pas que les batches d'implémentation ont été exécutés.**
