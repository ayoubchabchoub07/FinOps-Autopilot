# B03 — Ingestion RAW locale

Python 3.13, bibliothèque standard uniquement pour les adaptateurs. Aucun SDK,
téléchargement, identifiant cloud, endpoint ou service AWS. Depuis la racine :

```powershell
python -m data.generators.synthetic --config data/generators/demo_config.json --output data/generated/b03-demo
python -m data.adapters --adapter synthetic --manifest data/generated/b03-demo/dataset_manifest.json --raw-root data/raw
python -m data.adapters --adapter public --manifest data/tests/fixtures/b03/public/manifest.json --raw-root data/raw
python -m data.adapters --adapter aws_cur --manifest data/tests/fixtures/b03/aws_cur/manifest.json --raw-root data/raw
python -m data.adapters --adapter opencost --manifest data/tests/fixtures/b03/opencost/manifest.json --raw-root data/raw
python -m data.adapters --adapter aws_boto3 --manifest data/tests/fixtures/b03/aws_boto3/manifest.json --raw-root data/raw
```

Le générateur refuse un dossier existant ; réutiliser le manifeste déjà généré
pour rejouer les commandes d'adaptation. Aucun fichier B02 n'est modifié.
Les commandes AWS nomment les **interfaces de fixtures locales déconnectées**.
`source_uri` est une métadonnée descriptive, jamais une URL téléchargée.

API commune : instancier avec le chemin du manifeste ; `validate_manifest()`
valide et retourne son objet, `collect()` retourne des objets immuables contenant
octets/rôle/nombre de lignes, `write_raw(root)` retourne les reçus d'ingestion.
Les trois méthodes vérifient tous les fichiers et leurs hashes avant écriture.
Un manifeste invalide entraîne `ValueError` (CLI : code 2 et raison explicite).

## Stockage et recharges

```text
data/raw/<dataset>/<data_source>/<adapter>/<object_id>/
  payload                  # octets source inchangés, aucun enrichissement CSV
  source_manifest.json     # octets du manifeste source original
  labels.csv               # uniquement compagnon synthétique, pas des coûts
  ingestion_manifest.json  # provenance, UTC réel, run, schéma, hashes, rôle
  COMPLETED                # hash du manifeste d'ingestion, écrit en dernier
```

Chaque objet est créé exclusivement. Un objet existant est relu et vérifié ; s'il
est identique, son reçu initial est retourné (même run/heure d'ingestion), sans
dupliquer les données. Le replay ne crée pas de faux nouveau run réussi.
Des octets modifiés créent un autre objet ; aucune suppression ni écrasement.
L'identité par fichier évite aussi de recopier un fichier déjà ingéré dans un
autre manifeste/bundle. Les sources sont limitées à 64 MiB par fichier et 100
entrées par manifeste, pour ce mode local ; adapter ces limites explicitement
avant de traiter de gros exports réels.

Les chemins doivent rester dans le dossier du manifeste, y compris après
résolution des liens. Les sorties ne peuvent pas être ce dossier ou son enfant.
Le stockage RAW doit rester un espace local de confiance : ce n'est pas un
service multi-utilisateur ou un mécanisme WORM administré.

Une interruption ou une exécution concurrente peut laisser un dossier incomplet :
le prochain appel le refuse, sans l'effacer. Conserver les preuves, attendre le
processus encore actif le cas échéant, puis retenter. Si une intervention sur un
objet incomplet est nécessaire, la décider explicitement ; le programme ne
répare jamais silencieusement un RAW. L'atomicité est par objet, pas par bundle :
des objets antérieurs peuvent être complets si une écriture suivante échoue.

La déduplication métier et les corrections rétroactives sont réservées à B04.
Ne pas sommer les objets RAW directement. `k8s_usage` reste distinct de
`cloud_costs`. Les labels ne sont jamais une entrée de coût ou feature ML.
Les fixtures publiques ne sont pas promouvables en partitions train/test.

## Contrôles

```powershell
.venv/Scripts/python.exe -m pytest data/tests/b03 -q
python scripts/tasks.py test
python scripts/tasks.py lint
python scripts/tasks.py format-check
```

Les tests couvrent les cinq adaptateurs hors réseau, rejets, conservation d'octets,
replay/renommage, révision, corruption et séparation des labels/partitions.
Ruff inclut les nouveaux contrats/adaptateurs/tests ; les sources B02 historiques
restent exclues du reformatage. `.gitattributes` conserve les octets exacts des
fixtures B03 après clone Windows/Linux pour que leurs SHA-256 restent valides.

Documentation : [contrats et profils](../data-contracts/contracts-v1.md),
[preuves B03](../evidence/B03.md). Aucun B04 n'est lancé par ces commandes.
