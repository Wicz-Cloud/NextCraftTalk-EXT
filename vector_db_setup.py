"""
Vector Database Setup with ChromaDB
Handles embedding generation and similarity search
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path
from typing import List, Dict
import numpy as np
import concurrent.futures

class MinecraftVectorDB:
    def __init__(self, 
                 persist_directory: str = "./chroma_db",
                 collection_name: str = "minecraft_wiki",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize ChromaDB with sentence-transformers embeddings
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Load embedding model
        print(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Minecraft Wiki Knowledge Base"}
            )
            print(f"Created new collection: {collection_name}")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def add_documents(self, documents: List[Dict], batch_size: int = 100):
        """
        Add documents to the vector database
        documents: List of dicts with 'title', 'content', 'url'
        """
        print(f"Adding {len(documents)} documents to vector DB...")
        
        # Prepare batches
        batches = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            ids = [f"doc_{i+j}" for j in range(len(batch))]
            texts = [doc['content'] for doc in batch]
            metadatas = [
                {
                    'title': doc['title'],
                    'url': doc.get('url', ''),
                    'chunk_id': i+j
                }
                for j, doc in enumerate(batch)
            ]
            batches.append((ids, texts, metadatas))
        
        # Multi-threaded encoding
        def encode_batch(batch_data):
            ids, texts, metadatas = batch_data
            embeddings = self.embed_batch(texts)
            return ids, embeddings, texts, metadatas
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            encoded_batches = list(executor.map(encode_batch, batches))
        
        # Add to collection sequentially (ChromaDB may not be thread-safe for adds)
        for ids, embeddings, texts, metadatas in encoded_batches:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            print(f"Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
        
        print("✓ All documents indexed!")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for relevant documents
        Returns list of dicts with 'content', 'title', 'url', 'score'
        """
        # Generate query embedding
        query_embedding = self.embed_text(query)
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'title': results['metadatas'][0][i]['title'],
                    'url': results['metadatas'][0][i]['url'],
                    'score': 1 - results['distances'][0][i] if results['distances'] else 1.0
                })
        
        return formatted_results
    
    def reset_collection(self):
        """Delete and recreate the collection"""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Minecraft Wiki Knowledge Base"}
        )
        print("Collection reset!")
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            'total_documents': count,
            'collection_name': self.collection_name,
            'embedding_model': self.embedding_model
        }


def build_vector_db_from_json(json_path: str = "wiki_data/wiki_docs_chunks.json"):
    """Helper function to build vector DB from scraped JSON"""
    
    # Load documents
    print(f"Loading documents from {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    # Initialize vector DB
    vector_db = MinecraftVectorDB()
    
    # Reset if needed (uncomment to start fresh)
    # vector_db.reset_collection()
    
    # Check if already populated
    stats = vector_db.get_collection_stats()
    if stats['total_documents'] > 0:
        print(f"Collection already has {stats['total_documents']} documents")
        user_input = input("Reset and rebuild? (yes/no): ")
        if user_input.lower() == 'yes':
            vector_db.reset_collection()
        else:
            return vector_db
    
    # Add documents
    vector_db.add_documents(documents)
    
    # Print stats
    stats = vector_db.get_collection_stats()
    print(f"\nVector DB Stats:")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Collection: {stats['collection_name']}")
    
    return vector_db


if __name__ == "__main__":
    # Build vector database from scraped data
    db = build_vector_db_from_json()
    
    # Test search
    print("\n--- Testing Search ---")
    test_query = "How do I craft a diamond pickaxe?"
    results = db.search(test_query, n_results=3)
    
    print(f"\nQuery: {test_query}\n")
    for i, result in enumerate(results):
        print(f"Result {i+1} (score: {result['score']:.3f}):")
        print(f"  Title: {result['title']}")
        print(f"  Content preview: {result['content'][:200]}...")
        print()
