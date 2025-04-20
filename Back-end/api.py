from flask import Flask, request, jsonify
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime
import networkx as nx

app = Flask(__name__)

# List of fact-checking APIs with their endpoints and API keys
FACT_CHECK_APIS = {
    "google_factcheck": {
        "url": "https://factchecktools.googleapis.com/v1alpha1/claims:search",
        "key": "YOUR_GOOGLE_FACTCHECK_API_KEY"  # Replace with actual API key
    },
    "politifact": {
        "url": "https://www.politifact.com/api/factchecks/",
        "key": None  # PolitiFact doesn't require an API key for public endpoints
    },
    "open_ai": {
        "url": "https://api.openai.com/v1/completions",
        "key": "YOUR_OPENAI_API_KEY"  # Replace with actual API key
    }
}

def normalize_score(score, min_val=0, max_val=10):
    """Normalize scores to a 0-10 scale."""
    return ((score - min_val) / (max_val - min_val)) * 10

def check_temporal_patterns(claim, temporal_weight=1.0):
    """
    Analyze temporal patterns of a claim
    Returns a score between 0-10 where higher scores indicate more trustworthy temporal patterns
    """
    # Placeholder for actual temporal analysis logic
    # In a real implementation, this would analyze the time-based spread pattern of the claim
    
    # Example logic: newer claims might be less verified (lower score)
    # You could analyze publish dates, spread velocity, etc.
    current_date = datetime.now()
    claim_date = claim.get("date", current_date)
    
    if isinstance(claim_date, str):
        try:
            claim_date = datetime.strptime(claim_date, "%Y-%m-%d")
        except ValueError:
            claim_date = current_date
            
    days_since_claim = (current_date - claim_date).days
    
    # Check if we have time series data about the claim's spread/engagement
    engagement_data = claim.get("engagement_timeseries", [])
    
    if not engagement_data:
        # If no time series data, fall back to basic days-based heuristic
        if days_since_claim < 1:
            return 5.0 * temporal_weight  # New claims start neutral
        elif days_since_claim > 365:
            return 6.0 * temporal_weight  # Older verified claims slightly more trustworthy
        else:
            return 7.0 * temporal_weight  # Claims with some verification time but still recent
    
    # Analyze temporal engagement patterns
    try:
        # Convert to numpy array for analysis
        data = np.array(engagement_data)
        
        # Calculate rate of change between data points
        changes = np.diff(data)
        
        # Check for sudden peaks (high standard deviation in changes)
        std_change = np.std(changes)
        mean_change = np.mean(changes)
        
        # Sudden spikes often indicate viral misinformation (lower score)
        # Gradual or consistent growth patterns tend to be more reliable
        if std_change > 3 * mean_change and mean_change > 0:
            # High volatility with growth indicates potential viral misinformation
            temporal_score = 4.0
        elif std_change > 2 * mean_change and mean_change > 0:
            # Moderate volatility with growth
            temporal_score = 5.0
        elif mean_change > 0:
            # Steady growth pattern, more trustworthy
            temporal_score = 7.0
        else:
            # Declining interest or stable pattern
            temporal_score = 6.0
            
        return temporal_score * temporal_weight
    except:
        # If analysis fails, return neutral score
        return 5.0 * temporal_weight

def analyze_semantic_alignment(claim, reference_data, semantic_weight=1.0):
    """
    Analyze semantic alignment between the claim and reference data
    Returns a score between 0-10 where higher scores indicate better alignment
    """
    # Placeholder for actual semantic analysis logic
    # In a real implementation, this would use NLP techniques to analyze semantic similarity
    
    # Example: simple keyword matching (would be replaced with embeddings in production)
    claim_text = claim.get("text", "").lower()
    reference_text = reference_data.get("reference_text", "").lower()
    
    if not reference_text:
        return 5.0 * semantic_weight  # Neutral score if no reference
        
    # Simple word overlap calculation
    claim_words = set(claim_text.split())
    reference_words = set(reference_text.split())
    
    if not claim_words:
        return 5.0 * semantic_weight
        
    overlap = len(claim_words.intersection(reference_words))
    alignment_score = min(10.0, (overlap / len(claim_words)) * 10)
    
    return alignment_score * semantic_weight

def evaluate_graph_structure(claim, graph_data, graph_weight=1.0):
    """
    Evaluate the claim based on its position in a knowledge graph
    Returns a score between 0-10 where higher scores indicate better graph positioning
    """
    # Placeholder for actual graph analysis logic
    # In a real implementation, this would analyze the claim's position in a knowledge graph
    
    if not graph_data:
        return 5.0 * graph_weight  # Neutral score if no graph data
        
    try:
        # Create a graph from the provided data
        G = nx.Graph()
        
        # Add nodes and edges from graph_data
        for node in graph_data.get("nodes", []):
            G.add_node(node["id"], **node.get("attributes", {}))
            
        for edge in graph_data.get("edges", []):
            G.add_edge(edge["source"], edge["target"], weight=edge.get("weight", 1.0))
            
        # Find the claim node in the graph
        claim_id = claim.get("id")
        if claim_id in G:
            # Calculate centrality measures
            degree_centrality = nx.degree_centrality(G)[claim_id]
            
            try:
                betweenness_centrality = nx.betweenness_centrality(G)[claim_id]
                eigenvector_centrality = nx.eigenvector_centrality(G)[claim_id]
                
                # Higher centrality could indicate more important/verified information
                graph_score = ((degree_centrality + betweenness_centrality + eigenvector_centrality) / 3) * 10
            except:
                # Fallback if certain centrality measures fail
                graph_score = degree_centrality * 10
                
            return min(10.0, graph_score) * graph_weight
            
    except Exception as e:
        print(f"Error in graph analysis: {str(e)}")
        
    return 5.0 * graph_weight  # Neutral score on failure

