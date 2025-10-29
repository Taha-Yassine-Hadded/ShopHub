import spacy
import re
from typing import Dict, List, Optional

# Charger le modèle français de SpaCy
try:
    nlp = spacy.load("fr_core_news_sm")
except OSError:
    print("Le modèle français n'est pas installé. Exécutez: python -m spacy download fr_core_news_sm")
    nlp = None

# Dictionnaire des catégories et leurs variantes
CATEGORIES = {
    "lave-vaisselle": ["lave-vaisselle", "lave vaisselle", "lavevaisselle", "lave-vaisselles"],
    "lave-linge": ["lave-linge", "lave linge", "lavelinge", "machine à laver", "lave-linges"],
    "réfrigérateurs": ["réfrigérateur", "réfrigérateurs", "frigo", "frigidaire", "réfrigérateur"],
    "aspirateurs": ["aspirateur", "aspirateurs", "aspiro"],
    "cuisinières": ["cuisinière", "cuisinières", "cuisiniere", "cuisinieres"],
    "micro-ondes": ["micro-onde", "micro-ondes", "microonde", "microondes", "micro onde"],
    "sèche-linge": ["sèche-linge", "sèche linge", "sechelinge", "sécheur", "sèche-linges"]
}

# Dictionnaire des marques
MARQUES = {
    "samsung": ["samsung"],
    "lg": ["lg"],
    "beko": ["beko"],
    "bosch": ["bosch"],
    "whirlpool": ["whirlpool"]
}

# Mapping vers les URIs de l'ontologie
CATEGORY_URIS = {
    "lave-vaisselle": "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Lave-vaisselle",
    "lave-linge": "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Lave-linge",
    "réfrigérateurs": "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Réfrigérateurs",
    "aspirateurs": "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Aspirateurs",
    "cuisinières": "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Cuisinières",
    "micro-ondes": "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Micro-ondes",
    "sèche-linge": "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Sèche-linge"
}

MARQUE_URIS = {
    "samsung": "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Samsung",
    "lg": "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#LG",
    "beko": "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Beko",
    "bosch": "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Bosch",
    "whirlpool": "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Whirlpool"
}


def extraire_entites_stock(question: str) -> Dict:
    """
    Analyse une question en langage naturel et extrait les entités pour le stock.
    
    Args:
        question: La question de l'utilisateur en français
        
    Returns:
        Un dictionnaire contenant les entités extraites (catégorie, marque, quantité de stock, etc.)
    """
    question_lower = question.lower().strip()
    
    entites = {
        "categorie": None,
        "categorie_uri": None,
        "marque": None,
        "marque_uri": None,
        "stock_min": None,
        "stock_max": None,
        "statut_stock": None,  # "rupture", "stock_faible", "en_stock"
        "intention": "recherche"  # recherche, liste, alerte
    }
    
    # Détecter l'intention
    if any(mot in question_lower for mot in ["tous", "liste", "affiche", "montre-moi tous"]):
        entites["intention"] = "liste"
    elif any(mot in question_lower for mot in ["alerte", "rupture", "stock faible", "stock-faible"]):
        entites["intention"] = "alerte"
    
    # Détecter le statut du stock
    if any(mot in question_lower for mot in ["rupture", "en rupture", "en-rupture", "épuisé", "épuisée"]):
        entites["statut_stock"] = "rupture"
    elif any(mot in question_lower for mot in ["stock faible", "stock-faible", "faible", "critique", "bas", "basse"]):
        entites["statut_stock"] = "stock_faible"
    elif any(mot in question_lower for mot in ["disponible", "en stock", "en-stock", "en stock", "disponibles"]):
        entites["statut_stock"] = "en_stock"
    
    # Extraire la catégorie
    for categorie_key, variantes in CATEGORIES.items():
        for variante in variantes:
            if variante in question_lower:
                entites["categorie"] = categorie_key
                entites["categorie_uri"] = CATEGORY_URIS.get(categorie_key)
                break
        if entites["categorie"]:
            break
    
    # Extraire la marque
    for marque_key, variantes in MARQUES.items():
        for variante in variantes:
            if variante in question_lower:
                entites["marque"] = marque_key
                entites["marque_uri"] = MARQUE_URIS.get(marque_key)
                break
        if entites["marque"]:
            break
    
    # Extraire les quantités de stock
    # Patterns: "moins de X unités", "inférieur à X", "< X", "maximum X"
    stock_patterns = [
        r"(?:moins de|inférieur[e]? à|au maximum|maximum|stock <|stock inférieur à)\s*(\d+)",
        r"(?:plus de|supérieur[e]? à|au minimum|minimum|stock >|stock supérieur à)\s*(\d+)",
        r"(?:entre|de)\s*(\d+)\s*(?:et|à)\s*(\d+)\s*(?:unités?)?",
        r"(\d+)\s*(?:unités?|unités disponibles)"
    ]
    
    for pattern in stock_patterns:
        match = re.search(pattern, question_lower)
        if match:
            if "moins" in question_lower or "inférieur" in question_lower or "<" in question_lower or "max" in question_lower:
                entites["stock_max"] = int(match.group(1))
            elif "plus" in question_lower or "supérieur" in question_lower or ">" in question_lower or "min" in question_lower:
                entites["stock_min"] = int(match.group(1))
            elif "entre" in question_lower or ("de" in question_lower and "et" in question_lower):
                if len(match.groups()) >= 2:
                    entites["stock_min"] = int(match.group(1))
                    entites["stock_max"] = int(match.group(2))
            else:
                entites["stock_max"] = int(match.group(1))
            break
    
    return entites


