import spacy
import re
from typing import Dict, List, Optional

# Charger le modèle français de SpaCy
try:
    nlp = spacy.load("fr_core_news_sm")
except OSError:
    print("Le modèle français n'est pas installé. Exécutez: python -m spacy download fr_core_news_sm")
    nlp = None

# Dictionnaire des pays et leurs variantes
PAYS = {
    "tunisie": ["tunisie", "tunisien", "tunisienne", "tunisiens", "tunis"],
    "france": ["france", "français", "française", "paris", "lyon"],
    "allemagne": ["allemagne", "allemand", "allemande", "berlin"],
    "italie": ["italie", "italien", "italienne", "rome"],
    "espagne": ["espagne", "espagnol", "espagnole", "madrid"],
    "maroc": ["maroc", "marocain", "marocaine", "rabat"],
    "algérie": ["algérie", "algérien", "algérienne", "alger"],
    "belgique": ["belgique", "belge", "bruxelles"],
    "suisse": ["suisse", "genève", "zurich"],
    "canada": ["canada", "canadien", "canadienne", "montreal", "toronto"],
    "états-unis": ["états-unis", "usa", "américain", "américaine", "etats-unis"],
    "chine": ["chine", "chinois", "chinoise", "pékin", "beijing"],
    "japon": ["japon", "japonais", "japonaise", "tokyo"],
    "corée": ["corée", "coréen", "coréenne", "séoul", "korea"]
}

# Dictionnaire des noms de fournisseurs connus
FOURNISSEURS_CONNUS = {
    "samsung": ["samsung", "samsung electronics"],
    "lg": ["lg", "lg electronics"],
    "beko": ["beko"],
    "bosch": ["bosch"],
    "whirlpool": ["whirlpool"],
    "siemens": ["siemens"],
    "electrolux": ["electrolux"],
    "miele": ["miele"],
    "haier": ["haier"],
    "panasonic": ["panasonic"]
}


def extraire_entites_fournisseur(question: str) -> Dict:
    """
    Analyse une question en langage naturel et extrait les entités pour les fournisseurs.
    
    Args:
        question: La question de l'utilisateur en français
        
    Returns:
        Un dictionnaire contenant les entités extraites (nom, pays, ville, etc.)
    """
    question_lower = question.lower().strip()
    
    entites = {
        "nom_fournisseur": None,
        "pays": None,
        "ville": None,
        "intention": "recherche"  # recherche, liste
    }
    
    # Détecter l'intention
    if any(mot in question_lower for mot in ["tous", "liste", "affiche", "montre-moi tous"]):
        entites["intention"] = "liste"
    
    # Extraire le pays
    for pays_key, variantes in PAYS.items():
        for variante in variantes:
            if variante in question_lower:
                entites["pays"] = pays_key
                break
        if entites["pays"]:
            break
    
    # Extraire le nom du fournisseur
    for fournisseur_key, variantes in FOURNISSEURS_CONNUS.items():
        for variante in variantes:
            if variante in question_lower:
                entites["nom_fournisseur"] = fournisseur_key
                break
        if entites["nom_fournisseur"]:
            break
    
    # Si pas trouvé dans la liste connue, essayer d'extraire un nom propre
    if not entites["nom_fournisseur"] and nlp:
        doc = nlp(question)
        for ent in doc.ents:
            if ent.label_ == "ORG":  # Organisation
                entites["nom_fournisseur"] = ent.text.lower()
                break
    
    # Extraire la ville si mentionnée
    villes_patterns = [
        r"(?:à|de|en)\s+([A-Z][a-zéèêàâôù]+(?:\s+[A-Z][a-zéèêàâôù]+)?)",
        r"ville\s+de\s+([A-Z][a-zéèêàâôù]+)"
    ]
    
    for pattern in villes_patterns:
        match = re.search(pattern, question)
        if match:
            entites["ville"] = match.group(1).lower()
            break
    
    return entites


def construire_requete_sparql_fournisseur(entites: Dict) -> str:
    """
    Construit une requête SPARQL pour rechercher des fournisseurs.
    
    Args:
        entites: Dictionnaire contenant les entités extraites
        
    Returns:
        La requête SPARQL construite
    """
    # Template de base
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?fournisseur ?adresse ?telephone ?email ?pays
        WHERE {
            ?fournisseur a ns:Fournisseur .
    """
    
    filters = []
    
    # Filtre par pays
    if entites["pays"]:
        # Utiliser FILTER avec regex pour matcher le pays (insensible à la casse)
        pays_capitalise = entites["pays"].capitalize()
        filters.append(f'        FILTER (regex(?pays, "{pays_capitalise}", "i"))')
    
    # Filtre par nom de fournisseur
    if entites["nom_fournisseur"]:
        # Utiliser FILTER avec regex sur l'URI du fournisseur
        nom_fournisseur = entites["nom_fournisseur"].capitalize()
        filters.append(f'        FILTER (regex(str(?fournisseur), "{nom_fournisseur}", "i"))')
    
    # Filtre par ville (dans l'adresse)
    if entites["ville"]:
        ville_capitalise = entites["ville"].capitalize()
        filters.append(f'        FILTER (regex(?adresse, "{ville_capitalise}", "i"))')
    
    # Ajouter les propriétés OPTIONAL
    query += """
            OPTIONAL { ?fournisseur ns:aAdresse ?adresse . }
            OPTIONAL { ?fournisseur ns:aTéléphone ?telephone . }
            OPTIONAL { ?fournisseur ns:aEmail ?email . }
            OPTIONAL { ?fournisseur ns:aPays ?pays . }
    """
    
    # Ajouter les filtres
    if filters:
        query += "\n" + "\n".join(filters) + "\n"
    
    query += "        }\n    "
    
    return query


def analyser_question_fournisseur(question: str) -> Dict:
    """
    Fonction principale qui analyse une question sur les fournisseurs.
    
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
    entites = extraire_entites_fournisseur(question)
    
    # Construire la requête SPARQL
    sparql_query = construire_requete_sparql_fournisseur(entites)
    
    return {
        "entites": entites,
        "sparql_query": sparql_query,
        "question_originale": question
    }


# Test de la fonction (pour développement)
if __name__ == "__main__":
    # Exemples de questions
    questions_test = [
        "Quels sont les fournisseurs en Tunisie ?",
        "Montre-moi les fournisseurs Samsung",
        "Fournisseur Samsung en Tunisie",
        "Liste des fournisseurs français",
        "Cherche fournisseur LG",
        "Fournisseurs de Paris"
    ]
    
    print("=== TEST DU MODULE NLP FOURNISSEURS ===\n")
    for q in questions_test:
        print(f"Question: {q}")
        resultat = analyser_question_fournisseur(q)
        print(f"Entités: {resultat['entites']}")
        print(f"SPARQL:\n{resultat['sparql_query']}")
        print("-" * 80)

