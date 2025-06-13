#!/bin/bash

# Mise à jour de pip
pip install --upgrade pip

# Installation des dépendances
pip install -r requirements.txt

# Lancement de l’application Flask avec gunicorn
gunicorn -w 1 -b 0.0.0.0:8000 src.serge.mainserge:app
