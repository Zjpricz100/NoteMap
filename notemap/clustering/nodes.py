from notemap.clustering.umap import *
from notemap.embeddings.embed import MANIFEST_PATH
import json
from bokeh.palettes import Category20

#COLOR_DICT = {i: color for i, color in enumerate(Viridis256)}
LAYOUT_PATH = "notemap/graph/layout.json"
COLOR_SPACE_AMT = 256


def create_layout(embeddings: np.ndarray,
                  hdb_params: dict, umap1_params: dict, umap2_params: dict, SEED):
    """Builds an importable Serialized Graph object for Graphology. Embeddings are EXPECTED to be 2D.
    hdb params are passed in as a dictionary.
    umap params are passed in as a dictionary with umap1 being transformation 1 and umap2 being transformation 2.
    """

    # Dimension Reduce the embeddings for visualization, cluster with HDBSCAN
    reduced_embeddings = umap_reduce(
        embeddings, 
        n_neighbors=umap1_params["n_neighbors"], 
        n_components=umap1_params["n_components"], 
        min_distance=umap1_params["min_distance"], 
        seed=SEED)


    node_labels = hdb_cluster(
        reduced_embeddings, 
        min_samples=hdb_params["min_samples"],
        min_cluster_size=hdb_params["min_cluster_size"],
        method=hdb_params["method"]
    )

    reduced_embeddings_2d = umap_reduce(
        embeddings, 
        n_neighbors=umap2_params["n_neighbors"], 
        n_components=umap2_params["n_components"], 
        min_distance=umap2_params["min_distance"], 
        seed=SEED)
    
    noise_count = int((node_labels == -1).sum())
    print(f"Unlabeled points: {noise_count}/{len(node_labels)}")

    # Setting up categorical colors
    num_clusters = int(node_labels.max()) + 1
    palette = Category20[num_clusters]
    color_dict = {i : color for i, color in enumerate(palette)}

    assert reduced_embeddings_2d.shape[1] == 2

    with open(MANIFEST_PATH, 'r') as f:
        manifest = json.load(f)
    
    nodes = []
    for i, (row, label) in enumerate(zip(manifest, node_labels)):
        if label >= 0:
            nodes.append({
                "key": row['chunk_id'],
                "attributes": {
                    "x": float(reduced_embeddings_2d[i, 0]),
                    "y": float(reduced_embeddings_2d[i, 1]),
                    "size": 10,
                    "color": str(color_dict[label]),
                    "label": str(row['source_path'])
                }
            })
    
    edges = []
    # do edges later

    # Write to json layout file for Sigma to render
    data = {"nodes": nodes, "edges": edges}
    with open(LAYOUT_PATH, "w") as f:
        json.dump(data, f)


