import json
import os
import re
from typing import List, Dict, Tuple
import glob

def load_json_files(data_dir: str = "data") -> List[Dict]:
    """Load all JSON data files from directory"""
    all_data = []
    
    # Find all JSON files in data directory
    json_files = glob.glob(os.path.join(data_dir, "*.json"))
    
    if not json_files:
        print(f"❌ No JSON files found in {data_dir} directory")
        return []
    
    print(f"📁 Found {len(json_files)} JSON files:")
    
    for filepath in json_files:
        try:
            print(f"   📄 Loading {os.path.basename(filepath)}...")
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                    print(f"   ✅ Loaded {len(data)} entries from {os.path.basename(filepath)}")
                else:
                    print(f"   ⚠️ Skipping {os.path.basename(filepath)} - not a list format")
        except Exception as e:
            print(f"   ❌ Error loading {os.path.basename(filepath)}: {e}")
    
    print(f"📊 Total entries loaded: {len(all_data)}")
    return all_data

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove special characters that don't add meaning
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)]', '', text)
    return text

def smart_chunking(content: str, chunk_size: int = 600, overlap: int = 150) -> List[str]:
    """Create overlapping chunks with better context preservation"""
    chunks = []
    start = 0
    
    while start < len(content):
        end = start + chunk_size
        
        # If not at the end, try to break at sentence boundary
        if end < len(content):
            # Look for sentence endings within the last 150 characters
            for i in range(end, max(start + chunk_size - 150, start), -1):
                if content[i] in '.!?':
                    end = i + 1
                    break
        
        chunk = content[start:end].strip()
        if chunk and len(chunk) > 100:  # Only keep meaningful chunks
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(content):
            break
    
    return chunks

def clean_and_chunk(data: List[Dict], chunk_size: int = 600, overlap: int = 150) -> Tuple[List[str], List[Dict]]:
    """Process data with improved chunking strategy"""
    chunks, metadata = [], []
    
    print(f"🔄 Processing {len(data)} data entries...")
    
    for i, entry in enumerate(data):
        try:
            content = clean_text(entry.get("content", ""))
            url = entry.get("url", "https://kct.ac.in")
            section = entry.get("section", "General")
            
            # Skip very short content
            if len(content) < 30:
                continue
                
            content_chunks = smart_chunking(content, chunk_size, overlap)
            
            for chunk in content_chunks:
                chunks.append(chunk)
                metadata.append({
                    "url": url, 
                    "section": section,
                    "content_length": len(chunk),
                    "original_content": content[:150] + "..." if len(content) > 150 else content,
                    "source_entry": i
                })
        except Exception as e:
            print(f"   ❌ Error processing entry {i}: {e}")
            continue
    
    return chunks, metadata

def save_chunks(chunks: List[str], metadata: List[Dict]) -> None:
    """Save processed chunks and metadata"""
    os.makedirs("vectorstore", exist_ok=True)
    
    # Save chunks
    with open("vectorstore/kct_chunks.json", "w", encoding="utf-8") as f:
        json.dump({
            "chunks": chunks, 
            "metadata": metadata,
            "total_chunks": len(chunks)
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Processed {len(chunks)} chunks with improved strategy")
    print(f"📊 Average chunk length: {sum(len(c) for c in chunks) / len(chunks):.1f} characters")

if __name__ == "__main__":
    print("🔄 Starting enhanced preprocessing...")
    
    # Load all available JSON files
    data = load_json_files("data")
    
    if not data:
        print("❌ No data to process. Please check your data directory.")
        exit(1)
    
    # Process and chunk the data
    chunks, metadata = clean_and_chunk(data)
    
    if not chunks:
        print("❌ No chunks created. Please check your data quality.")
        exit(1)
    
    # Save processed chunks
    save_chunks(chunks, metadata)
    print("✅ Enhanced preprocessing completed!")