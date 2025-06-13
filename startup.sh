#!/bin/bash
pip install --upgrade pip
pip install -r requirements.txt
gunicorn -w 1 -b 0.0.0.0:8000 src.serge.mainserge:app
