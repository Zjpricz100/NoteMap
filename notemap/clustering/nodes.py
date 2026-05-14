from notemap.clustering.umap import *
from notemap.embeddings.embed import MANIFEST_PATH
import json
from bokeh.palettes import Category20
import glasbey
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_distances
from scipy.sparse.csgraph import minimum_spanning_tree
from anthropic import Anthropic


#COLOR_DICT = {i: color for i, color in enumerate(Viridis256)}
LAYOUT_PATH = "notemap/graph/layout.json"
COLOR_SPACE_AMT = 256


def create_layout(embeddings: np.ndarray,
                  hdb_params: dict, umap1_params: dict, umap2_params: dict, client: Anthropic, model: str, SEED):
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
        min_samples=1,
        min_cluster_size=hdb_params["min_cluster_size"],
        method=hdb_params["method"]
    )

    reduced_embeddings_2d = pca_reduce(embeddings, n_components=2)

    reduced_embeddings_2d = umap_reduce(
        embeddings,
        n_neighbors=umap2_params["n_neighbors"],
        n_components=umap2_params["n_components"],
        min_distance=umap2_params["min_distance"],
        spread=1.0,
        seed=SEED)
    

    CANVAS = 100.0
    for dim in range(2):
        col = reduced_embeddings_2d[:, dim]
        lo, hi = col.min(), col.max()
        if hi > lo:
            reduced_embeddings_2d[:, dim] = (col - lo) / (hi - lo) * 2 * CANVAS - CANVAS

    noise_count = int((node_labels == -1).sum())
    print(f"Unlabeled points: {noise_count}/{len(node_labels)}")

    # Setting up categorical colors
    num_clusters = int(node_labels.max()) + 1
    palette = glasbey.create_palette(palette_size=256)
    color_dict = {i : color for i, color in enumerate(palette)}

    assert reduced_embeddings_2d.shape[1] == 2


    with open(MANIFEST_PATH, 'r') as f:
        manifest = json.load(f)
    data_chunks = manifest["chunks"]

    # Update manifest with centroid nodes
    create_centroid_nodes(reduced_embeddings_2d, node_labels, data_chunks, client, model, k=5)

    # Update manifest with non centroid edges from the MST
    compute_edges(embeddings, node_labels, data_chunks)

    with open(MANIFEST_PATH, 'r') as f:
        manifest = json.load(f)



    data_centroid_chunks = manifest["centroid_chunks"]
    data_edges = manifest["edges"]

    
    nodes = []

    # Non centroid nodess
    for i, (row, label) in enumerate(zip(data_chunks, node_labels)):
        if label >= 0:
            nodes.append({
                "key": row['chunk_id'],
                "attributes": {
                    "x": float(reduced_embeddings_2d[i, 0]),
                    "y": float(reduced_embeddings_2d[i, 1]),
                    "size": 8,
                    "color": str(color_dict[label]),
                    "label": str(row['summary'])
                }
            })
    
    # Centroid nodes
    for i, (row, label) in enumerate(zip(data_centroid_chunks, range(num_clusters))):
        if label >= 0:
            nodes.append({
                "key": row['chunk_id'],
                "attributes": {
                    "x": row['x'],
                    "y": row['y'],
                    "size": 16,
                    "color": str(color_dict[label]),
                    "label": str(row['summary'])
                }
            })
    
    # Edges
    edges = []
    for i, row in enumerate(data_edges):
        source = row["source"]
        target = row["target"]
        edges.append({
            "key": f"{source}->{target}",
            "source": source,
            "target": target,
            "attributes": row["attributes"]
        })
    
    # Write to json layout file for Sigma to render
    data = {"nodes": nodes, "edges": edges}
    with open(LAYOUT_PATH, "w") as f:
        json.dump(data, f)

