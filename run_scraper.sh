#!/bin/bash
set -euo pipefail

# Directory definitions
REPO_DIR="/root/dev/gold-silver"
LOG_FILE="${REPO_DIR}/cron.log"
PYTHON_BIN="${REPO_DIR}/.venv/bin/python"

# Export necessary environment variables for cron
export HOME="/root"
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Append all output with timestamps to cron.log
exec >> >(while IFS= read -r line; do echo "[$(date '+%Y-%m-%d %H:%M:%S')] $line"; done >> "$LOG_FILE") 2>&1

echo "=== Starting Daily Gold & Silver Scraper ==="

cd "$REPO_DIR"

# Sync with remote repository
git pull --rebase origin main || true

# Execute scraper script
"$PYTHON_BIN" scraper.py

# Check for modifications in rates.json
if git diff --quiet rates.json; then
    echo "No updates to rates.json. Already up to date."
else
    echo "rates.json updated. Committing and pushing to GitHub..."
    git config user.name "Pranab"
    git config user.email "72617824+PranabZz@users.noreply.github.com"
    git add rates.json
    git commit -m "chore(rates): update gold and silver rates for $(date +'%Y-%m-%d') [skip ci]"
    git push origin main
    echo "Successfully pushed update to GitHub."
fi

echo "=== Finished Scraper Run ==="
