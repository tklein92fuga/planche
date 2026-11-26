# Vérification visuelle des cartes et parcours

La référence fonctionnelle est la demande de reprendre les cartes illustrées et le principe de progression Khan Academy. La navigation générale et l’identité de Planche sont conservées. Les valeurs de progression proviennent de la bibliothèque, avec les statuts « À découvrir », « En cours » et « Terminé ».

## Références et preuves

- Grille Khan Academy fournie dans Screenshot 2026-11-24 at 03.10.55.png, image originale de 3438 × 1644 pixels, normalisée à 1719 × 822.
- Cartes illustrées fournies dans Screenshot 2026-11-24 at 03.12.23.png, image originale de 1776 × 654 pixels. Comparaison des proportions et de l’alignement de la rangée de cinq cartes.
- Rendu des parcours dans ../parcours-culturels.jpg, capturé dans le navigateur à 1719 × 822.
- Rendu des cartes dans ../cartes-oeuvres.jpg, capturé à 1719 × 822. Région comparée comprise entre les coordonnées 375,48 et 1567,584.
- Comparaisons côte à côte dans ../../work/comparaison-parcours.jpg et ../../work/comparaison-cartes.jpg.
- Vérification mobile à 390 × 844, capturée dans ../../work/parcours-mobile.jpg.

## Corrections effectuées

La première vérification des cartes a révélé une différence de largeur entre les affiches. Le centrage implicite des colonnes du bouton a été remplacé par une disposition verticale étirée. Les cinq cadres mesurent ensuite 195,20 × 292,80 pixels, avec moins de 0,02 pixel d’écart. Les titres réservent deux lignes et les scores occupent une ligne alignée.

La première grille de parcours montrait trente-deux cases par aperçu. Elle affiche désormais seize cases, commence par les œuvres déjà suivies et conserve l’accès paginé à la liste complète. Les cases reprennent le contour gris, le remplissage orange et la couronne violette des états de la référence.

Une capture réalisée pendant le changement de format a été remplacée par une capture stabilisée à 1719 × 822 avant la comparaison finale.

## Parcours vérifiés

- Ouverture d’une œuvre à partir de sa case.
- Ajout de Baldur’s Gate 3 à la bibliothèque de test.
- Passage au statut terminé, apparition de la couronne et mise à jour des compteurs et de l’XP.
- Navigation par genres, pays et récompenses.
- Détail d’une liste et passage à sa deuxième page.
- Affichage mobile sans débordement horizontal global.
- Aucune erreur JavaScript relevée dans la console du navigateur.

## Résultat

Aucun défaut visuel bloquant restant dans le périmètre vérifié. La disponibilité des couvertures et des pays dépend des sources. Le titre reste visible lorsqu’une couverture est absente. Les regroupements utilisent les métadonnées effectivement présentes.

final result: passed

## Parcours imbriqués et trophées — 24 novembre 2026

Référence fournie: profil PSN avec bandeau de statistiques, trophées par métal, liste filtrable et vitrine latérale. Adaptation à Planche avec arrondis, bleu nuit et accent vert, coupes SVG originales. Toutes les méta-listes et sous-listes de l’arborescence validée sont présentes. Les sélections non attribuées restent explicitement vides et ne déclenchent pas de récompense.

Vérifications: navigation Science-fiction → Cyberpunk, recherche de sous-listes, trois formats dans la liste Cyberpunk, profil avec trophée Larian Studios issu de la bibliothèque de test, filtre Débloqués, date dans la vitrine et absence d’erreurs JavaScript. Largeurs 390 et 1440 pixels sans débordement horizontal. Capture `../profil-trophees.jpg`. Les quatre tests Python et le scénario Node vérifient hiérarchie, union sans doublon, séparation lauréats/nominations, pagination, listes vides, conservation de la date et absence de double attribution. Origine de test 8002, bibliothèque de l’origine habituelle 8001 préservée.


## Méta-listes générales et source Metacritic — 24 novembre 2026

Les méta-listes générales proviennent du fichier d’arborescence initial. Genres et pays explicitement renseignés alimentent directement ces méta-listes. Les sous-listes éditoriales et les sous-listes par format ne sont publiées qu’à partir de quatre œuvres distinctes. Aucun sujet n’est déduit du seul titre d’une œuvre pour les règles générales.

Collecte des pages publiques Metacritic terminée au seuil inférieur à 70. Instantané de 7 515 jeux, tous avec un Metascore au moins égal à 70 et 10 critiques. Les jeux Steam ne sont plus servis par le catalogue. Liens avec les anciennes bibliothèques conservés par identifiants quand le rapprochement est certain. Test d’installation neuve et réouverture idempotente.

