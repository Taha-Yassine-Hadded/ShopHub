from fastapi import APIRouter
from SPARQLWrapper import SPARQLWrapper, JSON
from pydantic import BaseModel, Field
from typing import Optional

# Créer un router pour les fournisseurs
router = APIRouter()

# Configurations de connexion à Fuseki
sparql_query = SPARQLWrapper("http://localhost:3030/SmartCom/query")
sparql_update = SPARQLWrapper("http://localhost:3030/SmartCom/update")

# ==================== MODÈLES PYDANTIC ====================

class FournisseurInput(BaseModel):
    nom: str
    adresse: str = ""
    telephone: str = ""
    email: str = ""
    pays: str = ""

class FournisseurUpdate(BaseModel):
    fournisseur_uri: str
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    pays: Optional[str] = None

# ==================== ENDPOINTS ====================

# 1. READ ALL - Lire tous les fournisseurs
@router.get("/fournisseurs")
async def get_fournisseurs():
    """Récupérer la liste de tous les fournisseurs"""
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?fournisseur ?adresse ?telephone ?email ?pays
        WHERE {
            ?fournisseur a ns:Fournisseur .
            OPTIONAL { ?fournisseur ns:aAdresse ?adresse . }
            OPTIONAL { ?fournisseur ns:aTéléphone ?telephone . }
            OPTIONAL { ?fournisseur ns:aEmail ?email . }
            OPTIONAL { ?fournisseur ns:aPays ?pays . }
        }
    """
    
    print("Générée SPARQL Query:", query)
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        return {"fournisseurs": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

# 2. CREATE - Ajouter un fournisseur
@router.post("/add-fournisseur")
async def add_fournisseur(fournisseur: FournisseurInput):
    """Ajouter un nouveau fournisseur dans la base de données"""
    # Générer un URI unique pour le fournisseur
    fournisseur_nom_sanitized = fournisseur.nom.replace(" ", "_").replace("'", "")
    fournisseur_uri = f"<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#{fournisseur_nom_sanitized}>"
    
    # Construire la requête INSERT
    insert_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        INSERT DATA {{
            {fournisseur_uri} a ns:Fournisseur .
            {fournisseur_uri} ns:aAdresse "{fournisseur.adresse}"^^xsd:string .
            {fournisseur_uri} ns:aTéléphone "{fournisseur.telephone}"^^xsd:string .
            {fournisseur_uri} ns:aEmail "{fournisseur.email}"^^xsd:string .
            {fournisseur_uri} ns:aPays "{fournisseur.pays}"^^xsd:string .
        }}
    """
    
    print("Générée SPARQL Insert Query:", insert_query)
    sparql_update.setQuery(insert_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Fournisseur ajouté avec succès", "fournisseur_uri": fournisseur_uri}
    except Exception as e:
        return {"error": str(e)}

# 3. READ - Lire les détails d'un fournisseur
@router.get("/fournisseur")
async def get_fournisseur(fournisseur_uri: str):
    """Récupérer les détails d'un fournisseur spécifique"""
    query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?adresse ?telephone ?email ?pays
        WHERE {{
            <{fournisseur_uri}> a ns:Fournisseur .
            OPTIONAL {{ <{fournisseur_uri}> ns:aAdresse ?adresse . }}
            OPTIONAL {{ <{fournisseur_uri}> ns:aTéléphone ?telephone . }}
            OPTIONAL {{ <{fournisseur_uri}> ns:aEmail ?email . }}
            OPTIONAL {{ <{fournisseur_uri}> ns:aPays ?pays . }}
        }}
    """
    
    print("Générée SPARQL Query:", query)
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        return {"fournisseur": results["results"]["bindings"]}
    except Exception as e:
        return {"error": str(e)}

# 4. UPDATE - Modifier un fournisseur
@router.put("/update-fournisseur")
async def update_fournisseur(fournisseur: FournisseurUpdate):
    """Modifier les informations d'un fournisseur existant"""
    # Construire les clauses DELETE et INSERT dynamiquement
    delete_clauses = []
    insert_clauses = []
    where_clauses = []
    
    if fournisseur.adresse is not None:
        delete_clauses.append(f"<{fournisseur.fournisseur_uri}> ns:aAdresse ?oldAdresse .")
        insert_clauses.append(f"<{fournisseur.fournisseur_uri}> ns:aAdresse \"{fournisseur.adresse}\"^^xsd:string .")
        where_clauses.append(f"OPTIONAL {{ <{fournisseur.fournisseur_uri}> ns:aAdresse ?oldAdresse . }}")
    
    if fournisseur.telephone is not None:
        delete_clauses.append(f"<{fournisseur.fournisseur_uri}> ns:aTéléphone ?oldTelephone .")
        insert_clauses.append(f"<{fournisseur.fournisseur_uri}> ns:aTéléphone \"{fournisseur.telephone}\"^^xsd:string .")
        where_clauses.append(f"OPTIONAL {{ <{fournisseur.fournisseur_uri}> ns:aTéléphone ?oldTelephone . }}")
    
    if fournisseur.email is not None:
        delete_clauses.append(f"<{fournisseur.fournisseur_uri}> ns:aEmail ?oldEmail .")
        insert_clauses.append(f"<{fournisseur.fournisseur_uri}> ns:aEmail \"{fournisseur.email}\"^^xsd:string .")
        where_clauses.append(f"OPTIONAL {{ <{fournisseur.fournisseur_uri}> ns:aEmail ?oldEmail . }}")
    
    if fournisseur.pays is not None:
        delete_clauses.append(f"<{fournisseur.fournisseur_uri}> ns:aPays ?oldPays .")
        insert_clauses.append(f"<{fournisseur.fournisseur_uri}> ns:aPays \"{fournisseur.pays}\"^^xsd:string .")
        where_clauses.append(f"OPTIONAL {{ <{fournisseur.fournisseur_uri}> ns:aPays ?oldPays . }}")
    
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
        return {"message": "Fournisseur modifié avec succès"}
    except Exception as e:
        return {"error": str(e)}

# 5. DELETE - Supprimer un fournisseur
@router.delete("/delete-fournisseur")
async def delete_fournisseur(fournisseur_uri: str):
    """Supprimer un fournisseur de la base de données"""
    delete_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        DELETE WHERE {{
            <{fournisseur_uri}> ?p ?o .
        }}
    """
    
    print("Générée SPARQL Delete Query:", delete_query)
    sparql_update.setQuery(delete_query)
    sparql_update.method = "POST"
    try:
        sparql_update.query()
        return {"message": "Fournisseur supprimé avec succès"}
    except Exception as e:
        return {"error": str(e)}

