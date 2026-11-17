# ADR-007 — Topologie ECS Fargate, HTTPS, AuthN/AuthZ, accès Grafana et budget réseau

- Statut : **PROPOSED**.
- Gate : **G06** ; échéance selon le plan : **B12**.
- Date de consignation : 2026-11-15.
- Approbateur : utilisateur / approbateur à désigner ; aucune approbation enregistrée.

## Contexte et contraintes

Décision ouverte : Topologie ECS Fargate, HTTPS, AuthN/AuthZ, accès Grafana et budget réseau.
Les informations nécessaires ne sont pas établies dans le dépôt.
D01–D15 restent contraignantes ; aucun choix cloud n'est autorisé par cet ADR.

## Options et éléments à vérifier

Compose local ; ECS Fargate avec répartition Web/API/Grafana à définir. Comparer les options ALB, NAT et endpoints selon besoins et coûts. Exiger HTTPS, AuthN/AuthZ, protection Grafana et procédure d'arrêt.

## Décision proposée et repli de développement

**Décision définitive en attente.** Repli prescrit par le plan : Compose local ; infrastructure CloudFormation paramétrable.
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

[Plan directeur](../../FINOPS_IMPLEMENTATION_PLAN.md), §3 (G06), §1.3 et batch concerné.
L'[audit B00](../architecture/current-state.md) décrit l'état réel.
Aucune validation expérimentale ou cloud n'est revendiquée.