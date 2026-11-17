# Contrats logiques 1.0 — B03

Le [catalogue machine](../../data/contracts/catalog.json) contient les sept
datasets du §5, tous les champs, types, unités, nullabilité et clés composites.
`data.contracts.validate_record(dataset, record)` vérifie un enregistrement sans
le modifier. Ces contrats décrivent les futurs échanges CLEAN/métier ; B03 ne
produit ni CLEAN, ni KPI, ni modèle ML, ni recommandation.

## Règles communes

- Version `1.0` : chaque champ du catalogue doit être présent, même s'il vaut
  `null` lorsque `nullable=true`. Les champs inconnus sont rejetés par le
  validateur logique ; une évolution de contrat exige une nouvelle version.
- `string` : chaîne non vide ; identifiants conservés comme chaînes, jamais
  déduits d'un libellé. `object` : objet JSON ; `strings` : liste de chaînes.
- `decimal` : chaîne décimale exacte, éventuellement négative, sans notation
  scientifique, NaN, infini ou float binaire. Aucun arrondi dans B03. Les crédits
  restent négatifs. `nonnegative` ajoute la contrainte >=0.
- Timestamps ISO-8601 avec `T` et offset UTC (`Z` ou `+00:00`) ; aucune timezone
  implicite. Dates `YYYY-MM-DD`, mois `YYYY-MM` réellement valides.
- Devise obligatoire pour les montants ; en démo **USD uniquement**. EUR est
  refusé, jamais converti. Les bases `unblended`, `amortized` et `billed` sont
  sémantiquement distinctes ; une collection/agrégation devra être homogène.
- Clés du catalogue : identité logique, avec portée source/partition ci-dessous.
  `validate_record` vérifie les champs d'une ligne ; l'unicité d'une collection,
  la réconciliation et les formules métier appartiennent aux futurs producteurs.
- `data_source` : `synthetic`, `public`, `aws_real` dans le contrat logique.
  Les adaptateurs B03 refusent `aws_real` et conservent `DEMO` en métadonnées RAW.
  Un schéma capable de décrire AWS n'autorise aucune connexion AWS.

## Datasets, grain, clés et qualité

| Dataset | Grain et clé | Contraintes particulières |
|---|---|---|
| `cloud_costs` | Ligne source, clé `(data_source, source_file, source_record_id)` ; portée native à préserver | `usage_date` correspond au jour UTC de `usage_start_time`. Coût null uniquement pour `observation_status=missing` ; `zero_observed` exige zéro. Région, ressource, équipe et type de charge peuvent être null. Aucun coût OpenCost dans ce dataset. |
| `k8s_usage` | Observation d'un conteneur/workload dans une fenêtre, clé `(observation_time, cluster_id, namespace, workload, container)` | CPU en **cores**, mémoire en **bytes entiers >=0**, jamais en core-hours/byte-hours. Métriques absentes null avec `quality_flags`. Base unique `allocated_estimate`. Coût alloué séparé de la facture cloud. Dimension inconnue null, pas une chaîne inventée. |
| `resource_inventory` | Snapshot d'une ressource, clé `(snapshot_at, account_id, region, resource_type, resource_id)` | `tags` et `metrics_coverage` objets ; couverture inconnue `{}`, aucune métrique CPU/mémoire inventée. Attachement et stack CloudFormation null si non connus. |
| `finops_budgets` | Version d'un budget mensuel par périmètre, clé `(period_month, scope_type, scope_id, currency, effective_at)` | Montant >=0 ; scope global/account/service/team ; propriétaire, source et instant d'effet obligatoires. Règles et saisie G07 restent ouvertes. |
| `ml_forecast` | Prévision d'une date/série/version, clé `(run_id, target_date, account_id, service_name)` | Horodatage de génération et versions modèle/dataset requis ; deux bornes nulles ou intervalle contenant la prévision. Devise/base explicites ajoutées pour comparabilité. Aucun modèle créé en B03. |
| `ml_anomalies` | Événement identifié par `event_id` | Montants exacts, score éventuellement null, preuve structurée, statut open/acknowledged/resolved. `deviation_pct` null si attendu=0. Severity low/medium/high/critical. Formules et seuils seront testés en B06. |
| `optimization_recommendations` | Recommandation identifiée par `recommendation_id` | Estimations/risk_score null si indisponibles ; score 0..100. Preuve et raisons obligatoires. IDs/URLs de PR/Change Set null avant création. Statuts de politique/approbation/exécution séparés, aucune exécution implicite. Implémentation réservée aux lots ultérieurs. |

