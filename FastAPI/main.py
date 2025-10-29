# main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from SPARQLWrapper import SPARQLWrapper, JSON
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

import re
import os
import traceback

# Import AI translator
from app.ai_client import question_to_sparql

app = FastAPI()

FUSEKI_ENDPOINT = os.getenv("FUSEKI_ENDPOINT", "http://localhost:3030/SmartCom/query")
sparql = SPARQLWrapper(FUSEKI_ENDPOINT)
sparql.setReturnFormat(JSON)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# entity_mappings and base_query (unchanged)
entity_mappings = {
    "lave-vaisselle": "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Lave-vaisselle>",
    "lave-linge": "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Lave-linge>",
    "réfrigérateurs": "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Réfrigérateurs>",
    "aspirateurs": "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Aspirateurs>",
    "cuisinières": "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Cuisinières>",
    "micro-ondes": "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Micro-ondes>",
    "sèche-linge": "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Sèche-linge>",
    "beko": "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Beko>",
    "lg": "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#LG>",
    "samsung": "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Samsung>",
}

base_query = """
    PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
    SELECT ?produit ?description ?prix ?categorie ?marque ?image
    WHERE {
        ?produit a ns:Produit .
        {filter_clause}
        OPTIONAL { ?produit ns:aDescription ?description . }
        OPTIONAL { ?produit ns:aPrix ?prix . }
        OPTIONAL { ?produit ns:aSousCatégorie ?categorie . }
        OPTIONAL { ?produit ns:aProduitMarque ?marque . }
        OPTIONAL { ?produit ns:aImage ?image . }
    }
"""

def natural_to_sparql(question):
    # improved fallback: try to be permissive for many inputs
    q = (question or "").lower().strip()
    filters = []

    cat_match = re.search(r'(par categorie|par catégorie|by category)\s+([a-zA-Z0-9\-\u00C0-\u024F]+)', q)
    mar_match = re.search(r'(par marque|by brand)\s+([a-zA-Z0-9\-\u00C0-\u024F]+)', q)
    prix_match = re.search(r'(avec prix inférieur à|with price less than)\s+(\d+\.?\d*)', q)

    if cat_match:
        cat_name = cat_match.group(2)
        cat_uri = entity_mappings.get(cat_name, f"<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#{cat_name}>")
        if cat_name in entity_mappings:
            filters.append(f"?produit ns:aSousCatégorie ?categorie . FILTER (?categorie = {cat_uri})")
        else:
            filters.append(f"?produit ns:aSousCatégorie ?categorie . FILTER regex(str(?categorie), \"{cat_name}\", \"i\")")
    if mar_match:
        mar_name = mar_match.group(2)
        mar_uri = entity_mappings.get(mar_name, f"<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#{mar_name}>")
        if mar_name in entity_mappings:
            filters.append(f"?produit ns:aProduitMarque ?marqueUri . FILTER (?marqueUri = {mar_uri})")
        else:
            filters.append(f"?produit ns:aProduitMarque ?marqueUri . FILTER regex(str(?marqueUri), \"{mar_name}\", \"i\")")
    if prix_match:
        prix_value = prix_match.group(2)
        filters.append(f"?produit ns:aPrix ?prix . FILTER (?prix < {prix_value} && datatype(?prix) = <http://www.w3.org/2001/XMLSchema#decimal>)")

    # If question mentions 'produit' or 'liste' but parsing failed, return base_query (safe default)
    if not filters and ("liste" in q or "produit" in q or "products" in q):
        return base_query.replace("{filter_clause}", "")

    if filters:
        filter_clause = " . ".join(filters)
        return base_query.replace("{filter_clause}", filter_clause)

    return None

class NLQRequest(BaseModel):
    question: str

# Simple in-memory rate limiter (dev only)
NLQ_STATE = {"count": 0, "reset_at": None}
NLQ_MAX_PER_MINUTE = int(os.getenv("NLQ_MAX_PER_MINUTE", "60"))

def _rate_limit_allow():
    import time
    now = int(time.time())
    if NLQ_STATE["reset_at"] is None or now >= NLQ_STATE["reset_at"]:
        NLQ_STATE["reset_at"] = now + 60
        NLQ_STATE["count"] = 0
    if NLQ_STATE["count"] >= NLQ_MAX_PER_MINUTE:
        return False
    NLQ_STATE["count"] += 1
    return True

@app.post("/nlq")
async def nlq(req: NLQRequest):
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Empty question.")

    if not _rate_limit_allow():
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    # Try LLM first, but always capture raw errors
    sparql_query = None
    llm_debug = {"raw": None, "cleaned": None, "error": None}
    try:
        # request LLM with debug printing suppressed at model client; we capture the result
        sparql_query = await question_to_sparql(question, debug_print=True)
    except Exception as e:
        llm_debug["error"] = str(e)
        print("LLM transformation failed:", str(e))
        # print traceback for deeper debugging
        traceback.print_exc()

    # If LLM failed, fallback to deterministic parser
    if not sparql_query:
        print("Falling back to deterministic natural_to_sparql.")
        sparql_query = natural_to_sparql(question)

    # If still no query, return safe default (base list) rather than 400
    if not sparql_query:
        print("No SPARQL could be generated; returning base product list as fallback.")
        sparql_query = base_query.replace("{filter_clause}", "")

    # Execute SPARQL using threadpool (SPARQLWrapper is blocking)
    try:
        print("Executing SPARQL query:\n", sparql_query)
        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        results = await run_in_threadpool(sparql.query().convert)
        bindings = results.get("results", {}).get("bindings", [])
        # Return sparql for debugging in response
        return {"sparql": sparql_query, "results": bindings}
    except Exception as e:
        print("SPARQL execution error:", str(e))
        traceback.print_exc()
        # On SPARQL execution failure, return a 500 with the error detail
        raise HTTPException(status_code=500, detail=f"SPARQL execution error: {e}")

# keep /sparql GET for backward compatibility
@app.get("/sparql")
async def get_sparql_results(question: str):
    sparql_query = natural_to_sparql(question)
    if not sparql_query:
        return {"error": "Question non reconnue. Exemples : 'liste des produits', 'produits par categorie Lave-vaisselle et marque Beko', 'products with price less than 500'."}
    try:
        print("Générée SPARQL Query:", sparql_query)
        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return {"results": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 9000)))
