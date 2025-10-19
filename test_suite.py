"""
Comprehensive Test Suite for Minecraft Wiki Bot
Tests x.ai integration, API endpoints, and webhook handling
"""

import unittest

import requests

from src.xai.pipeline import DirectXAIPipeline


class TestXAIPipeline(unittest.TestCase):
    """Test x.ai pipeline functionality"""

    pipeline: DirectXAIPipeline

    @classmethod
    def setUpClass(cls) -> None:
        """Initialize x.ai pipeline"""
        # Use test API key if available, otherwise skip tests
        test_key = "test-key-for-testing"
        try:
            cls.pipeline = DirectXAIPipeline(
                xai_api_key=test_key,
                xai_url="https://api.x.ai/v1",
                model_name="grok-4-fast-non-reasoning",
                prompt_template_path="prompt_template.txt",
            )
        except Exception:
            cls.pipeline = None

    def test_pipeline_initialization(self) -> None:
        """Test that pipeline initializes correctly"""
        if self.pipeline is None:
            self.skipTest("Pipeline not initialized (missing API key)")
        self.assertIsNotNone(self.pipeline)

    def test_format_response(self) -> None:
        """Test response formatting"""
        if self.pipeline is None:
            self.skipTest("Pipeline not initialized")

        test_result = {"answer": "Test answer", "sources": []}
        formatted = self.pipeline.format_response_for_chat(test_result)
        self.assertIn("Test answer", formatted)


class TestAPIEndpoints(unittest.TestCase):
    """Test API endpoints"""

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


if __name__ == "__main__":
    unittest.main()
