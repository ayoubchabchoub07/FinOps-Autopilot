# ADR-006 — Modèle Bedrock, droits d'accès, coût et disponibilité Converse/tool use

- Statut : **PROPOSED**.
- Gate : **G05** ; échéance selon le plan : **B11**.
- Date de consignation : 2026-11-15.
- Approbateur : utilisateur / approbateur à désigner ; aucune approbation enregistrée.

## Contexte et contraintes

Décision ouverte : Modèle Bedrock, droits d'accès, coût et disponibilité Converse/tool use.
Les informations nécessaires ne sont pas établies dans le dépôt.
D01–D15 restent contraignantes ; aucun choix cloud n'est autorisé par cet ADR.

## Options et éléments à vérifier

Mock local ; modèle Bedrock compatible après comparaison. Vérifier droits, disponibilité régionale, Converse/tool use, qualité, coût et latence. G04 est nécessaire avant appel payant.

## Décision proposée et repli de développement

**Décision définitive en attente.** Repli prescrit par le plan : Mock déterministe local.
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

[Plan directeur](../../FINOPS_IMPLEMENTATION_PLAN.md), §3 (G05), §1.3 et batch concerné.
L'[audit B00](../architecture/current-state.md) décrit l'état réel.
Aucune validation expérimentale ou cloud n'est revendiquée.