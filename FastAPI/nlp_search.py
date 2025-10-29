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


def extraire_entites(question: str) -> Dict:
    """
    Analyse une question en langage naturel et extrait les entités pertinentes.
    
    Args:
        question: La question de l'utilisateur en français
        
    Returns:
        Un dictionnaire contenant les entités extraites (catégorie, marque, prix, etc.)
    """
    question_lower = question.lower().strip()
    
    entites = {
        "categorie": None,
        "categorie_uri": None,
        "marque": None,
        "marque_uri": None,
        "prix_min": None,
        "prix_max": None,
        "intention": "recherche"  # recherche, filtrage, liste
    }
    
    # Détecter l'intention
    if any(mot in question_lower for mot in ["tous", "liste", "affiche", "montre-moi tous"]):
        entites["intention"] = "liste"
    elif any(mot in question_lower for mot in ["filtre", "avec", "ayant"]):
        entites["intention"] = "filtrage"
    
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
    
    # Extraire le prix
    # Patterns: "moins de X", "inférieur à X", "< X", "maximum X", "prix < X"
    prix_patterns = [
        r"(?:moins de|inférieur[e]? à|max(?:imum)?|<|prix <)\s*(\d+)",
        r"(?:plus de|supérieur[e]? à|>|prix >)\s*(\d+)",
        r"(?:entre|de)\s*(\d+)\s*(?:et|à)\s*(\d+)",
        r"(\d+)\s*(?:euros?|€)"
    ]
    
    for pattern in prix_patterns:
        match = re.search(pattern, question_lower)
        if match:
            if "moins" in question_lower or "inférieur" in question_lower or "<" in question_lower or "max" in question_lower:
                entites["prix_max"] = int(match.group(1))
            elif "plus" in question_lower or "supérieur" in question_lower or ">" in question_lower:
                entites["prix_min"] = int(match.group(1))
            elif "entre" in question_lower or "de" in question_lower:
                if len(match.groups()) >= 2:
                    entites["prix_min"] = int(match.group(1))
                    entites["prix_max"] = int(match.group(2))
            else:
                entites["prix_max"] = int(match.group(1))
            break
    
    return entites


def construire_requete_sparql(entites: Dict) -> str:
    """
    Construit une requête SPARQL à partir des entités extraites.
    
    Args:
        entites: Dictionnaire contenant les entités extraites
        
    Returns:
        La requête SPARQL construite
    """
    # Template de base
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?produit ?description ?prix ?categorie ?marque ?image
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
            OPTIONAL { ?produit ns:aSousCatégorie ?categorie . }
            OPTIONAL { ?produit ns:aProduitMarque ?marque . }
            OPTIONAL { ?produit ns:aImage ?image . }
    """
    
    # Ajouter les filtres de prix
    prix_filters = []
    if entites["prix_min"] is not None:
        prix_filters.append(f"?prix > {entites['prix_min']}")
    if entites["prix_max"] is not None:
        prix_filters.append(f"?prix < {entites['prix_max']}")
    
    if prix_filters:
        query += "            FILTER (" + " && ".join(prix_filters) + ")\n"
    
    query += "        }\n    "
    
    return query


def analyser_question_nlp(question: str) -> Dict:
    """
    Fonction principale qui analyse une question et retourne les entités et la requête SPARQL.
    
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
    entites = extraire_entites(question)
    
    # Construire la requête SPARQL
    sparql_query = construire_requete_sparql(entites)
    
    return {
        "entites": entites,
        "sparql_query": sparql_query,
        "question_originale": question
    }


# Test de la fonction (pour développement)
if __name__ == "__main__":
    # Exemples de questions
    questions_test = [
        "Quels sont les produits de la catégorie lave-vaisselle ?",
        "Montre-moi les réfrigérateurs Samsung",
        "Je cherche des lave-linge avec un prix inférieur à 600 euros",
        "Produits Samsung moins de 500€",
        "Tous les aspirateurs"
    ]
    
    print("=== TEST DU MODULE NLP ===\n")
    for q in questions_test:
        print(f"Question: {q}")
        resultat = analyser_question_nlp(q)
        print(f"Entités: {resultat['entites']}")
        print(f"SPARQL:\n{resultat['sparql_query']}")
        print("-" * 80)