def create_centroid_nodes(reduced_embeddings_2d: np.ndarray, node_labels: np.ndarray, data_chunks: list[dict], client: Anthropic, model: str, k:int=5) -> None:
    assert(reduced_embeddings_2d.shape[1] == 2)
    num_clusters = int(node_labels.max()) + 1

    with open(MANIFEST_PATH, 'r') as f:
        data = json.load(f)

    centroid_nodes = []
    print(reduced_embeddings_2d.shape)
    print(node_labels.shape)
    print("Number of Clusters: ", num_clusters)

    clusters = []
    for label in range(num_clusters):
        label_mask = node_labels == label
        node_indices = np.where(label_mask)[0]
        nodes_in_cluster = reduced_embeddings_2d[node_indices]
        nn_cluster = NearestNeighbors(n_neighbors=k, algorithm="ball_tree").fit(nodes_in_cluster)

        centroid_x = nodes_in_cluster[:, 0].mean()
        centroid_y = nodes_in_cluster[:, 1].mean()
        centroid = np.array([[centroid_x, centroid_y]])

        # indices is (n_queries, k)
        _, indices = nn_cluster.kneighbors(centroid) # Get the k nearest neighbors to this centroid
        original_indices = node_indices[indices[0]]
        nearest_neighbors_in_cluster = [data_chunks[i] for i in original_indices]


        summaries_in_cluster = [c["summary"] for c in nearest_neighbors_in_cluster]
        cluster = {"id" : label, "summaries" : summaries_in_cluster, "x": centroid_x, "y": centroid_y}
        clusters.append(cluster)
    

    # Label each cluster with the LLM model
    print("Generating Cluster Labels... ")
    label_response = label_clusters(clusters, client, model)

    for cluster in clusters:
        centroid_entry = {
            "chunk_id": cluster["id"],
            "source_path": "CENTROID",
            "page_number": "N/A",
            "text": "N/A",
            "summary": label_response[cluster["id"]],
            "x": float(cluster["x"]),
            "y": float(cluster["y"])
        }
        centroid_nodes.append(centroid_entry)

    data["centroid_chunks"] = centroid_nodes
    

    with open(MANIFEST_PATH, 'w') as f:
        json.dump(data, f)

    print("Cluster Labels Generated")

def compute_edges(embeddings: np.ndarray, node_labels: np.ndarray, data_chunks: list[dict]):
    """Builds a MST from the embeddings to label edges."""
    valid = [(i, row["chunk_id"]) for i, (row, label) in enumerate(zip(data_chunks, node_labels)) if label >= 0]
    valid_indices = np.array([i for i, _ in valid])
    valid_ids = [chunk_id for _, chunk_id in valid]

    filtered_embeddings = embeddings[valid_indices]

    distances = cosine_distances(filtered_embeddings) # N x N
    mst = minimum_spanning_tree(distances)
    mst_coo = mst.tocoo()

    with open(MANIFEST_PATH, 'r') as f:
        data = json.load(f)

    data_edges = [] 

    # row, col is idx_start, idx_end. Use these values to index into node_labels to properly create edges
    for u, v, weight in zip(mst_coo.row, mst_coo.col, mst_coo.data):
        edge_entry = {
            "source" : valid_ids[u],
            "target" : valid_ids[v],
            "attributes" : {
                "size" : 2,
                "color" : "#000000",
                "weight" : weight
            }
        }
        data_edges.append(edge_entry)
    
    data["edges"] = data_edges

    with open(MANIFEST_PATH, 'w') as f:
        json.dump(data, f)


def build_prompt(clusters: list[dict]) -> str:
    """
    Builds a prompt to send to a client LLM for labeling

    Each cluster in clusters should be a dictionary with keys id and summaries
    """
    lines = []
    for c in clusters:
        summaries = c["summaries"]
        id = c["id"]
        lines.append(
            f'Cluster {id}:\n'
            f'Summaries {", ".join(summaries)}\n'
        )
    cluster_block = "\n\n".join(lines)

    return f"""You will be given several clusters of documents. Each cluster has a numerical id and a representative summary. Produce a short, descriptive label (2-3 words) for each cluster that captures what unifies the documents in it.

    {cluster_block}

    Respond with ONLY a JSON array of objects, one per cluster, in the same order:
    [{{"id": 0, "label": "..."}}, {{"id": 1, "label": "..."}}, ...]
    No prose, no markdown fences."""

def label_clusters(clusters: list[dict], client: Anthropic, model: str) -> dict:
    """Labels clusters using an LLM and a prompt"""
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": build_prompt(clusters)},
                ],
            }
        ],
    )
    raw = response.content[0].text.strip()
    return {item["id"]: item["label"] for item in json.loads(raw)}
