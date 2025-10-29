from fastapi import APIRouter
from SPARQLWrapper import SPARQLWrapper, JSON
from pydantic import BaseModel, Field
from typing import Optional

# Créer un router pour les clients
router = APIRouter()

# Configurations de connexion à Fuseki
sparql_query = SPARQLWrapper("http://localhost:3030/SmartCom/query")
sparql_update = SPARQLWrapper("http://localhost:3030/SmartCom/update")

# ==================== MODÈLES PYDANTIC ====================

class ClientInput(BaseModel):
    nom: str
    prenom: str = ""
    adresse: str = ""
    telephone: str = ""
    email: str = ""
    pays: str = ""

class ClientUpdate(BaseModel):
    client_uri: str
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    pays: Optional[str] = None

# ==================== ENDPOINTS ====================

# 1. READ ALL - Lire tous les clients
@router.get("/clients")
async def get_clients():
    """Récupérer la liste de tous les clients"""
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?client ?adresse ?telephone ?email ?pays
        WHERE {
            ?client a ns:Client .
            OPTIONAL { ?client ns:aAdresse ?adresse . }
            OPTIONAL { ?client ns:aTéléphone ?telephone . }
            OPTIONAL { ?client ns:aEmail ?email . }
            OPTIONAL { ?client ns:aPays ?pays . }
        }
    """
    
    print("Générée SPARQL Query:", query)
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        return {"clients": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

# 2. CREATE - Ajouter un client
@router.post("/add-client")
async def add_client(client: ClientInput):
    """Ajouter un nouveau client dans la base de données"""
    # Générer un URI unique pour le client
    client_nom = f"{client.nom}_{client.prenom}".replace(" ", "_").replace("'", "")
    client_uri = f"<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#{client_nom}>"
    
    # Construire la requête INSERT
    insert_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        INSERT DATA {{
            {client_uri} a ns:Client .
            {client_uri} ns:aAdresse "{client.adresse}"^^xsd:string .
            {client_uri} ns:aTéléphone "{client.telephone}"^^xsd:string .
            {client_uri} ns:aEmail "{client.email}"^^xsd:string .
            {client_uri} ns:aPays "{client.pays}"^^xsd:string .
        }}
    """
    
    print("Générée SPARQL Insert Query:", insert_query)
    sparql_update.setQuery(insert_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Client ajouté avec succès", "client_uri": client_uri}
    except Exception as e:
        return {"error": str(e)}

# 3. READ - Lire les détails d'un client
@router.get("/client")
async def get_client(client_uri: str):
    """Récupérer les détails d'un client spécifique"""
    query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?adresse ?telephone ?email ?pays
        WHERE {{
            <{client_uri}> a ns:Client .
            OPTIONAL {{ <{client_uri}> ns:aAdresse ?adresse . }}
            OPTIONAL {{ <{client_uri}> ns:aTéléphone ?telephone . }}
            OPTIONAL {{ <{client_uri}> ns:aEmail ?email . }}
            OPTIONAL {{ <{client_uri}> ns:aPays ?pays . }}
        }}
    """
    
    print("Générée SPARQL Query:", query)
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        return {"client": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

# 4. UPDATE - Modifier un client
@router.put("/update-client")
async def update_client(client: ClientUpdate):
    """Modifier les informations d'un client existant"""
    # Construire les clauses DELETE et INSERT dynamiquement
    delete_clauses = []
    insert_clauses = []
    where_clauses = []
    
    if client.adresse is not None:
        delete_clauses.append(f"<{client.client_uri}> ns:aAdresse ?oldAdresse .")
        insert_clauses.append(f"<{client.client_uri}> ns:aAdresse \"{client.adresse}\"^^xsd:string .")
        where_clauses.append(f"OPTIONAL {{ <{client.client_uri}> ns:aAdresse ?oldAdresse . }}")
    
    if client.telephone is not None:
        delete_clauses.append(f"<{client.client_uri}> ns:aTéléphone ?oldTelephone .")
        insert_clauses.append(f"<{client.client_uri}> ns:aTéléphone \"{client.telephone}\"^^xsd:string .")
        where_clauses.append(f"OPTIONAL {{ <{client.client_uri}> ns:aTéléphone ?oldTelephone . }}")
    
    if client.email is not None:
        delete_clauses.append(f"<{client.client_uri}> ns:aEmail ?oldEmail .")
        insert_clauses.append(f"<{client.client_uri}> ns:aEmail \"{client.email}\"^^xsd:string .")
        where_clauses.append(f"OPTIONAL {{ <{client.client_uri}> ns:aEmail ?oldEmail . }}")
    
    if client.pays is not None:
        delete_clauses.append(f"<{client.client_uri}> ns:aPays ?oldPays .")
        insert_clauses.append(f"<{client.client_uri}> ns:aPays \"{client.pays}\"^^xsd:string .")
        where_clauses.append(f"OPTIONAL {{ <{client.client_uri}> ns:aPays ?oldPays . }}")
    
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
        return {"message": "Client modifié avec succès"}
    except Exception as e:
        return {"error": str(e)}

# 5. DELETE - Supprimer un client
@router.delete("/delete-client")
async def delete_client(client_uri: str):
    """Supprimer un client de la base de données"""
    delete_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        DELETE WHERE {{
            <{client_uri}> ?p ?o .
        }}
    """
    
    print("Générée SPARQL Delete Query:", delete_query)
    sparql_update.setQuery(delete_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Client supprimé avec succès"}
    except Exception as e:
        return {"error": str(e)}

