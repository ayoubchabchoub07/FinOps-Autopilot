# B02 — Audit des datasets publics

Audit du **16 novembre 2026**. Objectif : identifier des données gratuites et
réutilisables pour l'apprentissage et la validation d'un forecast quotidien à
30 jours. Les verdicts ci-dessous portent sur les versions et échantillons
inspectés, pas sur toute donnée publique existante.

**Conclusion : `PUBLIC_VALIDATION_NOT_FEASIBLE` pour les candidats examinés ;
`external_validation=NOT_AVAILABLE`.** Aucun dataset n'est `ACCEPTED` pour
l'entraînement ou une validation externe réelle. Le repli synthétique prévu
par le plan est implémenté ; [G01 reste PROPOSED](../adr/ADR-002-datasets-publics.md).

## Méthode et limites de l'audit

Trois sources distinctes ont été examinées : FOCUS Sample Data, Microsoft FinOps
Toolkit et Google Borg. Le Sandbox FOCUS est étudié en complément, sans le compter
comme une source indépendante du dépôt FOCUS.

Les [mesures JSON](../evidence/B02-public-sources.json) enregistrent URL, commit,
octets, SHA-256, profils et références de licence. Le
[script](../../data/audit/public_sources.py) télécharge uniquement les objets
HTTPS listés dans son code, avec une limite de 2 Mo par objet. Le cache local
`.cache/public-audit/` est ignoré par Git. Aucun CSV tiers n'est republié ici.
Aucun compte AWS/GCP, moteur BigQuery ou API payante n'a été utilisé.

Le taux de jours absents est `(jours calendaires entre min/max − jours distincts) /
jours calendaires`. Il ne mesure pas la complétude des factures ni celle de chaque
compte/service. Un échantillon ayant au moins une ligne par jour peut rester très
incomplet. Les jours sans observation ne valent pas zéro.

## Comparaison

| Candidat | Contenu effectivement inspecté | Période / granularité | Verdict pour le besoin B02 |
|---|---|---|---|
| FOCUS Sample Data 1.0 | CSV 1 000 lignes, 44 colonnes, 755 423 octets | 01–30 septembre 2024 ; lignes de charges, plusieurs horodatages par jour | **LIMITED** : exploration de schéma/crédits, pas d'historique suffisant |
| Microsoft FinOps Toolkit | Fixture EA Actual Cost, 11 lignes, 55 colonnes, 11 535 octets | 4, 5 et 21 septembre 2023 ; dates de consommation | **LIMITED** : cas d'adaptation Azure uniquement |
| Google Borg 2019 | README, description et schéma protobuf ; aucune trace téléchargée | Mai 2019 documenté ; événements et usages, histogrammes CPU par cinq minutes | **REJECTED** pour coûts AWS facturés ; pas de données monétaires établies |
| FOCUS Sandbox | Page publique et présentation officielle ; aucune requête exécutée | Présentation officielle : septembre 2024 | **LIMITED** : outil d'exploration, pas un test indépendant du FOCUS source |

## FOCUS Sample Data

