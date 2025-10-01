#!/usr/bin/env bash
set -e
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env || true
export PYTHONUNBUFFERED=1
python -m app.bot.main
