#!/usr/bin/env bash

set -e

VENV_DIR=".venv"

echo "=== Google Scholar Scraper — Environment Setup ==="

if [ ! -d "$VENV_DIR" ]; then
    echo "[+] Creating virtual environment in '$VENV_DIR' …"
    python3 -m venv "$VENV_DIR"
else
    echo "[~] Virtual environment '$VENV_DIR' already exists, skipping creation."
fi

echo "[+] Activating environment and installing dependencies …"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -r requirements.txt

echo ""
echo "=== Setup complete ==="
echo ""
echo "To activate the environment in future sessions:"
echo "    source $VENV_DIR/bin/activate"
echo ""
echo "Usage examples:"
echo "    python web-scraper.py -k \"machine learning\" -p 5"
echo "    python web-scraper.py -k \"sobriété informatique\" -p 10 --year-low 2020 --year-high 2024"
echo "    python web-scraper.py -k \"deep learning\" -p 20 -o my_results.csv"
echo "    python web-scraper.py --help"
