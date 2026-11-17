# ADR-012 — Contrats 1.0 et RAW local immuable

- Statut : **PROPOSED** ; conventions locales implémentées dans le périmètre B03 autorisé.
- Date : 2026-11-17. Approbateur définitif : utilisateur, validation non enregistrée.
- Contexte : B02 fournit déjà un manifeste et des observations/labels distincts.
  Aucun dataset public réel ACCEPTED ; les connecteurs AWS restent déconnectés.

## Proposition et alternatives

Conserver les octets RAW et enrichir un sidecar, plutôt que réécrire les CSV avec
des colonnes d'ingestion. Cela préserve la preuve source ; B04 devra propager les
métadonnées aux lignes CLEAN. Clé de contenu par fichier/profil/partition/base/devise
et labels, plutôt que nom ou horodatage : une recharge renommée ne crée pas de
doublon. Les corrections sont de nouveaux objets, jamais des overwrites.

Un dossier créé exclusivement et un marqueur de complétude écrit en dernier
évitent de présenter une écriture partielle comme réussie. Une transaction globale
sur tout un bundle n'est pas fournie : choix local simple, avec refus explicite
des dossiers incomplets et procédure non destructive dans le runbook. Ce stockage
n'est pas un mécanisme WORM face à un administrateur malveillant ; les hashes
détectent les altérations ordinaires, sans authentifier leur auteur.

Les objets conservent le reçu de première ingestion et son chemin absolu local.
Un replay réutilise ce reçu ; le CLI ne prétend pas avoir créé un nouveau run.
La portabilité d'un stockage RAW déplacé entre machines nécessitera un format
de références relatif/versionné avant ce besoin ; ne pas déplacer le dossier
RAW pour en faire un catalogue portable sans cette évolution.

Les sept contrats logiques sont déclaratifs et contrôlés sans installer de moteur
ETL ni de SDK. Les interfaces Cur2/OpenCost/Inventory ne traitent que des fixtures :
CUR en sous-ensemble de colonnes natives, OpenCost/inventaire en projections locales
explicitement distinctes des réponses API. Cela teste leurs contrats et leur
traçabilité sans revendiquer des connecteurs réels déjà opérationnels.

## Impacts et décisions ouvertes

La déduplication métier entre révisions reste B04 ; aucun total sur toutes les
versions RAW. L'identité CUR doit intégrer partition/export/révision, car l'ID natif
n'est pas globalement stable. Le format de manifeste cloud, l'échelle, les droits
S3 et la topologie sont à décider avant la connexion réelle, avec leurs gates.
G01, G02 et les gates AWS restent ouverts. Aucun changement de D01–D15.

Sources : [plan B03](../architecture/B03-implementation.md),
[contrats](../data-contracts/contracts-v1.md), [runbook](../operations/raw-ingestion.md),
[preuves](../evidence/B03.md). La proposition pourra être révisée après retour
utilisateur ; aucune approbation cloud ou démarrage B04 n'en découle.
