from fastapi import FastAPI
from SPARQLWrapper import SPARQLWrapper, JSON
import re
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuration de la connexion à Fuseki
sparql = SPARQLWrapper("http://localhost:3030/SmartCom/query")

# Activer CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    # Ajoutez d'autres marques/catégories si nécessaire
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

    # Détection des filtres
    cat_match = re.search(r'(par categorie|by category)\s+(\w+(?:-\w+)?)', question)
    mar_match = re.search(r'(par marque|by brand)\s+(\w+)', question)
    prix_match = re.search(r'(avec prix inférieur à|with price less than)\s+(\d+\.?\d*)', question)

    # Construction des clauses de filtre
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

    # Si aucun filtre, utiliser la requête de base
    if not filters and "liste des produits" in question:
        return base_query.replace("{filter_clause}", "")
    elif not filters and "list of products" in question:
        return base_query.replace("{filter_clause}", "")

    # Combiner les filtres avec AND
    if filters:
        filter_clause = " . ".join(filters)
        return base_query.replace("{filter_clause}", filter_clause)

    return None

@app.get("/sparql")
async def get_sparql_results(question: str):
    sparql_query = natural_to_sparql(question)
    if not sparql_query:
        return {"error": "Question non reconnue. Exemples : 'liste des produits', 'produits par categorie Lave-vaisselle et marque Beko', 'products with price less than 500'."}

    print("Générée SPARQL Query:", sparql_query)  # Pour débogage
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        return {"results": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)