# ADR-003 — Coût de référence (ex. unblended/non amorti) + devise et conversion FX

- Statut : **PROPOSED**.
- Gate : **G02** ; échéance selon le plan : **B03**.
- Date de consignation : 2026-11-15 ; matérialisation locale B03 : 2026-11-17.
- Approbateur : utilisateur / approbateur à désigner ; aucune approbation enregistrée.

## Contexte et contraintes

Décision ouverte : Coût de référence (ex. unblended/non amorti) + devise et conversion FX.
Les informations nécessaires ne sont pas établies dans le dépôt.
D01–D15 restent contraignantes ; aucun choix cloud n'est autorisé par cet ADR.

## Options et éléments à vérifier

Base unblended/non amortie ; base amortie documentée ; conversion FX datée si nécessaire. Préciser champ source, arrondis et périmètre. CUR et OpenCost restent séparés.

## Décision proposée et repli de développement

**Décision définitive en attente.** Repli prescrit par le plan : Tout en USD dans le jeu de test, `cost_basis` explicite, refuser mélanges.
Il s'agit d'une cible de développement ; aucun composant correspondant n'est
implémenté par B00 et aucune donnée ou métrique n'est inventée.

## Approbation et impacts

Avant l'action dépendante, documenter les éléments comparés ci-dessus et obtenir
l'approbation explicite de l'utilisateur ou de l'approbateur désigné.
Consigner date, décision, preuve et impacts. Le repli local permet de poursuivre
le cadrage sans simuler la résolution du gate. G02 reste à approuver pour les sources réelles.

## Alternatives rejetées

Aucune option encore rejetée par une approbation au titre de ce gate.
Les options contraires à [ADR-001](ADR-001-decisions-validees.md) restent exclues.

## Preuve et documentation

[Plan directeur](../../FINOPS_IMPLEMENTATION_PLAN.md), §3 (G02), §1.3 et batch concerné.
L'[audit B00](../architecture/current-state.md) décrit l'état réel.
Aucune validation expérimentale ou cloud n'est revendiquée.

## Mise à jour B03 — repli local réellement implémenté

Le texte précédent décrit la proposition initiale B00. B03 matérialise maintenant
le repli, sans prétendre résoudre le gate pour AWS :

| Source autorisée localement | Base | Champ | Méthode |
|---|---|---|---|
| Générateur B02 | unblended | cost_amount | Valeur simulée en cents, conservée exactement ; pas un tarif AWS |
| Fixture publique artificielle | billed | BilledCost | Valeur native de démonstration, sans amortissement ou rapprochement CUR |
| Fixture CUR 2.0 | unblended | line_item_unblended_cost | Valeur native simulée, sans calcul NetUnblendedCost ni amortissement |
| Projection OpenCost artificielle | allocated_estimate | allocated_cost_amount | Allocation séparée, jamais additionnée à cloud_costs |
| Inventaire artificiel | aucune | aucun | Aucun montant ou taux inventé |

USD est obligatoire pour les fixtures de coût. Aucune conversion FX, aucun
arrondi de l'adaptateur, aucun mélange de bases dans un manifeste. Les crédits
négatifs sont conservés et un montant manquant reste manquant. Une base différente
exige un profil/version explicite ; le contrat logique décrit plusieurs bases
mais l'adaptateur ne déduit jamais leur équivalence.

Les sept contrats versionnés et les profils d'entrée sont documentés dans
[contracts-v1.md](../data-contracts/contracts-v1.md). Contrôles exécutés et limites :
[B03](../evidence/B03.md). La décision réelle (unblended/net/amortized, remboursements,
réservations et éventuel FX daté) reste **PROPOSED** ; pas d'approbation implicite.
