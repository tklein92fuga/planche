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
