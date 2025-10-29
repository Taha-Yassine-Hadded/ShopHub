from SPARQLWrapper import SPARQLWrapper, JSON, POST
from datetime import datetime
import uuid
from typing import Dict, List, Optional

class OrderService:
    def __init__(self, query_endpoint: str = "http://localhost:3030/SmartCom/query", 
                 update_endpoint: str = "http://localhost:3030/SmartCom/update"):
        self.query_endpoint = query_endpoint
        self.update_endpoint = update_endpoint
        
    def _execute_query(self, query: str, is_update: bool = False) -> Optional[List[Dict]]:
        """Execute SPARQL query and return results"""
        try:
            # Use different endpoints for query vs update operations
            endpoint = self.update_endpoint if is_update else self.query_endpoint
            sparql = SPARQLWrapper(endpoint)
            sparql.setQuery(query)
            
            if is_update:
                sparql.setMethod(POST)
                sparql.query()
                return True
            else:
                sparql.setReturnFormat(JSON)
                results = sparql.query().convert()
                
                if "boolean" in results:
                    return results["boolean"]
                elif "results" in results and "bindings" in results["results"]:
                    return results["results"]["bindings"]
                return []
        except Exception as e:
            print(f"SPARQL query error: {e}")
            return None

    def create_order_from_cart(self, client_id: int, order_details: Dict) -> Dict:
        """Create an order from cart items with customer details"""
        try:
            # Generate unique order ID
            order_id = str(uuid.uuid4())[:8]
            order_uri = f"ns:Commande_{order_id}"
            client_uri = f"ns:Client{client_id}"
            cart_uri = f"ns:Panier_Client{client_id}"
            
            print(f"Creating order {order_uri} for client {client_uri}")
            
            # Get cart items first
            cart_items_query = f"""
            PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
            SELECT ?produit ?quantity ?prix WHERE {{
                ?cartItem ns:inCart {cart_uri} ;
                         ns:refersToProduct ?produit ;
                         ns:hasQuantity ?quantity .
                ?produit ns:aPrix ?prix .
            }}
            """
            
            cart_items = self._execute_query(cart_items_query)
            if not cart_items:
                return {"success": False, "message": "Cart is empty"}
            
            # Calculate totals
            total_items = sum(int(item.get("quantity", {}).get("value", 0)) for item in cart_items)
            total_amount = sum(
                int(item.get("quantity", {}).get("value", 0)) * 
                float(item.get("prix", {}).get("value", 0)) 
                for item in cart_items
            )
            
            # Create order with all details
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            order_creation_query = f"""
            PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
            INSERT DATA {{
                {order_uri} a ns:Commande ;
                           ns:aCommandeClient {client_uri} ;
                           ns:aDateCommande "{current_date}"^^<http://www.w3.org/2001/XMLSchema#date> ;
                           ns:aMontantTotal {total_amount} ;
                           ns:aNombreArticles {total_items} ;
                           ns:aStatutCommande "En cours" ;
                           ns:aAdresseLivraison "{order_details.get('delivery_address', '')}" ;
                           ns:aTelephoneClient "{order_details.get('phone', '')}" ;
                           ns:aEmailClient "{order_details.get('email', '')}" ;
                           ns:aNomClient "{order_details.get('full_name', '')}" .
            }}
            """
            
            print(f"Order creation query: {order_creation_query}")
            
            # Execute order creation
            order_result = self._execute_query(order_creation_query, is_update=True)
            if not order_result:
                return {"success": False, "message": "Failed to create order"}
            
            # Add order items
            for item in cart_items:
                product_uri = item.get("produit", {}).get("value", "")
                quantity = int(item.get("quantity", {}).get("value", 0))
                price = float(item.get("prix", {}).get("value", 0))
                
                # Create order item
                order_item_id = str(uuid.uuid4())[:8]
                order_item_uri = f"ns:ArticleCommande_{order_item_id}"
                
                order_item_query = f"""
                PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
                INSERT DATA {{
                    {order_item_uri} a ns:ArticleCommande ;
                                    ns:dansCommande {order_uri} ;
                                    ns:refereAuProduit <{product_uri}> ;
                                    ns:aQuantiteCommandee {quantity} ;
                                    ns:aPrixUnitaire {price} ;
                                    ns:aSousTotal {quantity * price} .
                }}
                """
                
                self._execute_query(order_item_query, is_update=True)
            
            return {
                "success": True,
                "message": "Order created successfully",
                "order_id": order_id,
                "order_uri": order_uri,
                "total_amount": total_amount,
                "total_items": total_items,
                "order_details": order_details
            }
            
        except Exception as e:
            print(f"Error creating order: {e}")
            return {"success": False, "message": f"Error creating order: {str(e)}"}

    def get_order_details(self, order_id: str) -> Optional[Dict]:
        """Get order details by order ID"""
        order_uri = f"ns:Commande_{order_id}"
        
        query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?client ?date ?montant ?articles ?statut ?adresse ?telephone ?email ?nom WHERE {{
            {order_uri} ns:aCommandeClient ?client ;
                       ns:aDateCommande ?date ;
                       ns:aMontantTotal ?montant ;
                       ns:aNombreArticles ?articles ;
                       ns:aStatutCommande ?statut ;
                       ns:aAdresseLivraison ?adresse ;
                       ns:aTelephoneClient ?telephone ;
                       ns:aEmailClient ?email ;
                       ns:aNomClient ?nom .
        }}
        """
        
        results = self._execute_query(query)
        if results and len(results) > 0:
            result = results[0]
            return {
                "order_id": order_id,
                "client": result.get("client", {}).get("value", ""),
                "date": result.get("date", {}).get("value", ""),
                "total_amount": float(result.get("montant", {}).get("value", 0)),
                "total_items": int(result.get("articles", {}).get("value", 0)),
                "status": result.get("statut", {}).get("value", ""),
                "delivery_address": result.get("adresse", {}).get("value", ""),
                "phone": result.get("telephone", {}).get("value", ""),
                "email": result.get("email", {}).get("value", ""),
                "full_name": result.get("nom", {}).get("value", "")
            }
        return None

    def get_client_orders(self, client_id: int) -> List[Dict]:
        """Get all orders for a specific client"""
        client_uri = f"ns:Client{client_id}"
        
        query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?commande ?date ?montant ?articles ?statut WHERE {{
            ?commande ns:aCommandeClient {client_uri} ;
                     ns:aDateCommande ?date ;
                     ns:aMontantTotal ?montant ;
                     ns:aNombreArticles ?articles ;
                     ns:aStatutCommande ?statut .
        }}
        ORDER BY DESC(?date)
        """
        
        results = self._execute_query(query)
        orders = []
        
        if results:
            for result in results:
                order_uri = result.get("commande", {}).get("value", "")
                order_id = order_uri.split("_")[-1] if "_" in order_uri else order_uri
                
                orders.append({
                    "order_id": order_id,
                    "order_uri": order_uri,
                    "date": result.get("date", {}).get("value", ""),
                    "total_amount": float(result.get("montant", {}).get("value", 0)),
                    "total_items": int(result.get("articles", {}).get("value", 0)),
                    "status": result.get("statut", {}).get("value", "")
                })
        
        return orders
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order by updating its status"""
        try:
            order_uri = f"ns:Commande_{order_id}"
            
            # First check if order exists and can be cancelled
            check_query = f"""
            PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
            SELECT ?statut WHERE {{
                {order_uri} ns:aStatutCommande ?statut .
            }}
            """
            
            results = self._execute_query(check_query)
            if not results:
                return {"success": False, "message": "Order not found"}
            
            current_status = results[0].get("statut", {}).get("value", "").lower()
            
            # Check if order can be cancelled
            cancelable_statuses = ["en cours", "pending", "confirmée", "confirmed"]
            if current_status not in cancelable_statuses:
                return {"success": False, "message": "Order cannot be cancelled"}
            
            # Update order status to cancelled
            update_query = f"""
            PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
            DELETE {{ {order_uri} ns:aStatutCommande ?oldStatus }}
            INSERT {{ {order_uri} ns:aStatutCommande "Annulée" }}
            WHERE {{ {order_uri} ns:aStatutCommande ?oldStatus }}
            """
            
            result = self._execute_query(update_query, is_update=True)
            if result:
                return {"success": True, "message": "Order cancelled successfully"}
            else:
                return {"success": False, "message": "Failed to cancel order"}
                
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return {"success": False, "message": f"Error cancelling order: {str(e)}"}
    
    def get_all_orders(self) -> List[Dict]:
        """Get all orders in the system"""
        query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?commande ?client ?date ?montant ?articles ?statut ?adresse ?telephone ?email ?nom WHERE {
            ?commande a ns:Commande ;
                     ns:aCommandeClient ?client ;
                     ns:aDateCommande ?date ;
                     ns:aMontantTotal ?montant ;
                     ns:aNombreArticles ?articles ;
                     ns:aStatutCommande ?statut ;
                     ns:aAdresseLivraison ?adresse ;
                     ns:aTelephoneClient ?telephone ;
                     ns:aEmailClient ?email ;
                     ns:aNomClient ?nom .
        }
        ORDER BY DESC(?date)
        """
        
        results = self._execute_query(query)
        orders = []
        
        if results:
            for result in results:
                order_uri = result.get("commande", {}).get("value", "")
                order_id = order_uri.split("_")[-1] if "_" in order_uri else order_uri
                
                orders.append({
                    "id": order_id,
                    "order_id": order_id,
                    "order_uri": order_uri,
                    "client": result.get("client", {}).get("value", ""),
                    "order_date": result.get("date", {}).get("value", ""),
                    "created_at": result.get("date", {}).get("value", ""),
                    "total_amount": float(result.get("montant", {}).get("value", 0)),
                    "total_items": int(result.get("articles", {}).get("value", 0)),
                    "status": result.get("statut", {}).get("value", ""),
                    "delivery_address": result.get("adresse", {}).get("value", ""),
                    "phone": result.get("telephone", {}).get("value", ""),
                    "email": result.get("email", {}).get("value", ""),
                    "full_name": result.get("nom", {}).get("value", "")
                })
        
        return orders