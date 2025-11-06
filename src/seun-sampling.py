
import json
import gzip
import random
import glob
import os
import time


def get_sample_text_reservoir(data_dir, max_doc_tokens=2000):
    """
    This is just for sampling docs from dolma. Docs in dolma are as a line in a .json.gz files.
    Efficiently sample from large .json.gz files using reservoir sampling.
    Only requires ONE pass through the file - much faster than counting lines first.
    """
    file_list = glob.glob(os.path.join(data_dir, "*.json.gz"))
    if not file_list:
        print(f"No .json.gz files found in {data_dir}")
        return "", ""
    
    file_path = random.choice(file_list)
    
    try:
        selected_record = None
        line_count = 0
        
        # Single pass with reservoir sampling
        with gzip.open(file_path, "rt", encoding="utf-8") as f:
            for line in f:
                line_count += 1
                
                try:
                    record = json.loads(line)
                    
                    # Reservoir sampling: replace current selection with probability 1/line_count
                    if line_count == 1:
                        # Always keep the first valid record
                        selected_record = record
                    elif random.random() < (1.0 / line_count):
                        # Replace with probability 1/line_count
                        selected_record = record
                        
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed JSON line {line_count}: {e}")
                    continue
        
        if selected_record is None:
            print(f"No valid JSON records found in {file_path}")
            return "", ""
        
        text = selected_record.get("text", "")
        
        # Truncate text if it's too long
        if text and max_doc_tokens > 0:
            text = truncate_text_by_tokens(text, max_doc_tokens)
        
        return text, file_path
        
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return "", ""


