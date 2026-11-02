[Ελληνικά](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

# Ωρολόγιο (Emploi du temps)

**Une application Windows qui construit l’emploi du temps hebdomadaire des enseignants d’un établissement.**

Tu saisis les enseignants, les classes et les affectations. L’application remplit seule toute la semaine. Ensuite tu ajustes ce que tu veux par glisser-déposer et tu imprimes l’emploi du temps en PDF. Sans compte, sans abonnement, et les données restent sur ton ordinateur.

## Fonctionnalités

- **Remplissage automatique** avec Google OR-Tools. Toute la semaine est résolue d’un coup : toutes les heures sont placées avec le moins de trous possible pour les enseignants.
- **Règles de l’établissement :**
  - heures consécutives pour les élèves,
  - indisponibilités des enseignants,
  - trous et maximum d’heures par jour pour chaque enseignant,
  - heures doubles,
  - horaires d’ouverture (ex. vendredi seulement jusqu’à la 6e heure).
- **Cours simultanés :** des groupes au nom de ton choix, ex. les langues vivantes en parallèle.
- **Zones :** des heures de la semaine réservées à certains cours, ex. les options de terminale. Aucun autre cours du même niveau n’est placé dans une zone.
- **Modifications à la main :** glisser, échanger des heures, verrouiller. Le panneau « Problèmes » montre ce qui n’est pas respecté.
- **Impression** par enseignant et par classe, avec un archivage de chaque impression.
- **Plusieurs établissements**, chacun avec ses enseignants et son emploi du temps.
- **Plusieurs emplois du temps en une fois :** il en trouve 2 à 4 différents, aussi bons, et tu gardes celui que tu préfères.
- **Enregistrement automatique** et sauvegardes, avec récupération du dernier ou de l’avant-dernier enregistrement.
- **Cinq langues :** Ελληνικά, English, Français, Deutsch, Español. Choix au premier démarrage, modifiable dans les Réglages.

## Installation

1. Clique sur **Code → Download ZIP** et décompresse les fichiers dans un dossier.
2. Double-clique sur **`Start.cmd`**.

L’application a besoin de **Python**. S’il manque, `Start.cmd` te le demande et l’installe. La première fois, les bibliothèques nécessaires sont aussi téléchargées : il faut internet et quelques minutes. Une icône est ensuite créée sur le bureau.

**Configuration requise :** Windows 10 ou 11.

## Utilisation

1. Ajoute ton établissement : nom et horaires d’ouverture (clic sur les heures de la semaine).
2. Crée les classes, indique quels cours ont lieu en même temps et les zones éventuelles. Puis les enseignants et leurs affectations.
3. Clique sur **Remplissage automatique**, corrige ce que tu veux et imprime.

Instructions détaillées : [`INSTRUCTIONS-FR.txt`](INSTRUCTIONS-FR.txt).

> Les fichiers du programme gardent leurs noms grecs (`Ωρολόγιο.pyw`, `Ωρολόγιο.html` …), tout comme le dossier de données `Documents\Ωρολόγιο`. C’est normal.

## Licence

[MIT](LICENSE) : utilisation, modification et partage libres.
