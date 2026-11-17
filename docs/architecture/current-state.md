# B00 — État réel du dépôt et cadrage technique

> Instantané historique du B00, conservé comme preuve. Pour l'évolution au
> 16 novembre 2026, voir [B02](../evidence/B02.md) : audit public et générateur
> synthétique ajoutés. La correction de l'ordre B01 après B02 est documentée dans
> [B01](../evidence/B01.md) : socle local opérationnel, statut global PARTIAL
> tant que le déclenchement réel de la CI sur PR n'est pas vérifié.

Date : **2026-11-15**, fuseau de référence `Africa/Lagos`.
Périmètre autorisé : **B00 seulement**. Les observations portent sur ce checkout
et sur les commandes accessibles dans la session restreinte, pas sur tout le poste.

## Inventaire avant modification

| Élément | Observation |
|---|---|
| Git | Branche `main`, suivi local `origin/main`, un commit visible : `8b9a9cb Initial commit` |
| Fichier suivi | `README.md` uniquement, 326 octets, description produit en anglais |
| Fichier utilisateur non suivi | `FINOPS_IMPLEMENTATION_PLAN.md`, 66 831 octets, 942 lignes |
| Modifications suivies initiales | Aucune ; le plan est déjà non suivi avant B00 |
| Instructions locales | Aucun `AGENTS.md` trouvé dans le dépôt ni ses répertoires parents |
| PDF de référence | `FinOps Autopilot Period 2 Project Spec.pdf` et `FinOps_Autopilot_FR.pdf` absents ; aucun PDF trouvé dans le dépôt |
| Code et infrastructure | Aucun backend, frontend, ETL, ML, agent, template CloudFormation ou configuration Grafana |
| Dépendances | Aucun `pyproject.toml`, requirements, `package.json` ou lockfile |
| Validation / exécution | Aucun test, linter configuré, CI, script de lancement, Dockerfile ou manifeste Compose |
| Données / résultats | Aucun dataset, modèle, métrique, benchmark ou preuve AWS |

L'historique est celui disponible localement : aucun `fetch` ni inventaire distant
n'a été effectué. Aucun compte AWS ni configuration d'identifiants n'a été consulté.
Le README initial décrit une ambition ; le plan est une spécification, pas une preuve
d'implémentation. Les 942 lignes du plan ont été lues pour cadrer B00.

## Environnement observé

| Composant | Résultat | Portée et suite |
|---|---|---|
| Windows | `Microsoft Windows NT 10.0.26300.0` via .NET | WSL rapporte également la version Windows `10.0.26300.9974` |
| PowerShell | `5.1.26100.9818` | Commandes documentées avec chemins entre guillemets |
| Git | `2.51.0.windows.1` | Lecture du dépôt et contrôle du diff possibles |
| Python | `3.13.5`, launcher `py` : 3.13 64 bits | Compatibilité des dépendances futures à vérifier en B01/B04/B06 |
| uv | `0.12.2` | Disponible ; aucun gestionnaire ni lockfile encore adopté dans le dépôt |
| pytest | `9.2.0` via `python -m pytest --version` | Installation du poste uniquement ; aucune suite projet |
| Node / npm | `v22.17.0` / `10.9.2` | Disponibilité observée, pas de validation React/Vite |
| Docker Desktop | Produit `4.67.0.222858` détecté dans l'installation | Aucun lancement ou changement de paramètres effectué |
| Docker CLI / Compose | `29.3.1` / `v5.1.1` | Clients présents ; avertissement d'accès refusé à la configuration Docker |
| Moteur Docker | `docker version` échoue, code 1 | Pipe `docker_engine` introuvable dans cette session ; fonctionnement du moteur non démontré |
| WSL | `2.6.3.0`, noyau `6.6.87.2-1` | `--status` et `--list --verbose` : `E_ACCESSDENIED` ; distributions, mode WSL2 et intégration Docker non vérifiés |
| AWS CLI | Non détecté dans le PATH | Non requis pour B00 ni pour le futur mode local ; à préparer avant intégration autorisée |
| Ruff / cfn-lint / cfn-guard | Non détectés dans le PATH | Ruff attendu en B01 ; outils IaC en B10 |

