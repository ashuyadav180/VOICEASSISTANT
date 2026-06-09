"""Citation Knowledge Graph generation."""

import json
import logging
import urllib.request
import urllib.parse
from typing import Any

logger = logging.getLogger(__name__)

def _ok(result: Any) -> dict:
    return {"success": True, "result": result, "error": None}

def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}

def build_citation_graph(seed_doi_or_title: str) -> dict:
    """Builds a knowledge network around a seed paper."""
    try:
        # First find the paper ID
        search_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(seed_doi_or_title)}&limit=1&fields=paperId,title,citationCount"
        req = urllib.request.Request(search_url, headers={"User-Agent": "SIRI-Research-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            search_data = json.loads(resp.read())
            
        if not search_data.get("data"):
            return _err("Seed paper not found.")
            
        seed_paper = search_data["data"][0]
        paper_id = seed_paper["paperId"]
        
        # Now fetch its references and citations
        graph_url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=title,references.title,citations.title"
        req = urllib.request.Request(graph_url, headers={"User-Agent": "SIRI-Research-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            graph_data = json.loads(resp.read())
            
        references = [r.get("title") for r in graph_data.get("references", [])[:10] if r.get("title")]
        citations = [c.get("title") for c in graph_data.get("citations", [])[:10] if c.get("title")]
        
        return _ok({
            "seed_paper": seed_paper["title"],
            "total_citations": seed_paper.get("citationCount"),
            "key_references_it_builds_on": references,
            "key_papers_that_cite_it": citations
        })
    except Exception as e:
        return _err(f"Graph generation failed: {e}")
