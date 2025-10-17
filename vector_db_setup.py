"""
Vector Database Setup with ChromaDB
Handles embedding generation and similarity search
"""

import concurrent.futures
import json
import os

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class MinecraftVectorDB:
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "minecraft_wiki",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """
        Initialize ChromaDB with sentence-transformers embeddings
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )

        # Load embedding model
        print(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Minecraft Wiki Knowledge Base"},
            )
            print(f"Created new collection: {collection_name}")

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text"""
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()  # type: ignore

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()  # type: ignore

    def add_documents(self, documents: list[dict], batch_size: int = 100) -> None:
        """
        Add documents to the vector database
        documents: List of dicts with 'title', 'content', 'url'
        """
        print(f"Adding {len(documents)} documents to vector DB...")

        # Prepare batches
        batches = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            ids = [f"doc_{i + j}" for j in range(len(batch))]
            texts = [doc["content"] for doc in batch]
            metadatas = [
                {"title": doc["title"], "url": doc.get("url", ""), "chunk_id": i + j}
                for j, doc in enumerate(batch)
            ]
            batches.append((ids, texts, metadatas))

        # Multi-threaded encoding
        def encode_batch(batch_data: tuple) -> tuple:
            ids, texts, metadatas = batch_data
            embeddings = self.embed_batch(texts)
            return ids, embeddings, texts, metadatas

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            encoded_batches = list(executor.map(encode_batch, batches))

        # Add to collection sequentially (ChromaDB may not be thread-safe for adds)
        for ids, embeddings, texts, metadatas in encoded_batches:
            self.collection.add(
                ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
            )

            print(
                f"Added batch {i // batch_size + 1}/"
                f"{(len(documents) - 1) // batch_size + 1}"
            )

        print("✓ All documents indexed!")

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        """
        Search for relevant documents
        Returns list of dicts with 'content', 'title', 'url', 'score'
        """
        # Generate query embedding
        query_embedding = self.embed_text(query)

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,  # type: ignore
        )

        # Format results
        formatted_results = []
        if results["documents"] and len(results["documents"]) > 0:  # type: ignore
            for i in range(len(results["documents"][0])):  # type: ignore
                formatted_results.append(
                    {
                        "content": results["documents"][0][i],  # type: ignore
                        "title": results["metadatas"][0][i]["title"],  # type: ignore
                        "url": results["metadatas"][0][i]["url"],  # type: ignore
                        "score": (
                            1 - results["distances"][0][i]  # type: ignore
                            if results["distances"]
                            else 1.0
                        ),
                    }
                )

        return formatted_results

    def reset_collection(self) -> None:
        """Delete and recreate the collection"""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Minecraft Wiki Knowledge Base"},
        )
        print("Collection reset!")

    def get_collection_stats(self) -> dict:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            "total_documents": count,
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model,
        }


def build_vector_db_from_json(
    wiki_json_path: str = "wiki_data/wiki_docs_chunks.json",
    external_json_path: str = "wiki_data/external_urls_scraped.json",
) -> MinecraftVectorDB:
    """Helper function to build vector DB from scraped JSON files"""

    # Load wiki documents
    print(f"Loading wiki documents from {wiki_json_path}")
    with open(wiki_json_path, encoding="utf-8") as f:
        wiki_documents = json.load(f)

    # Load external URL documents if they exist
    external_documents = []
    if os.path.exists(external_json_path):
        print(f"Loading external URL documents from {external_json_path}")
        with open(external_json_path, encoding="utf-8") as f:
            external_documents = json.load(f)
    else:
        print(f"External URLs file not found: {external_json_path}")

    # Combine all documents
    all_documents = wiki_documents + external_documents
    print(
        f"Total documents to process: {len(all_documents)} "
        f"({len(wiki_documents)} wiki + {len(external_documents)} external)"
    )

    # Initialize vector DB
    vector_db = MinecraftVectorDB()

    # Reset if needed (uncomment to start fresh)
    # vector_db.reset_collection()

    # Check if already populated
    stats = vector_db.get_collection_stats()
    if stats["total_documents"] > 0:
        print(f"Collection already has {stats['total_documents']} documents")
        user_input = input("Reset and rebuild? (yes/no): ")
        if user_input.lower() == "yes":
            vector_db.reset_collection()
        else:
            return vector_db

    # Add documents
    vector_db.add_documents(all_documents)

    # Print stats
    stats = vector_db.get_collection_stats()
    print("\nVector DB Stats:")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Collection: {stats['collection_name']}")

    return vector_db


if __name__ == "__main__":
    # Build vector database from scraped data
    db = build_vector_db_from_json()

    # Test search
    print("\n--- Testing Search ---")
    test_query = "How do I craft a diamond pickaxe?"
    results = db.search(test_query, n_results=3)

    print(f"\nQuery: {test_query}\n")
    for i, result in enumerate(results):
        print(f"Result {i + 1} (score: {result['score']:.3f}):")
        print(f"  Title: {result['title']}")
        print(f"  Content preview: {result['content'][:200]}...")
        print()
