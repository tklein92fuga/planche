# Planche — chaque case compte

Application personnelle de suivi de films, séries TV, livres et jeux vidéo, sans compte ni dépendance à installer. Python 3.10 ou plus récent et un navigateur moderne suffisent.

## Démarrer

Dans le dossier du projet:

```sh
python3 server.py 8001
```

Ouvrir http://127.0.0.1:8001. Si ce port est occupé, choisir un autre numéro. Pour retrouver sa progression existante, conserver la même adresse et le même port: les données personnelles sont enregistrées dans le navigateur.

Après une mise à jour, arrêter puis relancer le serveur et recharger la page. Les fichiers de l’interface sont revalidés pour éviter de conserver une ancienne version.

## Trois pages

- **Vue d’ensemble** est le dashboard principal: œuvres terminées et en cours, sous-listes complètes, listes à poursuivre, progression en barres et cases, activité des sept derniers jours et vitrine des trophées. Les onglets Sous-listes / Méta-listes / Trophées proposent recherche, filtres et pagination de 12 cartes.
- **Découvrir** propose le catalogue, sa recherche et ses filtres. Les boutons **Terminé** et **En cours** enregistrent directement le statut. Une fiche permet aussi de remettre une œuvre **À découvrir**. Aucun ajout à une bibliothèque ou collection n’est nécessaire et aucun bouton d’actualisation n’est affiché.
- **Parcours** conserve la navigation Méta-liste → Sous-listes → Œuvres. Une case représente une œuvre; son état se répercute dans toutes les listes où elle apparaît.

Les anciennes pages Bibliothèque, Profil & trophées, Collections, Objectifs & badges et Pour moi sont retirées. Leurs anciennes adresses ouvrent le dashboard. Les données personnelles déjà enregistrées (y compris notes et critiques) sont conservées, même si leurs anciennes pages ne sont plus proposées.

Les compteurs de progression utilisent les identifiants canoniques: une œuvre est comptée une seule fois. Les doublons locaux d’une même œuvre reçoivent le même statut. Les imports déjà rapprochés par le catalogue sont reconnus même si leur titre traduit est différent. Les autres imports sont rapprochés par titre, format et année; une correspondance non identifiée n’est pas devinée.

L’import CSV/XLSX reste accessible en haut de page (8 Mo maximum). La première ligne doit contenir une colonne Titre; Type permet un fichier mixte. L’enrichissement facultatif recherche les champs manquants et les visuels disponibles. Le fichier d’exemple est `static/exemple.csv`. Les données d’exemple peuvent être retirées avec le bouton en bas de la navigation.

## Progression et trophées

Une sous-liste contient au moins trois œuvres distinctes. Les listes vides et les sections sans sous-liste sont masquées. Les plateformes de commercialisation ne génèrent plus de sous-listes. Les listes portant exactement sur les mêmes œuvres sont dédupliquées à l’échelle des parcours, puis après filtrage par format. Les chevauchements partiels sont autorisés.

Les sous-listes sont sélectionnées éditorialement ou regroupées à partir de métadonnées explicites: genres, types de jeux, décennies, sagas, développeurs, éditeurs, auteurs, pays. Les mouvements artistiques et psychologiques sont documentés dans `data/editorial-lists.json`. Les époques de livres désignent la première publication, pas le cadre historique de l’intrigue. Les métadonnées peuvent comporter des erreurs.

Terminer toutes les œuvres d’une sous-liste donne un trophée: bronze (3–14 œuvres), argent (15–49), or (50 et plus). Terminer toute une méta-liste donne un platine. Les sections intermédiaires ne donnent aucun trophée. Un filtre de format ne permet pas de gagner le trophée d’une liste mixte incomplète.

Le trophée conserve sa date et son métal une fois obtenu, même si un statut change ensuite. Les trophées de listes retirées restent enregistrés mais ne figurent plus dans la vitrine. Le dashboard distingue les listes actuellement complètes des trophées historiquement obtenus. Les aperçus montrent un nombre limité de cases, avec l’effectif complet indiqué; ouvrir une liste donne accès à toutes ses œuvres.

## Fiches au survol

Une fiche commune aux trois formats apparaît au survol ou au focus d’une case. Flèche bas donne accès à ses boutons et liens, Échap la ferme. Sur écran tactile, toucher la case ouvre la fiche. Les actions Terminé / En cours / Remettre à découvrir y sont également disponibles.

- Films: fiche JustWatch française vérifiée par identifiant IMDb ou titre original et année; offres numériques en France (abonnement, location, achat, gratuit), avec date de consultation. Les offres physiques et celles d’autres pays sont exclues. Les prix ne sont pas inférés. Cache de 24 heures.
- Jeux: lien Steam direct si l’identifiant est connu ou si le titre et l’année correspondent à une fiche de jeu. Sinon, lien de recherche Steam. Les jeux consoles ne sont pas tous commercialisés sur Steam.
- Livres: fiche Goodreads identifiée et lien distinct vers une édition française. Sinon, recherche Goodreads explicitement indiquée.

Une source indisponible ou une correspondance incertaine donne un lien de recherche, sans disponibilité inventée. La présentation utilise les styles de Planche.

## Catalogue et sources

La couverture dépend des sources accessibles et ne prétend pas être exhaustive. Une seule règle d’admission suffit:

