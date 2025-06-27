import json
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq
import os
from dotenv import load_dotenv
import re
from typing import List, Dict

# Load API key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

# Global variables
model = None
index = None
metadata = []
chunks = []

def initialize_system():
    """Initialize the system with proper error handling"""
    global model, index, metadata, chunks
    
    try:
        print("🔄 Initializing KCT RAG system...")
        
        # Initialize model
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Load FAISS index
        if os.path.exists("vectorstore/kct_index.faiss"):
            print("📚 Loading vector database...")
            index = faiss.read_index("vectorstore/kct_index.faiss")
        else:
            print("❌ Vector database not found!")
            return False
        
        # Load metadata and chunks
        if os.path.exists("vectorstore/kct_metadata.pkl"):
            with open("vectorstore/kct_metadata.pkl", "rb") as f:
                metadata = pickle.load(f)
        
        if os.path.exists("vectorstore/kct_chunks.json"):
            with open("vectorstore/kct_chunks.json", "r", encoding="utf-8") as f:
                chunks_data = json.load(f)
                chunks = chunks_data.get("chunks", [])
        
        print(f"✅ System initialized with {len(chunks)} chunks")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing system: {e}")
        return False

def enhanced_semantic_search(query: str, k: int = 5) -> List[Dict]:
    """Enhanced semantic search"""
    global model, index, chunks, metadata
    
    if model is None or index is None:
        initialize_system()
    
    if not chunks or not metadata:
        return []
    
    try:
        # Preprocess query
        query = re.sub(r'\s+', ' ', query.strip())
        
        kct_keywords = ["KCT", "Kumaraguru", "College", "Technology"]
        query_lower = query.lower()
        
        if not any(keyword.lower() in query_lower for keyword in kct_keywords):
            query = f"Kumaraguru College of Technology {query}"
        
        query_embedding = model.encode([query])
        
        search_k = min(k * 2, len(chunks))
        D, I = index.search(np.array(query_embedding), search_k)
        
        results = []
        for i, (distance, idx) in enumerate(zip(D[0], I[0])):
            if idx < len(chunks) and idx < len(metadata):
                chunk_text = chunks[idx]
                chunk_metadata = metadata[idx] if idx < len(metadata) else {}
                
                relevance_score = 1 / (1 + distance)
                
                results.append({
                    "text": chunk_text,
                    "relevance_score": relevance_score,
                    "distance": distance,
                    **chunk_metadata
                })
        
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:k]
        
    except Exception as e:
        print(f"Search error: {e}")
        return []

def create_conversational_prompt(query: str, context_chunks: List[Dict]) -> str:
    """Create a conversational prompt without source formatting"""
    
    relevant_chunks = [c for c in context_chunks if c.get("relevance_score", 0) > 0.3]
    
    if not relevant_chunks:
        relevant_chunks = context_chunks[:3] if context_chunks else []
    
    if relevant_chunks:
        context_parts = []
        for i, chunk in enumerate(relevant_chunks[:3]):
            context_parts.append(f"Information {i+1}: {chunk['text']}")
        context = "\n\n".join(context_parts)
    else:
        context = "General information about Kumaraguru College of Technology (KCT), a premier engineering institution in Coimbatore, Tamil Nadu."
    
    prompt = f"""You are a helpful assistant for Kumaraguru College of Technology (KCT).

QUESTION: {query}

AVAILABLE INFORMATION:
{context}

INSTRUCTIONS:
1. Provide a clear, concise answer using the information available
2. Be conversational and friendly
3. Use appropriate emojis to make the response engaging
4. Break down information into clear sections
5. Highlight important points
6. Do NOT include any source citations, references, or links in your response
7. If you don't have specific information, provide general helpful guidance

FORMAT YOUR RESPONSE:
[Your natural response here without any sources or citations]"""

    return prompt

def generate_response_without_sources(query: str) -> str:
    """Generate response without any source formatting"""
    try:
        if model is None:
            initialize_system()
        
        context_chunks = enhanced_semantic_search(query)
        
        if not context_chunks:
            return "I couldn't find relevant information about that topic. Please contact KCT directly for more details."
        
        prompt = create_conversational_prompt(query, context_chunks)
        
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system", 
                    "content": """You are a helpful assistant for KCT. Follow these rules:
                    1. Only use information from the provided sources
                    2. Be conversational and friendly
                    3. Use appropriate emojis
                    4. Do NOT include any source citations, references, or links
                    5. Make your response engaging and informative
                    6. Break down information into clear sections"""
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1200
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Remove any source-related text that might have been generated
        answer = re.sub(r'\*\*Sources.*?\*\*.*?(?=\n\n|\Z)', '', answer, flags=re.DOTALL)
        answer = re.sub(r'Sources Used:.*?(?=\n\n|\Z)', '', answer, flags=re.DOTALL)
        answer = re.sub(r'\[.*?\]\(.*?\)', '', answer)  # Remove markdown links
        answer = re.sub(r'Source:.*?\n', '', answer)  # Remove source lines
        
        return answer.strip()
        
    except Exception as e:
        print(f"Error generating response: {e}")
        return """Hello! I'm here to help you learn about Kumaraguru College of Technology (KCT). 🎓

KCT is a premier engineering institution in Coimbatore, Tamil Nadu. We offer various undergraduate and postgraduate programs in engineering and technology.

The college has state-of-the-art facilities, experienced faculty members, and an excellent placement record.

Please feel free to ask me about programs, admissions, facilities, or any other aspect of KCT!"""

def query_knowledge_base(query: str) -> str:
    """Main function to query the knowledge base and get a response without sources"""
    try:
        if model is None or index is None:
            initialize_system()
        
        response = generate_response_without_sources(query)
        return response
        
    except Exception as e:
        print(f"Error in query_knowledge_base: {e}")
        return """Hello! I'm here to help you learn about Kumaraguru College of Technology (KCT). 🎓

KCT is a premier engineering institution in Coimbatore, Tamil Nadu. We offer various undergraduate and postgraduate programs in engineering and technology.

The college has state-of-the-art facilities, experienced faculty members, and an excellent placement record.

What would you like to know about KCT today?"""
