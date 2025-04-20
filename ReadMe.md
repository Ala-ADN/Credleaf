# Credleaf

Credleaf is a web-based platform for data visualization and fact-checking, focused on analyzing and displaying healthcare and vaccine-related information through interactive network graphs, time series visualizations, and fact checking capabilities.

## Project Overview

Credleaf consists of four main components:

1. **Landing Page**: Entry point where users can enter URLs for analysis
2. **Time Series Visualization**: Displays temporal data related to vaccine publications with interactive charts
3. **Network Graph Visualization**: Shows relationships between concepts using interactive node-based networks
4. **Fact-Checking API**: Aggregates trust scores from multiple fact-checking services and advanced analysis parameters

## Technologies Used

### Front-end

- **[vis.js](https://visjs.github.io/vis-network/)**: Network visualization library for creating interactive graph networks
- **[Chart.js](https://www.chartjs.org/)**: Library for creating interactive charts and graphs in the time series visualization
- **[Tom Select](https://tom-select.js.org/)**: Enhanced select element for better user experience in node selection

### Back-end

- **[Python](https://www.python.org/)**: Core programming language for the back-end
- **[Flask](https://flask.palletsprojects.com/)**: Web framework for the fact-checking API
- **[NetworkX](https://networkx.org/)**: Python library for creation and manipulation of graph networks
- **[Ollama Embeddings](https://ollama.com/)**: Advanced embedding technology for semantic search and data representation
- **[Requests](https://docs.python-requests.org/)**: HTTP library for making calls to external fact-checking APIs

## Project Structure

```
ReadMe.md
Back-end/
    api.py                  # Flask API for fact-checking
    Graph/
        generate_graph.py   # Python script for graph generation
Front-end/
    Graph network/
        graph-data.js          # Data management for graph visualization
        graph-filter.js        # Filtering functionality for graph nodes
        graph-highlight.js     # Highlighting functionality for graph nodes
        graph-init.js          # Graph initialization logic
        graph.html             # Vaccine sentiment network visualization
        index_graph.html       # Alternative graph network entry point
        index.html             # Main network graph page
        large network.html     # Extended network visualization
        styles.css             # Styling for graph visualizations
    Landing page/
        index.html             # Main landing page
        logo.svg               # Credleaf logo
        redirect-page.html     # Post-submission redirect
    Time series/
        time-series.html       # Time series visualization of vaccine publication data
```

## Features

- **Fact-Checking API** with:

  - Integration with multiple fact-checking services (Google Fact Check, PolitiFact, OpenAI)
  - Aggregated trust scores based on multiple factors
  - Temporal pattern analysis
  - Semantic alignment evaluation
  - Graph structure analysis
  - Customizable parameter weights

- **Interactive network graph visualization** with:

  - Node highlighting
  - Neighborhood exploration
  - Filtering capabilities
  - Search functionality
  - Detailed tooltips
  - Physics-based layout with stabilization

- **Time series visualization** with:

  - Interactive charts
  - Hover functionality
  - Data highlighting
  - Custom legend

- **Landing page** with:
  - URL submission for analysis
  - Redirect to visualization pages

## Setup Instructions

### Installation

1. **Clone the repository**

   ```
   git clone <repository-url>
   cd Credleaf
   ```

2. **Install Python dependencies**

   ```
   pip install flask requests pandas numpy networkx matplotlib
   ```

3. **Set up Ollama Embeddings**

   - Install the Ollama CLI by following the instructions on the [Ollama website](https://ollama.com/).
   - Configure your embeddings by running:
     ```
     ollama configure --api-key <your-api-key>
     ```
   - Ensure the Ollama service is running locally or accessible via the configured API endpoint.

4. **Configure fact-checking API keys**

   - Open `Back-end/api.py`
   - Replace placeholder API keys in the `FACT_CHECK_APIS` dictionary with your actual API keys:
     ```python
     FACT_CHECK_APIS = {
         "google_factcheck": {
             "url": "https://factchecktools.googleapis.com/v1alpha1/claims:search",
             "key": "YOUR_GOOGLE_FACTCHECK_API_KEY"  # Replace with actual API key
         },
         "open_ai": {
             "url": "https://api.openai.com/v1/completions",
             "key": "YOUR_OPENAI_API_KEY"  # Replace with actual API key
         }
         # ...other APIs
     }
     ```

5. **Start the Flask API**

   ```
   cd Back-end
   python api.py
   ```

6. **Set up the web server**

   - Configure your web server to serve the Front-end directory
   - For local development, you can use Python's built-in HTTP server:
     ```
     cd Front-end
     python -m http.server 8000
     ```

7. **Access the application**
   - Open your web browser and navigate to:
     ```
     http://localhost:8000/Landing%20page/index.html
     ```

### Running Graph Generation

To generate new graph data from your datasets:

1. Navigate to the Back-end/Graph directory

   ```
   cd Back-end/Graph
   ```

2. Run the graph generation script with your input directory:
   ```
   python generate_graph.py --input <path-to-data> --output <output-path>
   ```

## Using the Fact-Checking API

### Endpoints

- **POST /factcheck**: Submit a claim for fact-checking
- **GET /health**: Check the API status and available fact-checking services

### Example Request

```json
POST /factcheck
Content-Type: application/json

{
  "claim": "The claim text to be fact-checked",
  "temporal_weight": 1.0,
  "semantic_weight": 1.0,
  "graph_weight": 1.0,
  "reference_data": {
    "reference_text": "Text to compare semantic alignment with"
  },
  "graph_data": {
    "nodes": [
      {"id": "claim_id", "attributes": {"label": "Claim Node"}},
      {"id": "node2", "attributes": {"label": "Related Node"}}
    ],
    "edges": [
      {"source": "claim_id", "target": "node2", "weight": 0.8}
    ]
  },
  "claim_id": "unique_id",
  "claim_date": "2023-04-15"
}
```

### Example Response

```json
{
  "claim": "The claim text to be fact-checked",
  "aggregate_trust_score": 6.75,
  "component_scores": {
    "api_average": 7.0,
    "temporal_analysis": 7.0,
    "semantic_alignment": 6.5,
    "graph_structure": 6.5
  },
  "api_details": [
    { "source": "google_factcheck", "score": 8.0 },
    { "source": "politifact", "score": 7.0 },
    { "source": "open_ai", "score": 6.0 }
  ],
  "explanation": {
    "score_range": "0-10 where 10 indicates highest trustworthiness",
    "weights": {
      "api": 1.0,
      "temporal": 1.0,
      "semantic": 1.0,
      "graph": 1.0
    }
  }
}
```

## Development Notes

When developing new features:

1. Graph data is defined in `graph-data.js` and includes nodes, edges, and their properties
2. Time series data is embedded directly in `time-series.html`
3. Event handling for node selection and highlighting is managed in `graph-highlight.js`
4. Filtering functionality is in `graph-filter.js`
5. Graph initialization and configuration is in `graph-init.js`
6. Fact-checking API logic is contained in `api.py`
