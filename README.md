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
- Avec l’option d’enrichissement, le serveur recherche les titres dans les catalogues Apple (films), Open Library (livres) et le catalogue Metacritic local (jeux PC et consoles). Il remplit les champs vides lorsqu’il trouve un titre correspondant. La couverture dépend du catalogue et peut manquer. Les listes sont enregistrées avant la recherche. Une connexion est nécessaire pour la recherche et pour afficher les visuels distants. Le titre et l’année servent à la recherche auprès des fournisseurs. Tu peux désactiver cette option à l’import.

## Suivre ta progression

- Dans la bibliothèque, ouvre une fiche pour modifier son statut, sa note ou sa critique. Le statut « Terminé » compte dans les statistiques et les objectifs à la date du changement.
- Crée des objectifs par format et par période. Les points et badges sont calculés à partir de l’état courant de ta bibliothèque. Une œuvre terminée rapporte 25 XP, une note 10 XP et une critique 15 XP. Chaque tranche de 100 XP ajoute un niveau.
- « À découvrir » classe tes œuvres restantes selon les genres et formats que tu as bien notés, ainsi que les œuvres en cours.
- La sauvegarde est locale au navigateur. Elle persiste après fermeture de l’onglet et redémarrage du serveur. Effacer les données du site efface la bibliothèque.

 
## Catalogue

L’onglet « Découvrir » présente toutes les œuvres de la base, avec une recherche par titre et auteur, des filtres de format, de genre, de période, de score et de récompenses, un tri et une pagination. Le bouton « Réinitialiser » affiche à nouveau toutes les œuvres. Les anciens liens vers « Catalogue » restent valides. « Pour moi » propose les recommandations issues de ta bibliothèque. Ouvre une fiche pour consulter ses critères, leurs sources et leurs dates de vérification, puis ajoute l’œuvre à la collection de ton choix. Les scores publics restent distincts de ta note personnelle.

Les règles initiales sont IMDb au moins 7/10 et 1 000 votes, Metacritic au moins 70/100 et 10 critiques professionnelles, Open Library au moins 3,5/5 et 20 avis. Une édition française explicitement identifiée dans Open Library est exigée pour chaque livre, y compris les livres primés. Les notes de lecteurs portent sur l’œuvre, toutes langues et éditions confondues. Le seuil de 20 avis pour les livres est un réglage initial.

Le catalogue livré contient un instantané réel, consultable sans relancer une collecte. Les photos distantes nécessitent une connexion. Les films IMDb gardent leurs titres de référence, parfois en anglais, et n’ont pas tous une affiche. Le bouton « Actualiser les sources » lance une collecte en arrière-plan. Laisse le serveur ouvert pendant la mise à jour. L’état des sources signale les collectes en cours, les interruptions et les limites d’accès. Les résultats précédents sont conservés en cas d’erreur, et Metacritic réutilise les pages déjà collectées pendant 24 heures.

Tu peux aussi actualiser depuis le Terminal sur macOS ou Linux.

```sh
python3 catalog.py
```

Pour une seule source, utilise par exemple `python3 catalog.py metacritic`, `python3 catalog.py books`, `python3 catalog.py imdb` ou `python3 catalog.py awards`. Les collectes simultanées sont verrouillées. Le téléchargement initial IMDb représente environ 230 Mo, mis en cache dans `data/cache/`. La collecte Metacritic lit le classement public de toutes les plateformes, jusqu’à atteindre les scores inférieurs à 70. Elle conserve les données précédentes en cas d’interruption et reprend les pages en cache.

La base active est `data/catalog.sqlite3`. L’instantané Metacritic est livré dans `data/metacritic-seed/*.part`, restauré dans `data/metacritic.json.gz`, puis appliqué à SQLite. Cette migration retire les anciens jeux Steam du catalogue et conserve leurs références dans une table historique pour retrouver les liens personnels quand le titre et l’année correspondent, ainsi que pour les jeux primés explicitement rapprochés. Au premier démarrage, elle est restaurée depuis l’instantané compressé livré dans `data/seed/`. Pour conserver un catalogue actualisé entre installations, copie aussi ce fichier. Tes collections personnelles restent dans le navigateur à leur adresse habituelle.

### Sources et couverture

