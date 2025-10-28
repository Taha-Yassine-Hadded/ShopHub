from fastapi import FastAPI
from SPARQLWrapper import SPARQLWrapper, JSON, POST
import re
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from pydantic import BaseModel, Field
from produits import router as produits_router


app = FastAPI()

# Configurations de connexion à Fuseki
sparql_query = SPARQLWrapper("http://localhost:3030/SmartCom/query")  # Pour les requêtes SELECT
sparql_update = SPARQLWrapper("http://localhost:3030/SmartCom/update")  # Pour les requêtes UPDATE

# Activer CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(produits_router)

# Modèle Pydantic pour valider les données de l'avis
class AvisInput(BaseModel):
    product_uri: str
    note: float = Field(ge=0, le=5)
    commentaire: str

# Modèle pour récupérer un avis existant
class AvisUpdate(BaseModel):
    avis_uri: str
    note: float = Field(ge=0, le=5)
    commentaire: str

# Dictionnaire pour mapper les noms textuels aux URIs
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

# Template de base pour les requêtes avec filtres multiples
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

# Fonction pour transformer une question naturelle en SPARQL avec filtres multiples
def natural_to_sparql(question):
    question = question.lower().strip()
    filters = []

    cat_match = re.search(r'(par categorie|by category)\s+(\w+(?:-\w+)?)', question)
    mar_match = re.search(r'(par marque|by brand)\s+(\w+)', question)
    prix_match = re.search(r'(avec prix inférieur à|with price less than)\s+(\d+\.?\d*)', question)

    if cat_match:
        cat_name = cat_match.group(2)
        cat_uri = entity_mappings.get(cat_name, f"<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#{cat_name}>")
        filters.append(f"?produit ns:aSousCatégorie ?categorie . FILTER (?categorie = {cat_uri})")
    if mar_match:
        mar_name = mar_match.group(2)
        mar_uri = entity_mappings.get(mar_name, f"<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#{mar_name}>")
        filters.append(f"?produit ns:aProduitMarque ?marqueUri . FILTER (?marqueUri = {mar_uri})")
    if prix_match:
        prix_value = prix_match.group(2)
        filters.append(f"?produit ns:aPrix ?prix . FILTER (?prix < {prix_value} && datatype(?prix) = <http://www.w3.org/2001/XMLSchema#decimal>)")

    if not filters and "liste des produits" in question:
        return base_query.replace("{filter_clause}", "")
    elif not filters and "list of products" in question:
        return base_query.replace("{filter_clause}", "")

    if filters:
        filter_clause = " . ".join(filters)
        return base_query.replace("{filter_clause}", filter_clause)

    return None

# Endpoint pour récupérer les produits
@app.get("/sparql")
async def get_sparql_results(question: str):
    sparql_query.setQuery(natural_to_sparql(question))
    if not sparql_query.query:
        return {"error": "Question non reconnue. Exemples : 'liste des produits', 'produits par categorie Lave-vaisselle et marque Beko', 'products with price less than 500'."}

    print("Générée SPARQL Query:", sparql_query.query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        return {"results": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

# Endpoint pour récupérer les avis d'un produit
@app.get("/avis")
async def get_avis(product_uri: str):
    query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?avis ?note ?commentaire
        WHERE {{
            ?avis a ns:Avis .
            ?avis ns:aAvisProduit <{product_uri}> .
            ?avis ns:aNote ?note .
            ?avis ns:aCommentaire ?commentaire .
        }}
    """
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        return {"avis": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

# Endpoint pour ajouter un avis
@app.post("/add-avis")
async def add_avis(avis: AvisInput):
    if not avis.product_uri.startswith("<http://") or not avis.product_uri.endswith(">"):
        avis.product_uri = f"<{avis.product_uri}>"
    avis_uri = f"<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Avis_{uuid4()}>"
    insert_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        INSERT DATA {{
            {avis_uri} a ns:Avis .
            {avis_uri} ns:aNote "{avis.note}"^^xsd:decimal .
            {avis_uri} ns:aCommentaire "{avis.commentaire}"^^xsd:string .
            {avis_uri} ns:aAvisProduit {avis.product_uri} .
        }}
    """
    print("Générée SPARQL Update Query:", insert_query)
    sparql_update.setQuery(insert_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Avis ajouté avec succès", "avis_uri": avis_uri}
    except Exception as e:
        return {"error": str(e)}

# Endpoint pour supprimer un avis
@app.delete("/delete-avis")
async def delete_avis(avis_uri: str):
    delete_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        DELETE WHERE {{
            <{avis_uri}> ?p ?o .
        }}
    """
    sparql_update.setQuery(delete_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Avis supprimé avec succès"}
    except Exception as e:
        return {"error": str(e)}

# Endpoint pour modifier un avis
@app.put("/update-avis")
async def update_avis(avis: AvisUpdate):
    update_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        DELETE {{
            <{avis.avis_uri}> ns:aNote ?oldNote .
            <{avis.avis_uri}> ns:aCommentaire ?oldCommentaire .
        }}
        INSERT {{
            <{avis.avis_uri}> ns:aNote "{avis.note}"^^xsd:decimal .
            <{avis.avis_uri}> ns:aCommentaire "{avis.commentaire}"^^xsd:string .
        }}
        WHERE {{
            <{avis.avis_uri}> ns:aNote ?oldNote .
            <{avis.avis_uri}> ns:aCommentaire ?oldCommentaire .
        }}
    """
    sparql_update.setQuery(update_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Avis modifié avec succès"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)