"""
minecraft_wiki_scraper.py
-----------------------------------
Fetches, cleans, chunks, and (optionally) embeds Minecraft Wiki pages
into a local Chroma vector database for RAG or chatbot use.
-----------------------------------
Requires:
    pip install requests beautifulsoup4 sentence-transformers chromadb tqdm
"""

import concurrent.futures
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Optional: for vector embedding
try:
    from chromadb import Client
    from sentence_transformers import SentenceTransformer

    EMBEDDING_DEPS_AVAILABLE = True
except ImportError:
    EMBEDDING_DEPS_AVAILABLE = False


class MinecraftWikiScraper:
    def __init__(self, output_dir: str = "wiki_data", embed: bool = True):
        self.base_url = "https://minecraft.wiki"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "MinecraftRAGBot/1.1 (Open Source Educational Tool)"}
        )
        self.embed = embed and EMBEDDING_DEPS_AVAILABLE
        if embed and not EMBEDDING_DEPS_AVAILABLE:
            print("Warning: Embedding dependencies not available, disabling embedding")

        if self.embed:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.chroma = Client()
            self.collection = self.chroma.get_or_create_collection("minecraft_wiki")

    def categorize_url(self, url: str) -> str:
        """Categorize URL based on domain and content"""
        if "minecraft.net" in url:
            if "tips" in url or "beginners" in url:
                return "Beginner Guide"
            return "Official Documentation"
        elif "help.minecraft.net" in url:
            return "Help Center"
        elif "crafting" in url:
            return "Crafting Guide"
        elif "instructables" in url:
            return "Tutorial"
        else:
            return "General Guide"

    def _extract_title(self, html_content: str, url: str) -> str:
        """Extract page title from HTML with multiple fallback methods"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Try various title sources
            title = None

            # Try <title> tag
            if soup.title:
                title = soup.title.string

            # Try h1
            if not title:
                h1 = soup.find("h1")
                if h1:
                    title = h1.get_text(strip=True)

            # Try og:title
            if not title:
                og_title = soup.find("meta", property="og:title")
                if og_title:
                    title = og_title.get("content")

            # Fallback to URL
            if not title:
                from urllib.parse import urlparse

                title = urlparse(url).path.split("/")[-1].replace("-", " ").title()

            # Clean title
            title = re.sub(r"\s*[|\-–—]\s*Minecraft.*$", "", title, flags=re.IGNORECASE)
            title = title.strip()

            return title or "Untitled"

        except Exception:
            from urllib.parse import urlparse

            return urlparse(url).path.split("/")[-1] or "Untitled"

    # ---------------------------------------------------------------------
    # 1. CATEGORY PAGE GATHERING
    # ---------------------------------------------------------------------
    def get_category_pages(self, category: str) -> list[str]:
        """Fetch all pages in a given Minecraft Wiki category with pagination."""
        pages = []
        url = f"{self.base_url}/api.php"
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": 500,
            "format": "json",
        }

        while True:
            try:
                r = self.session.get(url, params=params, timeout=10)  # type: ignore
                r.raise_for_status()
                data = r.json()
                members = data.get("query", {}).get("categorymembers", [])
                pages.extend([m["title"] for m in members])

                if "continue" in data:
                    params.update(data["continue"])
                    time.sleep(0.5)
                else:
                    break
            except Exception as e:
                print(f"Error fetching category {category}: {e}")
                break
        return pages

    # ---------------------------------------------------------------------
    # 2. PAGE FETCHING AND CLEANING
    # ---------------------------------------------------------------------
    def fetch_page_content(self, title: str) -> dict | None:
        """Fetch and clean a wiki page using the MediaWiki API."""
        url = f"{self.base_url}/api.php"
        params = {
            "action": "parse",
            "page": title,
            "format": "json",
            "prop": "text",
        }

        try:
            r = self.session.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()

            if "parse" not in data:
                return None

            html_content = data["parse"]["text"]["*"]
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove non-content elements but preserve crafting tables
            for tag in soup(["script", "style", "nav", "footer", "noscript"]):
                tag.decompose()

            # Keep tables that contain crafting recipe (have specific classes
            # or content)
            for table in soup.find_all("table"):
                # Check if this table contains crafting recipe information
                table_text = table.get_text().lower()
                if any(
                    keyword in table_text
                    for keyword in ["crafting", "recipe", "ingredients", "grid"]
                ):
                    # Convert table to readable text format
                    table_str = self._convert_crafting_table_to_text(table)
                    # Replace table with formatted recipe text
                    table.replace_with(
                        f"\n\nCRAFTING RECIPE:\n{table_str}\n\n---RECIPE END---\n\n"
                    )
                else:
                    table.decompose()

            text = soup.get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", text)

            return {
                "title": title,
                "content": text,
                "url": f"{self.base_url}/wiki/{title.replace(' ', '_')}",
            }
        except Exception as e:
            print(f"Error fetching page {title}: {e}")
            return None

    def _convert_crafting_table_to_text(self, table: BeautifulSoup) -> str:
        """Convert a crafting table to readable text format"""
        try:
            # Collect all text only from table cells, not from the entire table
            cells_text = []
            for cell in table.find_all(["td", "th"]):
                cell_text = cell.get_text(separator=" ", strip=True)
                if cell_text:
                    cells_text.append(cell_text)

            # Extract item names from images in cells
            item_names = []
            for cell in table.find_all(["td", "th"]):
                imgs = cell.find_all("img")
                for img in imgs:
                    alt = img.get("alt", "")
                    if alt:
                        # Clean up the alt text
                        alt = re.sub(r" \(item\)$", "", alt)
                        alt = re.sub(r" \(block\)$", "", alt)
                        # Skip unwanted patterns
                        if not any(
                            skip in alt.lower()
                            for skip in [
                                "inventory sprite",
                                "invicon",
                                "sprite",
                                "linking to",
                                "with description",
                            ]
                        ):
                            if 2 <= len(alt) <= 30:
                                item_names.append(alt)

            # If we found item names from images, use those
            if len(item_names) >= 2:
                # Remove duplicates
                unique_items = list(dict.fromkeys(item_names))
                return "Ingredients: " + " + ".join(unique_items)

            # Fallback: try to extract reasonable words from cell text
            potential_items = []
            for text in cells_text:
                words = text.split()
                for word in words:
                    word = word.strip()
                    # Look for capitalized words that look like item names
                    if (
                        len(word) >= 3
                        and len(word) <= 20
                        and word[0].isupper()
                        and not word.startswith("(")
                        and not word.endswith(")")
                        and word
                        not in ["Crafting", "Ingredients", "Result", "Recipe", "Grid"]
                    ):
                        potential_items.append(word)

            if len(potential_items) >= 2:
                unique_items = list(dict.fromkeys(potential_items))
                return "Ingredients: " + " + ".join(unique_items[:4])

            # Final fallback
            return "Crafting recipe available"

        except Exception as e:
            print(f"Error converting crafting table: {e}")
            return "Crafting recipe available"

    # ---------------------------------------------------------------------
    # 3. CHUNKING LOGIC
    # ---------------------------------------------------------------------
    def chunk_document(self, doc: dict, chunk_size: int = 600) -> list[dict]:
        """Split document text into smaller chunks for embedding."""
        text = doc["content"]
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size):
            chunk_words = words[i : i + chunk_size]
            chunk_text = " ".join(chunk_words)
            chunks.append(
                {"title": doc["title"], "content": chunk_text, "url": doc["url"]}
            )
        return chunks

    # ---------------------------------------------------------------------
    # 4. STORAGE
    # ---------------------------------------------------------------------
    def save_json(self, data: list[dict], filename: str) -> None:
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(data)} entries to {path}")

    # ---------------------------------------------------------------------
    # 5. SCRAPING + EMBEDDING PIPELINE
    # ---------------------------------------------------------------------
    def scrape_categories(self, categories: list[str] | None = None) -> list[dict]:
        if categories is None:
            categories = [
                "Crafting",
                "Smelting",
                "Brewing",
                "Enchanting",
                "Items",
                "Blocks",
                "Recipes",
            ]

        all_titles = set()
        for cat in categories:
            print(f"Fetching category: {cat}")
            pages = self.get_category_pages(cat)
            all_titles.update(pages)
            time.sleep(1)

        print(f"Total pages to scrape: {len(all_titles)}")
        documents = []

        # Multi-threaded fetching
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.fetch_page_content, title): title
                for title in sorted(all_titles)
            }
            for future in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(futures),
                desc="Scraping pages",
            ):
                doc = future.result()
                if doc:
                    documents.append(doc)
                time.sleep(0.1)  # Reduced sleep for politeness

        return documents

    def _clean_html_content(self, html_content: str, url: str = "") -> str:
        """Clean HTML content with enhanced domain-specific handling"""
        soup = BeautifulSoup(html_content, "html.parser")

        # Domain-specific cleaning
        if "minecraft.net" in url:
            # Remove minecraft.net specific elements
            for tag in soup.select(
                ".cookie-banner, .header, .footer, .nav, .advertisement"
            ):
                tag.decompose()

        if "help.minecraft.net" in url:
            # Focus on article content for help center
            article = soup.find("article") or soup.find("main") or soup
            soup = BeautifulSoup(str(article), "html.parser")

        # Remove common non-content elements
        for tag in soup(
            [
                "script",
                "style",
                "nav",
                "footer",
                "noscript",
                "header",
                "aside",
                "iframe",
                "form",
                "button",
            ]
        ):
            tag.decompose()

        # Remove elements by class
        for selector in [
            ".cookie",
            ".banner",
            ".ad",
            ".advertisement",
            ".social",
            ".share",
            ".comment",
            ".navigation",
            ".sidebar",
        ]:
            for element in soup.select(selector):
                element.decompose()

        # Handle tables (keep crafting tables)
        for table in soup.find_all("table"):
            table_text = table.get_text().lower()
            if any(
                keyword in table_text
                for keyword in ["crafting", "recipe", "ingredients", "grid"]
            ):
                table_str = self._convert_crafting_table_to_text(table)
                table.replace_with(
                    f"\n\nCRAFTING RECIPE:\n{table_str}\n\n---RECIPE END---\n\n"
                )
            else:
                table.decompose()

        # Extract text
        text = str(soup.get_text(" ", strip=True))
        text = re.sub(r"\s+", " ", text)

        # Remove common footer/header text
        text = re.sub(
            r"(Cookie Policy|Privacy Policy|Terms of Service).*$",
            "",
            text,
            flags=re.IGNORECASE,
        )

        return text.strip()

    def scrape_urls(self, urls: list[str]) -> list[dict]:
        """Scrape content directly from a list of URLs with multi-threading,
        retries, and cleaning."""
        documents = []

        def fetch_and_clean(url: str, max_retries: int = 3) -> dict | None:
            for attempt in range(max_retries):
                try:
                    # Use longer timeout for external sites
                    timeout = (
                        30
                        if any(
                            domain in url
                            for domain in ["minecraft.net", "help.minecraft.net"]
                        )
                        else 15
                    )

                    response = requests.get(
                        url,
                        headers={
                            "User-Agent": "MinecraftRAGBot/1.1 "
                            "(Open Source Educational Tool)"
                        },
                        timeout=timeout,
                    )
                    if response.status_code == 200:
                        cleaned_content = self._clean_html_content(response.text, url)
                        if (
                            cleaned_content.strip() and len(cleaned_content) > 100
                        ):  # Validate content
                            title = self._extract_title(response.text, url)
                            category = self.categorize_url(url)
                            return {
                                "url": url,
                                "content": cleaned_content,
                                "title": title,
                                "category": category,
                            }
                        else:
                            print(f"No content extracted from {url}")
                            return None
                    else:
                        print(f"Failed to fetch {url}: {response.status_code}")
                        if attempt < max_retries - 1:
                            time.sleep(2**attempt)  # Exponential backoff
                            continue
                        return None
                except Exception as e:
                    print(
                        f"Error fetching {url} (attempt {attempt + 1}/"
                        f"{max_retries}): {e}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2**attempt)  # Exponential backoff
                        continue
                    return None
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(fetch_and_clean, url): url for url in urls}
            for future in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(futures),
                desc="Scraping URLs",
            ):
                doc = future.result()
                if doc:
                    documents.append(doc)
                time.sleep(0.5)  # Be polite to servers

        return documents

    def run(self) -> None:
        print("🚀 Starting Minecraft Wiki scraping...")
        docs = self.scrape_categories()

        # Save full docs
        self.save_json(docs, "wiki_docs_full.json")

        # Chunk & optionally embed
        all_chunks = []
        for doc in docs:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        self.save_json(all_chunks, "wiki_docs_chunks.json")

        if self.embed:
            print("🔍 Generating embeddings and storing in Chroma...")
            texts = [c["content"] for c in all_chunks]
            metas = [{"title": c["title"], "url": c["url"]} for c in all_chunks]
            embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=16)

            # Convert numpy array to list for ChromaDB
            embeddings_list = (
                embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings
            )

            self.collection.add(
                documents=texts,
                embeddings=embeddings_list,
                metadatas=metas,  # type: ignore
                ids=[f"chunk_{i}" for i in range(len(all_chunks))],
            )
            print(
                f"✅ Added {len(all_chunks)} chunks to Chroma collection "
                f"'minecraft_wiki'"
            )

        print(f"🏁 Done! Scraped {len(docs)} pages and {len(all_chunks)} chunks.")


# -------------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------------
if __name__ == "__main__":
    scraper = MinecraftWikiScraper(output_dir="wiki_data", embed=True)
    scraper.run()
