# Updated rag_utils.py
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import torch

class RAGSystem:
    def __init__(self, embedding_model="all-MiniLM-L6-v2", chat_model="llama3", ollama_host="http://localhost:11434"):
        # Embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Ollama configuration
        self.ollama_host = ollama_host
        self.chat_model = chat_model
        
        # FAISS vector index
        self.dimension = 384  # for all-MiniLM-L6-v2
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Storage for texts
        self.texts = []
    
    def ingest_document(self, filepath):
        # PDF processing
        import PyPDF2
        
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            page_texts = [page.extract_text() for page in reader.pages]
        
        # Embed and store texts
        for text in page_texts:
            # Split long texts into chunks
            chunks = self._split_text(text)
            for chunk in chunks:
                embedding = self.embedding_model.encode(chunk)
                
                # Convert to numpy array and ensure float32
                embedding_np = np.array(embedding, dtype=np.float32).reshape(1, -1)
                
                # Add to FAISS index
                self.index.add(embedding_np)
                self.texts.append(chunk)
    
    def _split_text(self, text, max_chunk_size=500):
        # Split text into chunks
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) > max_chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            
            current_chunk.append(word)
            current_length += len(word)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def retrieve_context(self, query, top_k=3):
        # Embed query
        query_embedding = self.embedding_model.encode(query)
        query_embedding_np = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        
        # Search similar texts
        D, I = self.index.search(query_embedding_np, top_k)
        
        # Retrieve and return top contexts
        return [self.texts[i] for i in I[0]]
    
    def generate_response(self, query, context, language='english'):
        # Prepare prompt with context
        system_prompt = (
            "You are a helpful AI assistant that can respond in both Bangla and English. "
            "Use the provided context to answer the query accurately."
        )
        
        # Combine context and query
        augmented_query = f"Context: {' '.join(context)}\n\nQuery: {query}"
        
        # Generate response via Ollama
        import ollama
        response = ollama.chat(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": augmented_query}
            ]
        )
        
        # Translate if needed
        if language.lower() == 'bangla':
            # Placeholder for translation
            # In a real implementation, use a dedicated translation service
            return response['message']['content']
        
        return response['message']['content']