Vérification navigateur sur l’origine de test 8002, navigation Fantasy → Films et Livres, recherche Cyberpunk 2077, source Metacritic et preuve de 86/100 sur 106 critiques, couvertures affichées, aucune erreur JavaScript. Capture `../catalogue-metacritic.jpg`. Huit tests Python et scénario Node validés, incluant les seuils, la structure des pages, la migration et le filtre récompenses combiné au score.


## Sous-listes éditoriales et filtre de format — 24 novembre 2026

Suppression des sous-listes automatiques par format, seuil ramené à trois œuvres selon la demande. Ajout de 17 sélections par saga, réalisateur, acteur ou événement historique, sélectionnées par titre, année et format. Les décennies portent sur les années de sortie. Les anciennes sous-listes pertinentes continuent de fonctionner.

Nouvelle navigation Tout / Films / Jeux vidéo / Livres. Chaque vue filtre les membres, les compteurs et la pagination, sans modifier la sélection complète utilisée pour les trophées. Ajout d’icônes SVG originales pellicule, manette et livre sur chaque case et sur les couvertures de cartes.

Contrôles navigateur: neuf films de la Seconde Guerre mondiale, trilogies de trois films, filtre Jeux vidéo montrant uniquement des icônes de manette (120 cases), filtre Livres montrant uniquement des livres (43 cases). Capture `../parcours-sagas-filtres.jpg`. Largeur mobile 390 pixels, aucun débordement, les quatre boutons restent visibles. Aucune erreur JavaScript. Neuf tests Python et deux scénarios Node vérifient aussi la recherche pendant un changement de filtre et l’absence de trophée attribué pour la seule partie visible d’une liste mixte.


## Navigation en cours et retrait des icônes de format — 24 novembre 2026

L’accueil affiche uniquement les méta-listes sous forme de cartes. Chaque carte ouvre un cours avec ses sous-listes dans le menu latéral et une grille de progression par sous-liste. La recherche d’une sous-liste retrouve sa méta-liste au premier niveau. Suppression des icônes de format dans les cases, cartes et filtres. Les trophées restent disponibles sur le profil.

Horreur → Films de John Carpenter contient The Thing (1982), Halloween (1978), They Live (1988) et In the Mouth of Madness (1994), rapprochés par titre, année et format, sous réserve des critères du catalogue. Références: https://theofficialjohncarpenter.com/biography/ et https://theofficialjohncarpenter.com/credits/. Le compteur Horreur porte sur les quatre œuvres de cette sous-liste. Les méta-listes sans sous-listes sont retirées, y compris dans les projections par format.

Contrôle navigateur: aucun bouton d’œuvre à l’accueil, aucune icône de format dans le DOM, ouverture de Horreur puis John Carpenter et affichage des quatre titres, retour à la grille de méta-listes. Mobile 390 pixels sans débordement dans les deux vues. Aucune erreur JavaScript. Capture `../parcours-horreur-carpenter.jpg`. Neuf tests Python et deux tests Node validés.


## Métadonnées et alignements — 25 novembre 2026

Corrections motivées par les deux captures utilisateur: suppression du centrage implicite des titres dans leurs colonnes, alignement des lignes sur le haut, colonnes de largeur commune, espacement explicite entre barres et cases/légende. Mesures navigateur sur trois lignes de réalisateurs: même abscisse pour les titres (530 px) et les cases (766 px), même décalage vertical (28 px), espace cases/barres de 18 px. Fiche Keanu Reeves: espace barre/légende de 28 px.

Regroupements automatiques par métadonnées, minimum trois identifiants canoniques et déduplication des sélections identiques dans une méta-liste. Enrichissement de 453 jeux depuis leurs pages publiques Metacritic: développeurs, éditeurs et franchises explicitement déclarés. Pas de studios/éditeurs de films inventés. Recherche, critère et pagination de 40 sous-listes ajoutés dans les cours.

Contrôles de l’interface: filtrage sur les réalisateurs, Édités par Nintendo (128 œuvres), TPS (117 œuvres). Capture `../sous-listes-alignees.jpg`. Mobile 390 px: largeur du document 390 px, ligne 368 px, aucune erreur JavaScript. Onze tests Python et deux scénarios Node validés, dont la provenance des rôles de société, le seuil, les décennies et l’absence de regroupements générés identiques au sein d’une méta-liste.


## Fiches au survol et Goodreads — 26 novembre 2026

