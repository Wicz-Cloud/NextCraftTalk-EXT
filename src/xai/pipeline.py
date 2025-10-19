"""
Direct x.ai Query Pipeline
Bypasses RAG and queries x.ai directly for Minecraft answers
"""

import logging
import time
from pathlib import Path
from typing import Any

import requests

from ..core.config import settings

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

logger = logging.getLogger(__name__)

if not WATCHDOG_AVAILABLE:
    logger.warning("watchdog not available. Prompt template will not auto-reload.")

if WATCHDOG_AVAILABLE:

    class PromptTemplateWatcher(FileSystemEventHandler):
        """File watcher for prompt template changes

        Monitors prompt_template.txt for modifications and triggers
        automatic reloading without requiring a container restart.
        Depends on the 'watchdog' library.
        """

        def __init__(self, rag_pipeline: "DirectXAIPipeline") -> None:
            self.rag_pipeline = rag_pipeline

        def on_modified(self, event: Any) -> None:
            """Called when the prompt template file is modified"""
            if event.src_path.endswith(self.rag_pipeline.prompt_template_path):
                logger.info("📝 Prompt template changed, reloading...")
                self.rag_pipeline.reload_prompt_template()

else:

    class PromptTemplateWatcher:
        """Dummy file watcher when watchdog is not available"""

        def __init__(self, rag_pipeline: "DirectXAIPipeline") -> None:
            pass

        def on_modified(self, event: Any) -> None:
            pass


