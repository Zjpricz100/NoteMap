import Graph from "graphology";
import Sigma from "sigma";

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

const graphData = await getGraphData();
const graph = new Graph();
graph.import(graphData);
const renderer = new Sigma(graph, document.getElementById("container") as HTMLElement);







