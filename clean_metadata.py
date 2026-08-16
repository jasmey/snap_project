import re
import csv
import pandas as pd

def parse_amazon_dataset(file_path, output_csv_path):
    all_products = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        blocks = f.read().split("\n\n")
        
    for block in blocks:
        if not block.strip():
            continue
            
        product = {
            'id': '', 'asin': '', 'title': '', 'group': '', 
            'salesrank': '', 'similar_count': '0', 'similar_asins': '',
            'categories_count': '0', 'categories_list': '',
            'reviews_total': '0', 'reviews_downloaded': '0', 'reviews_avg_rating': '0',
            'reviews_list': ''
        }
        
        categories = []
        reviews = []
        
        for line in block.split('\n'):
            line_str = line.strip()
            if not line_str:
                continue
                
            if line_str.startswith('Id:'):
                product['id'] = line_str.split(':', 1)[1].strip()
            elif line_str.startswith('ASIN:'):
                product['asin'] = line_str.split(':', 1)[1].strip()
            elif line_str.startswith('title:'):
                product['title'] = line_str.split(':', 1)[1].strip()
            elif line_str.startswith('group:'):
                product['group'] = line_str.split(':', 1)[1].strip()
            elif line_str.startswith('salesrank:'):
                product['salesrank'] = line_str.split(':', 1)[1].strip()
                
            elif line_str.startswith('similar:'):
                parts = line_str.split(':', 1)[1].strip().split()
                if parts:
                    product['similar_count'] = parts[0]
                    product['similar_asins'] = ";".join(parts[1:]) 
                    
            elif line_str.startswith('categories:'):
                product['categories_count'] = line_str.split(':', 1)[1].strip()
                
            elif line_str.startswith('|'):
                categories.append(line_str)
                
            elif line_str.startswith('reviews:'):
                total_m = re.search(r'total:\s*(\d+)', line_str)
                down_m = re.search(r'downloaded:\s*(\d+)', line_str)
                avg_m = re.search(r'avg rating:\s*([\d.]+)', line_str)
                
                product['reviews_total'] = total_m.group(1) if total_m else '0'
                product['reviews_downloaded'] = down_m.group(1) if down_m else '0'
                product['reviews_avg_rating'] = avg_m.group(1) if avg_m else '0'
                
            elif re.match(r'^\d{4}-\d{1,2}-\d{1,2}', line_str):
                parts = line_str.split()
                date = parts[0]
                
                cust = re.search(r'cutomer:\s*(\S+)', line_str)
                rating = re.search(r'rating:\s*(\d+)', line_str)
                votes = re.search(r'votes:\s*(\d+)', line_str)
                helpful = re.search(r'helpful:\s*(\d+)', line_str)
                
                rev_str = f"date:{date}|user:{cust.group(1) if cust else ''}|score:{rating.group(1) if rating else ''}|votes:{votes.group(1) if votes else ''}|help:{helpful.group(1) if helpful else ''}"
                reviews.append(rev_str)
        
        product['categories_list'] = " ; ".join(categories)
        product['reviews_list'] = " ; ".join(reviews)
        
        all_products.append(product)
        
    df = pd.DataFrame(all_products)
    
    df.to_csv(output_csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"Success! Processed {len(df)} items into {output_csv_path}")

# Run the program (Change these filenames to match your local computer setup)
parse_amazon_dataset("amazon-meta.txt", "amazon_meta_clean.csv")
