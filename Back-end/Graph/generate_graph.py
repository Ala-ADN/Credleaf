import os
import numpy as np
import pandas as pd
import random
import networkx as nx
import seaborn as sns
import json
from pyvis.network import Network
from sklearn.metrics.pairwise import cosine_similarity
from langchain_community.document_loaders.pdf import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
import matplotlib.colors as mcolors

# Convert documents to a DataFrame format
def documents2Dataframe(docs):
    df = pd.DataFrame(columns=["page_content", "source", "page"])
    for doc in docs:
        source = doc.metadata.get("source", "")
        page = doc.metadata.get("page", 0)
        df = pd.concat([df, pd.DataFrame([{
            "page_content": doc.page_content,
            "source": source,
            "page": page
        }])], ignore_index=True)
    return df

# Generate graph from DataFrame using embeddings and similarity
def df2Graph(df, model, similarity_threshold=0.8):
    # Get embeddings for all text chunks
    embeddings = []
    for _, row in df.iterrows():
        try:
            embedding = model.embed_query(row["page_content"])
            embeddings.append(embedding)
        except Exception as e:
            print(f"Error embedding text: {e}")
            embeddings.append(None)
    
    # Calculate similarity matrix
    valid_indices = [i for i, e in enumerate(embeddings) if e is not None]
    valid_embeddings = [embeddings[i] for i in valid_indices]
    
    if not valid_embeddings:
        return []
    
    similarity_matrix = cosine_similarity(valid_embeddings)
    
    # Build concept graph from similarity
    concepts_list = []
    for i in range(len(valid_indices)):
        source_idx = valid_indices[i]
        source_text = df.iloc[source_idx]["page_content"]
        source_doc = df.iloc[source_idx]["source"]
        
        for j in range(i + 1, len(valid_indices)):
            target_idx = valid_indices[j]
            similarity = similarity_matrix[i][j]
            
            if similarity >= similarity_threshold:
                target_text = df.iloc[target_idx]["page_content"]
                target_doc = df.iloc[target_idx]["source"]
                
                # Create a shorter representation for nodes
                source_short = " ".join(source_text.split()[:5]) + "..."
                target_short = " ".join(target_text.split()[:5]) + "..."
                
                concepts_list.append({
                    "source": source_short,
                    "target": target_short,
                    "source_doc": source_doc,
                    "target_doc": target_doc,
                    "similarity": similarity,
                    "relationship": f"Similarity: {similarity:.2f}"
                })
    
    return concepts_list

# Convert graph data to DataFrame format
def graph2Df(concepts_list):
    if not concepts_list:
        return pd.DataFrame(columns=["node_1", "node_2", "edge", "weight"])
    
    df = pd.DataFrame(columns=["node_1", "node_2", "edge", "weight"])
    for concept in concepts_list:
        df = pd.concat([df, pd.DataFrame([{
            "node_1": concept["source"],
            "node_2": concept["target"],
            "edge": concept["relationship"],
            "weight": concept["similarity"]
        }])], ignore_index=True)
    return df

# Assign colors to community clusters
def colors2Community(communities):
    # Get a list of distinct colors
    color_list = list(mcolors.TABLEAU_COLORS.values())
    
    # Extend color list if needed
    while len(color_list) < len(communities):
        color_list.extend(mcolors.TABLEAU_COLORS.values())
    
    df = pd.DataFrame(columns=["node", "group", "color"])
    
    for i, community in enumerate(communities):
        color = color_list[i % len(color_list)]
        for node in community:
            df = pd.concat([df, pd.DataFrame([{
                "node": node,
                "group": i, 
                "color": color
            }])], ignore_index=True)
    
    return df