- [IMDb](https://data.imdb.com/non-commercial-datasets/) fournit les notes, nombres de votes et caractéristiques des films, courts métrages et téléfilms. Les jeux de données sont destinés à un usage personnel et non commercial.
- [Open Library](https://openlibrary.org/dev/docs/api/search) fournit les notes de lecteurs et les références d’éditions françaises. Cette base collaborative peut contenir des erreurs bibliographiques.
- [Metacritic](https://www.metacritic.com/browse/game/) fournit les jeux PC et consoles, leurs genres, leur année, leurs couvertures et le Metascore de référence. Chaque jeu doit avoir au moins 70/100 et 10 critiques professionnelles. Les nombres de critiques et les plateformes sont conservés dans ses preuves. Le Metascore n’est pas une moyenne calculée par Planche entre plateformes. Les anciennes notes Steam sont retirées du catalogue. Les anciennes références Steam servent uniquement à conserver les liens avec les bibliothèques et récompenses existantes.
- Wikidata fournit les prix et nominations documentés pour les Oscars du meilleur film, Cannes, Berlin, Venise, Goncourt, Femina, Booker, International Booker, Pulitzer fiction, Hugo, Nebula et Game Awards. Seules les distinctions rattachées à une œuvre sont retenues. Les éditions françaises des livres sont vérifiées ensuite dans Open Library. La couverture dépend des contributions et de l’accès à Wikidata.
- Des distinctions vérifiées directement auprès de leurs organisateurs sont livrées dans `data/verified-awards.json` pour initialiser ce filtre lorsque la collecte internationale est limitée.

L’instantané livré comprend 7 515 jeux admissibles Metacritic. Son état et sa date sont affichés dans les sources. La collecte dépend de la disponibilité et de la structure des pages publiques de Metacritic. Le catalogue expose sa couverture réelle dans l’état des sources. Il ne représente pas l’ensemble des œuvres satisfaisant tous les critères envisagés.

 
## Cartes et parcours

Toutes les cartes utilisent un cadre portrait 2:3, un titre sur deux lignes et des scores alignés. Les jeux du catalogue utilisent les couvertures fournies par Metacritic. Les anciennes fiches personnelles peuvent conserver leur image d’origine. Les livres utilisent Open Library. Les affiches de films proviennent des résumés Wikipédia et sont cherchées à la demande, puis mises en cache. Une carte conserve son titre lorsqu’aucune image exploitable n’est disponible.

L’onglet « Parcours » utilise l’arborescence éditoriale de `data/taxonomy.json`. Seules les sous-listes contenant plus de trois œuvres (quatre minimum) distinctes sont publiées. Les sections et méta-listes devenues vides sont supprimées des parcours et du profil. Les méta-listes générales utilisent les genres ou pays explicitement renseignés, ainsi que les sous-listes conservées. Elles redeviennent accessibles même si aucune ancienne sous-liste thématique n’atteint le seuil. Des sous-listes Films, Livres en français et Jeux vidéo sont ajoutées quand le format compte au moins quatre œuvres. Leurs effectifs et leur progression sont recalculés sans doublon. Cyberpunk est une sous-liste de Science-fiction. Les prix et les nominations ont des méta-listes distinctes. Les sections intermédiaires servent uniquement à naviguer. La recherche retrouve toutes les sous-listes et le filtre permet de choisir une famille.

Une case représente une œuvre. Le contour gris indique une œuvre à découvrir, l’orange une œuvre en cours et la couronne violette une œuvre terminée. Clique sur une case pour ouvrir sa fiche, l’ajouter à ta bibliothèque ou modifier son statut. Une œuvre terminée valide toutes ses occurrences. Les pourcentages des méta-listes utilisent l’union des identifiants du catalogue, sans doublon.

Le fichier éditorial conserve les sujets possibles, mais seules les sélections atteignant le minimum de quatre œuvres apparaissent dans le site. L’affectation éditoriale reste partielle. Le premier ensemble relie les sélections Cyberpunk, Space opera et Post-apocalyptique par titres exacts, les créateurs par crédits exacts présents dans le catalogue et plusieurs prix par preuves sourcées avec distinction entre nominations et lauréats. Les listes sans affectation, ainsi que celles contenant une, deux ou trois œuvres, sont exclues des parcours et des trophées. Les œuvres restent soumises aux règles d’entrée du catalogue, dont l’édition française pour les livres. Les listes ne prétendent pas contenir toute l’œuvre d’un créateur.

### Profil et trophées

« Profil & trophées » rassemble les statistiques personnelles, la vitrine chronologique, les prochaines listes à terminer et tous les trophées filtrables par nom, famille, statut et métal. Les coupes originales en SVG s’inspirent des trophées de consoles. Le déblocage est automatique après une sauvegarde de la bibliothèque, et lors de l’ouverture des parcours ou du profil pour reprendre une bibliothèque existante.

- Bronze pour une sous-liste de 4 à 14 œuvres.
- Argent pour 15 à 49 œuvres.
- Or à partir de 50 œuvres.
- Platine pour une méta-liste dont toutes les sous-listes sont documentées et toutes les œuvres terminées.

Les listes de moins de quatre œuvres ne donnent aucun trophée. Les trophées historiques des listes retirées restent enregistrés localement, mais sont exclus du profil et de ses compteurs. Les sections intermédiaires ne donnent aucun trophée. La date, le métal et la version de sélection sont enregistrés au premier déblocage dans `planche.trophies.v1`, dans le stockage du navigateur. Un trophée acquis reste dans la vitrine après une modification du statut ou du catalogue. Effacer les données du navigateur efface aussi les trophées. Utilise la même adresse et le même port pour retrouver tes données personnelles.

Après installation de cette version, redémarre le serveur puis recharge la page. Depuis le dossier du projet, exécute `python3 server.py 8001` et ouvre `http://127.0.0.1:8001/#profil`.

Vérification des règles de progression et de trophées avec `python3 -m unittest discover -s tests` et `node tests/trophies.mjs`. Le serveur n’a aucune dépendance supplémentaire.

Les pays proviennent de la propriété « pays d’origine » de Wikidata. La première sélection concerne 131 œuvres. Les genres du catalogue de jeux proviennent de Metacritic, et les sujets des livres d’Open Library. Certaines anciennes fiches personnelles peuvent garder leurs métadonnées historiques. Les données manquantes sont omises. Les sources bibliographiques et les pays restent susceptibles d’erreurs de leurs catalogues d’origine.

La sélection de récompenses initiale comprend notamment les dix films nommés à l’Oscar du meilleur film 2024 et cinq lauréats des Game Awards, ainsi que les distinctions déjà présentes. Elle est documentée dans `data/verified-awards.json`. Les métadonnées complémentaires livrées sont appliquées au premier démarrage, y compris sur une installation existante.

Les icônes proviennent de Lucide, dont la licence figure dans `static/icons/LICENSE`.
