"""
SPARQL Queries for Cart (Panier) Operations
This module contains all SPARQL queries related to cart management
"""

from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Dict, List, Optional
import uuid
from datetime import datetime

class CartQueries:
    def __init__(self, sparql_endpoint: str = "http://localhost:3030/SmartCom"):
        self.sparql_endpoint = sparql_endpoint
        self.query_endpoint = f"{sparql_endpoint}/query"
        self.update_endpoint = f"{sparql_endpoint}/update"
        
    def _execute_query(self, query: str, is_update: bool = False):
        """Execute SPARQL query or update"""
        try:
            sparql = SPARQLWrapper(self.update_endpoint if is_update else self.query_endpoint)
            sparql.setQuery(query)
            
            if is_update:
                sparql.setMethod('POST')
                return sparql.query()
            else:
                sparql.setReturnFormat(JSON)
                results = sparql.query().convert()
                
                # Handle ASK queries differently
                if "boolean" in results:
                    return results
                else:
                    return results["results"]["bindings"]
        except Exception as e:
            print(f"SPARQL Error: {e}")
            return None

    def get_cart_items(self, client_id: int = 1) -> List[Dict]:
        """Get all items in the cart for a specific client with quantities"""
        cart_uri = f"ns:Panier_Client{client_id}"  # Use single cart per client
        
        print(f"Getting cart items for client {client_id}, cart: {cart_uri}")
        
        query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        
        SELECT ?produit ?quantity
               (SAMPLE(?description) AS ?desc) 
               (SAMPLE(?prix) AS ?price) 
               (SAMPLE(?image) AS ?img) 
               (SAMPLE(?marque) AS ?brand) 
               (SAMPLE(?categorie) AS ?cat)
        WHERE {{
            ?cartItem ns:inCart {cart_uri} ;
                     ns:refersToProduct ?produit ;
                     ns:hasQuantity ?quantity .
            
            OPTIONAL {{ ?produit ns:aDescription ?description }}
            OPTIONAL {{ ?produit ns:aPrix ?prix }}
            OPTIONAL {{ ?produit ns:aImage ?image }}
            OPTIONAL {{ ?produit ns:aProduitMarque ?marque }}
            OPTIONAL {{ ?produit ns:aSousCatégorie ?categorie }}
        }}
        GROUP BY ?produit ?quantity
        """
        
        print(f"Cart items query: {query}")
        
        results = self._execute_query(query)
        print(f"Cart items results: {results}")
        
        items = []
        if results:
            for result in results:
                item = {
                    "product_uri": result.get("produit", {}).get("value", ""),
                    "description": result.get("desc", {}).get("value", ""),
                    "price": float(result.get("price", {}).get("value", 0)) if result.get("price") else 0,
                    "image": result.get("img", {}).get("value", ""),
                    "brand": result.get("brand", {}).get("value", ""),
                    "category": result.get("cat", {}).get("value", ""),
                    "quantity": int(result.get("quantity", {}).get("value", 1))
                }
                items.append(item)
                print(f"Added item: {item}")
        
        print(f"Total unique items found: {len(items)}")
        return items

    def get_cart_summary(self, client_id: int) -> dict:
        """Get cart summary (total items and amount)"""
        cart_uri = f"ns:Panier_Client{client_id}"  # Use single cart per client
        
        print(f"Getting cart summary for client {client_id}, cart: {cart_uri}")
        
        query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT (SUM(?quantity) AS ?totalItems) (SUM(?quantity * ?prix) AS ?totalAmount) WHERE {{
            ?cartItem ns:inCart {cart_uri} ;
                     ns:refersToProduct ?produit ;
                     ns:hasQuantity ?quantity .
            ?produit ns:aPrix ?prix .
        }}
        """
        
        print(f"Cart summary query: {query}")
        
        results = self._execute_query(query)
        print(f"Cart summary results: {results}")
        
        if results and len(results) > 0:
            total_items = int(results[0]["totalItems"]["value"]) if results[0]["totalItems"]["value"] else 0
            total_amount = float(results[0]["totalAmount"]["value"]) if results[0]["totalAmount"]["value"] else 0.0
            print(f"Parsed summary - Items: {total_items}, Amount: {total_amount}")
            return {"totalItems": total_items, "totalAmount": total_amount}
        
        print("No results found, returning zeros")
        return {"totalItems": 0, "totalAmount": 0.0}

    def add_to_cart(self, client_id: int, product_uri: str, quantity: int = 1) -> bool:
        """Add a product to the cart with specified quantity"""
        client_uri = f"ns:Client{client_id}"
        cart_uri = f"ns:Panier_Client{client_id}"  # Use single cart per client
        
        print(f"Adding to cart - Client: {client_uri}, Cart: {cart_uri}, Product: {product_uri}, Quantity: {quantity}")
        
        # Ensure product_uri is properly formatted
        if not product_uri.startswith('<') and not product_uri.startswith('ns:'):
            if product_uri.startswith('http://'):
                product_uri = f"<{product_uri}>"
            else:
                product_uri = f"ns:{product_uri}"
        
        print(f"Formatted product URI: {product_uri}")
        
        # First, get product price for cart amount calculation
        price_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?prix WHERE {{
            {product_uri} ns:aPrix ?prix .
        }}
        """
        print(f"Price query: {price_query}")
        price_results = self._execute_query(price_query)
        print(f"Price results: {price_results}")
        product_price = 0
        if price_results and len(price_results) > 0:
            product_price = float(price_results[0]["prix"]["value"])
        print(f"Product price: {product_price}")

        # Check if cart already exists, if not create it
        cart_check_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        ASK WHERE {{
            {client_uri} ns:aPasseCommande {cart_uri} .
            {cart_uri} a ns:Panier .
        }}
        """
        print(f"Cart check query: {cart_check_query}")
        cart_exists = self._execute_query(cart_check_query)
        print(f"Cart exists result: {cart_exists}")
        
        if not cart_exists or not cart_exists.get('boolean', False):
            print("Creating new cart...")
            # Create cart if it doesn't exist
            create_cart_query = f"""
            PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
            INSERT DATA {{
                {cart_uri} a ns:Panier .
                {client_uri} ns:aPasseCommande {cart_uri} .
            }}
            """
            print(f"Create cart query: {create_cart_query}")
            create_result = self._execute_query(create_cart_query, is_update=True)
            print(f"Create cart result: {create_result}")

        # Add product to cart with quantity as a property
        print(f"Adding product to cart with quantity {quantity}...")
        
        # Check if product already exists in cart
        check_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?cartItem ?currentQuantity WHERE {{
            ?cartItem ns:inCart {cart_uri} ;
                     ns:refersToProduct {product_uri} ;
                     ns:hasQuantity ?currentQuantity .
        }}
        """
        
        print(f"Check existing product query: {check_query}")
        existing_results = self._execute_query(check_query)
        print(f"Existing product results: {existing_results}")
        
        if existing_results and len(existing_results) > 0:
            # Product exists, update quantity
            existing_item = existing_results[0]["cartItem"]["value"]
            current_qty = int(existing_results[0]["currentQuantity"]["value"])
            new_qty = current_qty + quantity
            
            update_query = f"""
            PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
            DELETE {{
                <{existing_item}> ns:hasQuantity {current_qty} .
            }}
            INSERT {{
                <{existing_item}> ns:hasQuantity {new_qty} .
            }}
            WHERE {{
                <{existing_item}> ns:hasQuantity {current_qty} .
            }}
            """
            print(f"Update quantity query: {update_query}")
            result = self._execute_query(update_query, is_update=True)
            print(f"Update result: {result}")
            return result is not None
        else:
            # Product doesn't exist, create new cart item
            item_id = f"CartItem_{uuid.uuid4().hex[:8]}"
            
            insert_query = f"""
            PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
            INSERT DATA {{
                {cart_uri} ns:aContientProduit {product_uri} .
                ns:{item_id} a ns:CartItem ;
                           ns:refersToProduct {product_uri} ;
                           ns:inCart {cart_uri} ;
                           ns:hasQuantity {quantity} .
            }}
            """
            print(f"Insert new product query: {insert_query}")
            
            result = self._execute_query(insert_query, is_update=True)
            print(f"Insert result: {result}")
            return result is not None

    def remove_from_cart(self, client_id: int, product_uri: str) -> bool:
        """Remove a product from the cart"""
        client_uri = f"ns:Client{client_id}"
        cart_uri = f"ns:Panier_Client{client_id}"  # Use single cart per client
        
        # Ensure product_uri is properly formatted
        if not product_uri.startswith('<') and not product_uri.startswith('ns:'):
            if product_uri.startswith('http://'):
                product_uri = f"<{product_uri}>"
            else:
                product_uri = f"ns:{product_uri}"

        delete_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        DELETE WHERE {{
            {cart_uri} ns:aContientProduit {product_uri} .
        }}
        """
        
        result = self._execute_query(delete_query, is_update=True)
        return result is not None

    def update_cart_quantity(self, client_id: int, product_uri: str, new_quantity: int) -> bool:
        """Update the quantity of a product in the cart"""
        if new_quantity < 1:
            return False
            
        cart_uri = f"ns:Panier_Client{client_id}"
        
        # Ensure product_uri is properly formatted
        if not product_uri.startswith('<') and not product_uri.startswith('ns:'):
            if product_uri.startswith('http://'):
                product_uri = f"<{product_uri}>"
            else:
                product_uri = f"ns:{product_uri}"
        
        print(f"Updating quantity for product {product_uri} to {new_quantity} in cart {cart_uri}")
        
        # Update the quantity property of the existing cart item
        update_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        DELETE {{
            ?cartItem ns:hasQuantity ?oldQuantity .
        }}
        INSERT {{
            ?cartItem ns:hasQuantity {new_quantity} .
        }}
        WHERE {{
            ?cartItem ns:inCart {cart_uri} ;
                     ns:refersToProduct {product_uri} ;
                     ns:hasQuantity ?oldQuantity .
        }}
        """
        
        print(f"Update quantity query: {update_query}")
        
        result = self._execute_query(update_query, is_update=True)
        print(f"Update quantity result: {result}")
        
        return result is not None

    def clear_cart(self, client_id: int) -> bool:
        """Clear all items from the cart"""
        client_uri = f"ns:Client{client_id}"
        cart_uri = f"ns:Panier_Client{client_id}"  # Use single cart per client

    def clear_cart(self, client_id: int) -> bool:
        """Clear all items from the cart for a specific client"""
        cart_uri = f"ns:Panier_Client{client_id}"
        
        query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        DELETE {{
            ?cartItem ?p ?o .
        }}
        WHERE {{
            ?cartItem ns:inCart {cart_uri} ;
                     ?p ?o .
        }}
        """
        
        return self._execute_query(query, is_update=True)

    def create_order_from_cart(self, client_id: int) -> Dict:
        """Convert cart to order (Commande)"""
        # Get cart summary first
        cart_summary = self.get_cart_summary(client_id)
        
        if cart_summary["totalItems"] == 0:
            return {"success": False, "message": "Cart is empty"}
        
        # Generate unique order ID
        order_id = f"Commande_{uuid.uuid4().hex[:8]}"
        order_uri = f"<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#{order_id}>"
        client_uri = f"<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Client{client_id}>"
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Create order
        insert_order_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        
        INSERT DATA {{
            {order_uri} a ns:Commande .
            {order_uri} ns:aAppartientAClient {client_uri} .
            {order_uri} ns:aDateCommande "{current_date}"^^<http://www.w3.org/2001/XMLSchema#date> .
            {order_uri} ns:aMontantTotal {cart_summary["totalAmount"]} .
            {order_uri} ns:aNumero "{order_id}" .
            {order_uri} ns:aQuantite {cart_summary["totalItems"]} .
            {order_uri} ns:aReduction 0 .
            {order_uri} ns:aStatut "En cours" .
        }}
        """
        
        # Execute order creation
        order_result = self._execute_query(insert_order_query, is_update=True)
        
        if order_result is not None:
            # Clear cart after successful order creation
            self.clear_cart(client_id)
            return {
                "success": True, 
                "order_id": order_id,
                "total_amount": cart_summary["totalAmount"],
                "total_items": cart_summary["totalItems"]
            }
        
        return {"success": False, "message": "Failed to create order"}