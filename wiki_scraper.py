"""
Minecraft Wiki Scraper
Fetches and processes recipe and gameplay information from minecraft.wiki
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from typing import List, Dict
import re

class MinecraftWikiScraper:
    def __init__(self, output_dir: str = "wiki_data"):
        self.base_url = "https://minecraft.wiki"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MinecraftRAGBot/1.0 (Educational Purpose)'
        })
    
    def get_category_pages(self, category: str) -> List[str]:
        """Fetch all pages in a category"""
        pages = []
        url = f"{self.base_url}/w/api.php"
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': f'Category:{category}',
            'cmlimit': 500,
            'format': 'json'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            members = data.get('query', {}).get('categorymembers', [])
            pages = [member['title'] for member in members]
        except Exception as e:
            print(f"Error fetching category {category}: {e}")
        
        return pages
    
    def fetch_page_content(self, title: str) -> Dict:
        """Fetch page content via MediaWiki API"""
        url = f"{self.base_url}/w/api.php"
        params = {
            'action': 'parse',
            'page': title,
            'format': 'json',
            'prop': 'text|sections'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            data = response.json()
            
            if 'parse' in data:
                html_content = data['parse']['text']['*']
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove scripts, styles, and navigation
                for tag in soup(['script', 'style', 'nav', 'footer']):
                    tag.decompose()
                
                # Extract text
                text = soup.get_text(separator='\n', strip=True)
                
                # Clean up excessive whitespace
                text = re.sub(r'\n\s*\n+', '\n\n', text)
                
                return {
                    'title': title,
                    'content': text,
                    'url': f"{self.base_url}/w/{title.replace(' ', '_')}"
                }
        except Exception as e:
            print(f"Error fetching page {title}: {e}")
        
        return None
    
    def scrape_recipes(self) -> List[Dict]:
        """Scrape crafting and recipe-related pages"""
        categories = [
            'Crafting',
            'Smelting',
            'Brewing',
            'Enchanting',
            'Items',
            'Blocks',
            'Recipes'
        ]
        
        all_pages = set()
        for category in categories:
            print(f"Fetching category: {category}")
            pages = self.get_category_pages(category)
            all_pages.update(pages)
            time.sleep(1)  # Rate limiting
        
        documents = []
        for i, page_title in enumerate(all_pages):
            print(f"Scraping {i+1}/{len(all_pages)}: {page_title}")
            doc = self.fetch_page_content(page_title)
            if doc:
                documents.append(doc)
            time.sleep(0.5)  # Rate limiting
        
        return documents
    
    def chunk_document(self, doc: Dict, chunk_size: int = 500) -> List[Dict]:
        """Split document into smaller chunks for embeddings"""
        content = doc['content']
        chunks = []
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        'title': doc['title'],
                        'content': current_chunk.strip(),
                        'url': doc['url']
                    })
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append({
                'title': doc['title'],
                'content': current_chunk.strip(),
                'url': doc['url']
            })
        
        return chunks
    
    def save_documents(self, documents: List[Dict], filename: str = "wiki_docs.json"):
        """Save scraped documents to JSON"""
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(documents)} documents to {output_path}")
    
    def run(self):
        """Main scraping pipeline"""
        print("Starting Minecraft Wiki scraping...")
        documents = self.scrape_recipes()
        
        # Chunk documents
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)
        
        # Save both full docs and chunks
        self.save_documents(documents, "wiki_docs_full.json")
        self.save_documents(all_chunks, "wiki_docs_chunks.json")
        
        print(f"Scraping complete! Total chunks: {len(all_chunks)}")
        return all_chunks


if __name__ == "__main__":
    scraper = MinecraftWikiScraper()
    scraper.run()
