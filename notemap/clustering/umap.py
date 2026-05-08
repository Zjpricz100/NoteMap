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


def umap_reduce(embeddings: np.ndarray, dim=2, seed=None):
    """Reduces all embeddings to dimensionality dim"""
    reducer = umap.UMAP(
        n_neighbors=15,
        n_components=dim,
        metric='cosine',
        min_dist=0.1,
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


    