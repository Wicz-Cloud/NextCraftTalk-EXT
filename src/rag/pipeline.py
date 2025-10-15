"""
RAG Pipeline - Retrieval-Augmented Generation
Combines vector search with LLM generation via Ollama
"""

import requests

from ..data.vector_db import MinecraftVectorDB


class MinecraftRAGPipeline:
    def __init__(
        self,
        vector_db: MinecraftVectorDB,
        ollama_url: str = "http://localhost:11434",
        model_name: str = "phi3:mini",
        top_k: int = 2,
    ):  # Reduced from 5 to 2
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
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                print(f"✓ Connected to Ollama. Available models: {model_names}")
                if self.model_name not in model_names:
                    print(
                        f"⚠ Warning: Model {self.model_name} not found. Pull it with: ollama pull {self.model_name}"
                    )
            else:
                print("⚠ Ollama connection failed")
        except Exception as e:
            print(f"⚠ Could not connect to Ollama: {e}")

    def retrieve_context(self, query: str) -> list[dict]:
        """Retrieve relevant documents from vector DB"""
        results = self.vector_db.search(query, n_results=self.top_k)

        # Filter out low-relevance results (score > 0.5 means less similar)
        filtered_results = []
        for result in results:
            # Convert distance to similarity score (lower distance = higher similarity)
            similarity = 1 - result.get("score", 1.0)
            if similarity > 0.1:  # Only keep reasonably similar results
                filtered_results.append(result)

        return filtered_results[:3]  # Limit to top 3 most relevant

    def build_prompt(self, query: str, context_docs: list[dict]) -> str:
        """Build prompt for LLM with retrieved context"""

        # Build context from retrieved documents, limiting total length
        context_parts = []
        total_length = 0
        max_context_length = 2000  # Reduced from 3000 to 2000 characters

        for i, doc in enumerate(context_docs):
            doc_content = f"[Source {i+1}: {doc['title']}]\n{doc['content']}"
            if total_length + len(doc_content) > max_context_length:
                # Truncate if too long
                remaining = max_context_length - total_length
                if remaining > 200:  # Only add if we have space for meaningful content
                    doc_content = doc_content[:remaining] + "..."
                    context_parts.append(doc_content)
                break
            context_parts.append(doc_content)
            total_length += len(doc_content)

        context = "\n\n---\n\n".join(context_parts)

        # Construct prompt
        prompt = f"""
You are a kind, playful Minecraft helper for kids.
You should sound like a friendly guide, not a computer or a teacher.

MINECRAFT INFO:
{context}

KID'S QUESTION:
{query}

YOUR JOB:
- Speak like you’re talking to a 10-year-old.
- Use simple, cheerful words and short sentences.
- Never mention words like "context", "source", "data", "ID", or anything that sounds technical.
- Never talk about wiki pages, codes, or versions.
- Ignore any confusing or technical text you see.
- Only use information from the Minecraft game. Ignore any real-world crafting instructions.
- Only tell:
  1. How to get each ingredient (where to find or make it)
  2. How to craft or build the item
- Show the crafting recipe in a fun text grid (3x3 if needed).
- Use bullet points for steps.
- Keep answers short, fun, and clear.
- If you don’t know, say “I don’t know that yet!”
- Do not add extra info or explanations.

ANSWER:
"""

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
                "top_k": 40,
                "num_predict": 1000,  # Increased to 1000 tokens for longer responses
                "num_ctx": 2048,  # Increased back to 2048 for better context
                "repeat_penalty": 1.1,
            },
        }

        try:
            response = requests.post(
                url, json=payload, timeout=180
            )  # Increased to 3 minutes
            if response.status_code == 200:
                data = response.json()
                answer = data.get("response", "").strip()
                if answer:
                    return answer
                else:
                    return "I found some information but couldn't generate a complete answer. Please try rephrasing your question."
            else:
                return f"Error generating response: {response.status_code}"
        except requests.exceptions.Timeout:
            return "The AI is taking too long to respond. Please try a simpler question or try again later."
        except Exception as e:
            return f"Error connecting to LLM: {str(e)}"

    def answer_question(self, query: str, include_sources: bool = True) -> dict:
        """
        Complete RAG pipeline: retrieve, generate, format

        Returns:
            dict with 'answer', 'sources', 'context_used'
        """

        # Step 1: Retrieve relevant context
        minecraft_query = f"Minecraft {query}"
        context_docs = self.retrieve_context(minecraft_query)

        if not context_docs:
            return {
                "answer": "I couldn't find any relevant information in my knowledge base.",
                "sources": [],
                "context_used": 0,
            }

        # Step 2: Build prompt
        prompt = self.build_prompt(query, context_docs)

        # Step 3: Generate response
        answer = self.generate_response(prompt)

        # Step 4: Format sources
        sources = []
        if include_sources:
            for doc in context_docs[:3]:  # Top 3 sources
                sources.append(
                    {
                        "title": doc["title"],
                        "url": doc["url"],
                        "relevance": doc["score"],
                    }
                )

        return {"answer": answer, "sources": sources, "context_used": len(context_docs)}

    def format_response_for_chat(self, result: dict) -> str:
        """Format the RAG result for chat display"""

        message = result["answer"]

        # Add sources if available
        if result["sources"]:
            message += "\n\n**Sources:**\n"
            for source in result["sources"]:
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
        "What do I need to make a golden apple?",
    ]

    print("\n" + "=" * 60)
    print("Testing RAG Pipeline")
    print("=" * 60)

    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)

        result = rag.answer_question(query)
        formatted = rag.format_response_for_chat(result)

        print(formatted)
        print("-" * 60)


if __name__ == "__main__":
    test_rag_pipeline()
