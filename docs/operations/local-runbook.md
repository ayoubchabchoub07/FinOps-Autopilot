# B01 — Exécuter le socle local

Prérequis : Python 3.13, uv 0.12.2, Node.js 22 (>=22.12), npm et Docker Desktop
avec moteur Linux/Compose démarré. Les installations initiales et constructions
d'images nécessitent Internet ; aucun compte AWS n'est utilisé.
Python 3.13 est validé pour B01/B02 uniquement, pas pour les futurs lots PySpark/ML.

Depuis la racine du dépôt, PowerShell :

```powershell
python -m pip install uv==0.12.2
python scripts/tasks.py setup
docker compose config --quiet
python scripts/tasks.py dev
python scripts/tasks.py smoke
```

`setup` restaure les dépendances verrouillées, copie `.env.example` dans `.env`
uniquement si absent et crée un mot de passe aléatoire uniquement si absent.
`dev` construit les images puis attend l'état sain des trois services.
Un échec est propagé par un code de sortie non nul.

- Frontend : <http://127.0.0.1:18000/>.
- Santé API via proxy : <http://127.0.0.1:18000/api/health/live> et
  <http://127.0.0.1:18000/api/health/ready>.
- Grafana : <http://127.0.0.1:18000/grafana/> ; utilisateur `finops-local`
  (modifiable avant la première initialisation avec `GRAFANA_ADMIN_USER`).
- Mot de passe : fichier local ignoré `.local/secrets/grafana-admin-password`.
  Consulter ce fichier en privé pour se connecter ; ne jamais le joindre aux preuves.
  Grafana persiste son compte dans son volume : changer le fichier après la première
  initialisation ne réinitialise pas automatiquement le mot de passe en base.

API et Grafana restent sur le réseau interne ; seul nginx est publié sur la
boucle locale. Son réseau `ingress` permet cette publication. Aucun port n'est
publié sur toutes les interfaces. Ne pas supprimer le répertoire de secrets ou
le volume pour résoudre un incident d'authentification.

Le port 8080 a été refusé par Windows pendant la vérification ; 18000 a été testé.
Pour changer de port, définir `FINOPS_WEB_PORT` dans `.env`, relancer `dev` puis
`smoke` (qui retrouve le port effectivement publié via Compose).

## Contrôles et arrêt

```powershell
python scripts/tasks.py test
python scripts/tasks.py lint
python scripts/tasks.py format-check
python scripts/tasks.py typecheck
python scripts/tasks.py build
python -m unittest discover -s data/tests -v
docker compose ps
python scripts/tasks.py down
```

`test` exécute pytest (API, configuration et tests B02) puis les quatre tests React.
Les sources B02 sont conservées à l'identique dans `data/`. Ruff porte sur
`backend/` et `scripts/` ; aucun reformatage des livrables B02 n'est effectué.
`down` arrête uniquement le projet `finops-autopilot-local` et préserve son volume.
Ne pas ajouter `-v` ou lancer un nettoyage global Docker.

Les équivalents PowerShell `scripts/setup.ps1`, `dev.ps1`, `test.ps1`, `lint.ps1`,
`format-check.ps1`, `typecheck.ps1`, `build.ps1`, `smoke.ps1` et `down.ps1`
délèguent au même lanceur. Si la politique du poste interdit les scripts PowerShell,
utiliser directement les commandes Python ci-dessus, sans modifier cette politique.

Pour modifier le frontend avec rechargement automatique, démarrer dans deux terminaux :

```powershell
.venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
npm.cmd --prefix frontend run dev -- --host 127.0.0.1
```

Vite écoute sur 5173 et relaie `/api/` vers 8000. Son lien Grafana nécessite la
stack Compose sur 18000 ; adapter `frontend/vite.config.ts` si ce port change.
En lancement natif, FastAPI lit l'environnement du processus (valeurs locales
par défaut), et non le fichier `.env` ; Compose charge ce fichier.

## Contrat de santé et erreurs

`/health/live` renvoie 200 si le processus répond. `/health/ready` renvoie 200
après démarrage avec `FINOPS_MODE=local`, `FINOPS_AWS_ENABLED=false` et
`FINOPS_LLM_PROVIDER=mock`. Il renvoie 503 avec `not_started` ou
`local_configuration_required` sinon. Aucun accès cloud ni dataset n'est requis.
Les sondes Compose vérifient également Grafana et nginx ; `smoke` teste depuis
l'hôte les trois services, les ressources JS et le refus anonyme de l'API Grafana.
Le frontend affiche une erreur explicite et propose une nouvelle tentative.

En cas d'échec : lire `docker compose ps` et `docker compose logs --tail 100`,
vérifier `.env`, le port disponible et la présence du fichier secret. Ne pas
publier les logs sans inspection. Sous Linux, le répertoire de secrets est en
0700 et le fichier en 0644 pour le montage utilisé par Grafana UID 472.
Contrôle spécifique Linux : `python -m scripts.tests.check_secret_permissions`.

Le workflow `.github/workflows/ci.yml` reprend ces commandes sur les PR, sans
déploiement ni identifiants AWS. Son déclenchement distant n'a pas été exécuté
dans cette mission locale ; voir les [preuves B01](../evidence/B01.md).
