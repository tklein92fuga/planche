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
