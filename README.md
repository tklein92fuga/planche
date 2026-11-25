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

Les règles initiales sont IMDb au moins 7/10 et 1 000 votes, Metacritic au moins 70/100 et 10 critiques professionnelles, Goodreads en priorité (au moins 3,5/5 et 20 avis pour les nouveaux livres), Open Library en complément. Une édition française explicitement identifiée dans Open Library est exigée pour chaque livre, y compris les livres primés. Les notes de lecteurs portent sur l’œuvre, toutes langues et éditions confondues. Le seuil de 20 avis pour les livres est un réglage initial.

Le catalogue livré contient un instantané réel, consultable sans relancer une collecte. Les photos distantes nécessitent une connexion. Les films IMDb gardent leurs titres de référence, parfois en anglais, et n’ont pas tous une affiche. Le bouton « Actualiser les sources » lance une collecte en arrière-plan. Laisse le serveur ouvert pendant la mise à jour. L’état des sources signale les collectes en cours, les interruptions et les limites d’accès. Les résultats précédents sont conservés en cas d’erreur, et Metacritic réutilise les pages déjà collectées pendant 24 heures.

Tu peux aussi actualiser depuis le Terminal sur macOS ou Linux.

```sh
python3 catalog.py
```

Pour une seule source, utilise par exemple `python3 catalog.py metacritic`, `python3 catalog.py books`, `python3 catalog.py imdb` ou `python3 catalog.py awards`. Les collectes simultanées sont verrouillées. Le téléchargement initial IMDb représente environ 230 Mo, mis en cache dans `data/cache/`. La collecte Metacritic lit le classement public de toutes les plateformes, jusqu’à atteindre les scores inférieurs à 70. Elle conserve les données précédentes en cas d’interruption et reprend les pages en cache.

La base active est `data/catalog.sqlite3`. L’instantané Metacritic est livré dans `data/metacritic-seed/*.part`, restauré dans `data/metacritic.json.gz`, puis appliqué à SQLite. Cette migration retire les anciens jeux Steam du catalogue et conserve leurs références dans une table historique pour retrouver les liens personnels quand le titre et l’année correspondent, ainsi que pour les jeux primés explicitement rapprochés. Au premier démarrage, elle est restaurée depuis l’instantané compressé livré dans `data/seed/`. Pour conserver un catalogue actualisé entre installations, copie aussi ce fichier. Tes collections personnelles restent dans le navigateur à leur adresse habituelle.

### Sources et couverture

