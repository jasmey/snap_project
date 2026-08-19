# Split metadata.csv + copurchasing.csv into one pair of CSVs per genre.


import argparse
import csv
import re
import sys
from collections import defaultdict

csv.field_size_limit(1 << 31)

TRAILING_ID = re.compile(r"\[\d+\]$")

DEFAULT_GENRES = [
    "Science Fiction & Fantasy",
    "Parenting & Families",
    "Cooking, Food & Wine",
]

ID, GROUP, CATS = 0, 3, 8 


def top_genres(categories_list):
    # Level-1 shelves (directly below Books > Subjects) for one product.
    out = set()
    for path in categories_list.split(" ; "):
        nodes = [TRAILING_ID.sub("", n).strip()
                 for n in path.split("|") if n.strip()]
        if len(nodes) >= 3 and nodes[0] == "Books" and nodes[1] == "Subjects":
            out.add(nodes[2])
    return out


def slug(name): #filename-safe version of a genre name
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metadata", nargs="?", default="amazon_meta_clean_filtered.csv")
    ap.add_argument("copurchasing", nargs="?", default="amazon_copurchasing_clean_filtered.csv")
    ap.add_argument("--genres", nargs="+", default=DEFAULT_GENRES)
    ap.add_argument("--edges", choices=["both", "either"], default="either")
    ap.add_argument("--include-neighbors", action="store_true",
                    help="with --edges either, also emit metadata for the "
                         "out-of-genre endpoints")
    ap.add_argument("--prefix", default="", help="output filename prefix")
    args = ap.parse_args()

    genres = args.genres
    want = {g.casefold(): g for g in genres}

    # 1) which node ids belong to each genre
    members = {g: set() for g in genres}
    header = None
    with open(args.metadata, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        for row in r:
            if not row:
                continue
            if header is None and not row[ID].lstrip("-").isdigit():
                header = row
                continue
            if row[GROUP] != "Book":
                continue
            nid = int(row[ID])
            for g in top_genres(row[CATS]):
                target = want.get(g.casefold())
                if target:
                    members[target].add(nid)

    for g in genres:
        if not members[g]:
            print(f"warning: no books matched genre {g!r}", file=sys.stderr)

    # 2) filter edges based on #1
    edge_header = None
    kept = {g: 0 for g in genres}
    neighbors = {g: set() for g in genres}
    touched = {g: set() for g in genres}
    writers, handles = {}, []
    for g in genres:
        fh = open(f"{args.prefix}copurchasing_{slug(g)}.csv", "w",
                  newline="", encoding="utf-8")
        handles.append(fh)
        writers[g] = csv.writer(fh, lineterminator="\n")

    with open(args.copurchasing, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        for row in r:
            if not row or len(row) < 2:
                continue
            if edge_header is None and not row[0].lstrip("-").isdigit():
                edge_header = row
                for g in genres:
                    writers[g].writerow(row)
                continue
            a, b = int(row[0]), int(row[1])
            for g in genres:
                m = members[g]
                ina, inb = a in m, b in m
                if (ina and inb) if args.edges == "both" else (ina or inb):
                    writers[g].writerow([a, b])
                    kept[g] += 1
                    touched[g].update((a, b))
                    if not ina:
                        neighbors[g].add(a)
                    if not inb:
                        neighbors[g].add(b)
    for fh in handles:
        fh.close()

    # 3) metadata for the nodes that were kept in #2
    emit = {}
    for g in genres:
        s = set(members[g])
        if args.edges == "either" and args.include_neighbors:
            s |= neighbors[g]
        emit[g] = s

    writers, handles = {}, []
    for g in genres:
        fh = open(f"{args.prefix}metadata_{slug(g)}.csv", "w",
                  newline="", encoding="utf-8")
        handles.append(fh)
        w = csv.writer(fh, lineterminator="\n")
        if header:
            w.writerow(header)
        writers[g] = w

    written = defaultdict(int)
    with open(args.metadata, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        for row in r:
            if not row or not row[ID].lstrip("-").isdigit():
                continue
            nid = int(row[ID])
            for g in genres:
                if nid in emit[g]:
                    writers[g].writerow(row)
                    written[g] += 1
    for fh in handles:
        fh.close()

    # output
    print(f"edge rule: {args.edges}\n")
    w = max(len(g) for g in genres)
    print(f"{'genre'.ljust(w)}  {'books':>8}  {'edges':>9}  {'in-graph':>9}  {'meta rows':>9}")
    for g in genres:
        isolated = len(members[g] - touched[g])
        print(f"{g.ljust(w)}  {len(members[g]):>8,}  {kept[g]:>9,}  "
              f"{len(members[g]) - isolated:>9,}  {written[g]:>9,}")
    print("\n(in-graph = genre books that appear in at least one kept edge; "
          "the rest are isolated)")

    pairs = [(a, b) for i, a in enumerate(genres) for b in genres[i + 1:]]
    overlaps = [(a, b, len(members[a] & members[b])) for a, b in pairs]
    if any(n for *_, n in overlaps):
        print("\nbooks in more than one of these genres (they appear in both files):")
        for a, b, n in overlaps:
            if n:
                print(f"  {a} & {b}: {n:,}")


if __name__ == "__main__":
    sys.exit(main())