def generate_save_html_graph(input_directory, output_path):
    outputdirectory = os.path.join("knowledge_graph", "data_output")
    loader = PyPDFDirectoryLoader(input_directory)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150,
        length_function=len,
        is_separator_regex=False,
    )
    pages = splitter.split_documents(documents)
    df = documents2Dataframe(pages)

    model = OllamaEmbeddings(model="nomic-embed-text")
    regenerate = True

    if regenerate:
        print("Computing embeddings and building graph...")
        concepts_list = df2Graph(df, model=model, similarity_threshold=0.8)
        print("Graph construction complete.")

        dfg1 = graph2Df(concepts_list)
        os.makedirs(outputdirectory, exist_ok=True)
        dfg1.to_csv(os.path.join(outputdirectory, "graph.csv"), sep="|", index=False)
        df.to_csv(os.path.join(outputdirectory, "chunks.csv"), sep="|", index=False)
    else:
        dfg1 = pd.read_csv(os.path.join(outputdirectory, "graph.csv"), sep="|")

    dfg1.replace("", np.nan, inplace=True)
    dfg1.dropna(subset=["node_1", "node_2", "edge"], inplace=True)
    dfg1['count'] = 4

    G = nx.Graph()
    nodes = pd.concat([dfg1['node_1'], dfg1['node_2']], axis=0).unique()
    for node in nodes:
        G.add_node(str(node))

    for _, row in dfg1.iterrows():
        G.add_edge(str(row["node_1"]), str(row["node_2"]), title=row["edge"], weight=row['count'] / 4)

    communities_generator = nx.community.girvan_newman(G)
    try:
        next_level_communities = next(communities_generator)
        next_level_communities = next(communities_generator)
    except StopIteration:
        next_level_communities = [list(G.nodes)]

    communities = sorted(map(sorted, next_level_communities))
    colors = colors2Community(communities)
    
    # Add node attributes
    for _, row in colors.iterrows():
        G.nodes[row['node']]['group'] = row['group']
        G.nodes[row['node']]['color'] = row['color']
        G.nodes[row['node']]['size'] = G.degree[row['node']] * 2 + 5  # Scale node size based on degree
        G.nodes[row['node']]['font'] = {"color": "#36454F"}
        G.nodes[row['node']]['label'] = row['node']
        G.nodes[row['node']]['shape'] = "dot"

    # Create the network visualization
    net = Network(
        notebook=False,
        cdn_resources="remote",
        height="900px",
        width="100%",
        select_menu=True,
        font_color="#36454F",
        filter_menu=False,
    )
    
    # Add the graph to the network
    net.from_nx(G)
    
    # Generate node selection options for dropdown
    select_options = ""
    for node_id in G.nodes():
        select_options += f'<option value="{node_id}">{node_id}</option>\n'
    
    # Save node colors for the highlight functionality
    node_colors = {}
    for node_id in G.nodes():
        node_colors[node_id] = G.nodes[node_id].get('color', "#97c2fc")
    
    # Set the physics options
    net.set_options("""
    {
        "configure": {
            "enabled": false
        },
        "edges": {
            "color": {
                "inherit": true
            },
            "smooth": {
                "enabled": true,
                "type": "dynamic"
            }
        },
        "interaction": {
            "dragNodes": true,
            "hideEdgesOnDrag": false,
            "hideNodesOnDrag": false
        },
        "physics": {
            "barnesHut": {
                "avoidOverlap": 0,
                "centralGravity": 5.05,
                "damping": 0.09,
                "gravitationalConstant": -18100,
                "springConstant": 0.001,
                "springLength": 380
            },
            "enabled": true,
            "forceAtlas2Based": {
                "avoidOverlap": 0,
                "centralGravity": 0.015,
                "damping": 0.4,
                "gravitationalConstant": -31,
                "springConstant": 0.08,
                "springLength": 100
            },
            "repulsion": {
                "centralGravity": 0.2,
                "damping": 0.09,
                "nodeDistance": 150,
                "springConstant": 0.05,
                "springLength": 400
            },
            "solver": "forceAtlas2Based",
            "stabilization": {
                "enabled": true,
                "fit": true,
                "iterations": 1000,
                "onlyDynamicEdges": false,
                "updateInterval": 50
            }
        }
    }
    """)

    # Add color data to be used by the highlighting function
    net.html = """
    <html>
        <head>
            <meta charset="utf-8">
            {head}
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/css/bootstrap.min.css" integrity="sha384-eOJMYsd53ii+scO/bJGFsiCZc+5NDVN2yr8+0RDqr0Ql0h+rP48ckxlpbzKgwra6" crossorigin="anonymous">
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/js/bootstrap.bundle.min.js" integrity="sha384-JEW9xMcG8R+pH31jmWH6WWP0WintQrMb4s7ZOdauHnUtxwoG2vI5DkLtS3qm9Ekf" crossorigin="anonymous"></script>
        </head>
        <body>
            <div class="card" style="width: 100%">
                <div id="select-menu" class="card-header">
                    <div class="row no-gutters">
                        <div class="col-10 pb-2">
                            <select class="form-select" aria-label="Default select example" onchange="selectNode([value]);" id="select-node" placeholder="Select node...">
                                <option selected>Select a Node by ID</option>
                                {select_options}
                            </select>
                        </div>
                        <div class="col-2 pb-2">
                            <button type="button" class="btn btn-primary btn-block" onclick="neighbourhoodHighlight({{nodes: []}});">Reset Selection</button>
                        </div>
                    </div>
                </div>
                <div id="mynetwork" class="card-body"></div>
            </div>
            <div id="loadingBar">
              <div class="outerBorder">
                <div id="text">0%</div>
                <div id="border">
                  <div id="bar"></div>
                </div>
              </div>
            </div>
            <script type="text/javascript">
                // Store original colors
                var nodeColors = {JSON_COLORS};
                
                function neighbourhoodHighlight(params) {
                    allNodes = nodes.get({ returnType: "Object" });
                    if (params.nodes.length > 0) {
                        highlightActive = true;
                        var selectedNode = params.nodes[0];
                        var degrees = 2;

                        for (let nodeId in allNodes) {
                            allNodes[nodeId].color = "rgba(200,200,200,0.5)";
                            if (allNodes[nodeId].hiddenLabel === undefined) {
                                allNodes[nodeId].hiddenLabel = allNodes[nodeId].label;
                                allNodes[nodeId].label = undefined;
                            }
                        }
                        var connectedNodes = network.getConnectedNodes(selectedNode);
                        var allConnectedNodes = [];

                        for (i = 1; i < degrees; i++) {
                            for (j = 0; j < connectedNodes.length; j++) {
                                allConnectedNodes = allConnectedNodes.concat(network.getConnectedNodes(connectedNodes[j]));
                            }
                        }

                        for (i = 0; i < allConnectedNodes.length; i++) {
                            allNodes[allConnectedNodes[i]].color = "rgba(150,150,150,0.75)";
                            if (allNodes[allConnectedNodes[i]].hiddenLabel !== undefined) {
                                allNodes[allConnectedNodes[i]].label = allNodes[allConnectedNodes[i]].hiddenLabel;
                                allNodes[allConnectedNodes[i]].hiddenLabel = undefined;
                            }
                        }

                        for (i = 0; i < connectedNodes.length; i++) {
                            allNodes[connectedNodes[i]].color = nodeColors[connectedNodes[i]];
                            if (allNodes[connectedNodes[i]].hiddenLabel !== undefined) {
                                allNodes[connectedNodes[i]].label = allNodes[connectedNodes[i]].hiddenLabel;
                                allNodes[connectedNodes[i]].hiddenLabel = undefined;
                            }
                        }

                        allNodes[selectedNode].color = nodeColors[selectedNode];
                        if (allNodes[selectedNode].hiddenLabel !== undefined) {
                            allNodes[selectedNode].label = allNodes[selectedNode].hiddenLabel;
                            allNodes[selectedNode].hiddenLabel = undefined;
                        }
                    } else if (highlightActive === true) {
                        for (let nodeId in allNodes) {
                            allNodes[nodeId].color = nodeColors[nodeId];
                            if (allNodes[nodeId].hiddenLabel !== undefined) {
                                allNodes[nodeId].label = allNodes[nodeId].hiddenLabel;
                                allNodes[nodeId].hiddenLabel = undefined;
                            }
                        }
                        highlightActive = false;
                    }

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
                
                function selectNode(nodes) {
                    network.selectNodes(nodes);
                    neighbourhoodHighlight({ nodes: nodes });
                    return nodes;
                }
                
                // Add progress bar functionality
                network.on("stabilizationProgress", function(params) {
                    document.getElementById('loadingBar').removeAttribute("style");
                    var maxWidth = 496;
                    var minWidth = 20;
                    var widthFactor = params.iterations/params.total;
                    var width = Math.max(minWidth,maxWidth * widthFactor);
                    document.getElementById('bar').style.width = width + 'px';
                    document.getElementById('text').innerHTML = Math.round(widthFactor*100) + '%';
                });
                network.once("stabilizationIterationsDone", function() {
                    document.getElementById('text').innerHTML = '100%';
                    document.getElementById('bar').style.width = '496px';
                    document.getElementById('loadingBar').style.opacity = 0;
                    setTimeout(function () {document.getElementById('loadingBar').style.display = 'none';}, 500);
                });
                
                // Initialize TomSelect for better node selection
                new TomSelect("#select-node", {
                    create: false,
                    sortField: {
                        field: "text",
                        direction: "asc"
                    }
                });
            </script>
            <style>
                #mynetwork {
                    width: 100%;
                    height: 900px;
                    background-color: #ffffff;
                    border: 1px solid lightgray;
                    position: relative;
                    float: left;
                }
                
                #loadingBar {
                    position:absolute;
                    top:0px;
                    left:0px;
                    width: 100%;
                    height: 900px;
                    background-color:rgba(200,200,200,0.8);
                    -webkit-transition: all 0.5s ease;
                    -moz-transition: all 0.5s ease;
                    -ms-transition: all 0.5s ease;
                    -o-transition: all 0.5s ease;
                    transition: all 0.5s ease;
                    opacity:1;
                }
                
                #bar {
                    position:absolute;
                    top:0px;
                    left:0px;
                    width:20px;
                    height:20px;
                    margin:auto auto auto auto;
                    border-radius:11px;
                    border:2px solid rgba(30,30,30,0.05);
                    background: rgb(0, 173, 246);
                    box-shadow: 2px 0px 4px rgba(0,0,0,0.4);
                }
                
                #border {
                    position:absolute;
                    top:10px;
                    left:10px;
                    width:500px;
                    height:23px;
                    margin:auto auto auto auto;
                    box-shadow: 0px 0px 4px rgba(0,0,0,0.2);
                    border-radius:10px;
                }
                
                #text {
                    position:absolute;
                    top:8px;
                    left:530px;
                    width:30px;
                    height:50px;
                    margin:auto auto auto auto;
                    font-size:22px;
                    color: #000000;
                }
                
                div.outerBorder {
                    position:relative;
                    top:400px;
                    width:600px;
                    height:44px;
                    margin:auto auto auto auto;
                    border:8px solid rgba(0,0,0,0.1);
                    background: rgb(252,252,252);
                    background: -moz-linear-gradient(top,  rgba(252,252,252,1) 0%, rgba(237,237,237,1) 100%);
                    background: -webkit-gradient(linear, left top, left bottom, color-stop(0%,rgba(252,252,252,1)), color-stop(100%,rgba(237,237,237,1)));
                    background: -webkit-linear-gradient(top,  rgba(252,252,252,1) 0%,rgba(237,237,237,1) 100%);
                    background: -o-linear-gradient(top,  rgba(252,252,252,1) 0%,rgba(237,237,237,1) 100%);
                    background: -ms-linear-gradient(top,  rgba(252,252,252,1) 0%,rgba(237,237,237,1) 100%);
                    background: linear-gradient(to bottom,  rgba(252,252,252,1) 0%,rgba(237,237,237,1) 100%);
                    filter: progid:DXImageTransform.Microsoft.gradient( startColorstr='#fcfcfc', endColorstr='#ededed',GradientType=0 );
                    border-radius:72px;
                    box-shadow: 0px 0px 10px rgba(0,0,0,0.2);
                }
            </style>
        </body>
    </html>
    """
    
    # Replace the placeholder with the actual node colors
    net.html = net.html.replace('{JSON_COLORS}', json.dumps(node_colors))
    net.html = net.html.replace('{select_options}', select_options)
    
    # Generate the file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    net.save_graph(output_path)
    print(f"Graph saved to {output_path}")
    
    return output_path

# Add a main function to make it runnable as a script
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python generate_graph.py <pdf_directory> <output_html_path>")
        sys.exit(1)
    
    pdf_directory = sys.argv[1]
    output_html_path = sys.argv[2]
    
    if not os.path.exists(pdf_directory):
        print(f"Error: PDF directory {pdf_directory} does not exist")
        sys.exit(1)
    
    generate_save_html_graph(pdf_directory, output_html_path)