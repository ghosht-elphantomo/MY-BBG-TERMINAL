"""Fusionne l'archive BRVM locale avec celle de main (deux exécutions concurrentes peuvent archiver la même séance).
  python3 scripts/archive_merge.py OURS_DIR
OURS_DIR contient brvm.json et brvm_daily.csv produits par cette exécution ; seed/ contient la version de main.
CSV : union des lignes, clé (date, ticker), la version de cette exécution l'emporte. JSON : la photo la plus récente (ts)."""
import csv, json, os, sys

ours = sys.argv[1]
seed = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "seed")


def rows(p):
    if not os.path.exists(p):
        return None, []
    with open(p, newline="", encoding="utf8") as f:
        r = list(csv.reader(f))
    return (r[0], r[1:]) if r else (None, [])


h1, a = rows(os.path.join(seed, "brvm_daily.csv"))
h2, b = rows(os.path.join(ours, "brvm_daily.csv"))
hdr = h2 or h1
merged = {}
for r in a + b:
    if len(r) >= 2:
        merged[(r[0], r[1])] = r
order = sorted(merged, key=lambda k: k[0])  # tri stable par date ; ordre d'origine conservé dans une même séance
with open(os.path.join(seed, "brvm_daily.csv"), "w", newline="", encoding="utf8") as f:
    w = csv.writer(f, lineterminator="\n")
    if hdr:
        w.writerow(hdr)
    w.writerows(merged[k] for k in order)

pj, oj = os.path.join(seed, "brvm.json"), os.path.join(ours, "brvm.json")
if os.path.exists(oj):
    mine = json.load(open(oj, encoding="utf8"))
    theirs = json.load(open(pj, encoding="utf8")) if os.path.exists(pj) else {}
    if (mine.get("ts") or 0) >= (theirs.get("ts") or 0):
        with open(oj, encoding="utf8") as s, open(pj, "w", encoding="utf8") as d:
            d.write(s.read())
print("archive fusionnée :", len(order), "lignes")