Version : `adbdd17a132984d6e8583c149c236d2199c3f5bc`.
[CSV inspecté](https://raw.githubusercontent.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS-Sample-Data/adbdd17a132984d6e8583c149c236d2199c3f5bc/FOCUS-1.0/focus_sample.csv),
[description](https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS-Sample-Data/blob/adbdd17a132984d6e8583c149c236d2199c3f5bc/FOCUS-1.0/README.md),
[licence CC BY 4.0](https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS-Sample-Data/blob/adbdd17a132984d6e8583c149c236d2199c3f5bc/license.md).
Accès HTTPS gratuit observé. Usage académique/publication possible selon CC BY 4.0,
avec attribution, lien de licence et indication des modifications ;
[conditions officielles](https://creativecommons.org/licenses/by/4.0/).

Mesures locales : USD seulement, 33 services, 942 lignes AWS, 51 Microsoft et
7 Oracle. Les 30 jours sont représentés globalement et pour AWS ; Microsoft en
couvre 19, Oracle 6. Aucun montant, devise ou service manquant dans ce petit CSV ;
13 montants négatifs, 329 zéros et aucun doublon exact. Le taux global de dates
absentes est 0 %, sans garantie de complétude.

Champs utiles : `ChargePeriodStart`, `BilledCost`, `BillingCurrency`, `ServiceName`,
`SubAccountId`. La timezone n'est pas explicite dans les chaînes de dates inspectées.
FOCUS n'est pas le schéma natif CUR 2.0 ; tout mapping sera audité en B03.

Un mois ne permet pas un entraînement historique, un réglage temporel et un test
indépendant à 30 jours défendables. Le CSV complet et ses variantes plus grandes
n'ont pas été téléchargés ; aucune statistique du petit échantillon ne leur est attribuée.

## Microsoft FinOps Toolkit

Version : `3300217dd3b307f8b501aeb37ac5530c072fec3f`.
[Fixture inspectée](https://github.com/microsoft/finops-toolkit/blob/3300217dd3b307f8b501aeb37ac5530c072fec3f/src/powershell/Tests/Unit/assets/EA_ActualCost_Small.csv),
[licence MIT du dépôt](https://github.com/microsoft/finops-toolkit/blob/3300217dd3b307f8b501aeb37ac5530c072fec3f/LICENSE).
Licence lue ; conserver la notice de copyright et de licence lors d'une redistribution
de la fixture. Téléchargement HTTPS gratuit, sans compte. Aucune qualification de
facture réelle indépendante n'est déduite d'un fichier de tests.

Mesures : 3 dates distinctes sur une fenêtre de 18 jours, donc 15/18 = **83,33 %**
de dates absentes dans cette fenêtre ; USD, six valeurs `ConsumedService`, trois
montants nuls, aucun négatif ni doublon exact. `Date`, `Cost`, `BillingCurrency`
et `ConsumedService` sont présents. Les dates sont interprétées au format
mois/jour/année ; cette interprétation est confirmée par `09/21/2023`.

La fixture permet des tests de structure Azure, pas un historique d'apprentissage
ou de backtesting. Les exports du répertoire open-data, dont certains sont des
objets Git LFS, ne sont pas supposés identiques à cette fixture ni profilés ici.
Le mapping vers services AWS et base de coût CUR n'est pas établi.

## Google Borg 2019

Version : `48b12446464b0422abcc18e0ec5b0b13e2f3a90c`.
[Description et licence](https://github.com/google/cluster-data/blob/48b12446464b0422abcc18e0ec5b0b13e2f3a90c/ClusterData2019.md),
[schéma inspecté](https://github.com/google/cluster-data/blob/48b12446464b0422abcc18e0ec5b0b13e2f3a90c/clusterdata_trace_format_v3.proto).
CC BY 4.0 : réutilisation académique/publication avec attribution et conditions
ci-dessus. Documentation accessible gratuitement ; gratuité d'une analyse complète
via BigQuery **non établie** et aucune requête lancée.

La source décrit huit cellules, mai 2019 et environ **2,4 TiB compressés**. Ces
valeurs sont documentées, non mesurées localement. Le schéma expose CPU/mémoire
et temps relatifs ; il n'établit ni facture AWS, ni devise, ni nomenclature AWS.
Nombre de lignes et taux de trous : **NOT_MEASURED**. Un split temporel d'usage
est concevable, mais ne valide pas des coûts AWS. Aucun prix n'est ajouté aux
traces pour les transformer artificiellement en facture.

## Sandbox FOCUS et indépendance

La [page Sandbox](https://focus.finops.org/docs/tools-assets/tools/query-sandbox/)
et la [présentation officielle](https://www.finops.org/insights/focus-sandbox/)
ont été consultées le 16 novembre 2026. La présentation relie l'outil aux données
exemples FOCUS et décrit une plage en septembre 2024. La consultation de pages
n'a exigé aucun paiement ; une exécution SQL dans le Sandbox n'a pas été testée.
Taille, nombre de lignes et trous de son backend actuel : **NOT_MEASURED**.
La licence du dépôt s'applique au CSV audité ; aucune licence distincte du backend
actuel n'est présumée. La copie ou consultation de la même source dans cet outil
ne constituerait pas une validation indépendante.

## Conséquences et suite

- En B02, utiliser uniquement le [générateur synthétique](synthetic_strategy.md)
  pour les jeux locaux ; les données publiques restent des candidats limités.
- En B06, prévoir baseline/backtesting et évaluation sur labels injectés réservés.
  Ne présenter ni score synthétique ni variation de seed comme validation réelle.
- Réouvrir G01 si une source gratuite et licenciée apporte un historique comparable,
  une provenance vérifiée et une période indépendante. Profiler son contenu complet
  pertinent, puis obtenir l'approbation avant usage dépendant.
- Ne pas utiliser un jeu de validation externe pour ajuster des hyperparamètres.
