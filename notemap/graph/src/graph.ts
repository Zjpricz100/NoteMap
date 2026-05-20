import Graph from "graphology";
import Sigma from "sigma";
import noverlap from "graphology-layout-noverlap";
import * as pdfjsLib from "pdfjs-dist";
declare const __NOTEMAP_ROOT__: string;

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
    "pdfjs-dist/build/pdf.worker.min.mjs",
    import.meta.url
).toString();


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

const CMAP_URL = `/@fs${__NOTEMAP_ROOT__}/notemap/graph/node_modules/pdfjs-dist/cmaps/`;

let currentRenderTask: pdfjsLib.RenderTask | null = null;
let renderGeneration = 0;

async function renderPDFPage(pdfURL: string, pageNumber: number, canvas: HTMLCanvasElement): Promise<void> {
    const generation = ++renderGeneration;
    if (currentRenderTask) {
        currentRenderTask.cancel();
        currentRenderTask = null;
    }

    const pdf = await pdfjsLib.getDocument({ url: pdfURL, cMapUrl: CMAP_URL, cMapPacked: true }).promise;
    if (generation !== renderGeneration) return;

    const page = await pdf.getPage(pageNumber);
    if (generation !== renderGeneration) return;

    const naturalViewport = page.getViewport({ scale: 1.0 });
    const scale = canvas.clientWidth / naturalViewport.width;
    const viewport = page.getViewport({ scale });
    canvas.width = viewport.width;
    canvas.height = viewport.height;

    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const renderTask = page.render({ canvasContext: ctx, viewport, canvas });
    currentRenderTask = renderTask;
    try {
        await renderTask.promise;
    } catch (e: any) {
        if (e?.name !== "RenderingCancelledException") throw e;
    } finally {
        if (generation === renderGeneration) currentRenderTask = null;
    }
}

function setupToolTip(renderer: Sigma, graph: Graph): void {
    const canvas = document.getElementById("tooltip-img") as HTMLCanvasElement;
    const tooltip = document.getElementById("node-tooltip")!;
    const tooltipSource = document.getElementById("tooltip-source")!;
const tooltipPage = document.getElementById("tooltip-page")!;
    const tooltipLabel = document.getElementById("tooltip-label")!;

    renderer.on("enterNode", ({ node }) => {
        const attrs = graph.getNodeAttributes(node);

        tooltipLabel.textContent = attrs.label;

        // Populate the tooltip
        if (attrs.source_path === "CENTROID") {
            tooltipSource.textContent = "Cluster";
            tooltipPage.textContent = "";
            canvas.style.display = "none";
        } else {
            tooltipSource.textContent = attrs.source_path.split("/").at(-1)!;
            tooltipPage.textContent = `Page ${attrs.page_number}`;
            canvas.style.display = "block";

            tooltip.classList.remove("hidden");
            const pdfUrl = `/@fs${__NOTEMAP_ROOT__}/${attrs.source_path}`;
            renderPDFPage(pdfUrl, attrs.page_number, canvas);  // your job to write this
            return;
        }
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







