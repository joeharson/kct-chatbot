import json
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from typing import List, Dict

def create_enhanced_index():
    """Create enhanced FAISS index with better search capabilities"""
    
    try:
        print("🔄 Starting vector database creation...")
        
        # Check if input file exists
        chunks_file = "vectorstore/kct_chunks.json"
        if not os.path.exists(chunks_file):
            print(f"❌ Error: {chunks_file} not found!")
            print("   Please run preprocess.py first to create the chunks file.")
            return False
        
        print("📂 Loading preprocessed data...")
        with open(chunks_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            chunks = data["chunks"]
            metadata = data["metadata"]
        
        print(f"📊 Data loaded:")
        print(f"   • Chunks: {len(chunks)}")
        print(f"   • Metadata entries: {len(metadata)}")
        print(f"   • Average chunk length: {sum(len(c) for c in chunks) / len(chunks):.1f} characters")
        
        if len(chunks) == 0:
            print("❌ Error: No chunks found in the data file!")
            return False
        
        print("🧠 Initializing embedding model...")
        # Use a better embedding model for improved semantic search
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        print("🔢 Creating embeddings...")
        embeddings = model.encode(chunks, show_progress_bar=True)
        print(f"✅ Created embeddings with shape: {embeddings.shape}")
        
        print("🗂️ Building FAISS index...")
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(np.array(embeddings))
        
        print("💾 Saving vector database...")
        # Save FAISS index
        faiss.write_index(index, "vectorstore/kct_index.faiss")
        print("   ✅ FAISS index saved to vectorstore/kct_index.faiss")
        
        # Save metadata
        with open("vectorstore/kct_metadata.pkl", "wb") as f:
            pickle.dump(metadata, f)
        print("   ✅ Metadata saved to vectorstore/kct_metadata.pkl")
        
        print("\n🎉 Vector database creation completed successfully!")
        print("📊 Final statistics:")
        print(f"   • Vector dimension: {embeddings.shape[1]}")
        print(f"   • Total vectors: {embeddings.shape[0]}")
        print(f"   • Index type: FAISS L2 (Euclidean distance)")
        print(f"   • Storage location: vectorstore/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating vector database: {e}")
        return False

def test_vector_database():
    """Test the created vector database"""
    try:
        print("\n🧪 Testing vector database...")
        
        # Load the index
        if not os.path.exists("vectorstore/kct_index.faiss"):
            print("❌ Vector database not found!")
            return False
        
        index = faiss.read_index("vectorstore/kct_index.faiss")
        
        # Load chunks for testing
        with open("vectorstore/kct_chunks.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            chunks = data["chunks"]
        
        # Load model
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Test query
        test_query = "What programs does KCT offer?"
        query_embedding = model.encode([test_query])
        
        # Search
        k = 3
        D, I = index.search(np.array(query_embedding), k)
        
        print(f"✅ Test query: '{test_query}'")
        print(f"🔍 Found {len(I[0])} results:")
        
        for i, (dist, idx) in enumerate(zip(D[0], I[0])):
            if idx < len(chunks):
                relevance = 1 / (1 + dist)
                print(f"   {i+1}. Relevance: {relevance:.3f} | Preview: {chunks[idx][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing vector database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Vector Database Creation Script")
    print("=" * 40)
    
    success = create_enhanced_index()
    
    if success:
        test_vector_database()
        print("\n✅ Vector database is ready for use!")
    else:
        print("\n❌ Vector database creation failed!")
        print("Please check the errors above and try again.")
