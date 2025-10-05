"""
minecraft_wiki_scraper.py
-----------------------------------
Fetches, cleans, chunks, and (optionally) embeds Minecraft Wiki pages
into a local Chroma vector database for RAG or chatbot use.
-----------------------------------
Requires:
    pip install requests beautifulsoup4 sentence-transformers chromadb tqdm
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
import re
from tqdm import tqdm

# Optional: for vector embedding
from chromadb import Client
from sentence_transformers import SentenceTransformer


class MinecraftWikiScraper:
    def __init__(self, output_dir: str = "wiki_data", embed: bool = True):
        self.base_url = "https://minecraft.wiki"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MinecraftRAGBot/1.1 (Open Source Educational Tool)"
        })
        self.embed = embed
        if embed:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.chroma = Client()
            self.collection = self.chroma.get_or_create_collection("minecraft_wiki")

    # ---------------------------------------------------------------------
    # 1. CATEGORY PAGE GATHERING
    # ---------------------------------------------------------------------
    def get_category_pages(self, category: str) -> List[str]:
        """Fetch all pages in a given Minecraft Wiki category with pagination."""
        pages = []
        url = f"{self.base_url}/w/api.php"
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": 500,
            "format": "json",
        }

        while True:
            try:
                r = self.session.get(url, params=params, timeout=10)
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
    def fetch_page_content(self, title: str) -> Optional[Dict]:
        """Fetch and clean a wiki page using the MediaWiki API."""
        url = f"{self.base_url}/w/api.php"
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

            # Remove non-content elements
            for tag in soup(["script", "style", "nav", "footer", "table", "noscript"]):
                tag.decompose()

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

    # ---------------------------------------------------------------------
    # 3. CHUNKING LOGIC
    # ---------------------------------------------------------------------
    def chunk_document(self, doc: Dict, chunk_size: int = 600) -> List[Dict]:
        """Split document text into smaller chunks for embedding."""
        text = doc["content"]
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            chunks.append({
                "title": doc["title"],
                "content": chunk_text,
                "url": doc["url"]
            })
        return chunks

    # ---------------------------------------------------------------------
    # 4. STORAGE
    # ---------------------------------------------------------------------
    def save_json(self, data: List[Dict], filename: str):
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(data)} entries to {path}")

    # ---------------------------------------------------------------------
    # 5. SCRAPING + EMBEDDING PIPELINE
    # ---------------------------------------------------------------------
    def scrape_categories(self, categories: Optional[List[str]] = None) -> List[Dict]:
        if categories is None:
            categories = ["Crafting", "Smelting", "Brewing", "Enchanting", "Items", "Blocks", "Recipes"]

        all_titles = set()
        for cat in categories:
            print(f"Fetching category: {cat}")
            pages = self.get_category_pages(cat)
            all_titles.update(pages)
            time.sleep(1)

        print(f"Total pages to scrape: {len(all_titles)}")
        documents = []
        for title in tqdm(sorted(all_titles)):
            doc = self.fetch_page_content(title)
            if doc:
                documents.append(doc)
            time.sleep(0.5)

        return documents

    def run(self):
        print("🚀 Starting Minecraft Wiki scraping...")
        docs = self.scrape_categories()

        # Save full docs
        self.save_json(docs, "wiki_docs_full.json")

        # Chunk & optionally embed
        all_chunks = []
        for doc in tqdm(docs, desc="Chunking documents"):
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        self.save_json(all_chunks, "wiki_docs_chunks.json")

        if self.embed:
            print("🔍 Generating embeddings and storing in Chroma...")
            texts = [c["content"] for c in all_chunks]
            metas = [{"title": c["title"], "url": c["url"]} for c in all_chunks]
            embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=16)

            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metas,
                ids=[f"chunk_{i}" for i in range(len(all_chunks))],
            )
            print(f"✅ Added {len(all_chunks)} chunks to Chroma collection 'minecraft_wiki'")

        print(f"🏁 Done! Scraped {len(docs)} pages and {len(all_chunks)} chunks.")


# -------------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------------
if __name__ == "__main__":
    scraper = MinecraftWikiScraper(output_dir="wiki_data", embed=True)
    scraper.run()