def get_sample_text(data_dir, max_doc_tokens=2000):
    """
    Efficiently sample from large .json.gz files using streaming approach.
    Only loads one line at a time into memory instead of entire file.
    """
    file_list = glob.glob(os.path.join(data_dir, "*.json.gz"))
    if not file_list:
        print(f"No .json.gz files found in {data_dir}")
        return "", ""
    
    file_path = random.choice(file_list)
    
    try:
        # First pass: count lines efficiently
        with gzip.open(file_path, "rt", encoding="utf-8") as f:
            total_lines = sum(1 for _ in f)
        
        if total_lines == 0:
            print(f"No lines found in the file {file_path}.")
            return "", ""
        
        # Choose random line number
        target_line = random.randint(0, total_lines - 1)
        
        # Second pass: read until target line
        with gzip.open(file_path, "rt", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == target_line:
                    try:
                        record = json.loads(line)
                        text = record.get("text", "")
                        
                        # Truncate text if it's too long
                        if text and max_doc_tokens > 0:
                            text = truncate_text_by_tokens(text, max_doc_tokens)
                        
                        return text, file_path
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")
                        return "", ""
                        
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return "", ""
    
    return "", ""

def get_sample_text_from_subset(data_dir, file_patterns, max_doc_tokens=2000):
    """
    Sample from a subset of .json.gz files that contain specific strings in their names.
    
    Args:
        data_dir: Directory containing .json.gz files
        file_patterns: List of strings to match in filenames (case-insensitive)
        max_doc_tokens: Maximum number of tokens in sampled document
    
    Returns:
        Dict with text, file_path, and metadata
    """
    all_files = glob.glob(os.path.join(data_dir, "*.json.gz"))
    
    # Filter files based on patterns
    matching_files = []
    for file_path in all_files:
        filename = os.path.basename(file_path).lower()
        for pattern in file_patterns:
            if pattern.lower() in filename:
                matching_files.append(file_path)
                break
    
    if not matching_files:
        print(f"No .json.gz files found matching patterns {file_patterns} in {data_dir}")
        return None
    
    # Randomly select from matching files
    selected_file = random.choice(matching_files)
    
    try:
        selected_record = None
        line_count = 0
        line_number = 0
        
        # Use reservoir sampling for efficiency
        with gzip.open(selected_file, "rt", encoding="utf-8") as f:
            for line in f:
                line_count += 1
                
                try:
                    record = json.loads(line)
                    
                    # Reservoir sampling
                    if line_count == 1:
                        selected_record = record
                        line_number = line_count
                    elif random.random() < (1.0 / line_count):
                        selected_record = record
                        line_number = line_count
                        
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed JSON line {line_count}: {e}")
                    continue
        
        if selected_record is None:
            print(f"No valid JSON records found in {selected_file}")
            return None
        
        text = selected_record.get("text", "")
        
        # Truncate text if needed
        if text and max_doc_tokens > 0:
            text = truncate_text_by_tokens(text, max_doc_tokens)
        
        print(f"Sampled from: {os.path.basename(selected_file)}")
        
        return {
            "text": text,
            "source_file": selected_file,
            "source_filename": os.path.basename(selected_file),
            "line_number": line_number,
            "patterns_matched": file_patterns,
            "timestamp": time.time()
        }
        
    except Exception as e:
        print(f"Error processing file {selected_file}: {e}")
        return None


def sample_documents_to_jsonl(data_dir, category_patterns, num_samples_per_category=10, 
                             max_doc_tokens=2000, output_file="sampled_documents.jsonl"):
    """
    Sample documents from different category patterns and save to JSONL file.
    
    Args:
        data_dir: Directory containing .json.gz files
        category_patterns: Dict mapping category names to lists of file patterns
        num_samples_per_category: Number of documents to sample per category
        max_doc_tokens: Maximum tokens per document
        output_file: Path to output JSONL file
    """
    sampled_docs = []
    
    for category, patterns in category_patterns.items():
        print(f"\n=== Sampling {num_samples_per_category} documents from {category} ===")
        
        for i in range(num_samples_per_category):
            doc_data = get_sample_text_from_subset(data_dir, patterns, max_doc_tokens)
            
            if doc_data:
                doc_data["category"] = category
                doc_data["sample_index"] = i + 1
                sampled_docs.append(doc_data)
                print(f"  Sample {i+1}/{num_samples_per_category} completed")
            else:
                print(f"  Sample {i+1}/{num_samples_per_category} failed")
    
    # Save to JSONL file
    with open(output_file, "w", encoding="utf-8") as f:
        for doc in sampled_docs:
            f.write(json.dumps(doc) + "\n")
    
    print(f"\n=== Saved {len(sampled_docs)} documents to {output_file} ===")
    
    # Print summary statistics
    category_counts = {}
    for doc in sampled_docs:
        cat = doc["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    print("\nSummary by category:")
    for cat, count in category_counts.items():
        print(f"  {cat}: {count} documents")
    
    return sampled_docs


def truncate_text_by_tokens(text, max_tokens, tokenizer=None):
    """
    Truncate text to fit within max_tokens limit.
    If no tokenizer is provided, use rough word-based estimation (1 token ≈ 0.75 words).
    """
    if not text or max_tokens <= 0:
        return text
    
    if tokenizer is not None:
        try:
            # Use actual tokenizer if provided
            tokens = tokenizer.encode(text)
            if len(tokens) <= max_tokens:
                return text
            truncated_tokens = tokens[:max_tokens]
            return tokenizer.decode(truncated_tokens)
        except Exception as e:
            print(f"Warning: Tokenizer failed, falling back to word estimation: {e}")
            # Fall through to estimation method
    
    # Use rough estimation: 1 token ≈ 0.75 words, so max_words ≈ max_tokens * 0.75
    words = text.split()
    max_words = int(max_tokens * 0.75)
    
    if len(words) <= max_words:
        return text
    
    # Truncate at word boundaries
    truncated_words = words[:max_words]
    return ' '.join(truncated_words)

def main():
    # Define category patterns based on the comments in the file
    category_patterns = {
        "academic_research": ["semantic_scholar", "arxiv", "algebraic-stack", "open-web-math"],
        "code_technical": ["stackexchange", "starcoder", "flan"],
        "web_crawl": ["common_crawl", "refined_web", "c4"],
        "literature_books": ["gutenberg", "wiki", "wikibooks"],
        "community_forums": ["reddit", "stackexchange"],
        "encyclopedic": ["megawika", "wiki", "wikibooks"]
    }
    
    # Sample documents and save to JSONL
    data_dir = "/datasets/dolma_1.7/current"  # Change this to your actual data directory
    
    # For testing with sample data
    # data_dir = "/home/eisape/projects/diversify_lm_output/dolma/data_sample"
    
    sampled_docs = sample_documents_to_jsonl(
        data_dir=data_dir,
        category_patterns=category_patterns,
        num_samples_per_category=5,  # Adjust as needed
        max_doc_tokens=2000,
        output_file="sampled_dolma_documents.jsonl"
    )
    
    print(f"\nTotal documents sampled: {len(sampled_docs)}")


if __name__ == "__main__":
    main()


# Academic & Research Publications
# 	•	Semantic Scholar
# 	•	ArXiv
# 	•	Algebraic Stack (focuses on advanced mathematics, research-oriented)
# 	•	Open Web Math (if curated from academic or educational sources)

# Code, Programming, & Technical Q&A
# 	•	StackExchange (especially Stack Overflow and related technical Q&A)
# 	•	StarCoder (a code dataset, includes GitHub code and Q&A)
# 	•	Flan (a collection of instruction-tuned datasets often based on technical tasks)

# Web Crawl & General Web Content
# 	•	Dolma’s Common Crawl
# 	•	Refined Web
# 	•	Common Crawl news? (possibly a filtered subset of Common Crawl focused on news articles)
# 	•	C4? (likely refers to the Colossal Clean Crawled Corpus, which is based on Common Crawl)

# Literature & Books
# 	•	Project Gutenberg (classic books in the public domain)
# 	•	Wiki & Wikibooks (encyclopedic and instructional content)

# Community Forums & Discussion
# Sources based on user-generated posts or dialogue:
# 	•	Reddit (general discussions across topics)
# 	•	StackExchange (fits here too, but already categorized under Technical Q&A)

# Encyclopedic / Knowledge Bases
# 	•	Mega Wiki (likely a combined Wikipedia dump or derived content)
# 	•	Wiki & Wikibooks (can fit here too, though they’re also partly instructional)