def construire_requete_sparql_stock(entites: Dict) -> str:
    """
    Construit une requête SPARQL pour rechercher des produits en stock.
    
    Args:
        entites: Dictionnaire contenant les entités extraites
        
    Returns:
        La requête SPARQL construite
    """
    # Template de base
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?produit ?description ?prix ?stock ?categorie ?marque ?image
        WHERE {
            ?produit a ns:Produit .
    """
    
    filters = []
    
    # Ajouter le filtre de catégorie
    if entites["categorie_uri"]:
        filters.append(f"        ?produit ns:aSousCatégorie <{entites['categorie_uri']}> .")
    
    # Ajouter le filtre de marque
    if entites["marque_uri"]:
        filters.append(f"        ?produit ns:aProduitMarque <{entites['marque_uri']}> .")
    
    # Toujours récupérer les propriétés optionnelles
    query += "\n".join(filters) if filters else ""
    query += """
            OPTIONAL { ?produit ns:aDescription ?description . }
            OPTIONAL { ?produit ns:aPrix ?prix . }
            OPTIONAL { ?produit ns:aStockDisponible ?stock . }
            OPTIONAL { ?produit ns:aSousCatégorie ?categorie . }
            OPTIONAL { ?produit ns:aProduitMarque ?marque . }
            OPTIONAL { ?produit ns:aImage ?image . }
    """
    
    # Ajouter les filtres de stock (quantité)
    stock_filters = []
    
    # Filtre par statut
    if entites["statut_stock"] == "rupture":
        stock_filters.append("?stock = 0")
    elif entites["statut_stock"] == "stock_faible":
        stock_filters.append("?stock < 10 && ?stock > 0")
    elif entites["statut_stock"] == "en_stock":
        stock_filters.append("?stock > 0")
    
    # Filtres de quantité
    if entites["stock_min"] is not None:
        stock_filters.append(f"?stock >= {entites['stock_min']}")
    if entites["stock_max"] is not None:
        stock_filters.append(f"?stock <= {entites['stock_max']}")
    
    if stock_filters:
        query += "            FILTER (" + " && ".join(stock_filters) + ")\n"
    
    query += "        }\n    "
    
    return query


def analyser_question_stock(question: str) -> Dict:
    """
    Fonction principale qui analyse une question sur le stock et retourne les entités et la requête SPARQL.
    
    Args:
        question: La question de l'utilisateur en français
        
    Returns:
        Un dictionnaire contenant les entités extraites et la requête SPARQL générée
    """
    if not nlp:
        return {
            "error": "Le modèle NLP n'est pas chargé",
            "entites": {},
            "sparql_query": ""
        }
    
    # Extraire les entités
    entites = extraire_entites_stock(question)
    
    # Construire la requête SPARQL
    sparql_query = construire_requete_sparql_stock(entites)
    
    return {
        "entites": entites,
        "sparql_query": sparql_query,
        "question_originale": question
    }


# Test de la fonction (pour développement)
if __name__ == "__main__":
    # Exemples de questions
    questions_test = [
        "Quels sont les produits en rupture de stock ?",
        "Montre-moi le stock des lave-linge Samsung",
        "Produits avec stock faible",
        "Stock disponible pour les réfrigérateurs",
        "Tous les produits avec un stock supérieur à 50 unités",
        "Produits LG avec moins de 10 unités en stock",
        "Alerte stock : produits en rupture",
        "Liste des lave-vaisselle en stock"
    ]
    
    print("=== TEST DU MODULE NLP STOCK ===\n")
    for q in questions_test:
        print(f"Question: {q}")
        resultat = analyser_question_stock(q)
        print(f"Entités: {resultat['entites']}")
        print(f"SPARQL:\n{resultat['sparql_query']}")
        print("-" * 80)

