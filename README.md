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

 
## Catalogue

L’onglet « Découvrir » présente toutes les œuvres de la base, avec une recherche par titre et auteur, des filtres de format, de genre, de période, de score et de récompenses, un tri et une pagination. Le bouton « Réinitialiser » affiche à nouveau toutes les œuvres. Les anciens liens vers « Catalogue » restent valides. « Pour moi » propose les recommandations issues de ta bibliothèque. Ouvre une fiche pour consulter ses critères, leurs sources et leurs dates de vérification, puis ajoute l’œuvre à la collection de ton choix. Les scores publics restent distincts de ta note personnelle.

Les règles initiales sont IMDb au moins 7/10 et 1 000 votes, Steam au moins 80 % d’avis positifs affichés en anglais et 100 avis, Open Library au moins 3,5/5 et 20 avis. Une édition française explicitement identifiée dans Open Library est exigée pour chaque livre, y compris les livres primés. Les notes de lecteurs portent sur l’œuvre, toutes langues et éditions confondues. Le seuil de 20 avis pour les livres est un réglage initial.

Le catalogue livré contient un instantané réel, consultable sans relancer une collecte. Les photos distantes nécessitent une connexion. Les films IMDb gardent leurs titres de référence, parfois en anglais, et n’ont pas tous une affiche. Le bouton « Actualiser les sources » lance une collecte en arrière-plan. Laisse le serveur ouvert pendant la mise à jour. L’état des sources signale les collectes en cours, les interruptions et les limites d’accès. Les résultats précédents sont conservés en cas d’erreur, et Steam reprend au dernier lot enregistré.

Tu peux aussi actualiser depuis le Terminal sur macOS ou Linux.

```sh
python3 catalog.py
```

Pour une seule source, utilise par exemple `python3 catalog.py steam`, `python3 catalog.py books`, `python3 catalog.py imdb` ou `python3 catalog.py awards`. Les collectes simultanées sont verrouillées. Le téléchargement initial IMDb représente environ 230 Mo, mis en cache dans `data/cache/`. La collecte complète Steam peut être longue et interrompue par les limites du fournisseur.

La base active est `data/catalog.sqlite3`. Au premier démarrage, elle est restaurée depuis l’instantané compressé livré dans `data/seed/`. Pour conserver un catalogue actualisé entre installations, copie aussi ce fichier. Tes collections personnelles restent dans le navigateur à leur adresse habituelle.

### Sources et couverture

