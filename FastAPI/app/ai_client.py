import os
import re
import textwrap
import asyncio
import spacy
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

# --- Load SpaCy NLP model ---
try:
    NLP_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")  # or "fr_core_news_md"
    nlp = spacy.load(NLP_MODEL)
    print(f"✅ SpaCy model '{NLP_MODEL}' loaded successfully.")
except Exception as e:
    print(f"❌ Error loading SpaCy model '{NLP_MODEL}': {e}")
    nlp = None

# --- Ontology prefix ---
PREFIX = "PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>\n"

# --- Utility functions ---
def cleanup_text(text: str) -> str:
    """Removes extra spaces and line breaks."""
    return re.sub(r"\s+", " ", text).strip()


def build_sparql(entity: str, relation: str, question: str) -> str:
    """
    Build SPARQL queries for both explicit (relation/entity)
    and implicit (intent-based) questions.
    """
    question_lower = question.lower()

    # --- Intent: list all products (default or explicit) ---
    if any(keyword in question_lower for keyword in ["liste des produits", "produits", "liste des articles"]):
        return textwrap.dedent(f"""
        {PREFIX}
        SELECT ?produit ?nom ?prix ?marque WHERE {{
            ?produit a ns:Produit .
            OPTIONAL {{ ?produit ns:aNom ?nom. }}
            OPTIONAL {{ ?produit ns:aPrix ?prix. }}
            OPTIONAL {{ ?produit ns:aProduitMarque ?marque. }}
        }}
        """)

    # --- Intent: list all categories ---
    if any(keyword in question_lower for keyword in ["catégories", "types de produits", "sous-catégories"]):
        return textwrap.dedent(f"""
        {PREFIX}
        SELECT ?categorie WHERE {{
            ?categorie a ns:SousCatégorie .
        }}
        """)

    # --- Intent: list all brands ---
    if any(keyword in question_lower for keyword in ["marques", "brands"]):
        return textwrap.dedent(f"""
        {PREFIX}
        SELECT DISTINCT ?marque WHERE {{
            ?p ns:aProduitMarque ?marque .
        }}
        """)

    # --- Map of possible relations ---
    relation_map = {
        "auteur": "ns:aAuteur",
        "auteur de": "ns:aAuteur",
        "marque": "ns:aProduitMarque",
        "prix": "ns:aPrix",
        "description": "ns:aDescription",
        "catégorie": "ns:aSousCatégorie",
        "produit": "ns:Produit",
    }

    rel_uri = relation_map.get(relation.lower(), None) if relation else None

    # --- Fallback: no entity or relation, show products by default ---
    if not entity and not rel_uri:
        return textwrap.dedent(f"""
        {PREFIX}
        SELECT ?produit ?nom ?prix ?marque WHERE {{
            ?produit a ns:Produit .
            OPTIONAL {{ ?produit ns:aNom ?nom. }}
            OPTIONAL {{ ?produit ns:aPrix ?prix. }}
            OPTIONAL {{ ?produit ns:aProduitMarque ?marque. }}
        }}
        """)

    # --- Explicit relation + entity query ---
    if rel_uri and entity:
        return textwrap.dedent(f"""
        {PREFIX}
        SELECT ?result WHERE {{
            ?x {rel_uri} ?result .
            FILTER regex(str(?x), "{entity}", "i")
        }}
        """)

    # --- If still unclear, show all products as default ---
    return textwrap.dedent(f"""
    {PREFIX}
    SELECT ?produit ?nom ?prix ?marque WHERE {{
        ?produit a ns:Produit .
        OPTIONAL {{ ?produit ns:aNom ?nom. }}
        OPTIONAL {{ ?produit ns:aPrix ?prix. }}
        OPTIONAL {{ ?produit ns:aProduitMarque ?marque. }}
    }}
    """)


# --- Main function ---
async def question_to_sparql(question: str, debug_print: bool = True) -> str:
    """
    Converts a natural language question to a SPARQL query using SpaCy NER + rule mapping.
    """
    if nlp is None:
        raise RuntimeError("SpaCy NLP model not loaded properly.")

    # Run SpaCy pipeline asynchronously
    doc = await asyncio.to_thread(nlp, question)

    # Extract entities
    entities = [ent.text for ent in doc.ents]
    entity = entities[0] if entities else None

    # Detect relation keyword
    relation = None
    for token in doc:
        if token.lemma_.lower() in ["auteur", "prix", "marque", "description", "catégorie", "produit"]:
            relation = token.lemma_
            break

    # --- Build SPARQL query ---
    sparql = build_sparql(entity, relation, question)

    if debug_print:
        print("\n=== NLP ANALYSIS ===")
        print(f"Entities: {entities}")
        print(f"Relation: {relation}")
        print("Generated SPARQL >>>")
        print(sparql)
        print("<<< END SPARQL\n")

    return sparql
