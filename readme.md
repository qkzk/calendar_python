---
title : Cahier de texte vers Calendar
author: qkzk
date: 2019/09/02

---

# How to

## setup

~~~
$ activate
$ pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib markdown pytz
~~~

## lancer :

~~~
$ calpy
~~~

ou

~~~
$ calpy 1 36
~~~

Utilise un alias vers le fichier `calpy.sh`
alias calpy="~/scripts/calpy.sh"

# Mettre à jour Calendar avec les données du cahier de texte

Ce programme est de met à jour Google Calendar avec les événements indiqués
dans un fichier .md.

Il est le complément de [Cahier texte generator](https://github.com/qkzk/cahier_texte_generator).

On l'appelle après avoir installé les requirements et crée les environnements
virtuels avec :

```shell
$ python3 calendar_python.py 1 36
```

où `1` est le numéro d'une période et `36` le numéro d'une semaine de la
période.

---


Principe :

1. Je tape les informations d'une journée dans mon cahier de texte .md
2. Je lance le programme avec le minimum d'information
3. Les détails et descriptions de l'événement sont ajoutés automatiquement
4. Si l'événement est nouveau, il est crée, sinon il est mis à jour.


# Incertitudes

- [x] est-ce que je vais vraiment gagner du temps ?
* [ ] Quelle interface ? Script avec Q/R/Confirmations ou Interface graphique
*
    Idéalement accessible depuis els machines avec lesquelles j'édite donc

    - [ ] GUI possible
    - [x] CLI possible
    - [ ] Server Web trop compliqué

# TODO

* gui avec Q/R

# DONE

* formater les descriptions en html
* créer un calendrier particulier pour l'appli
* se connecter à un calendar et retrieve les événements
* se connecter à un calendar et maj un événement
* se connecter à un calendar et trouver le prochain événement par sa date
* se connecter à calender et maj un evenetment
* lire les événements d'un fichier md existant
* màj les events
* créer des events
* cli avec Q/R et des couleurs
* multiple weeks mode. $ calpy, input a period, input multiple weeks separated
  by spaces
* multiple weeks from same period from command line

# Sources :

* the usual suspects : stackoverflow, python docs, sam & max etc.
* [google calendar API python ref](https://developers.google.com/calendar/quickstart/python?authuser=2)