class DirectXAIPipeline:
    def __init__(
        self,
        xai_api_key: str,
        xai_url: str = "https://api.x.ai/v1",
        model_name: str = "grok-4-fast-non-reasoning",
        prompt_template_path: str = "prompt_template.txt",
    ):
        """
        Initialize direct x.ai pipeline (no RAG)

        Args:
            xai_api_key: x.ai API key for authentication
            xai_url: x.ai API endpoint
            model_name: Model to use (grok-4-fast-non-reasoning)
            prompt_template_path: Path to prompt template file
        """
        self.xai_api_key = xai_api_key
        self.xai_url = xai_url
        self.model_name = model_name
        self.prompt_template_path = prompt_template_path

        # Load prompt template from external file (see prompt_template.txt)
        self.prompt_template = self._load_prompt_template()

        # Start file watcher for automatic prompt reloading
        # (requires watchdog dependency)
        self._start_file_watcher()

        # Test x.ai connection (depends on x.ai API key)
        self._test_xai_connection()

    def _load_prompt_template(self) -> str:
        """Load prompt template from file"""
        try:
            with open(self.prompt_template_path, encoding="utf-8") as f:
                template = f.read().strip()
            logger.info(f"✓ Loaded prompt template from {self.prompt_template_path}")
            return template
        except FileNotFoundError:
            logger.warning(
                f"Prompt template file not found at " f"{self.prompt_template_path}"
            )
            logger.info("Using default prompt template...")
            return self._get_default_prompt_template()
        except Exception as e:
            logger.warning(f"Error loading prompt template: {e}")
            logger.info("Using default prompt template...")
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

    def _test_xai_connection(self) -> None:
        """Test if x.ai API is accessible"""
        try:
            # Test with a simple chat completion request
            headers = {
                "Authorization": f"Bearer {self.xai_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
                "temperature": 0.1,
            }
            response = requests.post(
                f"{self.xai_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=10,
            )
            if response.status_code == 200:
                logger.info(f"✓ Connected to x.ai API. Using model: {self.model_name}")
            else:
                logger.warning(f"x.ai API connection failed: {response.status_code}")
                if response.status_code == 401:
                    logger.warning("  Check your XAI_API_KEY in .env file")
                elif response.status_code == 400:
                    logger.warning("  API request format may be incorrect")
        except Exception as e:
            print(f"⚠ Could not connect to x.ai API: {e}")

    def _start_file_watcher(self) -> None:
        """Start file watcher for prompt template changes

        Uses watchdog library to monitor prompt_template.txt for changes.
        When file is modified, automatically reloads the prompt template.
        Requires 'watchdog' dependency (added to requirements.txt).
        """
        if not WATCHDOG_AVAILABLE:
            logger.warning("File watcher not available (watchdog not installed)")
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
            logger.info(f"👀 Started watching {self.prompt_template_path} for changes")
        except Exception as e:
            logger.warning(f"Failed to start file watcher: {e}")

    def reload_prompt_template(self) -> None:
        """Reload prompt template from file

        Called automatically when prompt_template.txt is modified,
        or can be triggered manually via API endpoint.
        """
        try:
            old_template = self.prompt_template
            self.prompt_template = self._load_prompt_template()
            if self.prompt_template != old_template:
                logger.info("✅ Prompt template reloaded successfully!")
            else:
                logger.debug("ℹ️ Prompt template unchanged")
        except Exception as e:
            logger.warning(f"Failed to reload prompt template: {e}")

    def stop_file_watcher(self) -> None:
        """Stop the file watcher

        Called during shutdown to clean up resources.
        """
        if hasattr(self, "observer") and self.observer:
            self.observer.stop()
            self.observer.join()
            logger.debug("🛑 Stopped file watcher")

    def __del__(self) -> None:
        """Cleanup when object is destroyed"""
        self.stop_file_watcher()

    def generate_response(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate response using x.ai API"""

        url = f"{self.xai_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.xai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": 1500,  # Increased for more comprehensive responses
            "stream": False,
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=60,
            )
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    answer = str(data["choices"][0]["message"]["content"]).strip()
                    if answer:
                        return answer
                    else:
                        return (
                            "I found some information but couldn't generate a "
                            "complete answer. Please try rephrasing your question."
                        )
                else:
                    return "Error: No response generated by x.ai"
            else:
                return (
                    f"Error generating response: {response.status_code} - "
                    f"{response.text}"
                )
        except requests.exceptions.Timeout:
            return (
                "The AI is taking too long to respond. Please try a simpler "
                "question or try again later."
            )
        except Exception as e:
            logger.error(f"Error connecting to x.ai API: {str(e)}")
            return "An internal error occurred while connecting to x.ai API. Please try again later."

    def answer_question(self, query: str, include_sources: bool = True) -> dict:
        """
        Direct x.ai query: bypass RAG and ask x.ai directly

        Returns:
            dict with 'answer', 'sources', 'context_used'
        """

        start_time = time.time()

        # Direct x.ai query - no RAG retrieval
        if settings.verbose_logging:
            logger.info("🤖 Querying x.ai directly (no RAG)")
        else:
            logger.info("🤖 Processing query with x.ai")

        # Build simple prompt for x.ai
        prompt = f"""You are a helpful Minecraft assistant for kids.

Question: {query}

Please provide a clear, kid-friendly answer about Minecraft. Keep it simple and fun!"""

        # Generate response directly from x.ai
        generate_start = time.time()
        answer = self.generate_response(prompt)
        generate_time = time.time() - generate_start

        if settings.verbose_logging:
            logger.info(f"⏱️ x.ai response generation took {generate_time:.2f}s")
        else:
            logger.debug(f"⏱️ x.ai response generation took {generate_time:.2f}s")

        response = {
            "answer": answer,
            "sources": [],  # No sources since we're not using RAG
            "context_used": 0,  # No context retrieved
        }

        if settings.verbose_logging:
            total_time = time.time() - start_time
            print(f"⏱️ Total direct x.ai processing took {total_time:.2f}s")

        return response

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
    """Test the direct x.ai pipeline with sample queries"""

    # Initialize components
    print("Initializing direct x.ai pipeline...")
    rag = DirectXAIPipeline(
        xai_api_key="your-xai-api-key-here"  # Replace with actual key for testing
    )

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
