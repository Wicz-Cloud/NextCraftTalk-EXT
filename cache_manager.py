"""
Cache Manager - SQLite-based caching for common recipes
Provides instant responses for frequently asked questions
"""

import sqlite3
from typing import Optional, Dict, List
from datetime import datetime
import json
import hashlib

class RecipeCache:
    def __init__(self, db_path: str = "recipe_cache.db"):
        """Initialize SQLite cache database"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()
    
    def _create_tables(self):
        """Create cache tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Cache table for Q&A
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT UNIQUE NOT NULL,
                query_text TEXT NOT NULL,
                answer TEXT NOT NULL,
                sources TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            )
        """)
        
        # Popular recipes table for instant lookup
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS popular_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT UNIQUE NOT NULL,
                recipe_data TEXT NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Query statistics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_normalized TEXT,
                count INTEGER DEFAULT 1,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        print("✓ Cache database initialized")
    
    def _hash_query(self, query: str) -> str:
        """Create hash of normalized query for cache lookup"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get_cached_answer(self, query: str) -> Optional[Dict]:
        """Retrieve cached answer if it exists"""
        query_hash = self._hash_query(query)
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT query_text, answer, sources, access_count
            FROM qa_cache
            WHERE query_hash = ?
        """, (query_hash,))
        
        result = cursor.fetchone()
        
        if result:
            # Update access statistics
            cursor.execute("""
                UPDATE qa_cache
                SET access_count = access_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE query_hash = ?
            """, (query_hash,))
            self.conn.commit()
            
            return {
                'answer': result[1],
                'sources': json.loads(result[2]) if result[2] else [],
                'cached': True,
                'access_count': result[3] + 1
            }
        
        return None
    
def cache_answer(self, query: str, answer: str, sources: List[Dict] = None):
    """Store answer in cache"""
    query_hash = self._hash_query(query)
    sources_json = json.dumps(sources) if sources else None
    
    cursor = self.conn.cursor()
    
    try:
        # Log the schema to verify
        cursor.execute("PRAGMA table_info(qa_cache)")
        schema = cursor.fetchall()
        print("qa_cache schema:", schema)
        
        # Log the query details
        print(f"Executing INSERT for query_hash: {query_hash}, query: {query}")
        
        cursor.execute("""
            INSERT OR REPLACE INTO qa_cache (query_hash, query_text, answer, sources)
            VALUES (?, ?, ?, ?)
        """, (query_hash, query, answer, sources_json))
        
        self.conn.commit()
        print("✓ Successfully cached answer")
    except Exception as e:
        print(f"Error caching answer: {e}")
        print(f"Query hash: {query_hash}")
        print(f"Query: {query}")
        print(f"Answer: {answer[:100]}...")
        print(f"Sources: {sources_json}")
        raise
    def add_popular_recipe(self, item_name: str, recipe_data: Dict, category: str = "crafting"):
        """Add a popular recipe for instant lookup"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO popular_recipes (item_name, recipe_data, category)
                VALUES (?, ?, ?)
            """, (item_name.lower(), json.dumps(recipe_data), category))
            
            self.conn.commit()
        except Exception as e:
            print(f"Error adding popular recipe: {e}")
    
    def get_popular_recipe(self, item_name: str) -> Optional[Dict]:
        """Retrieve a popular recipe"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT recipe_data, category
            FROM popular_recipes
            WHERE item_name = ?
        """, (item_name.lower(),))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'recipe': json.loads(result[0]),
                'category': result[1],
                'cached': True
            }
        
        return None
    
    def log_query(self, query: str):
        """Log query for statistics"""
        normalized = query.lower().strip()
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO query_stats (query_normalized, count)
            VALUES (?, 1)
            ON CONFLICT(query_normalized) DO UPDATE SET
                count = count + 1,
                last_seen = CURRENT_TIMESTAMP
        """, (normalized,))
        
        self.conn.commit()
    
    def get_popular_queries(self, limit: int = 10) -> List[tuple]:
        """Get most popular queries"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT query_normalized, count, last_seen
            FROM query_stats
            ORDER BY count DESC
            LIMIT ?
        """, (limit,))
        
        return cursor.fetchall()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM qa_cache")
        cached_answers = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM popular_recipes")
        popular_recipes = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(access_count) FROM qa_cache")
        total_cache_hits = cursor.fetchone()[0] or 0
        
        return {
            'cached_answers': cached_answers,
            'popular_recipes': popular_recipes,
            'total_cache_hits': total_cache_hits
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM qa_cache")
        cursor.execute("DELETE FROM query_stats")
        self.conn.commit()
        print("✓ Cache cleared")
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def seed_popular_recipes():
    """Seed cache with common Minecraft recipes"""
    cache = RecipeCache()
    
    popular_items = [
        {
            'name': 'diamond pickaxe',
            'category': 'crafting',
            'recipe': {
                'ingredients': ['3 Diamonds', '2 Sticks'],
                'pattern': 'Place 3 diamonds across the top row, and 2 sticks vertically down the middle column',
                'result': '1 Diamond Pickaxe'
            }
        },
        {
            'name': 'crafting table',
            'category': 'crafting',
            'recipe': {
                'ingredients': ['4 Wooden Planks'],
                'pattern': '2x2 grid of wooden planks',
                'result': '1 Crafting Table'
            }
        },
        {
            'name': 'furnace',
            'category': 'crafting',
            'recipe': {
                'ingredients': ['8 Cobblestone'],
                'pattern': 'Fill all slots except the center in a 3x3 grid',
                'result': '1 Furnace'
            }
        },
        {
            'name': 'golden apple',
            'category': 'crafting',
            'recipe': {
                'ingredients': ['1 Apple', '8 Gold Ingots'],
                'pattern': 'Place apple in center, surround with 8 gold ingots',
                'result': '1 Golden Apple'
            }
        },
        {
            'name': 'brewing stand',
            'category': 'crafting',
            'recipe': {
                'ingredients': ['1 Blaze Rod', '3 Cobblestone'],
                'pattern': 'Blaze rod in center, 3 cobblestone across bottom row',
                'result': '1 Brewing Stand'
            }
        }
    ]
    
    for item in popular_items:
        cache.add_popular_recipe(item['name'], item['recipe'], item['category'])
    
    print(f"✓ Seeded {len(popular_items)} popular recipes")
    cache.close()


if __name__ == "__main__":
    # Seed popular recipes
    seed_popular_recipes()
    
    # Test cache
    cache = RecipeCache()
    
    # Test caching
    print("\n--- Testing Cache ---")
    cache.cache_answer(
        "How do I craft a diamond sword?",
        "To craft a diamond sword, you need 2 diamonds and 1 stick...",
        [{'title': 'Diamond Sword', 'url': 'https://minecraft.wiki/w/Diamond_Sword'}]
    )
    
    # Retrieve cached answer
    result = cache.get_cached_answer("how do i craft a diamond sword?")
    if result:
        print(f"✓ Cache hit! Answer: {result['answer'][:50]}...")
    
    # Get stats
    stats = cache.get_cache_stats()
    print(f"\nCache Stats: {stats}")
    
    cache.close()
