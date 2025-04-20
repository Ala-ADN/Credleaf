// Global variables for the graph
var edges;
var nodes;
var allNodes;
var allEdges;
var nodeColors;
var originalNodes;
var network;
var container;
var options, data;
var highlightActive = false;
var filterActive = false;
var filter = {
  item: "",
  property: "",
  value: [],
};

// Calculate node size based on connections
function calculateNodeSize(connections) {
  // Base size is 5, increases with number of connections
  return 5 + connections * 1.5;
}

// Node data for the graph
function loadGraphData() {
  // Define the vaccine-related statements
  const provaxStatements = [
    {
      id: "provax1",
      label: "Vaccines save lives",
      content:
        "Vaccines have been scientifically proven to save millions of lives worldwide",
    },
    {
      id: "provax2",
      label: "Herd immunity protects everyone",
      content:
        "High vaccination rates create herd immunity that protects vulnerable populations",
    },
    {
      id: "provax3",
      label: "Vaccines undergo rigorous testing",
      content:
        "All vaccines undergo extensive clinical trials to ensure safety and efficacy",
    },
    {
      id: "provax4",
      label: "Side effects are rare",
      content:
        "Serious vaccine side effects are extremely rare compared to disease complications",
    },
    {
      id: "provax5",
      label: "Scientific consensus supports vaccines",
      content:
        "The global scientific community strongly supports vaccination programs",
    },
    {
      id: "provax6",
      label: "Vaccines eliminated smallpox",
      content: "Vaccination successfully eliminated smallpox from the world",
    },
  ];

  const antivaxStatements = [
    {
      id: "antivax1",
      label: "Vaccines contain toxins",
      content:
        "Vaccines contain dangerous chemicals and toxins that harm the body",
    },
    {
      id: "antivax2",
      label: "Natural immunity is better",
      content:
        "Natural immunity from getting sick is superior to vaccine-induced immunity",
    },
    {
      id: "antivax3",
      label: "Vaccines cause autism",
      content:
        "There's a link between childhood vaccines and autism development",
    },
    {
      id: "antivax4",
      label: "Big pharma conspiracy",
      content: "Pharmaceutical companies hide vaccine dangers for profit",
    },
    {
      id: "antivax5",
      label: "Government control",
      content:
        "Mandatory vaccines are government overreach and violation of freedom",
    },
    {
      id: "antivax6",
      label: "Alternative health remedies",
      content:
        "Natural remedies and healthy lifestyle are better than vaccines",
    },
    {
      id: "antivax7",
      label: "Vaccine injuries unreported",
      content:
        "Most vaccine injuries go unreported and compensation is difficult",
    },
  ];

  const hesitancyStatements = [
    {
      id: "hesitancy1",
      label: "Need more research",
      content: "We need more long-term studies on vaccine effects",
    },
    {
      id: "hesitancy2",
      label: "Individual risk assessment",
      content: "People should assess their personal risk before vaccination",
    },
    {
      id: "hesitancy3",
      label: "Transparency concerns",
      content:
        "More transparency needed about vaccine development and ingredients",
    },
    {
      id: "hesitancy4",
      label: "Medical exemptions",
      content:
        "Some people have legitimate medical reasons to avoid certain vaccines",
    },
    {
      id: "hesitancy5",
      label: "Timing concerns",
      content: "Concerned about timing and number of vaccines given at once",
    },
  ];

  // Create node objects with appropriate colors and groups
  const nodeData = [];

  // ProVax nodes - coherent cluster with consistent green color (group 1)
  provaxStatements.forEach((statement) => {
    nodeData.push({
      id: statement.id,
      label: statement.label,
      content: statement.content,
      group: 1, // ProVax group
      shape: "dot",
      size: 5, // Will be updated based on connections later
      color: "#34A853", // Green color
      font: { color: "#36454F" },
    });
  });

  // AntiVax nodes - erratic cluster with varying red shades (group 2)
  antivaxStatements.forEach((statement, index) => {
    nodeData.push({
      id: statement.id,
      label: statement.label,
      content: statement.content,
      group: 2, // AntiVax group
      shape: "dot",
      size: 5, // Will be updated based on connections later
      // Varying shades of red to show erratic nature
      color: `rgb(${200 + Math.floor(Math.random() * 55)}, ${
        20 + Math.floor(Math.random() * 40)
      }, ${20 + Math.floor(Math.random() * 30)})`,
      font: { color: "#36454F" },
    });
  });

  // Hesitancy nodes - middle ground with amber/yellow colors (group 3)
  hesitancyStatements.forEach((statement) => {
    nodeData.push({
      id: statement.id,
      label: statement.label,
      content: statement.content,
      group: 3, // Hesitancy group
      shape: "dot",
      size: 5, // Will be updated based on connections later
      color: "#FBBC05", // Amber/yellow color
      font: { color: "#36454F" },
    });
  });

  // Create the nodes dataset
  nodes = new vis.DataSet(nodeData);

  // Hard-coded edge connections with cosine similarity values
  // These values are designed to demonstrate:
  // 1. ProVax - coherent cluster (high similarity within group)
  // 2. AntiVax - erratic connections with varied similarity
  // 3. Hesitancy - bridge between groups

  // Track connections count for each node to adjust size later
  const nodeConnections = {};
  [...provaxStatements, ...antivaxStatements, ...hesitancyStatements].forEach(
    (statement) => {
      nodeConnections[statement.id] = 0;
    }
  );

  // Hard-coded edge list with cosine similarity values
  const edgeList = [
    // ProVax cluster
    { from: "provax1", to: "provax2", similarity: 0.8 },
    { from: "provax1", to: "provax3", similarity: 0.7 },
    { from: "provax1", to: "provax4", similarity: 0.8 },
    { from: "provax1", to: "provax5", similarity: 0.9 },
    { from: "provax1", to: "provax6", similarity: 0.8 },

    // AntiVax tree structure (3 levels)
    // Level 1 (root) to Level 2 connections
    { from: "antivax1", to: "antivax2", similarity: 0.51 },
    { from: "antivax1", to: "antivax3", similarity: 0.5 },
    { from: "antivax1", to: "antivax4", similarity: 0.3 },

    // Level 2 to Level 3 connections
    { from: "antivax2", to: "antivax5", similarity: 0.23 },
    { from: "antivax2", to: "antivax6", similarity: 0.35 },
    { from: "antivax3", to: "antivax7", similarity: 0.3 }, // Hesitancy statements connecting to both ProVax and AntiVax (0.3-0.65)
    // Connections to ProVax
    { from: "hesitancy1", to: "provax3", similarity: 0.42 },
    { from: "hesitancy3", to: "provax3", similarity: 0.56 },
    { from: "hesitancy4", to: "provax4", similarity: 0.62 },
    { from: "hesitancy5", to: "provax3", similarity: 0.45 },

    // Connections to AntiVax
    { from: "hesitancy1", to: "antivax7", similarity: 0.52 },
    { from: "hesitancy2", to: "antivax2", similarity: 0.48 },

    // Reduced connections within hesitancy group (minimum needed to keep all connected)
    { from: "hesitancy1", to: "hesitancy3", similarity: 0.67 },
    { from: "hesitancy2", to: "hesitancy4", similarity: 0.72 },
    { from: "hesitancy3", to: "hesitancy5", similarity: 0.64 },
    { from: "hesitancy2", to: "hesitancy3", similarity: 0.51 },
  ];

  // Create edges and update node connections
  const edgeData = [];
  edgeList.forEach((edge) => {
    edgeData.push({
      from: edge.from,
      to: edge.to,
      width: edge.similarity * 3, // Scale width by similarity
      title: `Similarity: ${edge.similarity.toFixed(2)}`, // Show similarity in tooltip
      value: edge.similarity,
    });

    // Update connection counts for node sizing
    nodeConnections[edge.from] = (nodeConnections[edge.from] || 0) + 1;
    nodeConnections[edge.to] = (nodeConnections[edge.to] || 0) + 1;
  });

  // Update node sizes based on number of connections
  const updatedNodeData = nodes.get();
  updatedNodeData.forEach((node) => {
    node.size = calculateNodeSize(nodeConnections[node.id] || 0);
  });
  nodes.update(updatedNodeData);

  // Create the edges dataset
  edges = new vis.DataSet(edgeData);

  // Store original node colors
  storeNodeColors();

  // Populate the dropdown with node options
  populateNodeDropdown();

  return { nodes: nodes, edges: edges };
}

// Store the original colors of nodes for later restoration
function storeNodeColors() {
  nodeColors = {};
  allNodes = nodes.get({ returnType: "Object" });
  for (let nodeId in allNodes) {
    nodeColors[nodeId] = allNodes[nodeId].color;
  }
}

// Populate the node dropdown with options
function populateNodeDropdown() {
  const selectElement = document.getElementById("select-node");
  if (!selectElement) return;

  // Clear existing options except the first default one
  while (selectElement.options.length > 1) {
    selectElement.remove(1);
  }

  // Add all nodes to dropdown
  allNodes = nodes.get({ returnType: "Object" });
  for (let nodeId in allNodes) {
    const option = document.createElement("option");
    option.value = nodeId;
    option.text = allNodes[nodeId].label;
    selectElement.add(option);
  }

  // Initialize Tom Select
  new TomSelect("#select-node", {});
}
