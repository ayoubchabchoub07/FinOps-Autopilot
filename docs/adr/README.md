# Registre des décisions d'architecture

Date : 2026-11-15. Source : [plan directeur](../../FINOPS_IMPLEMENTATION_PLAN.md),
§1.2 et §3 ; PDF originaux absents. Une décision acceptée n'est pas une fonctionnalité réalisée.

Mise à jour du 16 novembre 2026 : [G01 / ADR-002](ADR-002-datasets-publics.md)
documente l'audit B02 et le repli synthétique exécuté ; statut `PROPOSED` maintenu.

| Périmètre | ADR | Statut | Échéance | Objet |
|---|---|---|---|---|
| D01–D15 | [ADR-001](ADR-001-decisions-validees.md) | ACCEPTED selon le plan | Transverse | Les 15 décisions déjà validées |
| G01 | [ADR-002](ADR-002-datasets-publics.md) | PROPOSED | B02 | Dataset(s) publics : licence gratuite et autorisant usage académique, historique, coût comparable, granularité, provenance |
| G02 | [ADR-003](ADR-003-base-de-cout-devise.md) | PROPOSED | B03 | Coût de référence (ex. unblended/non amorti) + devise et conversion FX |
| G03 | [ADR-004](ADR-004-granularite-ml.md) | PROPOSED | B06 | Suffisance des séries temporelles par service/compte ; granularité du modèle |
| G04 | [ADR-005](ADR-005-activation-aws.md) | PROPOSED | B10–B12 | Région AWS, compte, accès aux exports CUR 2.0, quotas et budget maximal |
| G05 | [ADR-006](ADR-006-modele-bedrock.md) | PROPOSED | B11 | Modèle Bedrock, droits d'accès, coût et disponibilité Converse/tool use |
| G06 | [ADR-007](ADR-007-topologie-ecs-securite.md) | PROPOSED | B12 | Topologie ECS Fargate, HTTPS, AuthN/AuthZ, accès Grafana et budget réseau |
| G07 | [ADR-008](ADR-008-budgets-finops.md) | PROPOSED | B08 | Règles et saisie budgets mensuels |
| G08 | [ADR-009](ADR-009-perimetre-gitops.md) | PROPOSED | B15 | Périmètre exact des ressources CloudFormation optimisables, politiques et approbateurs |
| G09 | [ADR-010](ADR-010-rapport-rag-optionnel.md) | PROPOSED | Backlog | Rapport mensuel RAG/Knowledge Bases |
| B01 local | [ADR-011](ADR-011-fondations-locales.md) | PROPOSED | B01 | Intégration de B02, versions, réseau et secrets locaux ; CI distante non vérifiée |
| B03 local | [ADR-012](ADR-012-raw-local-immuable.md) | PROPOSED | B03 | Contrats 1.0, sidecars, identité RAW et limites des connecteurs déconnectés |

## Tenue du registre

Chaque ADR contient contexte, options, contraintes, décision, impacts, approbateur,
date, alternatives rejetées et preuve/documentation. Conserver le statut
`PROPOSED` sans approbation explicite. Enregistrer l'approbateur, la date et la
référence de preuve lors de l'approbation, sans réécrire l'historique.

Les replis locaux du plan permettent de progresser sans inventer les choix AWS.
Une décision d'architecture ne vaut pas autorisation d'exécution d'un Change Set :
revue PR et autorisation d'exécution restent distinctes.

Les échéances reprennent la table §3. Résoudre le gate avant l'action dépendante,
même si son interface est préparée plus tôt (budgets B07, modèle Bedrock B12).
