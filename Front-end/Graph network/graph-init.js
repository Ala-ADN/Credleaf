// Graph initialization and configuration

// This method is responsible for drawing the graph, returns the drawn network
function drawGraph() {
  container = document.getElementById("mynetwork");

  // Load the nodes data
  loadGraphData();

  // Define graph options
  options = {
    configure: {
      enabled: false,
    },
    edges: {
      color: {
        inherit: true,
      },
      smooth: {
        enabled: true,
        type: "dynamic",
      },
    },
    interaction: {
      dragNodes: true,
      hideEdgesOnDrag: false,
      hideNodesOnDrag: false,
    },
    physics: {
      barnesHut: {
        avoidOverlap: 0,
        centralGravity: 5.05,
        damping: 0.09,
        gravitationalConstant: -18100,
        springConstant: 0.001,
        springLength: 380,
      },
      enabled: true,
      forceAtlas2Based: {
        avoidOverlap: 0,
        centralGravity: 0.015,
        damping: 0.4,
        gravitationalConstant: -31,
        springConstant: 0.08,
        springLength: 100,
      },
      repulsion: {
        centralGravity: 0.2,
        damping: 0.09,
        nodeDistance: 150,
        springConstant: 0.05,
        springLength: 400,
      },
      solver: "forceAtlas2Based",
      stabilization: {
        enabled: true,
        fit: true,
        iterations: 1000,
        onlyDynamicEdges: false,
        updateInterval: 50,
      },
    },
  };

  // Create the network
  data = { nodes: nodes };
  network = new vis.Network(container, data, options);

  // Set up event listeners
  network.on("selectNode", neighbourhoodHighlight);

  // Progress bar setup
  setupProgressBar();

  return network;
}

// Set up the loading/progress bar
function setupProgressBar() {
  network.on("stabilizationProgress", function (params) {
    const widthFactor = params.iterations / params.total;
    document.getElementById("text").innerHTML =
      Math.round(widthFactor * 100) + "%";
  });

  network.once("stabilizationIterationsDone", function () {
    setTimeout(function () {
      document.getElementById("loadingBar").style.display = "none";
    }, 500);
  });
}

// Initialize the graph when the page is loaded
document.addEventListener("DOMContentLoaded", function () {
  drawGraph();
});
