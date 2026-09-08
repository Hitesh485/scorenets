#!/bin/bash
set -e
sudo tar -xf /tmp/sn_ql_deploy.tar -C /var/www/scorenet
sudo chown -R www-data:www-data \
  /var/www/scorenet/brand/auth.js \
  /var/www/scorenet/brand/boot.js \
  /var/www/scorenet/football/player-transfers \
  /var/www/scorenet/football/player-of-the-season \
  /var/www/scorenet/tv-schedule \
  /var/www/scorenet/betting-tips-today \
  /var/www/scorenet/assets/www.sofascore.com
rm -f /tmp/sn_ql_deploy.tar
echo DEPLOY_OK
wc -c \
  /var/www/scorenet/football/player-transfers/index.html \
  /var/www/scorenet/football/player-of-the-season/index.html \
  /var/www/scorenet/tv-schedule/index.html \
  /var/www/scorenet/betting-tips-today/index.html
python3 - <<'PY'
from pathlib import Path
import re
t = Path("/var/www/scorenet/index.html").read_text(encoding="utf-8", errors="replace")
m = re.search(r"auth\.js\?v=[^\"]+", t)
print(m.group(0) if m else "no-auth-ref")
PY
