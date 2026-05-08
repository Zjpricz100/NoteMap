from sklearn.datasets import fetch_openml
from sklearn.decomposition import PCA
import numpy as np
import pandas as pd
import plotly.express as px
import json
from pathlib import Path

# Dimension reduction and clustering libraries
import umap
import hdbscan
import sklearn.cluster as cluster
from sklearn.metrics import adjusted_rand_score, adjusted_mutual_info_score


def umap_reduce(embeddings: np.ndarray, n_neighbors, n_components, min_distance=0.0, seed=None):
    """Reduces all embeddings to dimensionality dim"""
    reducer = umap.UMAP(
        n_neighbors=n_neighbors,
        n_components=n_components,
        metric='cosine',
        min_dist=min_distance,
        random_state=seed,
        n_jobs=1
    )
    return reducer.fit_transform(embeddings)



def plot_embeddings(embeddings: np.ndarray, manifest_path: Path):
    """Scatter plots 2D embeddings colored by source document using plotly."""
    assert embeddings.shape[1] == 2
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    df = pd.DataFrame({
        "x": embeddings[:, 0],
        "y": embeddings[:, 1],
        "source_doc": [Path(m["source_path"]).name for m in manifest],
        "chunk_id": [m["chunk_id"] for m in manifest],
        "page": [m["page_number"] for m in manifest],
    })

    fig = px.scatter(
        df, x="x", y="y",
        color="source_doc",
        hover_data=["chunk_id", "page"],
        title="UMAP projection of document embeddings",
    )
    fig.show()

def hdb_cluster(clusterable_embeddings: np.ndarray, min_samples: int, min_cluster_size: int, method: str="leaf"):
    labels = hdbscan.HDBSCAN(
        min_samples=min_samples,
        min_cluster_size=min_cluster_size,
        cluster_selection_method=method
    ).fit_predict(clusterable_embeddings)
    return labels

def plot_embedding_clusters(reduced_embeddings: np.ndarray, cluster_labels: np.ndarray, manifest_path: Path):
    """Scatter plots 2d embeddings colored by HDBSCAN cluster label. Expects embeddings to be reduced to 2D"""
    assert reduced_embeddings.shape[1] == 2
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    
    clustered = cluster_labels >= 0
    df = pd.DataFrame({
        "x": reduced_embeddings[clustered, 0],
        "y": reduced_embeddings[clustered, 1],
        "cluster": [str(l) for l in cluster_labels[clustered]],
        "source_doc": [Path(m["source_path"]).name for m, c in zip(manifest, clustered) if c],
        "page": [m["page_number"] for m, c in zip(manifest, clustered) if c],
    })
    fig = px.scatter(
        df, x="x", y="y",
        color="cluster",
        hover_data=["source_doc", "page"],
        title="HDBSCAN Clusters of Document Embeddings",
    )
    fig.show()

    noise_count = int((cluster_labels == -1).sum())
    print(f"Unlabeled points: {noise_count}/{len(cluster_labels)}")
    


    