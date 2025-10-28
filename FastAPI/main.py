from fastapi import FastAPI, HTTPException
from SPARQLWrapper import SPARQLWrapper, JSON
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cart_queries import CartQueries
from order_service import OrderService

app = FastAPI()

# Initialize cart queries and order service
cart_queries = CartQueries()
order_service = OrderService()

# Pydantic models for request bodies
class AddToCartRequest(BaseModel):
    product_uri: str
    client_id: int = 1
    quantity: int = 1

class RemoveFromCartRequest(BaseModel):
    product_uri: str
    client_id: int = 1

class UpdateQuantityRequest(BaseModel):
    product_uri: str
    quantity: int

class OrderRequest(BaseModel):
    full_name: str
    email: str
    phone: str
    delivery_address: str

# Configuration de la connexion à Fuseki
sparql = SPARQLWrapper("http://localhost:3030/SmartCom/query")
from fastapi import FastAPI
from SPARQLWrapper import SPARQLWrapper, JSON, POST
import re
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from pydantic import BaseModel, Field

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

# Cart endpoints
@app.get("/cart/{client_id}")
async def get_cart(client_id: int = 1):
    """Get all items in the cart for a client"""
    try:
        items = cart_queries.get_cart_items(client_id)
        summary = cart_queries.get_cart_summary(client_id)
        return {
            "items": items or [],
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add new endpoints for order management
@app.get("/orders")
async def get_all_orders():
    """Get all orders in the system"""
    try:
        orders = order_service.get_all_orders()
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders/{client_id}")
async def get_client_orders(client_id: int):
    """Get all orders for a specific client"""
    try:
        orders = order_service.get_client_orders(client_id)
        return {"orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel a specific order"""
    try:
        result = order_service.cancel_order(order_id)
        if result["success"]:
            return {"message": result["message"]}
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/order/{order_id}")
async def get_order_details(order_id: str):
    """Get detailed information about a specific order"""
    try:
        order = order_service.get_order_details(order_id)
        if order:
            return order
        else:
            raise HTTPException(status_code=404, detail="Order not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cart/{client_id}/summary")
async def get_cart_summary(client_id: int = 1):
    """Get cart summary (total items and amount)"""
    try:
        summary = cart_queries.get_cart_summary(client_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cart/add")
async def add_to_cart(request: AddToCartRequest):
    """Add a product to the cart"""
    try:
        success = cart_queries.add_to_cart(request.client_id, request.product_uri, request.quantity)
        if success:
            return {"success": True, "message": f"Product added to cart with quantity {request.quantity}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add product to cart")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cart/remove")
async def remove_from_cart(request: RemoveFromCartRequest):
    """Remove a product from the cart"""
    try:
        success = cart_queries.remove_from_cart(request.client_id, request.product_uri)
        if success:
            return {"success": True, "message": "Product removed from cart"}
        else:
            raise HTTPException(status_code=400, detail="Failed to remove product from cart")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cart/{client_id}/clear")
async def clear_cart(client_id: int = 1):
    """Clear all items from the cart"""
    try:
        success = cart_queries.clear_cart(client_id)
        if success:
            return {"success": True, "message": "Cart cleared"}
        else:
            raise HTTPException(status_code=400, detail="Failed to clear cart")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cart/{client_id}/checkout")
async def checkout_cart(client_id: int, order_details: OrderRequest):
    """Convert cart to order with customer details"""
    try:
        # Check if cart is empty before proceeding
        cart_summary = cart_queries.get_cart_summary(client_id)
        if not cart_summary or cart_summary.get("totalItems", 0) == 0:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Convert Pydantic model to dict
        order_data = order_details.dict()
        
        # Create order using the order service
        result = order_service.create_order_from_cart(client_id, order_data)
        
        if result["success"]:
            # Clear the cart after successful order creation
            cart_queries.clear_cart(client_id)
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/cart/{client_id}/update-quantity")
async def update_cart_quantity(client_id: int, request: UpdateQuantityRequest):
    """Update quantity of an item in the cart"""
    try:
        success = cart_queries.update_cart_quantity(client_id, request.product_uri, request.quantity)
        if success:
            return {"success": True, "message": f"Quantity updated to {request.quantity}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update quantity")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
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