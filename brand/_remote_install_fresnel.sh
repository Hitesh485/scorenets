#!/bin/bash
set -e
sudo tar -xf /tmp/sn_fresnel_deploy.tar -C /var/www/scorenet
sudo chown www-data:www-data \
  /var/www/scorenet/brand/brand.css \
  /var/www/scorenet/football/player-transfers/index.html \
  /var/www/scorenet/football/player-of-the-season/index.html \
  /var/www/scorenet/tv-schedule/index.html \
  /var/www/scorenet/betting-tips-today/index.html
rm -f /tmp/sn_fresnel_deploy.tar
echo DEPLOY_OK
grep -o 'brand.css?v=[^"]*' /var/www/scorenet/football/player-transfers/index.html | head -1
