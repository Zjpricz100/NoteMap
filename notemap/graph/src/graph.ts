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

const graphData = await getGraphData();
const graph = new Graph();
const renderer = new Sigma(graph, document.getElementById("container") as HTMLElement, {
    labelRenderedSizeThreshold: 100
});

graph.import(graphData);
//noverlap.assign(graph, {maxIterations: 50, settings: {margin:5}});

renderer.refresh();
centerCamera(renderer);







