"""
Comprehensive Test Suite for Minecraft Wiki Bot
Tests all components: scraping, vector DB, RAG, caching, API
"""

import unittest
import requests
import json
from pathlib import Path
import time

from vector_db import MinecraftVectorDB
from rag_pipeline import MinecraftRAGPipeline
from cache_manager import RecipeCache


class TestVectorDatabase(unittest.TestCase):
    """Test vector database functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize test database"""
        cls.db = MinecraftVectorDB(
            persist_directory="./test_chroma_db",
            collection_name="test_minecraft"
        )
        
        # Add sample documents
        test_docs = [
            {
                'title': 'Diamond Pickaxe',
                'content': 'A diamond pickaxe is crafted with 3 diamonds and 2 sticks. Place diamonds across the top row and sticks down the middle.',
                'url': 'https://minecraft.wiki/w/Diamond_Pickaxe'
            },
            {
                'title': 'Crafting Table',
                'content': 'A crafting table is made from 4 wooden planks arranged in a 2x2 pattern.',
                'url': 'https://minecraft.wiki/w/Crafting_Table'
            }
        ]
        cls.db.add_documents(test_docs)
    
    def test_search_relevant_results(self):
        """Test that search returns relevant results"""
        results = self.db.search("how to craft diamond pickaxe", n_results=2)
        
        self.assertGreater(len(results), 0)
        self.assertIn('Diamond Pickaxe', results[0]['title'])
        self.assertGreater(results[0]['score'], 0.5)
    
    def test_collection_stats(self):
        """Test collection statistics"""
        stats = self.db.get_collection_stats()
        
        self.assertIn('total_documents', stats)
        self.assertGreaterEqual(stats['total_documents'], 2)


class TestRAGPipeline(unittest.TestCase):
    """Test RAG pipeline functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize RAG pipeline"""
        cls.db = MinecraftVectorDB(
            persist_directory="./test_chroma_db",
            collection_name="test_minecraft"
        )
        cls.rag = MinecraftRAGPipeline(cls.db)
    
    def test_context_retrieval(self):
        """Test context retrieval"""
        context = self.rag.retrieve_context("diamond pickaxe recipe")
        
        self.assertIsInstance(context, list)
        self.assertGreater(len(context), 0)
        self.assertIn('content', context[0])
    
    def test_prompt_building(self):
        """Test prompt construction"""
        context_docs = [
            {
                'title': 'Test Item',
                'content': 'Test content',
                'url': 'http://test.com'
            }
        ]
        
        prompt = self.rag.build_prompt("test query", context_docs)
        
        self.assertIn("test query", prompt.lower())
        self.assertIn("Test content", prompt)
    
    def test_answer_generation(self):
        """Test complete answer generation"""
        result = self.rag.answer_question("How do I craft a diamond pickaxe?")
        
        self.assertIn('answer', result)
        self.assertIn('sources', result)
        self.assertIsInstance(result['answer'], str)
        self.assertGreater(len(result['answer']), 10)


class TestCache(unittest.TestCase):
    """Test caching functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize test cache"""
        cls.cache = RecipeCache("test_cache.db")
    
    def test_cache_storage(self):
        """Test storing answers in cache"""
        query = "test craft diamond sword"
        answer = "Test answer for diamond sword"
        sources = [{'title': 'Diamond Sword', 'url': 'http://test.com'}]
        
        self.cache.cache_answer(query, answer, sources)
        
        # Retrieve cached answer
        result = self.cache.get_cached_answer(query)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['answer'], answer)
        self.assertTrue(result['cached'])
    
    def test_popular_recipes(self):
        """Test popular recipe storage"""
        self.cache.add_popular_recipe(
            "test_item",
            {'ingredients': ['A', 'B'], 'result': 'Test Item'},
            "crafting"
        )
        
        recipe = self.cache.get_popular_recipe("test_item")
        
        self.assertIsNotNone(recipe)
        self.assertIn('recipe', recipe)
        self.assertEqual(recipe['category'], 'crafting')
    
    def test_query_logging(self):
        """Test query statistics"""
        test_query = "test query for stats"
        
        self.cache.log_query(test_query)
        self.cache.log_query(test_query)  # Log twice
        
        popular = self.cache.get_popular_queries(limit=10)
        
        # Check if our query appears
        query_found = any(test_query.lower() in q[0] for q in popular)
        self.assertTrue(query_found)


class TestAPIEndpoints(unittest.TestCase):
    """Test FastAPI endpoints"""
    
    BASE_URL = "http://localhost:8000"
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn('status', data)
                self.assertEqual(data['status'], 'healthy')
            else:
                self.skipTest("Bot service not running")
        except requests.exceptions.ConnectionError:
            self.skipTest("Bot service not accessible")
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        try:
            response = requests.get(f"{self.BASE_URL}/", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn('status', data)
                self.assertIn('bot_name', data)
        except requests.exceptions.ConnectionError:
            self.skipTest("Bot service not accessible")
    
    def test_query_endpoint(self):
        """Test query endpoint"""
        try:
            response = requests.post(
                f"{self.BASE_URL}/test-query",
                params={"query": "How to craft diamond pickaxe?"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn('result', data)
                self.assertIn('source', data)
        except requests.exceptions.ConnectionError:
            self.skipTest("Bot service not accessible")
    
    def test_stats_endpoint(self):
        """Test statistics endpoint"""
        try:
            response = requests.get(f"{self.BASE_URL}/stats", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.assertIsInstance(data, dict)
        except requests.exceptions.ConnectionError:
            self.skipTest("Bot service not accessible")


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow"""
    
    def test_end_to_end_query(self):
        """Test complete query flow"""
        # Initialize components
        db = MinecraftVectorDB()
        rag = MinecraftRAGPipeline(db)
        cache = RecipeCache()
        
        # Test query
        query = "How do I craft a golden apple?"
        
        # Check cache first
        cached = cache.get_cached_answer(query)
        
        if not cached:
            # Generate answer
            result = rag.answer_question(query)
            
            # Cache result
            cache.cache_answer(query, result['answer'], result.get('sources'))
            
            self.assertIn('answer', result)
            self.assertIsInstance(result['answer'], str)
        
        # Verify cache works
        cached_result = cache.get_cached_answer(query)
        self.assertIsNotNone(cached_result)
        self.assertTrue(cached_result['cached'])


def run_tests():
    """Run all tests"""
    print("="*60)
    print("Running Minecraft Wiki Bot Test Suite")
    print("="*60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestVectorDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestRAGPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestCache))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("="*60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
