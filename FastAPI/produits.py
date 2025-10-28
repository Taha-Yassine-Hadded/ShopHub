from fastapi import APIRouter
from SPARQLWrapper import SPARQLWrapper, JSON
from pydantic import BaseModel, Field

# Créer un router pour les produits
router = APIRouter()

# Configurations de connexion à Fuseki
sparql_query = SPARQLWrapper("http://localhost:3030/SmartCom/query")
sparql_update = SPARQLWrapper("http://localhost:3030/SmartCom/update")

# ==================== MODÈLES PYDANTIC ====================

class ProduitInput(BaseModel):
    nom: str
    description: str = ""
    prix: float = Field(ge=0)
    categorie_uri: str
    marque_uri: str
    image: str = ""
    poids: float = Field(default=0, ge=0)
    stock_disponible: int = Field(default=0, ge=0)

class ProduitUpdate(BaseModel):
    produit_uri: str
    description: str = None
    prix: float = Field(default=None, ge=0)
    categorie_uri: str = None
    marque_uri: str = None
    image: str = None
    poids: float = Field(default=None, ge=0)
    stock_disponible: int = Field(default=None, ge=0)

# ==================== ENDPOINTS ====================

# 1. CREATE - Ajouter un produit
@router.post("/add-produit")
async def add_produit(produit: ProduitInput):
    """Ajouter un nouveau produit dans la base de données"""
    # Générer un URI unique pour le produit
    produit_nom_sanitized = produit.nom.replace(" ", "_")
    produit_uri = f"<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#{produit_nom_sanitized}>"
    
    # S'assurer que les URIs de catégorie et marque sont bien formattés
    categorie_uri = produit.categorie_uri if produit.categorie_uri.startswith("<") else f"<{produit.categorie_uri}>"
    marque_uri = produit.marque_uri if produit.marque_uri.startswith("<") else f"<{produit.marque_uri}>"
    
    # Construire la requête INSERT
    insert_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        INSERT DATA {{
            {produit_uri} a ns:Produit .
            {produit_uri} ns:aDescription "{produit.description}"^^xsd:string .
            {produit_uri} ns:aPrix "{produit.prix}"^^xsd:decimal .
            {produit_uri} ns:aSousCatégorie {categorie_uri} .
            {produit_uri} ns:aProduitMarque {marque_uri} .
            {produit_uri} ns:aImage "{produit.image}"^^xsd:anyURI .
            {produit_uri} ns:aPoids "{produit.poids}"^^xsd:decimal .
            {produit_uri} ns:aStockDisponible "{produit.stock_disponible}"^^xsd:integer .
        }}
    """
    
    print("Générée SPARQL Insert Query:", insert_query)
    sparql_update.setQuery(insert_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Produit ajouté avec succès", "produit_uri": produit_uri}
    except Exception as e:
        return {"error": str(e)}

# 2. READ - Lire les détails d'un produit
@router.get("/produit")
async def get_produit(produit_uri: str):
    """Récupérer les détails d'un produit spécifique"""
    query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?description ?prix ?categorie ?marque ?image ?poids ?stock
        WHERE {{
            <{produit_uri}> a ns:Produit .
            OPTIONAL {{ <{produit_uri}> ns:aDescription ?description . }}
            OPTIONAL {{ <{produit_uri}> ns:aPrix ?prix . }}
            OPTIONAL {{ <{produit_uri}> ns:aSousCatégorie ?categorie . }}
            OPTIONAL {{ <{produit_uri}> ns:aProduitMarque ?marque . }}
            OPTIONAL {{ <{produit_uri}> ns:aImage ?image . }}
            OPTIONAL {{ <{produit_uri}> ns:aPoids ?poids . }}
            OPTIONAL {{ <{produit_uri}> ns:aStockDisponible ?stock . }}
        }}
    """
    
    print("Générée SPARQL Query:", query)
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        return {"produit": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

# 3. UPDATE - Modifier un produit
@router.put("/update-produit")
async def update_produit(produit: ProduitUpdate):
    """Modifier les informations d'un produit existant"""
    # Construire les clauses DELETE et INSERT dynamiquement
    delete_clauses = []
    insert_clauses = []
    where_clauses = []
    
    if produit.description is not None:
        delete_clauses.append(f"<{produit.produit_uri}> ns:aDescription ?oldDescription .")
        insert_clauses.append(f"<{produit.produit_uri}> ns:aDescription \"{produit.description}\"^^xsd:string .")
        where_clauses.append(f"OPTIONAL {{ <{produit.produit_uri}> ns:aDescription ?oldDescription . }}")
    
    if produit.prix is not None:
        delete_clauses.append(f"<{produit.produit_uri}> ns:aPrix ?oldPrix .")
        insert_clauses.append(f"<{produit.produit_uri}> ns:aPrix \"{produit.prix}\"^^xsd:decimal .")
        where_clauses.append(f"OPTIONAL {{ <{produit.produit_uri}> ns:aPrix ?oldPrix . }}")
    
    if produit.categorie_uri is not None:
        categorie_uri = produit.categorie_uri if produit.categorie_uri.startswith("<") else f"<{produit.categorie_uri}>"
        delete_clauses.append(f"<{produit.produit_uri}> ns:aSousCatégorie ?oldCategorie .")
        insert_clauses.append(f"<{produit.produit_uri}> ns:aSousCatégorie {categorie_uri} .")
        where_clauses.append(f"OPTIONAL {{ <{produit.produit_uri}> ns:aSousCatégorie ?oldCategorie . }}")
    
    if produit.marque_uri is not None:
        marque_uri = produit.marque_uri if produit.marque_uri.startswith("<") else f"<{produit.marque_uri}>"
        delete_clauses.append(f"<{produit.produit_uri}> ns:aProduitMarque ?oldMarque .")
        insert_clauses.append(f"<{produit.produit_uri}> ns:aProduitMarque {marque_uri} .")
        where_clauses.append(f"OPTIONAL {{ <{produit.produit_uri}> ns:aProduitMarque ?oldMarque . }}")
    
    if produit.image is not None:
        delete_clauses.append(f"<{produit.produit_uri}> ns:aImage ?oldImage .")
        insert_clauses.append(f"<{produit.produit_uri}> ns:aImage \"{produit.image}\"^^xsd:anyURI .")
        where_clauses.append(f"OPTIONAL {{ <{produit.produit_uri}> ns:aImage ?oldImage . }}")
    
    if produit.poids is not None:
        delete_clauses.append(f"<{produit.produit_uri}> ns:aPoids ?oldPoids .")
        insert_clauses.append(f"<{produit.produit_uri}> ns:aPoids \"{produit.poids}\"^^xsd:decimal .")
        where_clauses.append(f"OPTIONAL {{ <{produit.produit_uri}> ns:aPoids ?oldPoids . }}")
    
    if produit.stock_disponible is not None:
        delete_clauses.append(f"<{produit.produit_uri}> ns:aStockDisponible ?oldStock .")
        insert_clauses.append(f"<{produit.produit_uri}> ns:aStockDisponible \"{produit.stock_disponible}\"^^xsd:integer .")
        where_clauses.append(f"OPTIONAL {{ <{produit.produit_uri}> ns:aStockDisponible ?oldStock . }}")
    
    if not delete_clauses:
        return {"error": "Aucun champ à modifier"}
    
    update_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        DELETE {{
            {' '.join(delete_clauses)}
        }}
        INSERT {{
            {' '.join(insert_clauses)}
        }}
        WHERE {{
            {' '.join(where_clauses)}
        }}
    """
    
    print("Générée SPARQL Update Query:", update_query)
    sparql_update.setQuery(update_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Produit modifié avec succès"}
    except Exception as e:
        return {"error": str(e)}

# 4. DELETE - Supprimer un produit
@router.delete("/delete-produit")
async def delete_produit(produit_uri: str):
    """Supprimer un produit de la base de données"""
    delete_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        DELETE WHERE {{
            <{produit_uri}> ?p ?o .
        }}
    """
    
    print("Générée SPARQL Delete Query:", delete_query)
    sparql_update.setQuery(delete_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Produit supprimé avec succès"}
    except Exception as e:
        return {"error": str(e)} 