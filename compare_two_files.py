import csv
from pathlib import Path
from collections import Counter
import pandas as pd
import re
import hashlib  # ADD THIS for faster comparison


def detect_delimiter(sample):
    try:
        return csv.Sniffer().sniff(
            sample, delimiters=[",", "\t", ";", "|"]
        ).delimiter
    except Exception:
        return "\t"


def read_table(path):
    ext = Path(path).suffix.lower()

    if ext in (".xls", ".xlsx"):
        df = pd.read_excel(path, dtype=str)
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            sample = f.read(4096)
        delim = detect_delimiter(sample)
        # OPTIMIZATION: Use C engine for CSV (faster)
        df = pd.read_csv(path, sep=delim, dtype=str, engine="c", low_memory=False)

    return df.fillna("")


def normalize_numeric(text):
    """
    Normalize numeric strings to handle decimal variations.
    """
    if not isinstance(text, str):
        text = str(text)
    
    text = text.strip()
    
    # Check if it's a number
    if re.match(r'^-?\d*\.?\d+$', text):
        try:
            num = float(text)
            if num.is_integer():
                return str(int(num))
            else:
                # Remove trailing zeros
                return ('%.10f' % num).rstrip('0').rstrip('.')
        except (ValueError, TypeError):
            return text.lower()
    
    return text.lower()


def normalize_cell(text):
    """
    Normalize cell content
    """
    if pd.isna(text) or text == "":
        return []
    
    text = normalize_numeric(str(text))
    
    if not text:
        return []
    
    # Split by comma or whitespace
    parts = []
    for part in text.split(','):
        parts.extend(part.split())
    
    return [part.strip() for part in parts if part.strip()]


def normalize_row(row):
    """
    Convert a full row into a sorted tuple for consistent comparison
    """
    values = []
    for cell in row:
        values.extend(normalize_cell(cell))
    
    return tuple(sorted(values))


# OPTIMIZATION: Add hash-based quick comparison
def get_file_hash(df):
    """Create a hash of the entire dataframe for quick comparison"""
    # Convert dataframe to string and hash it
    df_str = df.to_string(index=False, header=False)
    return hashlib.md5(df_str.encode()).hexdigest()


def compare_files(file1_path, file2_path, debug=False):
    """
    Compare two files and return detailed results
    OPTIMIZED for large files
    """
    try:
        # OPTIMIZATION: Quick file size check
        import os
        size1 = os.path.getsize(file1_path)
        size2 = os.path.getsize(file2_path)
        
        # If sizes are very different, files can't match
        if abs(size1 - size2) > 1000:  # More than 1KB difference
            if debug:
                print(f"File size mismatch: {size1} vs {size2}")
            return False
        
        df1 = read_table(file1_path)
        df2 = read_table(file2_path)
        
        # OPTIMIZATION: Quick shape comparison
        if df1.shape != df2.shape:
            if debug:
                print(f"Shape mismatch: {df1.shape} vs {df2.shape}")
            return False
        
        # OPTIMIZATION: Quick hash comparison for identical files
        hash1 = get_file_hash(df1)
        hash2 = get_file_hash(df2)
        
        if hash1 == hash2:
            if debug:
                print("Files are identical (hash match)")
            return True
        
        # OPTIMIZATION: Sample first 1000 rows for quick mismatch detection
        sample_size = min(1000, len(df1), len(df2))
        df1_sample = df1.head(sample_size)
        df2_sample = df2.head(sample_size)
        
        rows1_sample = [normalize_row(r) for r in df1_sample.values.tolist()]
        rows2_sample = [normalize_row(r) for r in df2_sample.values.tolist()]
        
        if Counter(rows1_sample) != Counter(rows2_sample):
            if debug:
                print("Sample rows don't match - files are different")
            return False
        
        # Full comparison only if sample matches
        rows1 = [normalize_row(r) for r in df1.values.tolist()]
        rows2 = [normalize_row(r) for r in df2.values.tolist()]
        
        # Use Counter for comparison
        counter1 = Counter(rows1)
        counter2 = Counter(rows2)
        
        match = counter1 == counter2
        
        if debug or not match:
            print(f"\n{'='*50}")
            print(f"COMPARISON RESULTS")
            print(f"{'='*50}")
            print(f"File 1: {file1_path}")
            print(f"File 2: {file2_path}")
            print(f"Rows in file 1: {len(rows1)}")
            print(f"Rows in file 2: {len(rows2)}")
            print(f"Unique rows in file 1: {len(set(rows1))}")
            print(f"Unique rows in file 2: {len(set(rows2))}")
            print(f"Match: {match}")
            
            if not match:
                print(f"\n{'='*50}")
                print(f"DIFFERENCES FOUND")
                print(f"{'='*50}")
                
                # Find rows only in file1
                unique_to_1 = set(counter1.keys()) - set(counter2.keys())
                if unique_to_1:
                    print(f"\nRows ONLY in File 1: {len(unique_to_1)}")
                    for i, row in enumerate(list(unique_to_1)[:5]):
                        print(f"  {i+1}. {row}")
                
                # Find rows only in file2
                unique_to_2 = set(counter2.keys()) - set(counter1.keys())
                if unique_to_2:
                    print(f"\nRows ONLY in File 2: {len(unique_to_2)}")
                    for i, row in enumerate(list(unique_to_2)[:5]):
                        print(f"  {i+1}. {row}")
                
                # Check for count differences
                common = set(counter1.keys()) & set(counter2.keys())
                count_diffs = [(r, counter1[r], counter2[r]) for r in common 
                              if counter1[r] != counter2[r]]
                if count_diffs:
                    print(f"\nRows with different counts: {len(count_diffs)}")
                    for i, (row, c1, c2) in enumerate(count_diffs[:3]):
                        print(f"  {i+1}. {row}")
                        print(f"     Count in file1: {c1}, file2: {c2}")
            
            print(f"\n{'='*50}")
        
        return match
        
    except Exception as e:
        print(f"ERROR comparing files: {str(e)}")
        return False