`cloud_costs` ajoute `observation_status` au minimum §5 pour distinguer absence,
zéro observé et manquant. `k8s_usage` et `resource_inventory` portent aussi
`source_file`, `ingestion_run_id`, `ingested_at`, en plus de `run_id` prévu au §5.
Les datasets ML/recommandations ajoutent devise/base pour interdire les comparaisons
ambiguës. L'unité des économies est un montant mensuel estimé, pas réalisé.

## Provenance RAW et futur CLEAN

RAW conserve les octets natifs ; les colonnes d'ingestion ne sont pas ajoutées au
CSV source. Elles vivent dans `ingestion_manifest.json` et seront propagées aux
lignes CLEAN en B04. Le manifeste indique profil, version, rôle, source, fichier,
hash, rows, run UUID, heure UTC d'ingestion effective, licence et origine.
`generation_reference_time` B02 reste la date reproductible déclarée, distincte
de `ingested_at`. Une copie du manifeste source préserve sa provenance complète.

La clé RAW est un hash du contenu, du profil/version, du rôle/partition et des
métadonnées sémantiques (base/devise, hash des labels). Le chemin source et l'heure
d'exécution ne modifient pas cette identité. Une copie renommée est donc réutilisée.
Une révision de contenu est conservée à côté de la version précédente : B04 devra
résoudre la déduplication métier/révision avant tout total. Ne pas sommer toutes
les révisions RAW comme si elles étaient des factures indépendantes.

Pour CUR, `identity_line_item_id` n'est unique que dans sa partition et ne suffit
pas à rapprocher des rapports/révisions. Le futur connecteur devra conserver
export, période, partition et version native. Cette limitation est explicitée
dans la [documentation AWS](https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2-identity.html).

## Profils d'entrée B03 et base G02

| Adaptateur / profil versionné | Format autorisé | Base et champ natif |
|---|---|---|
| `SyntheticAdapter`, `synthetic-costs/1.0` | Manifeste B02 + six CSV vérifiés ; trois observations collectées, labels compagnons archivés séparément | `unblended`, `cost_amount`, hypothèse de simulation uniquement |
| `PublicDatasetAdapter`, `public-focus-fixture/1.0` | CSV artificiel local : x_SourceRecordId, ChargePeriodStart, BillingAccountId, ServiceName, BilledCost, BillingCurrency | `billed`, `BilledCost` ; pas un mapping AWS unblended |
| `Cur2Adapter`, `cur2-fixture/1.0` | Fixture CSV des colonnes identity_line_item_id, line_item_usage_start_date, line_item_usage_account_id, line_item_product_code, line_item_unblended_cost, line_item_currency_code | `unblended`, `line_item_unblended_cost` ; aucune lecture d'export AWS réel |
| `OpenCostAdapter`, `opencost-projection-fixture/1.0` | Tableau JSON local projeté sur les champs k8s hors provenance/run ; ce n'est pas une réponse API native | `allocated_estimate`, `allocated_cost_amount` ; aucun ajout à cloud_costs |
| `AwsInventoryAdapter`, `inventory-projection-fixture/1.0` | Tableau JSON local de snapshots, hors provenance/run ; ce n'est pas une réponse boto3 native | Pas de montant ni devise inventés |

Les fixtures sont écrites pour ce dépôt, déclarées CC0-1.0 pour leur contenu
artificiel seulement. Aucune donnée tierce redistribuée ; aucune validation
externe acquise. `public` qualifie ici le chemin de l'adaptateur, **pas une preuve
d'origine réelle** : `fixture=true`, `DEMO` et provenance artificielle obligatoires.
`x_SourceRecordId` est une extension locale, pas une colonne FOCUS standard.
Le profil public ne prétend pas certifier la conformité FOCUS complète.

Les profils JSON de projection ne convertissent pas les heures OpenCost en cores
ni les réponses AWS en snapshots. Ces connecteurs restent à concevoir/implémenter
dans la phase autorisée, avec mapping explicitement testé. Les
[exemples OpenCost](https://opencost.io/docs/integrations/api-examples/)
distinguent notamment les mesures intégrées dans le temps.

Le champ public suit la définition de
[BilledCost FOCUS](https://focus.finops.org/docs/specification/v1-0/columns/cost-and-usage/billed-cost/),
et le champ CUR est décrit par
[AWS Data Exports](https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2-line-item.html).
Ces documents sont des références de schéma, pas des sources de données ingérées.
Décision finale G02 : [ADR-003](../adr/ADR-003-base-de-cout-devise.md).
