import re
import csv
import pandas as pd

def parse_amazon_dataset(file_path, output_csv_path):
    all_links = []
    # Stream the file line-by-line to avoid large memory usage and
    # robustly skip comments/blank/malformed lines.
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 2:
                # skip malformed lines
                continue
            from_node_id, to_node_id = parts[0], parts[1]
            try:
                from_node_id = int(from_node_id)
                to_node_id = int(to_node_id)
            except ValueError:
                # skip lines where node ids are not integers
                continue
            all_links.append((from_node_id, to_node_id))
        
    df = pd.DataFrame(all_links, columns=['from_node_id', 'to_node_id'])
    
    df.to_csv(output_csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"Success! Processed {len(df)} items into {output_csv_path}")

# Run the program (Change these filenames to match your local computer setup)
parse_amazon_dataset("amazon-copurchasing.txt", "amazon_copurchasing_clean.csv")
