# ADR-002 — Dataset(s) publics : licence gratuite et autorisant usage académique, historique, coût comparable, granularité, provenance

- Statut : **PROPOSED**.
- Gate : **G01** ; échéance selon le plan : **B02**.
- Date de consignation : 2026-11-15.
- Mise à jour : 2026-11-16, audit B02 réalisé ; statut PROPOSED maintenu.
- Approbateur : utilisateur / approbateur à désigner ; aucune approbation enregistrée.

## Contexte et contraintes

Décision ouverte : Dataset(s) publics : licence gratuite et autorisant usage académique, historique, coût comparable, granularité, provenance.
Au B00, les informations nécessaires n'étaient pas établies dans le dépôt.
L'audit B02 ci-dessous apporte désormais une première vérification des sources.
D01–D15 restent contraignantes ; aucun choix cloud n'est autorisé par cet ADR.

## Options et éléments à vérifier

Dataset public de coûts compatible et gratuit ; source publique limitée à certains tests ; générateur synthétique reproductible. Vérifier licence, provenance, couverture et indépendance de la validation en B02.

## Décision proposée et repli de développement

**Décision définitive en attente.** Repli prescrit par le plan : Générateur synthétique, validation externe = `NOT_AVAILABLE`.
Ce repli, non implémenté en B00, est désormais exécutable en B02 sous forme de
données explicitement `synthetic`/`DEMO`. Aucune métrique ML réelle n'est inventée.

## Approbation et impacts

Avant l'action dépendante, documenter les éléments comparés ci-dessus et obtenir
l'approbation explicite de l'utilisateur ou de l'approbateur désigné.
Consigner date, décision, preuve et impacts. Le repli local permet de poursuivre
le développement local sans simuler la résolution du gate.

## Alternatives rejetées

Aucune option encore rejetée par une approbation au titre de ce gate.
Les options contraires à [ADR-001](ADR-001-decisions-validees.md) restent exclues.

## Preuve et documentation

[Plan directeur](../../FINOPS_IMPLEMENTATION_PLAN.md), §3 (G01), §1.3 et batch concerné.
L'[audit B00](../architecture/current-state.md) décrit l'état réel.
Aucune validation ML réelle ou cloud n'est revendiquée.

## Résultat B02 et décision en attente

L'[audit public](../data-contracts/public_dataset_audit.md) examine trois sources
distinctes et le Sandbox FOCUS en complément. FOCUS Sample Data et la fixture
Microsoft sont `LIMITED` ; Google Borg est `REJECTED` pour la validation de coûts
AWS facturés. Aucun candidat n'est `ACCEPTED` pour apprentissage ou validation externe.
Ces verdicts techniques ne valent pas approbation utilisateur d'un dataset.

Conclusion limitée aux candidats inspectés : `PUBLIC_VALIDATION_NOT_FEASIBLE`,
validation externe `NOT_AVAILABLE`. Les licences, URLs, versions, hashes et limites
sont tracés dans [les preuves publiques](../evidence/B02-public-sources.json).

Le [générateur](../data-contracts/synthetic_strategy.md) applique le repli déjà
prévu par le plan. Une seed réservée au test ne le rend pas indépendant du simulateur.
L'utilisateur a demandé B02 le 16 novembre 2026 ; cette demande ne constitue pas
une approbation de source publique ni une autorisation AWS. G01 reste PROPOSED
jusqu'à une décision explicite sur une source compatible ou sur ses limites.

Réouvrir l'audit si un historique gratuit/licencié/comparable devient disponible,
sans utiliser le test public indépendant pour ajuster les hyperparamètres.
