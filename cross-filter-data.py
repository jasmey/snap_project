"""
Filter amazon_meta_clean.csv and amazon_copurchasing_clean.csv to only include nodes referenced in both
"""

import argparse
import csv
import os
import sys


def read_metadata_ids(path):
    # convert metadata into a dict of id:row
    rows = {}
    header = None
    with open(path, "r", encoding="utf-8", newline="") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            first = line.split(",", 1)[0].strip().strip('"')
            if i == 0 and not first.lstrip("-").isdigit():
                header = line          # file has a header row -> keep it
                continue
            rows[int(first)] = line
    return header, rows


def read_edges(path):
    # convert copurchasing data into a list of edges (from_node_id, to_node_id)
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if r and len(r) >= 2]
    header = None
    if rows and not rows[0][0].lstrip("-").isdigit():
        header = rows.pop(0)
    edges = [(int(a), int(b)) for a, b, *_ in rows]
    return header, edges


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metadata", nargs="?", default="amazon_meta_clean.csv")
    ap.add_argument("copurchasing", nargs="?", default="amazon_copurchasing_clean.csv")
    ap.add_argument("--prune-isolated", action="store_true",
                    help="iterate until no node is left without edges") #remove all disconnected nodes
    args = ap.parse_args()

    meta_header, meta_rows = read_metadata_ids(args.metadata)
    edge_header, edges = read_edges(args.copurchasing)

    meta_ids = set(meta_rows)
    edge_nodes = {n for e in edges for n in e}

    keep = meta_ids & edge_nodes
    kept_edges = [e for e in edges if e[0] in keep and e[1] in keep]

    if args.prune_isolated: #isolated nodes won't give us useful insights
        while True:
            still_connected = {n for e in kept_edges for n in e}
            new_keep = keep & still_connected
            if new_keep == keep:
                break
            keep = new_keep
            kept_edges = [e for e in kept_edges if e[0] in keep and e[1] in keep]

### write the filtered data to new files
    meta_out = _suffixed(args.metadata)
    edge_out = _suffixed(args.copurchasing)

    with open(meta_out, "w", encoding="utf-8", newline="") as f:
        if meta_header:
            f.write(meta_header)
        for nid in sorted(keep):
            f.write(meta_rows[nid])

    with open(edge_out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        if edge_header:
            w.writerow(edge_header)
        w.writerows(kept_edges)

    print(f"metadata:     {len(meta_ids):>9,} -> {len(keep):>9,} rows   ({meta_out})")
    print(f"copurchasing: {len(edges):>9,} -> {len(kept_edges):>9,} edges  ({edge_out})")
    dropped_meta = len(meta_ids - keep)
    dropped_nodes = len(edge_nodes - meta_ids)
    print(f"  {dropped_meta:,} metadata ids had no edges; "
          f"{dropped_nodes:,} edge endpoints had no metadata row")


def _suffixed(path):
    root, ext = os.path.splitext(path)
    return f"{root}_filtered{ext}"


if __name__ == "__main__":
    sys.exit(main())