# Planche

Carnet culturel personnel pour organiser tes films, livres et jeux vidéo. La bibliothèque de démonstration contient 12 œuvres. Utilise « Retirer la démo » pour commencer avec tes propres listes.

## Démarrer

Python 3.10 ou plus récent suffit. Depuis le dossier `planche`, lance cette commande dans le Terminal.

```sh
python3 server.py
```

Ouvre [Planche dans ton navigateur](http://127.0.0.1:8000). Garde le Terminal ouvert pendant l’utilisation. Si le port est occupé, lance `python3 server.py 8001` et ouvre l’adresse indiquée dans le Terminal. Réutilise ensuite le même navigateur, le même profil et la même adresse pour retrouver tes données.

## Importer tes listes

- Formats CSV (virgule, point-virgule ou tabulation) et Excel `.xlsx` (premier onglet, valeurs enregistrées). Jusqu’à 8 Mo et 10 000 lignes. Enregistre les anciens fichiers `.xls` en `.xlsx` ou en CSV.
- La première ligne contient les noms de colonnes. Seul `Titre` est obligatoire. Colonnes facultatives : `Type` (Film, Livre, Jeu), `Année`, `Genre`, `Durée` (minutes) ou `Pages`, `Auteur` ou `Réalisateur` ou `Studio`, `Statut`, `Note` (sur 5), `Critique` et `Image` (URL).
- Une colonne `Vu` contenant `Oui`, `1` ou `VRAI` fonctionne aussi pour un suivi cinéma. Les lignes sans titre sont ignorées. Les titres réimportés dans la même collection sont dédoublonnés avec le format et l’année si elle est disponible.
- Le [fichier d’exemple](static/exemple.csv) est aussi disponible dans la fenêtre d’import.
- Avec l’option d’enrichissement, le serveur recherche les titres dans les catalogues Apple (films), Open Library (livres) et Steam (jeux PC). Il remplit les champs vides lorsqu’il trouve un titre correspondant. La couverture dépend du catalogue et peut manquer. Les listes sont enregistrées avant la recherche. Une connexion est nécessaire pour la recherche et pour afficher les visuels distants. Le titre et l’année servent à la recherche auprès des fournisseurs. Tu peux désactiver cette option à l’import.

## Suivre ta progression

- Dans la bibliothèque, ouvre une fiche pour modifier son statut, sa note ou sa critique. Le statut « Terminé » compte dans les statistiques et les objectifs à la date du changement.
- Crée des objectifs par format et par période. Les points et badges sont calculés à partir de l’état courant de ta bibliothèque. Une œuvre terminée rapporte 25 XP, une note 10 XP et une critique 15 XP. Chaque tranche de 100 XP ajoute un niveau.
- « À découvrir » classe tes œuvres restantes selon les genres et formats que tu as bien notés, ainsi que les œuvres en cours.
- La sauvegarde est locale au navigateur. Elle persiste après fermeture de l’onglet et redémarrage du serveur. Effacer les données du site efface la bibliothèque.
