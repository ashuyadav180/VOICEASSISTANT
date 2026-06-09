"""Global Research Intelligence tools."""

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

def search_semantic(query: str, limit: int = 10) -> dict:
    """Semantic Scholar API search."""
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit={limit}&fields=title,abstract,year,authors,citationCount,isOpenAccess,url"
        req = urllib.request.Request(url, headers={"User-Agent": "SIRI-Research-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return _ok(data.get("data", []))
    except Exception as e:
        return _err(f"Semantic Scholar search failed: {e}")

def search_pubmed(query: str, limit: int = 5) -> dict:
    """NCBI PubMed E-utilities search."""
    try:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={urllib.parse.quote(query)}&retmode=json&retmax={limit}"
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
            
        id_list = data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return _ok([])
            
        summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(id_list)}&retmode=json"
        with urllib.request.urlopen(summary_url, timeout=15) as resp:
            summary_data = json.loads(resp.read())
            
        results = []
        for pid in id_list:
            doc = summary_data.get("result", {}).get(pid, {})
            if doc:
                results.append({
                    "title": doc.get("title"),
                    "pubdate": doc.get("pubdate"),
                    "source": doc.get("source"),
                    "authors": [a.get("name") for a in doc.get("authors", [])],
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/"
                })
        return _ok(results)
    except Exception as e:
        return _err(f"PubMed search failed: {e}")

def get_author_profile(name: str) -> dict:
    """Fetch author profile from Semantic Scholar."""
    try:
        url = f"https://api.semanticscholar.org/graph/v1/author/search?query={urllib.parse.quote(name)}&limit=1&fields=name,url,hIndex,paperCount,citationCount"
        req = urllib.request.Request(url, headers={"User-Agent": "SIRI-Research-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            
        if not data.get("data"):
            return _err("Author not found")
            
        author = data["data"][0]
        return _ok(author)
    except Exception as e:
        return _err(f"Author lookup failed: {e}")

def analyze_trend(topic: str) -> dict:
    """Analyze research trends by counting papers over the last 5 years on OpenAlex."""
    try:
        from datetime import datetime
        current_year = datetime.now().year
        
        # We query openalex for works containing the concept, grouped by publication_year
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(topic)}&group_by=publication_year"
        req = urllib.request.Request(url, headers={"User-Agent": "mailto:siri@local.host"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            
        group_by = data.get("group_by", [])
        trends = {}
        for group in group_by:
            year = group.get("key")
            count = group.get("count")
            try:
                year_int = int(year)
                if current_year - 5 <= year_int <= current_year:
                    trends[year] = count
            except ValueError:
                pass
                
        sorted_trends = dict(sorted(trends.items()))
        return _ok({
            "topic": topic,
            "yearly_paper_counts": sorted_trends
        })
    except Exception as e:
        return _err(f"Trend analysis failed: {e}")