Les sorties et codes de retour sont conservés dans
[B00-environment.json](../evidence/B00-environment.json).
Les restrictions observées ne prouvent ni une désinstallation de WSL ni une panne
générale du poste. Avant le test Compose B01, vérifier dans une session autorisée
que Docker Desktop est démarré et que le moteur Linux et son intégration WSL2 sont accessibles.
Aucun téléchargement, installation ou démarrage de service n'a été effectué en B00.

## Cadrage retenu

Les [ADR](../adr/README.md) reprennent les décisions D01–D15 telles qu'attestées
par le plan et gardent G01–G09 au statut `PROPOSED`. Aucun choix de dataset,
région, compte, budget AWS, modèle Bedrock ou topologie cloud n'est inventé.

La cible reste : sources → RAW/CLEAN/CURATED → forecast/anomalies →
FastAPI/React/Grafana et assistant Bedrock ; puis extension d'optimisation.
Cette chaîne n'existe pas encore. Les transformations locales et Glue partageront
leur logique ; CUR facturé et OpenCost alloué restent distincts. Le mode local
utilisera des sources explicitement étiquetées et un fournisseur LLM mock.

Le [README](../../README.md) définit les interfaces de commandes futures et les
sondes exécutables aujourd'hui. Le fichier [.env.example](../../.env.example)
est uniquement un contrat de configuration proposé : aucun chargement ni contrôle
de ces variables n'est implémenté. `FINOPS_AWS_ENABLED=false` ne constitue donc pas
un garde-fou logiciel déjà testé. Les exclusions Git seront traitées en B01.

## Blocages et risques de régression

| Constat | Impact | Traitement / échéance |
|---|---|---|
| PDF absents | Concordance directe avec les documents originaux non vérifiable | Limite documentée ; vérifier leur contenu s'ils deviennent disponibles |
| Moteur Docker inaccessible et WSL restreint | Empêche de prouver un démarrage Compose dans cette session | À résoudre pour les critères d'acceptation B01 ; ne bloque pas l'audit B00 |
| Aucune base exécutable | Aucun test fonctionnel ou linter projet à lancer | B01, après autorisation |
| Versions présentes sans locks | Compatibilité et reproductibilité non démontrées | Sélection et verrouillage B01 ; validation PySpark/ML dans leurs batches |
| Gates G01–G09 ouverts | Actions dépendantes non approuvées | ADR `PROPOSED` et replis locaux définis dans le plan |
| Plan initial non suivi | Risque d'oublier la spécification dans une future livraison Git | Signalé ; aucun staging, commit ou push automatique |
| Aucun `.gitignore` initial | De futurs fichiers locaux pourraient être ajoutés par erreur | Aucun secret créé en B00 ; exclusions obligatoires B01 avant configuration réelle |

Il n'y a pas de comportement applicatif existant à régresser. Le risque immédiat
est documentaire : écraser les exigences utilisateur ou présenter la cible comme
réalisée. Le paragraphe original du README est conservé. Dans le plan, seules la
mention de statut et la ligne de progression B00 sont mises à jour après contrôle ;
les exigences et les statuts B01–B16 restent inchangés.

## Critères de sortie B00

- Audit et environnement consignés, avec limites explicites.
- Décisions D01–D15 retrouvables et gates G01–G09 non approuvés séparés.
- README de démarrage documentaire et exemple de configuration présents.
- Dépôt lisible et état Git connu ; linter/démarrage préexistants : non applicables.
- Aucun code utilisateur écrasé ; aucune exécution AWS ni implémentation B01.

Voir les commandes et résultats dans [le compte rendu B00](../evidence/B00.md).
