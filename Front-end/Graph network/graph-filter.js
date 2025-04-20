// Filter highlight functionality
function filterHighlight(params) {
  allNodes = nodes.get({ returnType: "Object" });
  // if something is selected:
  if (params.nodes.length > 0) {
    filterActive = true;
    let selectedNodes = params.nodes;

    // hiding all nodes and saving the label
    for (let nodeId in allNodes) {
      allNodes[nodeId].hidden = true;
      if (allNodes[nodeId].savedLabel === undefined) {
        allNodes[nodeId].savedLabel = allNodes[nodeId].label;
        allNodes[nodeId].label = undefined;
      }
    }

    for (let i = 0; i < selectedNodes.length; i++) {
      allNodes[selectedNodes[i]].hidden = false;
      if (allNodes[selectedNodes[i]].savedLabel !== undefined) {
        allNodes[selectedNodes[i]].label =
          allNodes[selectedNodes[i]].savedLabel;
        allNodes[selectedNodes[i]].savedLabel = undefined;
      }
    }
  } else if (filterActive === true) {
    // reset all nodes
    for (let nodeId in allNodes) {
      allNodes[nodeId].hidden = false;
      if (allNodes[nodeId].savedLabel !== undefined) {
        allNodes[nodeId].label = allNodes[nodeId].savedLabel;
        allNodes[nodeId].savedLabel = undefined;
      }
    }
    filterActive = false;
  }

  // transform the object into an array
  var updateArray = [];
  if (params.nodes.length > 0) {
    for (let nodeId in allNodes) {
      if (allNodes.hasOwnProperty(nodeId)) {
        updateArray.push(allNodes[nodeId]);
      }
    }
    nodes.update(updateArray);
  } else {
    for (let nodeId in allNodes) {
      if (allNodes.hasOwnProperty(nodeId)) {
        updateArray.push(allNodes[nodeId]);
      }
    }
    nodes.update(updateArray);
  }
}

function selectNodes(nodes) {
  network.selectNodes(nodes);
  filterHighlight({ nodes: nodes });
  return nodes;
}

function highlightFilter(filter) {
  let selectedNodes = [];
  let selectedProp = filter["property"];
  if (filter["item"] === "node") {
    let allNodes = nodes.get({ returnType: "Object" });
    for (let nodeId in allNodes) {
      if (
        allNodes[nodeId][selectedProp] &&
        filter["value"].includes(allNodes[nodeId][selectedProp].toString())
      ) {
        selectedNodes.push(nodeId);
      }
    }
  } else if (filter["item"] === "edge") {
    let allEdges = edges.get({ returnType: "object" });
    // check if the selected property exists for selected edge and select the nodes connected to the edge
    for (let edge in allEdges) {
      if (
        allEdges[edge][selectedProp] &&
        filter["value"].includes(allEdges[edge][selectedProp].toString())
      ) {
        selectedNodes.push(allEdges[edge]["from"]);
        selectedNodes.push(allEdges[edge]["to"]);
      }
    }
  }
  selectNodes(selectedNodes);
}