- 14 vérifications Python et les deux scénarios JavaScript de progression/trophées passent.
- Vérification dans le navigateur: The Thing (IMDb exact, offres JustWatch FR), L’art d’aimer (Goodreads 3,99/5 et édition française), Cyberpunk 2077 (Metacritic et Steam app/1091500).
- Clavier: focus sur case affiche la fiche, Flèche bas atteint Fermer, Échap ferme la fiche.
- La fiche est dans le viewport 1280×720 sans débordement horizontal; liste des offres défilable, lien de plateforme en premier. Le toucher est pris en charge par le gestionnaire de clic; pas de simulation tactile effectuée.
- Aucun prix de location n’est inféré. Les offres sont consultées à la demande et conservées 24 heures. La fiche de recherche remplace une correspondance non vérifiée.
- Snapshot portable: 846 rapprochements Goodreads dont 845 notes publiques actualisées et une note historique étiquetée 2017. Les livres sans rapprochement restent Open Library. Les éditions françaises sont obligatoires.
- Trois listes de courants psychologiques et quatre mouvements artistiques/littéraires vérifiés, tous à au moins trois œuvres; époques des livres par première publication.


## Dashboard de complétion — 26 novembre 2026

- Navigation réduite à Vue d’ensemble / Découvrir / Parcours. Les anciennes routes reviennent à l’accueil; les données personnelles sont conservées.
- Dashboard: compteurs uniques, listes commencées, prochaine liste à finir, progression en barres et cases, rythme réel des sept jours, vitrine, recherche et filtres sur sous-listes / méta-listes / trophées (12 par page). Les aperçus limités indiquent l’effectif complet.
- Découvrir ne propose plus d’actualisation ni d’ajout; Terminé et En cours modifient le statut partagé. Les fiches proposent aussi Remettre à découvrir. Les fiches au survol reprennent ces actions.
- Vérification réelle: The Shawshank Redemption passe À découvrir → En cours (conservé après rechargement) → Terminé; compteur du dashboard 4 → 5 et case cochée; retour À découvrir ramène le compteur à 4. L’œuvre utilisée pour ce test a retrouvé son statut initial.
- Le bouton Continuer ouvre la sous-liste concernée avec le même compteur et les mêmes états.
- Bureau 1280×720 et mobile 390×844: aucun débordement horizontal. Navigation à trois liens sur mobile. Les barres exposent leurs valeurs aux aides de lecture.
- 16 tests Python, scénarios JavaScript trophées et filtres, et nouveau test des statuts partagés passent. Le nouveau test conserve critiques/notes, met à jour les doublons canoniques et permet l’annulation du statut.
- En-têtes de revalidation et version d’interface mis à jour pour éviter une ancienne interface en cache.

## Séries TV IMDb — 26 novembre 2026

- Instantané officiel IMDb: 8 628 séries (6 813 tvSeries et 1 815 tvMiniSeries), note globale ≥7/10 et ≥1 000 votes. Les épisodes sont exclus; films et séries restent deux formats distincts.
- Filtre TV ajouté au catalogue, aux parcours et au dashboard. La projection TV contient 326 sous-listes sans doublon exact et avec au moins trois œuvres.
- Dates de début/fin issues d’IMDb; durée indicative, sans total de visionnage inventé. Une case correspond à une série ou mini-série entière.
- Vérification réelle dans le navigateur: Breaking Bad, 2008–2013, 9,5/10, affiche et fiche JustWatch française vérifiée par IMDb, offres Netflix et achat. Les offres portent un avertissement de variation par saison.
- Passage Terminé: compteur TV 1 et huit listes commencées; retour À découvrir: compteur 0, aucune liste commencée. Le statut de test a été réinitialisé.
- 18 tests Python passent, ainsi que les scénarios JavaScript de trophées, filtres, statuts et imports. Tests ajoutés pour les seuils, le rejet des épisodes, la séparation film/série et l’installation idempotente sans suppression des films.
- Les nouveaux instantanés s’appliquent aussi aux installations existantes. La progression personnelle reste dans le navigateur.


## Exclusion des talk-shows — 26 novembre 2026

- Migration sur la base existante: 109 entrées retirées (106 TV et 3 films), avec suppression de leurs caches de visuels et liens. Zéro genre Talk-Show restant dans works.
- Résultat: 8 522 séries et mini-séries, 16 801 films; 320 sous-listes en vue TV. Livres et jeux inchangés.
- Les relevés historiques sont filtrés avant installation; IMDb et les autres collectes refusent les nouveaux titres portant ce genre. Une modification de la règle force la migration même si le relevé compressé est identique.
- 19 tests Python passent, incluant le rejet du genre Talk-Show quel que soit le format, l’élimination des anciennes entrées et l’installation répétée sans réapparition.


## Liens vers les notes

IMDb (films/séries) et Metacritic (jeux) sont accessibles sur les cartes et dans les fiches au survol, en plus des liens JustWatch/Steam existants. Les destinations sont validées; les jeux sans référence Metacritic vérifiée n’obtiennent pas de lien inventé. Test `node tests/source-links.mjs` ajouté; progression et trophées inchangés.
