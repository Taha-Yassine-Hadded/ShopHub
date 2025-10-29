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


def extraire_entites_client(question: str) -> Dict:
    """
    Analyse une question en langage naturel et extrait les entités pour les clients.
    
    Args:
        question: La question de l'utilisateur en français
        
    Returns:
        Un dictionnaire contenant les entités extraites (nom, prénom, pays, ville, email, etc.)
    """
    question_lower = question.lower().strip()
    
    entites = {
        "nom_client": None,
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
    
    # Extraire les noms propres (potentiels noms/prénoms de clients)
    if nlp:
        doc = nlp(question)
        for ent in doc.ents:
            if ent.label_ == "PER":  # Personne
                # Si c'est la première personne trouvée, c'est peut-être le nom ou prénom
                if not entites["nom_client"]:
                    entites["nom_client"] = ent.text.lower()
                    break
    
    # Extraire la ville si mentionnée
    villes_patterns = [
        r"(?:à|de|en)\s+([A-Z][a-zéèêàâôù]+(?:\s+[A-Z][a-zéèêàâôù]+)?)",
        r"ville\s+de\s+([A-Z][a-zéèêàâôù]+)",
        r"client\s+de\s+([A-Z][a-zéèêàâôù]+)"
    ]
    
    for pattern in villes_patterns:
        match = re.search(pattern, question)
        if match:
            entites["ville"] = match.group(1).lower()
            break
    
    return entites


def construire_requete_sparql_client(entites: Dict) -> str:
    """
    Construit une requête SPARQL pour rechercher des clients.
    
    Args:
        entites: Dictionnaire contenant les entités extraites
        
    Returns:
        La requête SPARQL construite
    """
    # Template de base
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?client ?adresse ?telephone ?email ?pays
        WHERE {
            ?client a ns:Client .
    """
    
    filters = []
    
    # Filtre par pays
    if entites["pays"]:
        # Utiliser FILTER avec regex pour matcher le pays (insensible à la casse)
        pays_capitalise = entites["pays"].capitalize()
        filters.append(f'        FILTER (regex(?pays, "{pays_capitalise}", "i"))')
    
    # Filtre par nom de client
    if entites["nom_client"]:
        # Utiliser FILTER avec regex sur l'URI du client
        nom_client = entites["nom_client"].capitalize()
        filters.append(f'        FILTER (regex(str(?client), "{nom_client}", "i"))')
    
    # Filtre par ville (dans l'adresse)
    if entites["ville"]:
        ville_capitalise = entites["ville"].capitalize()
        filters.append(f'        FILTER (regex(?adresse, "{ville_capitalise}", "i"))')
    
    # Ajouter les propriétés OPTIONAL
    query += """
            OPTIONAL { ?client ns:aAdresse ?adresse . }
            OPTIONAL { ?client ns:aTéléphone ?telephone . }
            OPTIONAL { ?client ns:aEmail ?email . }
            OPTIONAL { ?client ns:aPays ?pays . }
    """
    
    # Ajouter les filtres
    if filters:
        query += "\n" + "\n".join(filters) + "\n"
    
    query += "        }\n    "
    
    return query


def analyser_question_client(question: str) -> Dict:
    """
    Fonction principale qui analyse une question sur les clients.
    
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
    entites = extraire_entites_client(question)
    
    # Construire la requête SPARQL
    sparql_query = construire_requete_sparql_client(entites)
    
    return {
        "entites": entites,
        "sparql_query": sparql_query,
        "question_originale": question
    }


# Test de la fonction (pour développement)
if __name__ == "__main__":
    # Exemples de questions
    questions_test = [
        "Quels sont les clients en Tunisie ?",
        "Montre-moi les clients de Paris",
        "Client Jean Dupont",
        "Liste des clients français",
        "Cherche client en France",
        "Clients de Lyon"
    ]
    
    print("=== TEST DU MODULE NLP CLIENTS ===\n")
    for q in questions_test:
        print(f"Question: {q}")
        resultat = analyser_question_client(q)
        print(f"Entités: {resultat['entites']}")
        print(f"SPARQL:\n{resultat['sparql_query']}")
        print("-" * 80)

