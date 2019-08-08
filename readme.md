---
title : Cahier de texte vers Calendar
author: qkzk
date: 2019/08/08
---

# Mettre à jour Calendar avec les données du cahier de texte

L'objectif de ce programme est de mettre à jour Google Calendar pour faire
apparaître dans les descriptions de chaque événement les informations d'un
cours et d'une journée de cours

Il faudrait que ce soit :

* fiable
* automatisé
* avec des retours faciles à comprendre
* facile à utiliser

Principe :

1. Je tape les informations d'une journée dans mon cahier de texte .md
2. Je lance le programme avec le minimum d'information
3. Les détails et descriptions de l'événement sont ajoutés automatiquement

# Beaucoup d'étapes il faut découper

# Incertitudes

* peut-on formater directement les descriptions ? Ce serait pratique d'avoir
    au moins des listes et du gras

* est-ce que je vais vraiment gagner du temps ?
* Quelle interface ? Script avec Q/R/Confirmations ou Interface graphique
    Idéalement accessible depuis els machines avec lesquelles j'édite donc
    GUI possible
    CLI possible
    Server Web encore plus difficile et compliqué

# TODO
* gui / cli avec Q/R

# DONE
* créer un calendrier particulier pour l'appli
* se connecter à un calendar et retrieve les événements
* se connecter à un calendar et maj un événement
* se connecter à un calendar et trouver le prochain événement par sa date
* se connecter à calender et maj un evenetment
