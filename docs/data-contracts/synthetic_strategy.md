# B02 — Données synthétiques et traçabilité

Générateur **1.0.0**, schéma `synthetic-costs/1.0`. Code :
[synthetic.py](../../data/generators/synthetic.py), paramètres :
[demo_config.json](../../data/generators/demo_config.json).
Python standard uniquement, vérifié avec Python 3.13.5 ; aucune dépendance cloud.
B01 n'est pas réalisé : aucune intégration Compose/CI n'est revendiquée.

## Exécuter depuis la racine sous PowerShell

```powershell
python -m unittest discover -s data/tests -v
python -m data.generators.synthetic --config data/generators/demo_config.json --output data/generated/my-demo
Get-Content data/generated/my-demo/dataset_manifest.json -Encoding UTF8
```

Utiliser un nouveau nom de dossier à chaque exécution : tout chemin de sortie
déjà existant est refusé. Les fichiers générés sont ignorés par Git. Le manifeste
est écrit en dernier ; son absence signifie que la sortie n'est pas complète.
Une interruption système peut laisser un dossier partiel, qui n'est pas réutilisé
ou effacé automatiquement.

## Simulation et paramètres

La configuration d'exemple génère **365 jours × 2 comptes × 3 services = 2 190
observations**, du 1er janvier au 31 décembre 2025. Les noms de comptes, région,
montants et variations sont artificiels. Les noms EC2/S3/RDS ne rendent pas les
montants conformes aux tarifs AWS.

| Composante | Règle de l'exemple |
|---|---|
| Coût de base | 10 000, 2 500, 7 000 cents selon service ; facteur 1 ou 2 selon compte |
| Tendance | +3 points de base par jour depuis le début |
| Saisonnalité | Sept facteurs selon le jour de semaine, lundi à dimanche |
| Régime | Facteur 1,25 à partir du jour d'index 180 |
| Bruit | Tirage déterministe uniforme en points de base dans ±800 |
| Manquants | Probabilité 200/10 000 ; montant vide et statut `missing` |
| Crédits | Probabilité 100/10 000 ; montant négatif valant environ un quart de la référence |
| Anomalies | Probabilité 250/10 000 ; pic à 2,5 fois la référence |

Les événements sont mutuellement exclusifs ; les fréquences réellement générées
ne sont pas promises égales aux probabilités. Les crédits ne sont pas étiquetés
comme anomalies. Aucun vrai zéro n'est généré par défaut ; un manquant n'est
jamais remplacé par zéro. Les montants observés sont calculés en cents entiers,
avec troncature après chaque facteur puis représentation à deux décimales.

Les tirages sont obtenus par SHA-256 de la version, seed, date, compte, service et
usage du tirage. Aucun état aléatoire global, heure courante, appel réseau ou ordre
de fichiers ne participe à la simulation. Les paramètres incluent limites et
validations ; les années bissextiles sont prises en compte. Maximum : un million
d'observations par exécution locale.

## Séparation temporelle et labels

| Partition | Dates incluses | Jours | Observations | Seed |
|---|---|---:|---:|---:|
| train | 2025-01-01 → 2025-08-07 | 219 | 1 314 | 42 |
| validation | 2025-08-08 → 2025-10-19 | 73 | 438 | 42 |
| test | 2025-10-20 → 2025-12-31 | 73 | 438 | 43 |

Les fractions portent sur les jours complets (60 %, 20 %, reste), toutes séries
ensemble. Le test emploie une seed différente, imposée distincte de celle du train.
Il est réservé à l'évaluation finale ; ce n'est **pas une source indépendante** :
les mécanismes de simulation restent communs. La validation externe réelle reste
`NOT_AVAILABLE`. Aucun entraînement ni feature engineering n'est réalisé en B02.

Chaque partition possède deux CSV : observations et `_labels.csv`. Les observations
n'incluent ni label d'anomalie, ni référence sans injection, ni delta injecté.
Les labels sont liés par `source_record_id`, et contiennent `event_type`,
`is_anomaly`, `baseline_cost` et `injected_delta`. Ils servent aux contrôles et à
l'évaluation, jamais aux entrées d'un modèle. La référence d'une ligne manquante
reste un oracle de simulation réservé aux labels ; elle n'est pas une observation
réelle à utiliser pour l'imputation. Aucun identifiant n'est partagé entre partitions.

En B06 : régler sur train/validation seulement, construire les features avec le
passé disponible, conserver le test scellé jusqu'à l'évaluation et rapporter
explicitement les limites de généralisation. Les tests B02 prouvent la séparation
des fichiers et des jours ; ils ne prouvent pas encore l'absence de fuite dans un
futur entraînement.

## Contrat B02, sans anticiper B03

Une ligne représente une journée UTC pour un compte/service. Les colonnes sont
décrites dans le manifeste. `cost_amount` est un décimal à deux chiffres, vide
uniquement lorsque `observation_status=missing`. `currency=USD`,
`data_source=synthetic`, `dataset_label=DEMO` et `cost_basis=unblended` sont explicites.
Cette base de coût est une hypothèse du simulateur ; **G02 reste ouvert** pour les
sources réelles. Les champs d'ingestion, adaptateurs RAW, contrats métier complets
et schémas Parquet appartiennent à B03/B04.

## Manifeste et licence

`dataset_manifest.json` inclut origine, licence, version/hash du générateur,
configuration complète, identifiant de configuration, schéma, période, splits,
volumes, événements, tailles et SHA-256 des six CSV. Le manifeste ne se hash pas
lui-même ; la [preuve de reproduction](../evidence/B02-reproducibility.json)
inclut son hash également. Le hash du générateur permet de distinguer des sources
modifiées même avant changement de numéro de version.

`generation_reference_time` est une référence UTC **déclarée dans la configuration**,
pas l'heure observée d'exécution. La maintenir identique permet de reproduire le
manifeste à l'octet près. La date de vérification effective est consignée dans B02.md.
L'exemple ne tente pas de deviner la date du poste.

Les seules données synthétiques produites sont déclarées `CC0-1.0` pour faciliter
leur réutilisation ; cette déclaration ne change pas la licence du code du dépôt
et ne couvre aucun dataset tiers. Les CSV téléchargés pour l'audit restent dans
un cache ignoré. Aucun coût réel, métrique ML ou résultat de validation externe
n'est fabriqué.
