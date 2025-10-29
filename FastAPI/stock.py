from fastapi import APIRouter
from SPARQLWrapper import SPARQLWrapper, JSON
from pydantic import BaseModel, Field
from typing import Optional

# Créer un router pour le stock
router = APIRouter()

# Configurations de connexion à Fuseki
sparql_query = SPARQLWrapper("http://localhost:3030/SmartCom/query")
sparql_update = SPARQLWrapper("http://localhost:3030/SmartCom/update")

# ==================== MODÈLES PYDANTIC ====================

class StockUpdate(BaseModel):
    produit_uri: str
    quantite: int = Field(ge=0)

class StockMovement(BaseModel):
    produit_uri: str
    quantite_ajoutee: int
    type_mouvement: str  # "entree" ou "sortie"

# ==================== ENDPOINTS ====================

# 1. GET - Récupérer tous les produits avec leur stock
@router.get("/stock/all")
async def get_all_stock():
    """Récupérer la liste de tous les produits avec leur stock"""
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?produit ?description ?prix ?stock ?categorie ?marque ?image
        WHERE {
            ?produit a ns:Produit .
            OPTIONAL { ?produit ns:aDescription ?description . }
            OPTIONAL { ?produit ns:aPrix ?prix . }
            OPTIONAL { ?produit ns:aStockDisponible ?stock . }
            OPTIONAL { ?produit ns:aSousCatégorie ?categorie . }
            OPTIONAL { ?produit ns:aProduitMarque ?marque . }
            OPTIONAL { ?produit ns:aImage ?image . }
        }
        ORDER BY ?produit
    """
    
    print("Générée SPARQL Stock Query:", query)
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        return {"produits": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

# 2. GET - Alertes de stock (rupture et stock faible)
@router.get("/stock/alerts")
async def get_stock_alerts():
    """Récupérer les produits en rupture de stock ou avec stock faible"""
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?produit ?description ?prix ?stock ?categorie ?marque
        WHERE {
            ?produit a ns:Produit .
            ?produit ns:aStockDisponible ?stock .
            OPTIONAL { ?produit ns:aDescription ?description . }
            OPTIONAL { ?produit ns:aPrix ?prix . }
            OPTIONAL { ?produit ns:aSousCatégorie ?categorie . }
            OPTIONAL { ?produit ns:aProduitMarque ?marque . }
            FILTER (?stock < 10)
        }
        ORDER BY ?stock
    """
    
    print("Générée SPARQL Stock Alerts Query:", query)
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        bindings = results["results"]["bindings"]
        
        # Séparer en rupture et stock faible
        rupture = [p for p in bindings if int(p.get("stock", {}).get("value", 0)) == 0]
        stock_faible = [p for p in bindings if 0 < int(p.get("stock", {}).get("value", 0)) < 10]
        
        return {
            "rupture": rupture,
            "stock_faible": stock_faible,
            "total_alertes": len(rupture) + len(stock_faible)
        }
    except Exception as e:
        return {"error": str(e)}

# 3. PUT - Modifier rapidement le stock d'un produit
@router.put("/stock/update")
async def update_stock(stock: StockUpdate):
    """Modifier le stock d'un produit"""
    update_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        DELETE {{
            <{stock.produit_uri}> ns:aStockDisponible ?oldStock .
        }}
        INSERT {{
            <{stock.produit_uri}> ns:aStockDisponible "{stock.quantite}"^^xsd:integer .
        }}
        WHERE {{
            OPTIONAL {{ <{stock.produit_uri}> ns:aStockDisponible ?oldStock . }}
        }}
    """
    
    print("Générée SPARQL Stock Update Query:", update_query)
    sparql_update.setQuery(update_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Stock mis à jour avec succès", "nouveau_stock": stock.quantite}
    except Exception as e:
        return {"error": str(e)}

# 4. GET - Statistiques globales du stock
@router.get("/stock/statistics")
async def get_stock_statistics():
    """Récupérer les statistiques globales du stock"""
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?produit ?prix ?stock
        WHERE {
            ?produit a ns:Produit .
            OPTIONAL { ?produit ns:aPrix ?prix . }
            OPTIONAL { ?produit ns:aStockDisponible ?stock . }
        }
    """
    
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        bindings = results["results"]["bindings"]
        
        # Calculer les statistiques
        total_produits = len(bindings)
        stocks = [int(p.get("stock", {}).get("value", 0)) for p in bindings]
        prix = [float(p.get("prix", {}).get("value", 0)) for p in bindings if p.get("prix")]
        
        stock_total = sum(stocks)
        produits_en_stock = len([s for s in stocks if s > 0])
        produits_rupture = len([s for s in stocks if s == 0])
        
        # Valeur totale du stock
        valeur_stock = 0
        for p in bindings:
            stock_val = int(p.get("stock", {}).get("value", 0))
            prix_val = float(p.get("prix", {}).get("value", 0))
            valeur_stock += stock_val * prix_val
        
        return {
            "total_produits": total_produits,
            "stock_total": stock_total,
            "produits_en_stock": produits_en_stock,
            "produits_rupture": produits_rupture,
            "valeur_stock": round(valeur_stock, 2)
        }
    except Exception as e:
        return {"error": str(e)}