- [IMDb](https://data.imdb.com/non-commercial-datasets/) fournit les notes, nombres de votes et caractéristiques des films, courts métrages et téléfilms. Les jeux de données sont destinés à un usage personnel et non commercial.
- [Open Library](https://openlibrary.org/dev/docs/api/search) fournit les notes de lecteurs et les références d’éditions françaises. Cette base collaborative peut contenir des erreurs bibliographiques.
- [Steam](https://partner.steamgames.com/doc/store/getreviews) fournit les avis de son catalogue PC. La collecte utilise les résultats du magasin français, affichés en anglais, sans compte utilisateur. Les changements du magasin et ses limites de requêtes peuvent interrompre la collecte.
- Wikidata fournit les prix et nominations documentés pour les Oscars du meilleur film, Cannes, Berlin, Venise, Goncourt, Femina, Booker, International Booker, Pulitzer fiction, Hugo, Nebula et Game Awards. Seules les distinctions rattachées à une œuvre sont retenues. Les éditions françaises des livres sont vérifiées ensuite dans Open Library. La couverture dépend des contributions et de l’accès à Wikidata.
- Des distinctions vérifiées directement auprès de leurs organisateurs sont livrées dans `data/verified-awards.json` pour initialiser ce filtre lorsque la collecte internationale est limitée.

Metacritic et les jeux exclusifs aux consoles restent à connecter. Le catalogue expose sa couverture réelle dans l’état des sources. Il ne représente pas l’ensemble des œuvres satisfaisant tous les critères envisagés.

 
## Cartes et parcours

Toutes les cartes utilisent un cadre portrait 2:3, un titre sur deux lignes et des scores alignés. Les jeux utilisent les couvertures verticales Steam lorsqu’elles existent. Les livres utilisent Open Library. Les affiches de films proviennent des résumés Wikipédia et sont cherchées à la demande, puis mises en cache. Une carte conserve son titre lorsqu’aucune image exploitable n’est disponible.

L’onglet « Parcours » applique l’arborescence complète de `data/taxonomy.json`, avec 53 méta-listes et 1 098 sous-listes. Cyberpunk est une sous-liste de Science-fiction. Les prix et les nominations ont des méta-listes distinctes. Les sections intermédiaires servent uniquement à naviguer. La recherche retrouve toutes les sous-listes et le filtre permet de choisir une famille.

Une case représente une œuvre. Le contour gris indique une œuvre à découvrir, l’orange une œuvre en cours et la couronne violette une œuvre terminée. Clique sur une case pour ouvrir sa fiche, l’ajouter à ta bibliothèque ou modifier son statut. Une œuvre terminée valide toutes ses occurrences. Les pourcentages des méta-listes utilisent l’union des identifiants du catalogue, sans doublon.

L’arborescence complète est installée, mais l’affectation éditoriale reste partielle. Le premier ensemble relie les sélections Cyberpunk, Space opera et Post-apocalyptique par titres exacts, les créateurs par crédits exacts présents dans le catalogue et plusieurs prix par preuves sourcées avec distinction entre nominations et lauréats. Les listes sans affectation affichent « Sélection à compléter ». Les œuvres restent soumises aux règles d’entrée du catalogue, dont l’édition française pour les livres. Les listes ne prétendent pas contenir toute l’œuvre d’un créateur.

### Profil et trophées

« Profil & trophées » rassemble les statistiques personnelles, la vitrine chronologique, les prochaines listes à terminer et tous les trophées filtrables par nom, famille, statut et métal. Les coupes originales en SVG s’inspirent des trophées de consoles. Le déblocage est automatique après une sauvegarde de la bibliothèque, et lors de l’ouverture des parcours ou du profil pour reprendre une bibliothèque existante.

- Bronze pour une sous-liste de 1 à 14 œuvres.
- Argent pour 15 à 49 œuvres.
- Or à partir de 50 œuvres.
- Platine pour une méta-liste dont toutes les sous-listes sont documentées et toutes les œuvres terminées.

Les listes vides ne donnent aucun trophée. Les sections intermédiaires ne donnent aucun trophée. La date, le métal et la version de sélection sont enregistrés au premier déblocage dans `planche.trophies.v1`, dans le stockage du navigateur. Un trophée acquis reste dans la vitrine après une modification du statut ou du catalogue. Effacer les données du navigateur efface aussi les trophées. Utilise la même adresse et le même port pour retrouver tes données personnelles.

Après installation de cette version, redémarre le serveur puis recharge la page. Depuis le dossier du projet, exécute `python3 server.py 8001` et ouvre `http://127.0.0.1:8001/#profil`.

Vérification des règles de progression et de trophées avec `python3 -m unittest discover -s tests` et `node tests/trophies.mjs`. Le serveur n’a aucune dépendance supplémentaire.

Les pays proviennent de la propriété « pays d’origine » de Wikidata. La première sélection concerne 131 œuvres. Les genres complémentaires des jeux et des livres sont issus respectivement de Steam et des sujets Open Library. Les données manquantes sont omises. Les sources bibliographiques et les pays restent susceptibles d’erreurs de leurs catalogues d’origine.

La sélection de récompenses initiale comprend notamment les dix films nommés à l’Oscar du meilleur film 2024 et cinq lauréats des Game Awards, ainsi que les distinctions déjà présentes. Elle est documentée dans `data/verified-awards.json`. Les métadonnées complémentaires livrées sont appliquées au premier démarrage, y compris sur une installation existante.

Les icônes proviennent de Lucide, dont la licence figure dans `static/icons/LICENSE`.
