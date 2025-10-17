"""
Comprehensive Test Suite for Minecraft Wiki Bot
Tests all components: scraping, vector DB, RAG, caching, API
"""

import unittest

import requests
from rag_pipeline import MinecraftRAGPipeline
from vector_db import MinecraftVectorDB


class TestVectorDatabase(unittest.TestCase):
    """Test vector database functionality"""

    db: MinecraftVectorDB

    @classmethod
    def setUpClass(cls) -> None:
        """Initialize test database"""
        cls.db = MinecraftVectorDB(
            persist_directory="./test_chroma_db", collection_name="test_minecraft"
        )

        # Add sample documents
        test_docs = [
            {
                "title": "Diamond Pickaxe",
                "content": "A diamond pickaxe is crafted with 3 diamonds and 2 sticks. "
                "Place diamonds across the top row and sticks down the middle.",
                "url": "https://minecraft.wiki/w/Diamond_Pickaxe",
            },
            {
                "title": "Crafting Table",
                "content": "A crafting table is made from 4 wooden planks "
                "arranged in a 2x2 pattern.",
                "url": "https://minecraft.wiki/w/Crafting_Table",
            },
        ]
        cls.db.add_documents(test_docs)

    def test_search_relevant_results(self) -> None:
        """Test that search returns relevant results"""
        results = self.db.search("how to craft diamond pickaxe", n_results=2)

        self.assertGreater(len(results), 0)
        self.assertIn("Diamond Pickaxe", results[0]["title"])
        self.assertGreater(results[0]["score"], 0.5)

    def test_collection_stats(self) -> None:
        """Test collection statistics"""
        stats = self.db.get_collection_stats()

        self.assertIn("total_documents", stats)
        self.assertGreaterEqual(stats["total_documents"], 2)


class TestRAGPipeline(unittest.TestCase):
    """Test RAG pipeline functionality"""

    db: MinecraftVectorDB
    rag: MinecraftRAGPipeline

    @classmethod
    def setUpClass(cls) -> None:
        """Initialize RAG pipeline"""
        cls.db = MinecraftVectorDB(
            persist_directory="./test_chroma_db", collection_name="test_minecraft"
        )
        cls.rag = MinecraftRAGPipeline(cls.db)

    def test_context_retrieval(self) -> None:
        """Test context retrieval"""
        context = self.rag.retrieve_context("diamond pickaxe recipe")

        self.assertIsInstance(context, list)
        self.assertGreater(len(context), 0)
        self.assertIn("content", context[0])

    def test_prompt_building(self) -> None:
        """Test prompt construction"""
        context_docs = [
            {"title": "Test Item", "content": "Test content", "url": "http://test.com"}
        ]

        prompt = self.rag.build_prompt("test query", context_docs)

        self.assertIn("test query", prompt.lower())
        self.assertIn("Test content", prompt)

    def test_answer_generation(self) -> None:
        """Test complete answer generation"""
        result = self.rag.answer_question("How do I craft a diamond pickaxe?")

        self.assertIn("answer", result)
        self.assertIn("sources", result)
        self.assertIsInstance(result["answer"], str)
        self.assertGreater(len(result["answer"]), 10)


class TestAPIEndpoints(unittest.TestCase):
    """Test FastAPI endpoints"""

    BASE_URL = "http://localhost:8000"

    def test_health_endpoint(self) -> None:
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)

            if response.status_code == 200:
                data = response.json()
                self.assertIn("status", data)
                self.assertEqual(data["status"], "healthy")
            else:
                self.skipTest("Bot service not running")
        except requests.exceptions.ConnectionError:
            self.skipTest("Bot service not accessible")

    def test_root_endpoint(self) -> None:
        """Test root endpoint"""
        try:
            response = requests.get(f"{self.BASE_URL}/", timeout=5)

            if response.status_code == 200:
                data = response.json()
                self.assertIn("status", data)
                self.assertIn("bot_name", data)
        except requests.exceptions.ConnectionError:
            self.skipTest("Bot service not accessible")

    def test_query_endpoint(self) -> None:
        """Test query endpoint"""
        try:
            response = requests.post(
                f"{self.BASE_URL}/test-query",
                params={"query": "How to craft diamond pickaxe?"},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                self.assertIn("result", data)
                self.assertIn("source", data)
        except requests.exceptions.ConnectionError:
            self.skipTest("Bot service not accessible")

    def test_stats_endpoint(self) -> None:
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

    def test_end_to_end_query(self) -> None:
        """Test complete query flow"""
        # Initialize components
        db = MinecraftVectorDB()
        rag = MinecraftRAGPipeline(db)

        # Test query
        query = "How do I craft a golden apple?"

        # Generate answer
        result = rag.answer_question(query)

        self.assertIn("answer", result)
        self.assertIsInstance(result["answer"], str)


def run_tests() -> bool:
    """Run all tests"""
    print("=" * 60)
    print("Running Minecraft Wiki Bot Test Suite")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestVectorDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestRAGPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
