import argparse
import csv
import re
import sys
import pandas as pd
from collections import defaultdict



def fileReduction(metaFile, edgeFile):
    # obtain the metadata and edgedata csv files
    df_meta = pd.read_csv(metaFile)
    df_edge = pd.read_csv(edgeFile)

    # sort by get nodes with the highest degree

    outDegree = df_edge['from_node_id'].value_counts()
    inDegree = df_edge['to_node_id'].value_counts()
    totalDegree = outDegree.add(inDegree, fill_value=0)
    tops = totalDegree.head(3000).index

    reducedEdges = df_edge[
        df_edge['from_node_id'].isin(tops) & df_edge['to_node_id'].isin(tops)
    ]

    reducedMeta = df_meta[df_meta['id'].isin(tops)]
    baseMeta = metaFile.removesuffix(".csv")
    baseEdge = edgeFile.removesuffix(".csv")
    newMeta = baseMeta + "_reduced.csv"
    newEdge = baseEdge + "_reduced.csv"
    reducedMeta.to_csv(newMeta, index=False)
    reducedEdges.to_csv(newEdge, index=False)



def main():

    fileReduction("metadata_science_fiction_fantasy.csv", "copurchasing_science_fiction_fantasy.csv")
    fileReduction("metadata_parenting_families.csv", "copurchasing_parenting_families.csv")
    fileReduction("metadata_cooking_food_wine.csv", "copurchasing_cooking_food_wine.csv")


if __name__ == "__main__":
    sys.exit(main())