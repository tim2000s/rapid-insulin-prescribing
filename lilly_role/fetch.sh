#!/bin/zsh
# usage: fetch.sh NAME URL  -> captures/NAME.(html|pdf) plus .txt, appends to access_log.csv
name=$1; url=$2
cd "$(dirname $0)"
ua="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
tmp=captures/$name.tmp
code=$(curl --http1.1 -sSL -m 240 -A "$ua" -H "Accept-Language: en-GB,en;q=0.9" -o $tmp -w "%{http_code}" "$url")
[ -f $tmp ] || { echo "$name,000,fetch-failed,$(date -u +%Y-%m-%dT%H:%MZ),\"$url\"" >> access_log.csv; echo "$name FAILED"; exit 1; }
type=$(file -b --mime-type $tmp)
case $type in
  application/pdf) mv $tmp captures/$name.pdf; pdftotext -layout captures/$name.pdf captures/$name.txt 2>/dev/null;;
  *) mv $tmp captures/$name.html; python3 html2txt.py captures/$name.html;;
esac
echo "$name,$code,$type,$(date -u +%Y-%m-%dT%H:%MZ),\"$url\"" >> access_log.csv
echo "$name $code $type $(wc -c < captures/$name.* | tail -1)"
