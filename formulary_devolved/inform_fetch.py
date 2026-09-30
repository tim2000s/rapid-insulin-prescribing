"""Navigate the NHS Wales InForm formulary (ASP.NET WebForms) by replaying tree postbacks.

InForm pages carry no stable per-drug URL: every section is reached by posting back the
BNF tree node. This script replays those postbacks and saves each page it lands on, so
that what was read can be checked later.

Usage: python3 inform_fetch.py <prefix> <out_stem> <node> [<node> ...]
where each node is "search:<text>" or a postback argument such as "sN||06" and later ones are taken from
links on the page before.
"""
import re, sys, html, requests

BASE = "https://formulary.wales.nhs.uk/indexNew.aspx?prefixUrl="
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Chrome/126"}


def hidden_fields(page):
    return {m.group(1): html.unescape(m.group(2)) for m in
            re.finditer(r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', page)}


def postback(s, url, page, target, arg, extra=None):
    data = hidden_fields(page)
    data["__EVENTTARGET"] = target
    data["__EVENTARGUMENT"] = arg
    data.update(extra or {})
    r = s.post(url, data=data, headers=UA, timeout=60)
    r.raise_for_status()
    return r.text


def main():
    prefix, stem, nodes = sys.argv[1], sys.argv[2], sys.argv[3:]
    url = BASE + prefix
    s = requests.Session()
    page = s.get(url, headers=UA, timeout=60).text
    for i, node in enumerate(nodes):
        if node.startswith("search:"):
            # The search box submits the text field together with the button name.
            page = postback(s, url, page, "", "", {"txtSearch": node[7:], "btnSearch": "Search"})
        else:
            target, arg = ("bnfTree", node) if "||" in node else node.split("::", 1)
            page = postback(s, url, page, target, arg)
        open(f"{stem}_{i}.html", "w").write(page)
        print(f"{stem}_{i}.html", len(page))


if __name__ == "__main__":
    main()
