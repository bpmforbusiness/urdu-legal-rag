#!/usr/bin/env python3
"""Download the Urdu-translated central acts published by NCPUL."""
import os
import re
import subprocess
import sys
import urllib.parse

BASE = "https://www.urducouncil.nic.in"
ACTS_PAGE = BASE + "/acts"
OUT = os.path.expanduser("~/urdu_rag/data/raw")


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    page = subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", ACTS_PAGE],
                          capture_output=True, text=True).stdout
    paths = sorted({h.strip() for h in re.findall(r'href="([^"]*\.pdf[^"]*)"', page)})
    acts = [p for p in paths if "/acts/" in p]
    print(f"{len(acts)} act PDFs on the page")
    for p in acts:
        url = BASE + urllib.parse.quote(p, safe="/%")
        name = re.sub(r"[^A-Za-z0-9._-]+", "-",
                      urllib.parse.unquote(os.path.basename(p))).strip("-")
        dest = os.path.join(OUT, name)
        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            print(f"  have {name}")
            continue
        subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", "-o", dest,
                        "--max-time", "240", url], capture_output=True)
        ok = os.path.exists(dest) and open(dest, "rb").read(5) == b"%PDF-"
        print(f"  {'OK  ' if ok else 'FAIL'} {name}")
        if not ok and os.path.exists(dest):
            os.remove(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
