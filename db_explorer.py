"""
ChromaDB Visual Explorer
A Streamlit app to visually explore the Minecraft vector database
"""

import chromadb
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from chromadb.config import Settings
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

# Page config
st.set_page_config(
    page_title="Minecraft Vector DB Explorer", page_icon="🎮", layout="wide"
)

st.title("🎮 Minecraft Vector Database Explorer")
st.markdown("Explore your ChromaDB collection of Minecraft knowledge")


# Initialize ChromaDB connection
@st.cache_resource
def init_chromadb():
    """Initialize ChromaDB client"""
    try:
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
        collection = client.get_collection(name="minecraft_wiki")
        return client, collection
    except Exception as e:
        st.error(f"Failed to connect to ChromaDB: {e}")
        return None, None


def main():
    client, collection = init_chromadb()

    if not collection:
        st.error(
            "Could not connect to ChromaDB. Make sure the database "
            "exists and is accessible."
        )
        return

    # Get collection stats
    try:
        count = collection.count()
        st.success(f"✅ Connected to collection with {count} documents")

        # Sidebar controls
        st.sidebar.header("🔍 Exploration Controls")

        # Get sample data
        if count > 0:
            results = collection.get(limit=min(1000, count))
            df = pd.DataFrame(
                {
                    "id": results["ids"],
                    "document": results["documents"],
                    "metadata": results["metadatas"],
                }
            )

            # Expand metadata
            if df["metadata"].notna().any():
                metadata_df = pd.json_normalize(df["metadata"])
                df = pd.concat([df.drop("metadata", axis=1), metadata_df], axis=1)

            # Display basic stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Documents", count)
            with col2:
                avg_length = df["document"].str.len().mean()
                st.metric("Avg Document Length", f"{avg_length:.0f} chars")
            with col3:
                if "source" in df.columns:
                    unique_sources = df["source"].nunique()
                    st.metric("Unique Sources", unique_sources)

            # Document explorer
            st.header("📄 Document Explorer")
            with st.expander("View Documents", expanded=False):
                st.dataframe(df[["id", "document"]].head(50), use_container_width=True)

            # Search functionality
            st.header("🔎 Semantic Search")
            query = st.text_input(
                "Enter a search query:", "How do I craft a diamond sword?"
            )

            if st.button("Search") and query:
                with st.spinner("Searching..."):
                    try:
                        search_results = collection.query(
                            query_texts=[query], n_results=min(10, count)
                        )

                        if search_results["documents"]:
                            st.subheader("Search Results")
                            for i, (doc, score, meta) in enumerate(
                                zip(
                                    search_results["documents"][0],
                                    (
                                        search_results["distances"][0]
                                        if "distances" in search_results
                                        else [0] * len(search_results["documents"][0])
                                    ),
                                    (
                                        search_results["metadatas"][0]
                                        if "metadatas" in search_results
                                        else [{}] * len(search_results["documents"][0])
                                    ),
                                    strict=False,
                                )
                            ):
                                with st.expander(
                                    f"Result {i+1} (Distance: {score:.3f})",
                                    expanded=i < 3,
                                ):
                                    st.write(doc)
                                    if meta:
                                        st.json(meta)
                        else:
                            st.warning("No results found")
                    except Exception as e:
                        st.error(f"Search failed: {e}")

            # Visualization
            st.header("📊 Vector Visualization")

            if count >= 10:  # Need minimum data for visualization
                viz_option = st.selectbox(
                    "Visualization Method:",
                    ["2D Scatter Plot", "3D Scatter Plot", "PCA Components"],
                )

                if st.button("Generate Visualization"):
                    with st.spinner("Computing embeddings and visualization..."):
                        try:
                            # Get embeddings
                            embeddings_results = collection.get(
                                include=["embeddings"], limit=min(500, count)
                            )
                            embeddings = np.array(embeddings_results["embeddings"])

                            if len(embeddings) < 10:
                                st.warning(
                                    "Need at least 10 documents for visualization"
                                )
                            else:
                                # Reduce dimensionality
                                if viz_option == "2D Scatter Plot":
                                    tsne = TSNE(
                                        n_components=2,
                                        random_state=42,
                                        perplexity=min(30, len(embeddings) - 1),
                                    )
                                    reduced = tsne.fit_transform(embeddings)

                                    fig = px.scatter(
                                        x=reduced[:, 0],
                                        y=reduced[:, 1],
                                        title="Document Embeddings (t-SNE)",
                                        labels={"x": "t-SNE 1", "y": "t-SNE 2"},
                                    )
                                    st.plotly_chart(fig, use_container_width=True)

                                elif viz_option == "3D Scatter Plot":
                                    tsne = TSNE(
                                        n_components=3,
                                        random_state=42,
                                        perplexity=min(30, len(embeddings) - 1),
                                    )
                                    reduced = tsne.fit_transform(embeddings)

                                    fig = go.Figure(
                                        data=[
                                            go.Scatter3d(
                                                x=reduced[:, 0],
                                                y=reduced[:, 1],
                                                z=reduced[:, 2],
                                                mode="markers",
                                                marker={"size": 4, "opacity": 0.7},
                                            )
                                        ]
                                    )
                                    fig.update_layout(
                                        title="Document Embeddings (3D t-SNE)",
                                        scene={
                                            "xaxis_title": "t-SNE 1",
                                            "yaxis_title": "t-SNE 2",
                                            "zaxis_title": "t-SNE 3",
                                        },
                                    )
                                    st.plotly_chart(fig, use_container_width=True)

                                elif viz_option == "PCA Components":
                                    pca = PCA(n_components=2)
                                    reduced = pca.fit_transform(embeddings)

                                    fig = px.scatter(
                                        x=reduced[:, 0],
                                        y=reduced[:, 1],
                                        title="PCA Visualization",
                                        labels={"x": "PC1", "y": "PC2"},
                                    )
                                    st.plotly_chart(fig, use_container_width=True)

                        except Exception as e:
                            st.error(f"Visualization failed: {e}")
            else:
                st.info("Need at least 10 documents for vector visualization")

        else:
            st.warning("No documents found in the collection")

    except Exception as e:
        st.error(f"Error accessing collection: {e}")


if __name__ == "__main__":
    main()