- IMDb ≥ 7/10 et au moins 1 000 votes pour les films.
- Metacritic ≥ 70/100 et au moins 10 critiques professionnelles pour les jeux, sur la version de référence affichée par Metacritic. Steam sert de destination commerciale, pas de base de sélection.
- Goodreads en priorité (au moins 3,5/5 et 20 avis pour les nouveaux livres), Open Library en complément. Une édition française explicitement identifiée est obligatoire. Les notes portent sur l’œuvre, toutes langues et éditions confondues.
- Prix ou nomination documenté dans Wikidata, en sélection internationale; une récompense d’auteur ne remplace pas une récompense de l’œuvre.

Le relevé livré relie 846 livres à Goodreads: 845 notes publiques actualisées et une note du relevé historique goodbooks-10k de 2017, signalée dans la fiche. Les autres livres conservent leur référence Open Library. Le rapprochement est conservateur, par titre et auteur. Aucun texte de critique de lecteur n’est copié et aucune protection d’accès n’est contournée.

Sources: [IMDb datasets](https://developer.imdb.com/non-commercial-datasets/), [Metacritic](https://www.metacritic.com/browse/game/), [Goodreads](https://www.goodreads.com/), [Open Library](https://openlibrary.org/dev/docs/api/search), [Wikidata](https://www.wikidata.org/), [JustWatch France](https://www.justwatch.com/fr). Le rapprochement initial des livres s’appuie sur [goodbooks-10k](https://github.com/zygmuntz/goodbooks-10k), sous CC BY-SA 4.0; attribution dans `data/GOODREADS-DATA-LICENSE.txt`.

Les couvertures de jeux viennent de Metacritic; celles des livres d’Open Library; les affiches de films de résumés Wikipédia, recherchées et mises en cache à la demande. Une fiche conserve son titre sans image disponible. Les icônes Lucide sont accompagnées de leur licence dans `static/icons/LICENSE`.

L’actualisation des sources reste possible depuis le dossier du projet, sans CTA dans l’interface:

```sh
python3 catalog.py
python3 goodreads_books.py
python3 enrich_metadata.py
```

La collecte peut être longue. `enrich_metadata.py` enrichit les crédits de jeux explicitement déclarés par Metacritic; la couverture livrée concerne 453 jeux. `goodreads_books.py` réutilise son cache et conserve une référence historique lorsqu’une fiche publique n’est pas accessible.

## Sauvegarde et vérification

Le catalogue utilise SQLite (`data/catalog.sqlite3`), restauré au premier démarrage à partir des instantanés livrés dans `data/seed/`, `data/metacritic-seed/` et `data/goodreads-seed/`. La progression reste locale au navigateur (`planche.v1`), les trophées dans `planche.trophies.v1`. Effacer les données du navigateur les efface aussi. Aucun statut personnel n’est envoyé sur GitHub.

```sh
python3 -m unittest discover -s tests
node tests/trophies.mjs
node tests/paths-filter.mjs
node tests/progress-state.mjs
```

Les tests vérifient notamment les identités, les éditions françaises, les filtres, l’absence de listes identiques, les statuts partagés et les conditions des trophées. Le serveur n’a pas de dépendance supplémentaire.

## Séries TV

Le catalogue livré ajoute **8 522 séries et mini-séries IMDb** (6 709 `tvSeries`, 1 813 `tvMiniSeries`), avec une note globale d’au moins 7/10 et 1 000 votes, comme pour les films. Les épisodes individuels `tvEpisode`, téléfilms et émissions spéciales ne sont pas assimilés à des séries. Les films déjà présents restent dans leur format.

Le filtre Séries TV fonctionne dans Découvrir, Parcours et le dashboard. Une case représente une série ou une mini-série complète: aucun décompte par saison ou épisode n’est proposé. Les statuts et trophées suivent les mêmes règles que les autres œuvres. Les regroupements par métadonnées comportent au moins trois œuvres et restent dédupliqués. La vue Séries TV contient initialement 320 sous-listes.

Les fiches affichent l’année de début et, lorsqu’elle existe dans la source, l’année de fin. Une année de fin manquante n’est pas interprétée comme une preuve de diffusion en cours. La durée IMDb est indicative, jamais multipliée pour inventer une durée totale. Les affiches et offres sont recherchées auprès de la fiche JustWatch de la série, vérifiée par identifiant IMDb; les offres peuvent dépendre de la saison. Wikipédia sert de complément de visuel lorsque possible.

L’instantané `data/imdb-tv-seed/` s’applique au démarrage, y compris à une installation existante, sans effacer les films ou la progression personnelle. `python3 imdb_tv.py` renouvelle uniquement cet instantané TV; `python3 catalog.py imdb` réactualise l’ensemble films et séries IMDb. Les références, genres, années et notes viennent des [datasets IMDb](https://data.imdb.com/non-commercial-datasets/), réservés à l’usage personnel non commercial selon leurs conditions. La fiche IMDb reste accessible dans les preuves de chaque titre.

L’import CSV/XLSX reconnaît Série TV, séries, TV show et mini-série dans la colonne Type.

Les œuvres portant le genre IMDb « Talk-Show » sont exclues du catalogue, y compris des anciennes installations. Le filtre s’applique à l’installation de l’instantané et aux prochaines collectes IMDb. Le nettoyage a retiré 106 séries et 3 entrées classées comme films; les parcours et leurs compteurs sont recalculés. Les notes et statuts personnels conservés dans le navigateur ne sont pas effacés.
