"""Find archived GAmSi Bundesbericht PDFs by probing the URL pattern
/media/dokumente/quartalsberichte/<year>/q<quarter>_<serial>/Bundesbericht_GAmSi_<yyyymm>_konsolidiert.pdf.
The serial is not documented, so a range is probed. Seven workers."""
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def probe(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, method="HEAD", headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
        return u if r.status == 200 else None
    except Exception:
        return None

if __name__ == "__main__":
    urls = [f"https://www.gkv-gamsi.de/media/dokumente/quartalsberichte/{y}/q{q}_{i}/Bundesbericht_GAmSi_{y}{q*3:02d}_konsolidiert.pdf"
            for y in range(2017, 2027) for q in range(1, 5) for i in range(8, 37)]
    with ThreadPoolExecutor(7) as ex:
        found = sorted(u for u in ex.map(probe, urls) if u)
    Path(__file__).with_name("gamsi_bundesbericht_urls.txt").write_text("\n".join(found) + "\n")
    print("\n".join(found))
