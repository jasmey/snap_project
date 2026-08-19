# Filters the cross-filtered data
#!/usr/bin/env python3
"""
Keep only group == "Book", then report how the genre taxonomy is distributed.

    python genre_stats.py metadata.csv
    python genre_stats.py metadata.csv --level 2 --top 30
    python genre_stats.py metadata.csv --keep books_only.csv --out genre_stats.csv

"Genre" = the node of the Amazon category path at --level, counting from the
first level below "Books > Subjects".  Level 1 gives the ~30 big shelves
(Religion & Spirituality, Nonfiction, ...); level 2 gives sub-genres
(Christianity, Politics, ...).

Two percentages are reported, because a book sits in several category paths:
  * %books  - share of books that touch the genre at least once (sums > 100%)
  * %paths  - share of all category-path assignments (sums to 100%)
"""

import argparse
import csv
import re
import sys
from collections import Counter

csv.field_size_limit(1 << 31)          # reviews_list / categories_list are huge

TRAILING_ID = re.compile(r"\[\d+\]$")


def genres_of(categories_list, level):
    """map genre labels in csv to set of genre names (at a given level), return count per"""
    found = set()
    off_taxonomy = 0
    for path in categories_list.split(" ; "):
        path = path.strip()
        if not path:
            continue
        nodes = [TRAILING_ID.sub("", n).strip()
                 for n in path.split("|") if n.strip()]
        # canonical book path: Books | Subjects | <genre> | <subgenre> | ...
        if len(nodes) >= 2 and nodes[0] == "Books" and nodes[1] == "Subjects":
            if len(nodes) > 1 + level:
                found.add(" > ".join(nodes[2:2 + level]))
            else:                      # path stops short of the requested depth
                found.add(" > ".join(nodes[2:]) or "(unclassified)")
        else:
            off_taxonomy += 1
    return found, off_taxonomy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metadata", nargs="?", default="amazon_meta_clean_filtered.csv")
    ap.add_argument("--level", type=int, default=1,
                    help="taxonomy depth below Books>Subjects (default 1)")
    ap.add_argument("--top", type=int, default=25, help="rows to print (0 = all)")
    ap.add_argument("--keep", help="write the Book-only rows to this CSV")
    ap.add_argument("--out", help="write the genre table to this CSV")
    args = ap.parse_args()

    books = 0
    total_rows = 0
    group_counts = Counter()
    books_per_genre = Counter()      # a book counts once per genre
    paths_per_genre = Counter()      # a book counts once per category path
    uncategorised = 0
    off_taxonomy_paths = 0

    with open(args.metadata, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        writer = None
        keep_fh = None
        if args.keep:
            keep_fh = open(args.keep, "w", newline="", encoding="utf-8")
            writer = csv.DictWriter(keep_fh, fieldnames=reader.fieldnames)
            writer.writeheader()

        for row in reader:
            total_rows += 1
            group_counts[row["group"]] += 1
            if row["group"] != "Book": #non-books get filtered out
                continue
            books += 1
            if writer:
                writer.writerow(row)

            genres, off = genres_of(row["categories_list"] or "", args.level)
            off_taxonomy_paths += off
            if not genres:
                uncategorised += 1
                continue
            for g in genres:
                books_per_genre[g] += 1
            # weight each book's paths so every book contributes exactly 1.0
            for g in genres:
                paths_per_genre[g] += 1 / len(genres)

        if keep_fh:
            keep_fh.close()

    total_weight = sum(paths_per_genre.values()) or 1 #avoid divide-by-zero if no books
    table = [
        (g, n, 100 * n / books, 100 * paths_per_genre[g] / total_weight) 
        for g, n in books_per_genre.most_common()
    ]

    print(f"rows read      : {total_rows:,}")
    print("by group       : " + ", ".join(
        f"{g or '(blank)'} {c:,} ({100*c/total_rows:.1f}%)"
        for g, c in group_counts.most_common()))
    print(f"books kept     : {books:,}")
    print(f"  of which with no Books>Subjects path: {uncategorised:,}")
    print(f"  category paths outside that taxonomy: {off_taxonomy_paths:,}")
    print(f"  distinct genres at level {args.level}: {len(table):,}\n")

    shown = table if args.top == 0 else table[:args.top]
    width = max((len(g) for g, *_ in shown), default=5)
    print(f"{'genre'.ljust(width)}  {'books':>9}  {'%books':>7}  {'%paths':>7}")
    for g, n, pb, pp in shown:
        print(f"{g.ljust(width)}  {n:>9,}  {pb:>6.2f}%  {pp:>6.2f}%")
    if args.top and len(table) > args.top:
        rest = sum(n for _, n, _, _ in table[args.top:])
        print(f"{'... other ' + str(len(table)-args.top) + ' genres':<{width}}  {rest:>9,}")

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["genre", "books", "pct_of_books", "pct_of_category_paths"])
            for g, n, pb, pp in table:
                w.writerow([g, n, f"{pb:.4f}", f"{pp:.4f}"])
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    sys.exit(main())