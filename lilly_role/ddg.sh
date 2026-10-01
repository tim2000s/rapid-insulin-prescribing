#!/bin/zsh
# usage: ddg.sh NAME "query" -> captures/ddg_NAME.html, prints result titles and URLs
cd "$(dirname $0)"
curl -sS -m 40 -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36" --data-urlencode "q=$2" "https://html.duckduckgo.com/html/" -o captures/ddg_$1.html
python3 - captures/ddg_$1.html <<'PY'
import re,sys,html,urllib.parse
t=open(sys.argv[1]).read()
for m in re.finditer(r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</a>',t,re.S):
    u=m.group(1); q=urllib.parse.parse_qs(urllib.parse.urlparse(u).query).get('uddg',[u])[0]
    print('*',html.unescape(re.sub('<[^>]+>','',m.group(2)))[:110],'\n ',q,'\n ',html.unescape(re.sub('<[^>]+>','',m.group(3)))[:220])
PY
