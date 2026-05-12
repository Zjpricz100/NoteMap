import Graph from "graphology";
import Sigma from "sigma";

const graph = new Graph();

// a method to add nodes 
graph.addNode('A', {
    label: 'A', 
    color: 'blue',
    size: 10,
    x: 0,
    y: 1
})
graph.addNode('B', {
    label: 'B', 
    color: 'Red',
    size: 10,
    x: 1,
    y: 1
})

graph.addEdge("A", "B", {size: 1, color: 'white'})




const renderer = new Sigma(graph, document.getElementById("container") as HTMLElement);
