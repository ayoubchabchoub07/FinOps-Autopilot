# ADR-001 — Décisions validées D01–D15

- Statut : **ACCEPTED — repris du plan**, aucune nouvelle approbation en B00.
- Date de consignation : 2026-11-15.
- Approbateur : utilisateur selon le plan §1.2 ; identité nominative et dates individuelles non disponibles.
- Preuve : [plan v1.0](../../FINOPS_IMPLEMENTATION_PLAN.md), §0, §1.2, §3 et §4 ; PDF originaux absents.

## Contexte et contraintes

Le dépôt ne contient pas de code. Le plan atteste que D01–D15 sont validées.
Cette acceptation documentaire ne prouve aucune réalisation et n'autorise aucune dépense AWS.

## Décision, options retenues et impacts

| ID | Décision validée selon le plan | Impact de mise en œuvre |
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

## Alternatives rejetées

Le plan exclut Terraform au profit de CloudFormation, les endpoints de prédiction
permanents au profit du batch et l'optimisation autonome ou destructrice en V1.
Le LLM ne peut pas approuver ni exécuter seul une modification AWS.
Aucune autre comparaison historique n'est inventée.

## Impacts et limites

Le total facturé CUR reste distinct des allocations OpenCost. Les coûts synthétiques
restent étiquetés. Les budgets AWS sont des alertes, sans plafond automatique garanti.
Les gates G01–G09 restent ouverts dans le [registre](README.md).
Aucune preuve d'exécution de la plateforme n'existe encore.