- [IMDb](https://data.imdb.com/non-commercial-datasets/) fournit les notes, nombres de votes et caractéristiques des films, courts métrages et téléfilms. Les jeux de données sont destinés à un usage personnel et non commercial.
- [Open Library](https://openlibrary.org/dev/docs/api/search) fournit les références d’éditions françaises et les notes des livres dont le rapprochement Goodreads reste à vérifier. Cette base collaborative peut contenir des erreurs bibliographiques.
- [Metacritic](https://www.metacritic.com/browse/game/) fournit les jeux PC et consoles, leurs genres, leur année, leurs couvertures et le Metascore de référence. Chaque jeu doit avoir au moins 70/100 et 10 critiques professionnelles. Les nombres de critiques et les plateformes sont conservés dans ses preuves. Le Metascore n’est pas une moyenne calculée par Planche entre plateformes. Les anciennes notes Steam sont retirées du catalogue. Les anciennes références Steam servent uniquement à conserver les liens avec les bibliothèques et récompenses existantes.
- Wikidata fournit les prix et nominations documentés pour les Oscars du meilleur film, Cannes, Berlin, Venise, Goncourt, Femina, Booker, International Booker, Pulitzer fiction, Hugo, Nebula et Game Awards. Seules les distinctions rattachées à une œuvre sont retenues. Les éditions françaises des livres sont vérifiées ensuite dans Open Library. La couverture dépend des contributions et de l’accès à Wikidata.
- Des distinctions vérifiées directement auprès de leurs organisateurs sont livrées dans `data/verified-awards.json` pour initialiser ce filtre lorsque la collecte internationale est limitée.

L’instantané livré comprend 7 515 jeux admissibles Metacritic. Son état et sa date sont affichés dans les sources. La collecte dépend de la disponibilité et de la structure des pages publiques de Metacritic. Le catalogue expose sa couverture réelle dans l’état des sources. Il ne représente pas l’ensemble des œuvres satisfaisant tous les critères envisagés.

 
## Cartes et parcours

Toutes les cartes utilisent un cadre portrait 2:3, un titre sur deux lignes et des scores alignés. Les jeux du catalogue utilisent les couvertures fournies par Metacritic. Les anciennes fiches personnelles peuvent conserver leur image d’origine. Les livres utilisent Open Library. Les affiches de films proviennent des résumés Wikipédia et sont cherchées à la demande, puis mises en cache. Une carte conserve son titre lorsqu’aucune image exploitable n’est disponible.

L’onglet « Parcours » utilise l’arborescence éditoriale de `data/taxonomy.json`. Seules les sous-listes contenant au moins trois œuvres distinctes sont publiées. Les sections et méta-listes devenues vides sont supprimées des parcours et du profil. La navigation commence par une grille de méta-listes, sans œuvres ni sous-listes affichées au premier niveau. Cliquer sur une méta-liste ouvre sa page de cours: titre, progression, menu latéral de ses sous-listes et une ligne de cases par sous-liste. Seules les méta-listes possédant des sous-listes disponibles sont publiées. La progression correspond à l’union des œuvres contenues dans ces sous-listes, sans doublon. Les sous-listes génériques par format sont supprimées. Horreur contient notamment « Films de John Carpenter », une sélection de quatre films admissibles, référencée sur le site officiel du réalisateur. Les nouvelles sélections regroupent des sagas (Retour vers le futur, Star Wars, Harry Potter, Le Seigneur des anneaux, Le Hobbit, Batman, John Wick), des réalisateurs (Nolan, Kubrick, Miyazaki), des interprètes (DiCaprio, Reeves) et des événements historiques (guerres mondiales, Vietnam, guerre froide et conquête spatiale). Les œuvres sont rapprochées par titre, année et format, depuis `data/editorial-lists.json`. Les époques du cinéma regroupent les sorties par décennie, sans confondre année de sortie et époque de l’histoire. Leurs effectifs et leur progression sont recalculés sans doublon. Cyberpunk est une sous-liste de Science-fiction. Les prix et les nominations ont des méta-listes distinctes. Les sections intermédiaires servent uniquement à naviguer. La recherche retrouve toutes les sous-listes et le filtre permet de choisir une famille.

La barre Tout / Films / Jeux vidéo / Livres filtre les parcours, leurs œuvres, leurs compteurs et leur pagination. Une liste doit contenir au moins trois œuvres du format choisi pour apparaître dans cette vue. Les filtres, cases et cartes n’utilisent plus d’icônes de format. Les cases conservent leurs couleurs de progression et les formats restent indiqués en texte dans les fiches et listes détaillées. Les trophées utilisent toujours la sélection complète, même lorsqu’un filtre masque une partie des œuvres.

Une case représente une œuvre. Le contour gris indique une œuvre à découvrir, l’orange une œuvre en cours et la couronne violette une œuvre terminée. Clique sur une case pour ouvrir sa fiche, l’ajouter à ta bibliothèque ou modifier son statut. Une œuvre terminée valide toutes ses occurrences. Les pourcentages des méta-listes utilisent l’union des identifiants du catalogue, sans doublon.

Le fichier éditorial conserve les sujets possibles, mais seules les sélections atteignant le minimum de trois œuvres apparaissent dans le site. L’affectation éditoriale reste partielle. Le premier ensemble relie les sélections Cyberpunk, Space opera et Post-apocalyptique par titres exacts, les créateurs par crédits exacts présents dans le catalogue et plusieurs prix par preuves sourcées avec distinction entre nominations et lauréats. Les listes sans affectation, ainsi que celles contenant une ou deux œuvres, sont exclues des parcours et des trophées. Les œuvres restent soumises aux règles d’entrée du catalogue, dont l’édition française pour les livres. Les listes ne prétendent pas contenir toute l’œuvre d’un créateur.

### Profil et trophées

« Profil & trophées » rassemble les statistiques personnelles, la vitrine chronologique, les prochaines listes à terminer et tous les trophées filtrables par nom, famille, statut et métal. Les coupes originales en SVG s’inspirent des trophées de consoles. Le déblocage est automatique après une sauvegarde de la bibliothèque, et lors de l’ouverture des parcours ou du profil pour reprendre une bibliothèque existante.

- Bronze pour une sous-liste de 3 à 14 œuvres.
- Argent pour 15 à 49 œuvres.
- Or à partir de 50 œuvres.
- Platine pour une méta-liste dont toutes les sous-listes sont documentées et toutes les œuvres terminées.

Les listes de moins de trois œuvres ne donnent aucun trophée. Les trophées historiques des listes retirées restent enregistrés localement, mais sont exclus du profil et de ses compteurs. Les sections intermédiaires ne donnent aucun trophée. La date, le métal et la version de sélection sont enregistrés au premier déblocage dans `planche.trophies.v1`, dans le stockage du navigateur. Un trophée acquis reste dans la vitrine après une modification du statut ou du catalogue. Effacer les données du navigateur efface aussi les trophées. Utilise la même adresse et le même port pour retrouver tes données personnelles.

Après installation de cette version, redémarre le serveur puis recharge la page. Depuis le dossier du projet, exécute `python3 server.py 8001` et ouvre `http://127.0.0.1:8001/#profil`.

Vérification des règles de progression et de trophées avec `python3 -m unittest discover -s tests` et `node tests/trophies.mjs` et `node tests/paths-filter.mjs`. Le serveur n’a aucune dépendance supplémentaire.

Les pays proviennent de la propriété « pays d’origine » de Wikidata. La première sélection concerne 131 œuvres. Les genres du catalogue de jeux proviennent de Metacritic, et les sujets des livres de Goodreads lorsqu’ils sont rapprochés, sinon d’Open Library. Certaines anciennes fiches personnelles peuvent garder leurs métadonnées historiques. Les données manquantes sont omises. Les sources bibliographiques et les pays restent susceptibles d’erreurs de leurs catalogues d’origine.

La sélection de récompenses initiale comprend notamment les dix films nommés à l’Oscar du meilleur film 2024 et cinq lauréats des Game Awards, ainsi que les distinctions déjà présentes. Elle est documentée dans `data/verified-awards.json`. Les métadonnées complémentaires livrées sont appliquées au premier démarrage, y compris sur une installation existante.

Les icônes proviennent de Lucide, dont la licence figure dans `static/icons/LICENSE`.


## Sous-listes issues des métadonnées

Les parcours génèrent aussi des sous-listes par genre, type de jeu (FPS, TPS, JRPG…), décennie de sortie, saga, studio/développeur, éditeur, auteur et pays de production lorsque le champ existe. Chaque sélection contient au moins trois œuvres distinctes. Les regroupements ayant exactement les mêmes membres au sein d’une méta-liste sont dédupliqués. Aucune catégorie générique fondée uniquement sur le format n’est ajoutée.

La navigation reste Méta-liste → Sous-listes → Œuvres. La page d’un cours propose une recherche de sous-liste, un filtre par critère et une pagination de 40 sous-listes pour garder une page réactive. La pagination des œuvres reste de 60. Les transferts volumineux de l’API sont compressés lorsque le navigateur le permet.

Les années, genres et auteurs viennent du catalogue existant. Les plateformes des jeux sont référencées dans les preuves Metacritic. Le fichier `data/company-metadata.json` enrichit 453 jeux avec les rôles explicitement crédités (Developer / Publisher) et les franchises déclarées par Metacritic. Cette couverture reste partielle; les studios ou éditeurs absents des sources ne sont pas déduits du titre. Les décennies regroupent les années de sortie, sans prétendre dater le cadre historique du récit.

Pour réactualiser cet enrichissement facultatif, lancer `python3 enrich_metadata.py` depuis le dossier du projet. Le script examine les titres les mieux notés ou les plus commentés, réutilise les pages en cache et enregistre les résultats de façon atomique. Il ne change pas les critères de note du catalogue. Le serveur relit automatiquement les sélections lorsque le fichier de métadonnées change.

Les barres des fiches sont séparées de la légende par 28 pixels; les barres des sous-listes restent à 18 pixels des cases. Les titres et les cases utilisent des colonnes communes, avec un placement adapté au mobile.


## Fiches au survol et liens externes

Survole une case de parcours pour ouvrir une fiche homogène avec couverture, titre, année, genres et note sourcée. Elle reste ouverte lorsque le pointeur rejoint ses liens. Au clavier, une case affiche la fiche à la prise de focus; Flèche bas donne accès aux boutons et liens, Échap la ferme. Sur écran tactile, toucher une case ouvre la fiche, puis le bouton permet de gérer l’œuvre dans la bibliothèque.

Pour les films, le serveur recherche une fiche JustWatch française et vérifie l’identifiant IMDb ou, à défaut, le titre original et l’année. Il affiche les offres numériques en France (abonnement, location, achat, gratuit) et leur date de consultation. Les offres physiques et celles d’autres pays sont exclues. Le lien mène à la fiche JustWatch. Les prix ne sont pas affichés. Les résultats sont conservés 24 heures. Si la correspondance ou la source est indisponible, une recherche JustWatch est proposée sans inventer d’offre.

Les jeux pointent vers Steam lorsque l’identifiant est déjà connu ou que titre et année de sortie correspondent à une fiche de jeu. Les autres proposent une recherche Steam; certains jeux consoles n’y sont pas commercialisés. La sélection de qualité reste fondée sur Metacritic. Les livres rapprochés ouvrent leur fiche Goodreads, avec un lien distinct vers l’édition française identifiée.

## Livres et Goodreads

Le relevé livré rapproche 846 livres avec Goodreads par titre et auteur, avec une édition française identifiée: 845 notes de lecteurs ont été consultées sur des fiches publiques, et une note provient du relevé historique goodbooks-10k de 2017, explicitement signalé. Les autres livres gardent leur référence Open Library, jusqu’à vérification. Les notes concernent l’œuvre, pas uniquement ses lecteurs francophones. La base n’est pas un export exhaustif de Goodreads.

`python3 goodreads_books.py` renouvelle les fiches publiques accessibles en réutilisant le cache local. Le script s’arrête sur une vérification d’accès et ne contourne pas les protections du site. Le rapprochement initial s’appuie sur [goodbooks-10k](https://github.com/zygmuntz/goodbooks-10k), distribué sous CC BY-SA 4.0; attribution dans `data/GOODREADS-DATA-LICENSE.txt`. Aucun texte de critique n’est copié. Le relevé compressé est livré dans `data/goodreads-seed/` et appliqué automatiquement aux installations existantes, sans toucher aux statuts et notes personnels.

Les parcours ajoutent l’expressionnisme allemand, le néoréalisme italien, la Nouvelle Vague, le modernisme littéraire (Joyce et Woolf), la psychanalyse (Freud et Fromm), la psychologie analytique (Jung), et la psychologie humaniste et quête de sens. Ils comprennent aussi des époques de publication des livres: avant 1500, XVIe–XVIIe, XVIIIe, XIXe, 1900–1945, 1946–1999 et depuis 2000. Une époque désigne l’année de première publication, pas le cadre du récit. Les affectations par mouvement sont éditoriales et leurs sources figurent dans `data/editorial-lists.json`. Le seuil de trois œuvres reste obligatoire.

Les plateformes de commercialisation restent dans les métadonnées des jeux, mais ne génèrent plus de sous-listes ni de trophées dans les parcours.
