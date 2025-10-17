"""
RAG Pipeline - Retrieval-Augmented Generation
Combines vector search with LLM generation via Ollama

Features:
- Dynamic prompt template loading from external file
- Automatic file watching for prompt changes (no restart needed)
- Fallback to default prompts if file loading fails
- Integration with ChromaDB vector database
"""

from pathlib import Path
from typing import Any

import requests

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠ Warning: watchdog not available. Prompt template will not auto-reload.")

from ..data.vector_db import MinecraftVectorDB


class PromptTemplateWatcher(FileSystemEventHandler):
    """File watcher for prompt template changes

    Monitors the prompt_template.txt file for modifications and triggers
    automatic reloading of the prompt template without requiring a container restart.
    Depends on the 'watchdog' library (added to requirements.txt).
    """

    def __init__(self, rag_pipeline: "MinecraftRAGPipeline") -> None:
        self.rag_pipeline = rag_pipeline

    def on_modified(self, event: Any) -> None:
        """Called when the prompt template file is modified"""
        if event.src_path.endswith(self.rag_pipeline.prompt_template_path):
            print("📝 Prompt template changed, reloading...")
            self.rag_pipeline.reload_prompt_template()


class MinecraftRAGPipeline:
    def __init__(
        self,
        vector_db: MinecraftVectorDB,
        ollama_url: str = "http://localhost:11434",
        model_name: str = "phi3:mini",
        top_k: int = 2,
        prompt_template_path: str = "prompt_template.txt",
    ):  # Reduced from 5 to 2
        """
        Initialize RAG pipeline

        Args:
            vector_db: Initialized MinecraftVectorDB instance
            ollama_url: Ollama API endpoint (configured via OLLAMA_URL in .env)
            model_name: Model to use (configured via MODEL_NAME in .env)
            top_k: Number of documents to retrieve
            prompt_template_path: Path to prompt template file
            (configured via PROMPT_TEMPLATE_PATH in .env)
        """
        self.vector_db = vector_db
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.top_k = top_k
        self.prompt_template_path = prompt_template_path

        # Load prompt template from external file (see prompt_template.txt)
        self.prompt_template = self._load_prompt_template()

        # Start file watcher for automatic prompt reloading
        # (requires watchdog dependency)
        self._start_file_watcher()

        # Test Ollama connection (depends on ollama service in docker-compose.yml)
        self._test_ollama_connection()

    def _load_prompt_template(self) -> str:
        """Load prompt template from file"""
        try:
            with open(self.prompt_template_path, encoding="utf-8") as f:
                template = f.read().strip()
            print(f"✓ Loaded prompt template from {self.prompt_template_path}")
            return template
        except FileNotFoundError:
            print(
                f"⚠ Warning: Prompt template file not found at "
                f"{self.prompt_template_path}"
            )
            print("Using default prompt template...")
            return self._get_default_prompt_template()
        except Exception as e:
            print(f"⚠ Warning: Error loading prompt template: {e}")
            print("Using default prompt template...")
            return self._get_default_prompt_template()

    def _get_default_prompt_template(self) -> str:
        """Return default prompt template if file loading fails"""
        return """You are a kind, playful Minecraft helper for kids.
You should sound like a friendly guide, not a computer or a teacher.

MINECRAFT INFO:
{context}

KID'S QUESTION:
{query}

YOUR JOB:
- Speak like you're talking to a 10-year-old.
- Use simple, cheerful words and short sentences.
- Never mention words like "context", "source", "data", "ID", or anything
  that sounds technical.
- Never talk about wiki pages, codes, or versions.
- Ignore any confusing or technical text you see.
- Only use information from the Minecraft game. Ignore any real-world
  crafting instructions.
- Only tell:
  1. How to get each ingredient (where to find or make it)
  2. How to craft or build the item
- Show the crafting recipe in a fun text grid (3x3 if needed).
- Use bullet points for steps.
- Keep answers short, fun, and clear.
- If you don't know, say "I don't know that yet!"
- Do not add extra info or explanations.

ANSWER:
"""

    def _test_ollama_connection(self) -> None:
        """Test if Ollama is accessible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                print(f"✓ Connected to Ollama. Available models: {model_names}")
                if self.model_name not in model_names:
                    print(
                        f"⚠ Warning: Model {self.model_name} not found. Pull it with: "
                        f"ollama pull {self.model_name}"
                    )
            else:
                print("⚠ Ollama connection failed")
        except Exception as e:
            print(f"⚠ Could not connect to Ollama: {e}")

    def _start_file_watcher(self) -> None:
        """Start file watcher for prompt template changes

        Uses watchdog library to monitor prompt_template.txt for changes.
        When file is modified, automatically reloads the prompt template.
        Requires 'watchdog' dependency (added to requirements.txt).
        """
        if not WATCHDOG_AVAILABLE:
            print("⚠ File watcher not available (watchdog not installed)")
            return

        try:
            template_path = Path(self.prompt_template_path)
            if not template_path.exists():
                print(
                    f"⚠ Prompt template file {self.prompt_template_path} does not "
                    f"exist, skipping file watcher"
                )
                return

            # Get the directory containing the template file
            watch_dir = (
                template_path.parent if template_path.is_file() else template_path
            )

            self.observer = Observer()
            self.watcher = PromptTemplateWatcher(self)
            self.observer.schedule(self.watcher, str(watch_dir), recursive=False)
            self.observer.start()
            print(f"👀 Started watching {self.prompt_template_path} for changes")
        except Exception as e:
            print(f"⚠ Failed to start file watcher: {e}")

    def reload_prompt_template(self) -> None:
        """Reload prompt template from file

        Called automatically when prompt_template.txt is modified,
        or can be triggered manually via API endpoint.
        """
        try:
            old_template = self.prompt_template
            self.prompt_template = self._load_prompt_template()
            if self.prompt_template != old_template:
                print("✅ Prompt template reloaded successfully!")
            else:
                print("ℹ️ Prompt template unchanged")
        except Exception as e:
            print(f"⚠ Failed to reload prompt template: {e}")

    def stop_file_watcher(self) -> None:
        """Stop the file watcher

        Called during shutdown to clean up resources.
        """
        if hasattr(self, "observer") and self.observer:
            self.observer.stop()
            self.observer.join()
            print("🛑 Stopped file watcher")

    def __del__(self) -> None:
        """Cleanup when object is destroyed"""
        self.stop_file_watcher()

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
            doc_content = f"[Source {i + 1}: {doc['title']}]\n{doc['content']}"
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

        # Use template with placeholders
        prompt = self.prompt_template.format(context=context, query=query)

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
                answer = str(data.get("response", "")).strip()
                if answer:
                    return answer
                else:
                    return (
                        "I found some information but couldn't generate a "
                        "complete answer. Please try rephrasing your question."
                    )
            else:
                return f"Error generating response: {response.status_code}"
        except requests.exceptions.Timeout:
            return (
                "The AI is taking too long to respond. Please try a simpler "
                "question or try again later."
            )
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
                "answer": (
                    "I couldn't find any relevant information in my knowledge base."
                ),
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

        message = str(result["answer"])

        # Add sources if available
        if result["sources"]:
            message += "\n\n**Sources:**\n"
            for source in result["sources"]:
                message += f"• [{source['title']}]({source['url']})\n"

        return message


def test_rag_pipeline() -> None:
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
