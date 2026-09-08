#!/bin/bash
set -e
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
mkdir -p /tmp/sn-ql-scrape
for path in football/player-of-the-season tv-schedule betting-tips-today football/player-transfers; do
  out="/tmp/sn-ql-scrape/$(echo "$path" | tr / _).html"
  code=$(curl -sL -A "$UA" -H 'Accept: text/html' -H 'Accept-Language: en-US,en;q=0.9' -o "$out" -w '%{http_code}' "https://www.sofascore.com/$path")
  bytes=$(wc -c < "$out" | tr -d ' ')
  echo "STATUS $code BYTES $bytes PATH $path"
  python3 - <<PY
from pathlib import Path
p=Path("$out")
t=p.read_text('utf-8','replace')[:160].replace('\n',' ')
print('HEAD', t)
PY
done