def query_fact_checking_api(api_name, claim):
    """Query a fact-checking API and get the trust score."""
    api_info = FACT_CHECK_APIS.get(api_name)
    if not api_info:
        return {"error": f"API {api_name} not configured"}
        
    url = api_info["url"]
    api_key = api_info["key"]
    
    try:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        params = {"query": claim}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            # Different APIs return different structures, so we need to handle them differently
            if api_name == "google_factcheck":
                claims = result.get("claims", [])
                if claims:
                    # Get the average rating from all matching claims
                    ratings = [c.get("ratingValue", 0) for c in claims if "ratingValue" in c]
                    if ratings:
                        return {"score": sum(ratings) / len(ratings), "source": api_name, "raw_response": result}
            
            elif api_name == "politifact":
                articles = result.get("results", [])
                if articles:
                    # Map PolitiFact ratings to scores (0-10)
                    rating_map = {
                        "true": 10.0,
                        "mostly-true": 8.0,
                        "half-true": 5.0,
                        "barely-true": 3.0,
                        "false": 0.0,
                        "pants-fire": 0.0
                    }
                    
                    ratings = [rating_map.get(a.get("ruling", {}).get("slug", ""), 5.0) for a in articles]
                    if ratings:
                        return {"score": sum(ratings) / len(ratings), "source": api_name, "raw_response": result}
            
            elif api_name == "open_ai":
                # Use OpenAI to evaluate truthfulness if configured
                completion = result.get("choices", [{}])[0].get("text", "")
                
                # Parse the completion to extract a score (implementation depends on prompt)
                try:
                    # Assuming the completion returns a score between 0-10
                    score = float(completion.strip())
                    return {"score": score, "source": api_name, "raw_response": result}
                except:
                    pass
            
            # Default handling for other APIs or when specific parsing fails
            return {"score": 5.0, "source": api_name, "raw_response": result}  # Neutral score
            
        return {"error": f"API request failed with status code {response.status_code}", "source": api_name}
        
    except Exception as e:
        return {"error": str(e), "source": api_name}

@app.route('/factcheck', methods=['POST'])
def fact_check():
    """
    API endpoint to check the factuality of a claim
    
    Requires JSON input with:
    - claim: text of the claim to check
    - temporal_weight: weight for temporal analysis (optional, default 1.0)
    - semantic_weight: weight for semantic alignment (optional, default 1.0)
    - graph_weight: weight for graph structure analysis (optional, default 1.0)
    - reference_data: dictionary containing reference text (optional)
    - graph_data: dictionary containing nodes and edges for graph analysis (optional)
    """
    data = request.get_json()
    
    if not data or not data.get('claim'):
        return jsonify({"error": "Missing required 'claim' field"}), 400
    
    claim = data.get('claim')
    
    # Get optional weight parameters with default values
    temporal_weight = float(data.get('temporal_weight', 1.0))
    semantic_weight = float(data.get('semantic_weight', 1.0))
    graph_weight = float(data.get('graph_weight', 1.0))
    
    # Get optional data parameters
    reference_data = data.get('reference_data', {})
    graph_data = data.get('graph_data', {})
    
    # Prepare the claim object with metadata
    claim_obj = {
        "text": claim,
        "id": data.get('claim_id', 'unknown'),
        "date": data.get('claim_date', datetime.now().strftime('%Y-%m-%d'))
    }
    
    # Query fact-checking APIs
    api_results = {}
    for api_name in FACT_CHECK_APIS:
        api_results[api_name] = query_fact_checking_api(api_name, claim)
    
    # Calculate scores from advanced parameters
    temporal_score = check_temporal_patterns(claim_obj, temporal_weight)
    semantic_score = analyze_semantic_alignment(claim_obj, reference_data, semantic_weight)
    graph_score = evaluate_graph_structure(claim_obj, graph_data, graph_weight)
    
    # Calculate the trust scores from APIs
    api_scores = []
    api_details = []
    
    for api_name, result in api_results.items():
        if "error" not in result:
            api_scores.append(result["score"])
            api_details.append({
                "source": api_name,
                "score": result["score"]
            })
    
    # Calculate the aggregate score
    if api_scores:
        api_avg_score = sum(api_scores) / len(api_scores)
    else:
        api_avg_score = 5.0  # Neutral score if no API results
    
    # Combine all scores with parameters
    total_weight = 1 + temporal_weight + semantic_weight + graph_weight
    aggregate_score = (
        api_avg_score + 
        temporal_score + 
        semantic_score + 
        graph_score
    ) / total_weight
    
    # Round the result to 2 decimal places
    aggregate_score = round(aggregate_score, 2)
    
    # Prepare the response
    response = {
        "claim": claim,
        "aggregate_trust_score": aggregate_score,
        "component_scores": {
            "api_average": round(api_avg_score, 2),
            "temporal_analysis": round(temporal_score, 2),
            "semantic_alignment": round(semantic_score, 2),
            "graph_structure": round(graph_score, 2)
        },
        "api_details": api_details,
        "explanation": {
            "score_range": "0-10 where 10 indicates highest trustworthiness",
            "weights": {
                "api": 1.0,  # Base weight for API results is always 1.0
                "temporal": temporal_weight,
                "semantic": semantic_weight,
                "graph": graph_weight
            }
        }
    }
    
    return jsonify(response)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "apis": list(FACT_CHECK_APIS.keys())})

if __name__ == '__main__':
    app.run(debug=True, port=8000)