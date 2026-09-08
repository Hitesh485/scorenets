#!/bin/bash
set -e
sudo tar -xf /tmp/sn_nav_fix_deploy.tar -C /var/www/scorenet
sudo chown -R www-data:www-data \
  /var/www/scorenet/brand/auth.js \
  /var/www/scorenet/brand/boot.js \
  /var/www/scorenet/brand/brand.css
rm -f /tmp/sn_nav_fix_deploy.tar
echo DEPLOY_OK
python3 - <<'PY'
from pathlib import Path
import re
t=Path('/var/www/scorenet/football/player-transfers/index.html').read_text(encoding='utf-8',errors='replace')
for k in ['auth.js','boot.js','brand.css']:
 m=re.search(rf'{k}\?v=[^\"]+', t)
 print(m.group(0) if m else f'missing {k}')
PY
