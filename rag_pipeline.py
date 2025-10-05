"""
RAG Pipeline - Retrieval-Augmented Generation
Combines vector search with LLM generation via Ollama
"""

import requests
from typing import List, Dict, Optional
from vector_db import MinecraftVectorDB
import json

class MinecraftRAGPipeline:
    def __init__(self,
                 vector_db: MinecraftVectorDB,
                 ollama_url: str = "http://localhost:11434",
                 model_name: str = "phi3:mini",
                 top_k: int = 5):
        """
        Initialize RAG pipeline
        
        Args:
            vector_db: Initialized MinecraftVectorDB instance
            ollama_url: Ollama API endpoint
            model_name: Model to use (phi3:mini, gemma2:2b, mistral, llama3)
            top_k: Number of documents to retrieve
        """
        self.vector_db = vector_db
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.top_k = top_k
        
        # Test Ollama connection
        self._test_ollama_connection()
    
    def _test_ollama_connection(self):
        """Test if Ollama is accessible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                print(f"✓ Connected to Ollama. Available models: {model_names}")
                if self.model_name not in model_names:
                    print(f"⚠ Warning: Model {self.model_name} not found. Pull it with: ollama pull {self.model_name}")
            else:
                print("⚠ Ollama connection failed")
        except Exception as e:
            print(f"⚠ Could not connect to Ollama: {e}")
    
    def retrieve_context(self, query: str) -> List[Dict]:
        """Retrieve relevant documents from vector DB"""
        results = self.vector_db.search(query, n_results=self.top_k)
        return results
    
    def build_prompt(self, query: str, context_docs: List[Dict]) -> str:
        """Build prompt for LLM with retrieved context"""
        
        # Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(context_docs):
            context_parts.append(f"[Source {i+1}: {doc['title']}]\n{doc['content']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Construct prompt
        prompt = f"""You are a helpful Minecraft assistant. Answer the user's question based on the information provided from the Minecraft Wiki.

CONTEXT FROM MINECRAFT WIKI:
{context}

USER QUESTION:
{query}

INSTRUCTIONS:
- Answer based ONLY on the information provided above
- If the context contains a recipe, format it clearly with ingredients and steps
- Use bullet points and clear formatting
- If the answer is not in the context, say "I don't have enough information about that in my knowledge base"
- Be concise but complete
- Include crafting grids or recipes when relevant

ANSWER:"""
        
        return prompt
    
    def generate_response(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate response using Ollama"""
        
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                return data.get('response', '').strip()
            else:
                return f"Error generating response: {response.status_code}"
        except Exception as e:
            return f"Error connecting to LLM: {str(e)}"
    
    def answer_question(self, query: str, include_sources: bool = True) -> Dict:
        """
        Complete RAG pipeline: retrieve, generate, format
        
        Returns:
            dict with 'answer', 'sources', 'context_used'
        """
        
        # Step 1: Retrieve relevant context
        context_docs = self.retrieve_context(query)
        
        if not context_docs:
            return {
                'answer': "I couldn't find any relevant information in my knowledge base.",
                'sources': [],
                'context_used': 0
            }
        
        # Step 2: Build prompt
        prompt = self.build_prompt(query, context_docs)
        
        # Step 3: Generate response
        answer = self.generate_response(prompt)
        
        # Step 4: Format sources
        sources = []
        if include_sources:
            for doc in context_docs[:3]:  # Top 3 sources
                sources.append({
                    'title': doc['title'],
                    'url': doc['url'],
                    'relevance': doc['score']
                })
        
        return {
            'answer': answer,
            'sources': sources,
            'context_used': len(context_docs)
        }
    
    def format_response_for_chat(self, result: Dict) -> str:
        """Format the RAG result for chat display"""
        
        message = result['answer']
        
        # Add sources if available
        if result['sources']:
            message += "\n\n**Sources:**\n"
            for source in result['sources']:
                message += f"• [{source['title']}]({source['url']})\n"
        
        return message


def test_rag_pipeline():
    """Test the RAG pipeline with sample queries"""
    
    # Initialize components
    print("Initializing RAG pipeline...")
    vector_db = MinecraftVectorDB()
    rag = MinecraftRAGPipeline(vector_db)
    
    # Test queries
    test_queries = [
        "How do I craft a diamond pickaxe?",
        "What is the recipe for a brewing stand?",
        "How do I enchant items?",
        "What do I need to make a golden apple?"
    ]
    
    print("\n" + "="*60)
    print("Testing RAG Pipeline")
    print("="*60)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        
        result = rag.answer_question(query)
        formatted = rag.format_response_for_chat(result)
        
        print(formatted)
        print("-" * 60)


if __name__ == "__main__":
    test_rag_pipeline()
