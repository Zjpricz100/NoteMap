import Graph from "graphology";
import Sigma from "sigma";
import noverlap from "graphology-layout-noverlap";

async function getGraphData() {
    try {
        const response = await fetch("./layout.json");
        if (!response.ok) throw new Error("Network Response Failed");

        const data = await response.json();
        return data

    } catch (error) {
        console.log("Failed to load JSON: ", error);
    }
}

async function centerCamera(renderer: Sigma) {
    const camera = renderer.getCamera();
    camera.setState({
        x: 0.7,
        y: 0.5,
        ratio: 1
    });
}

function setupToolTip(renderer: Sigma, graph: Graph): void {
    const tooltip = document.getElementById("node-tooltip")!;
    renderer.on("enterNode", ({ node }) => {
        const attributes = graph.getNodeAttributes(node);
        // Populate the tooltip

        tooltip.classList.remove("hidden");
    });

    renderer.on("leaveNode", () => {
        tooltip.classList.add("hidden");
    });

}

const graphData = await getGraphData();
const graph = new Graph();

const renderer = new Sigma(graph, document.getElementById("container") as HTMLElement, {
    labelRenderedSizeThreshold: 100
});

graph.import(graphData);
setupToolTip(renderer, graph);


//noverlap.assign(graph, {maxIterations: 50, settings: {margin:5}});

renderer.refresh();
centerCamera(renderer);
buildLegend(graphData);

function buildLegend(data: any) {
    const legendEl = document.getElementById("legend")!;

    const title = document.createElement("div");
    title.className = "legend-title";
    title.textContent = "Clusters";
    legendEl.appendChild(title);

    // Centroid nodes use their cluster index as their key ("0", "1", ...)
    const clusters: { id: number; color: string }[] = data.nodes
        .filter((n: any) => /^\d+$/.test(n.key))
        .map((n: any) => ({ id: n.attributes.label, color: n.attributes.color }))
        .sort((a: any, b: any) => a.id - b.id);

    console.log(data.nodes)

    for (const cluster of clusters) {
        const item = document.createElement("div");
        item.className = "legend-item";

        const swatch = document.createElement("span");
        swatch.className = "legend-swatch";
        swatch.style.backgroundColor = cluster.color;

        const label = document.createElement("span");
        label.className = "legend-label";
        label.textContent = `${cluster.id}`;

        item.appendChild(swatch);
        item.appendChild(label);
        legendEl.appendChild(item);
    }
}







