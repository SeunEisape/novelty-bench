import json
import csv
import argparse
from pathlib import Path


def jsonl_to_csv(jsonl_file, csv_file=None):
    """
    Convert JSONL file to CSV format.
    
    Args:
        jsonl_file: Path to input JSONL file
        csv_file: Path to output CSV file (optional, defaults to same name with .csv extension)
    """
    jsonl_path = Path(jsonl_file)
    
    if not jsonl_path.exists():
        print(f"Error: File {jsonl_file} not found")
        return
    
    # Default output filename
    if csv_file is None:
        csv_file = jsonl_path.with_suffix('.csv')
    
    # Read all records first to get all possible fields
    records = []
    all_fields = set()
    
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line)
            records.append(record)
            all_fields.update(record.keys())
    
    # Sort fields for consistent column order
    fieldnames = sorted(all_fields)
    
    # Move 'text' to the end since it's likely to be long
    if 'text' in fieldnames:
        fieldnames.remove('text')
        fieldnames.append('text')
    
    # Write to CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            # Handle list fields by converting to string
            processed_record = {}
            for field, value in record.items():
                if isinstance(value, list):
                    processed_record[field] = json.dumps(value)
                else:
                    processed_record[field] = value
            
            writer.writerow(processed_record)
    
    print(f"Successfully converted {len(records)} records from {jsonl_file} to {csv_file}")
    print(f"Columns: {', '.join(fieldnames)}")


def main():
    parser = argparse.ArgumentParser(description="Convert sampled documents JSONL to CSV")
    parser.add_argument(
        "--input", 
        default="/home/eisape/projects/diversify_lm_output/sampled_dolma_documents.jsonl",
        help="Input JSONL file (default: sampled_dolma_documents.jsonl)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV file (default: same name with .csv extension)"
    )
    
    args = parser.parse_args()
    
    jsonl_to_csv(args.input, args.output)


if __name__ == "__main__":
    main()