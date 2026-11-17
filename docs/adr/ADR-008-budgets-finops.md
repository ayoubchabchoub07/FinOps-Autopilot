# ADR-008 — Règles et saisie budgets mensuels

- Statut : **PROPOSED**.
- Gate : **G07** ; échéance selon le plan : **B08**.
- Date de consignation : 2026-11-15.
- Approbateur : utilisateur / approbateur à désigner ; aucune approbation enregistrée.

## Contexte et contraintes

Décision ouverte : Règles et saisie budgets mensuels.
Les informations nécessaires ne sont pas établies dans le dépôt.
D01–D15 restent contraignantes ; aucun choix cloud n'est autorisé par cet ADR.

## Options et éléments à vérifier

Fichier versionné non sensible ; table dédiée et saisie contrôlée ; synchronisation AWS éventuelle. Définir propriétaire, période d'effet, périmètre et devise. Ne créer aucun budget fictif.

## Décision proposée et repli de développement

**Décision définitive en attente.** Repli prescrit par le plan : Table `finops_budgets` à partir d'un fichier de config versionné sans données sensibles.
Il s'agit d'une cible de développement ; aucun composant correspondant n'est
implémenté par B00 et aucune donnée ou métrique n'est inventée.

## Approbation et impacts

Avant l'action dépendante, documenter les éléments comparés ci-dessus et obtenir
l'approbation explicite de l'utilisateur ou de l'approbateur désigné.
Consigner date, décision, preuve et impacts. Le repli local permet de poursuivre
le cadrage sans simuler la résolution du gate. G09 reste facultatif.

## Alternatives rejetées

Aucune option encore rejetée par une approbation au titre de ce gate.
Les options contraires à [ADR-001](ADR-001-decisions-validees.md) restent exclues.

## Preuve et documentation

[Plan directeur](../../FINOPS_IMPLEMENTATION_PLAN.md), §3 (G07), §1.3 et batch concerné.
L'[audit B00](../architecture/current-state.md) décrit l'état réel.
Aucune validation expérimentale ou cloud n'est revendiquée.