from fastapi import APIRouter
from SPARQLWrapper import SPARQLWrapper, JSON
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Créer un router pour les promotions
router = APIRouter()

# Configurations de connexion à Fuseki
sparql_query = SPARQLWrapper("http://localhost:3030/SmartCom/query")
sparql_update = SPARQLWrapper("http://localhost:3030/SmartCom/update")

# ==================== MODÈLES PYDANTIC ====================

class PromotionInput(BaseModel):
    nom_promotion: str
    date_debut: str  # Format: "2025-01-01T00:00:00"
    date_fin: str
    pourcentage_reduction: float = Field(default=0, ge=0, le=100)
    reduction_fixe: float = Field(default=0, ge=0)
    produit_uri: str  # URI du produit à promouvoir

class PromotionUpdate(BaseModel):
    promotion_uri: str
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None
    pourcentage_reduction: Optional[float] = Field(default=None, ge=0, le=100)
    reduction_fixe: Optional[float] = Field(default=None, ge=0)

class RemiseInput(BaseModel):
    montant_remise: float = Field(ge=0)
    promotion_uri: str

# ==================== ENDPOINTS PROMOTIONS ====================

# 1. CREATE - Ajouter une promotion
@router.post("/add-promotion")
async def add_promotion(promotion: PromotionInput):
    """Ajouter une nouvelle promotion dans la base de données"""
    # Générer un URI unique pour la promotion
    promotion_nom_sanitized = promotion.nom_promotion.replace(" ", "_").replace("'", "")
    promotion_uri = f"<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#{promotion_nom_sanitized}>"
    
    # S'assurer que l'URI du produit est bien formatté
    produit_uri = promotion.produit_uri if promotion.produit_uri.startswith("<") else f"<{promotion.produit_uri}>"
    
    # Construire la requête INSERT
    insert_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        INSERT DATA {{
            {promotion_uri} a ns:prommotion .
            {promotion_uri} ns:aDateDebut "{promotion.date_debut}"^^xsd:dateTime .
            {promotion_uri} ns:aDateFin "{promotion.date_fin}"^^xsd:dateTime .
            {promotion_uri} ns:aPourcentageReduction "{promotion.pourcentage_reduction}"^^xsd:decimal .
            {promotion_uri} ns:aReduction "{promotion.reduction_fixe}"^^xsd:decimal .
            {promotion_uri} ns:aAppliqueAProduit {produit_uri} .
        }}
    """
    
    print("Générée SPARQL Insert Query:", insert_query)
    sparql_update.setQuery(insert_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {
            "message": "Promotion ajoutée avec succès", 
            "promotion_uri": promotion_uri,
            "produit_uri": produit_uri
        }
    except Exception as e:
        return {"error": str(e)}

# 2. READ ALL - Lire toutes les promotions
@router.get("/promotions")
async def get_promotions():
    """Récupérer la liste de toutes les promotions"""
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?promotion ?dateDebut ?dateFin ?pourcentage ?reduction ?produit
        WHERE {
            ?promotion a ns:prommotion .
            OPTIONAL { ?promotion ns:aDateDebut ?dateDebut . }
            OPTIONAL { ?promotion ns:aDateFin ?dateFin . }
            OPTIONAL { ?promotion ns:aPourcentageReduction ?pourcentage . }
            OPTIONAL { ?promotion ns:aReduction ?reduction . }
            OPTIONAL { ?promotion ns:aAppliqueAProduit ?produit . }
        }
        ORDER BY DESC(?dateDebut)
    """
    
    print("Générée SPARQL Query:", query)
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        return {"promotions": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

# 3. READ - Promotions actives (en cours)
@router.get("/promotions/actives")
async def get_active_promotions():
    """Récupérer les promotions actuellement actives"""
    # Date actuelle au format compatible avec la base de données
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    
    query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?promotion ?dateDebut ?dateFin ?pourcentage ?reduction ?produit
        WHERE {{
            ?promotion a ns:prommotion .
            ?promotion ns:aDateDebut ?dateDebut .
            ?promotion ns:aDateFin ?dateFin .
            OPTIONAL {{ ?promotion ns:aPourcentageReduction ?pourcentage . }}
            OPTIONAL {{ ?promotion ns:aReduction ?reduction . }}
            OPTIONAL {{ ?promotion ns:aAppliqueAProduit ?produit . }}
            FILTER (str(?dateDebut) <= "{now}" && str(?dateFin) >= "{now}")
        }}
        ORDER BY ?dateFin
    """
    
    print("Générée SPARQL Active Promotions Query:", query)
    print(f"Date actuelle utilisée: {now}")
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        return {"promotions_actives": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

# 4. READ - Promotions d'un produit spécifique
@router.get("/promotions/produit")
async def get_product_promotions(produit_uri: str):
    """Récupérer les promotions d'un produit spécifique"""
    query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?promotion ?dateDebut ?dateFin ?pourcentage ?reduction
        WHERE {{
            ?promotion a ns:prommotion .
            ?promotion ns:aAppliqueAProduit <{produit_uri}> .
            OPTIONAL {{ ?promotion ns:aDateDebut ?dateDebut . }}
            OPTIONAL {{ ?promotion ns:aDateFin ?dateFin . }}
            OPTIONAL {{ ?promotion ns:aPourcentageReduction ?pourcentage . }}
            OPTIONAL {{ ?promotion ns:aReduction ?reduction . }}
        }}
        ORDER BY DESC(?dateDebut)
    """
    
    print("Générée SPARQL Product Promotions Query:", query)
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        return {"promotions": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

# 5. UPDATE - Modifier une promotion
@router.put("/update-promotion")
async def update_promotion(promotion: PromotionUpdate):
    """Modifier les informations d'une promotion existante"""
    delete_clauses = []
    insert_clauses = []
    where_clauses = []
    
    if promotion.date_debut is not None:
        delete_clauses.append(f"<{promotion.promotion_uri}> ns:aDateDebut ?oldDateDebut .")
        insert_clauses.append(f"<{promotion.promotion_uri}> ns:aDateDebut \"{promotion.date_debut}\"^^xsd:dateTime .")
        where_clauses.append(f"OPTIONAL {{ <{promotion.promotion_uri}> ns:aDateDebut ?oldDateDebut . }}")
    
    if promotion.date_fin is not None:
        delete_clauses.append(f"<{promotion.promotion_uri}> ns:aDateFin ?oldDateFin .")
        insert_clauses.append(f"<{promotion.promotion_uri}> ns:aDateFin \"{promotion.date_fin}\"^^xsd:dateTime .")
        where_clauses.append(f"OPTIONAL {{ <{promotion.promotion_uri}> ns:aDateFin ?oldDateFin . }}")
    
    if promotion.pourcentage_reduction is not None:
        delete_clauses.append(f"<{promotion.promotion_uri}> ns:aPourcentageReduction ?oldPourcentage .")
        insert_clauses.append(f"<{promotion.promotion_uri}> ns:aPourcentageReduction \"{promotion.pourcentage_reduction}\"^^xsd:decimal .")
        where_clauses.append(f"OPTIONAL {{ <{promotion.promotion_uri}> ns:aPourcentageReduction ?oldPourcentage . }}")
    
    if promotion.reduction_fixe is not None:
        delete_clauses.append(f"<{promotion.promotion_uri}> ns:aReduction ?oldReduction .")
        insert_clauses.append(f"<{promotion.promotion_uri}> ns:aReduction \"{promotion.reduction_fixe}\"^^xsd:decimal .")
        where_clauses.append(f"OPTIONAL {{ <{promotion.promotion_uri}> ns:aReduction ?oldReduction . }}")
    
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
        return {"message": "Promotion modifiée avec succès"}
    except Exception as e:
        return {"error": str(e)}

# 6. DELETE - Supprimer une promotion
@router.delete("/delete-promotion")
async def delete_promotion(promotion_uri: str):
    """Supprimer une promotion de la base de données"""
    delete_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        DELETE WHERE {{
            <{promotion_uri}> ?p ?o .
        }}
    """
    
    print("Générée SPARQL Delete Query:", delete_query)
    sparql_update.setQuery(delete_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Promotion supprimée avec succès"}
    except Exception as e:
        return {"error": str(e)}

# ==================== ENDPOINTS REMISES ====================

# 7. CREATE - Ajouter une remise
@router.post("/add-remise")
async def add_remise(remise: RemiseInput):
    """Créer une remise et la lier à une promotion"""
    # Générer un URI unique pour la remise
    from uuid import uuid4
    remise_uri = f"<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Remise_{uuid4()}>"
    
    # S'assurer que l'URI de la promotion est bien formatté
    promotion_uri = remise.promotion_uri if remise.promotion_uri.startswith("<") else f"<{remise.promotion_uri}>"
    
    insert_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        INSERT DATA {{
            {remise_uri} a ns:Remise .
            {remise_uri} ns:aMontantRemise "{remise.montant_remise}"^^xsd:decimal .
            {promotion_uri} ns:aOffreRemise {remise_uri} .
        }}
    """
    
    print("Générée SPARQL Insert Remise Query:", insert_query)
    sparql_update.setQuery(insert_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Remise créée avec succès", "remise_uri": remise_uri}
    except Exception as e:
        return {"error": str(e)}

# 8. READ ALL - Lire toutes les remises
@router.get("/remises")
async def get_remises():
    """Récupérer la liste de toutes les remises"""
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?remise ?montant ?promotion
        WHERE {
            ?remise a ns:Remise .
            OPTIONAL { ?remise ns:aMontantRemise ?montant . }
            OPTIONAL { ?promotion ns:aOffreRemise ?remise . }
        }
    """
    
    print("Générée SPARQL Query:", query)
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        return {"remises": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

