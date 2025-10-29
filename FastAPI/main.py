from fastapi import FastAPI, HTTPException
from SPARQLWrapper import SPARQLWrapper, JSON
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from produits import router as produits_router
from fournisseurs import router as fournisseurs_router
from stock import router as stock_router
from clients import router as clients_router
from promotions import router as promotions_router
from nlp_search import analyser_question_nlp
from nlp_search_fournisseurs import analyser_question_fournisseur
from nlp_search_stock import analyser_question_stock
from nlp_search_clients import analyser_question_client
from cart_queries import CartQueries
from order_service import OrderService
import spacy
from spacy.lang.fr import French
from collections import defaultdict, Counter
import re
import os
import logging
import time
from uuid import uuid4
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from unidecode import unidecode
import nltk
import json
# Téléchargement des ressources NLTK
nltk.download('punkt')
nltk.download('stopwords')

# Configuration de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger le modèle SpaCy pour le français (à installer avec `python -m spacy download fr_core_news_sm`)
nlp = French()

app = FastAPI()  # Une seule instance de FastAPI

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
app.include_router(produits_router)
app.include_router(fournisseurs_router)
app.include_router(stock_router)
app.include_router(clients_router)
app.include_router(promotions_router)

# Modèles Pydantic
class NaturalQuery(BaseModel):
    question: str
    product_uri: str

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

class AvisInput(BaseModel):
    product_uri: str
    note: float = Field(ge=0, le=5)
    commentaire: str

class AvisUpdate(BaseModel):
    avis_uri: str
    note: float = Field(ge=0, le=5)
    commentaire: str

# Initialize cart queries and order service
cart_queries = CartQueries()
order_service = OrderService()

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

# Classe pour l'analyse de sentiment
class LexiconAnalyzer:
    def __init__(self, data_path):
        self.emolex_words = defaultdict(lambda: defaultdict(list))
        self.nrc_emotions = {}
        self.tunisian_words = {}
        self.emoji_emotions = {}
        self.emotions_list = ['anger', 'anticipation', 'disgust', 'fear', 'joy', 'negative', 'positive', 'sadness', 'surprise', 'trust']
        self.stop_words = {
            'french': set(stopwords.words('french')),
            'english': set(stopwords.words('english'))
        }
        self.french_keywords = set(['triste', 'génial', 'joyeux', 'heureux', 'content', 'belle', 'beau', 'joli', "j'adore", 'super', 'tristesse', 'colère', 'peur', 'joie'])
        self.tunisian_keywords = set(['farhèn', 'nebki', 'mridha', 'khayef', 'zwin', 'yallah', 'fer7an'])
        self.english_keywords = set(['happy', 'sad', 'angry', 'fear', 'joy', 'love', 'awesome', 'great'])
        self.data_path = data_path
        self.load_lexicons()
        self.load_emoji_emotions()

    def load_emoji_emotions(self):
        emoji_file = os.path.join(self.data_path, 'emojis.json')
        try:
            with open(emoji_file, 'r', encoding='utf-8') as f:
                emoji_data = json.load(f)
                for item in emoji_data:
                    emoji = item['emoji']
                    emotions = item['emotions']
                    self.emoji_emotions[emoji] = {emo: score for emo, score in emotions.items() if score > 0}
            logger.info(f"✅ Emojis chargés: {len(self.emoji_emotions)} emojis")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des emojis: {e}")

    def load_lexicons(self):
        lexicons_path = os.path.join(self.data_path, 'lexicons')
        onefile_path = os.path.join(self.data_path, 'OneFilePerEmotion')
        self.load_emolex_tunisian(os.path.join(lexicons_path, 'tunisian_emolex.txt'))
        self.load_emolex_french(os.path.join(lexicons_path, 'french_emolex.txt'))
        self.load_nrc_emotions(onefile_path)

    def load_emolex_tunisian(self, filepath):
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    next(f)  # Ignorer l'en-tête
                    for line in f:
                        parts = [p.strip() for p in line.split('\t')]
                        if len(parts) >= 12:
                            word = parts[-1].lower()
                            word_no_accent = unidecode(word)
                            emotion_scores = [int(parts[i]) for i in range(1, 11)]
                            word_emotions = [emo for i, emo in enumerate(self.emotions_list) if emotion_scores[i] == 1]
                            if word_emotions:
                                self.tunisian_words[word] = word_emotions
                                self.tunisian_words[word_no_accent] = word_emotions
                logger.info(f"✅ Tunisian: {len(self.tunisian_words)} mots")
            except Exception as e:
                logger.error(f"Tunisian error: {e}")

    def load_emolex_french(self, filepath):
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    next(f)  # Ignorer l'en-tête
                    for line in f:
                        parts = [p.strip() for p in line.split('\t')]
                        if len(parts) >= 12:
                            word = parts[-1].lower()
                            word_no_accent = unidecode(word)
                            emotion_scores = [int(parts[i]) for i in range(1, 11)]
                            for i, emo in enumerate(self.emotions_list):
                                if emotion_scores[i] == 1:
                                    self.emolex_words[emo]['french'].append(word)
                                    self.emolex_words[emo]['french'].append(word_no_accent)
                logger.info(f"✅ French EMOLEX")
            except Exception as e:
                logger.error(f"French error: {e}")

    def load_nrc_emotions(self, path):
        try:
            for filename in os.listdir(path):
                if '-NRC-Emotion-Lexicon.txt' in filename:
                    emotion = filename.replace('-NRC-Emotion-Lexicon.txt', '').lower()
                    filepath = os.path.join(path, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.nrc_emotions[emotion] = {line.split('\t')[0].lower() for line in f if len(line.split('\t')) == 2 and line.split('\t')[1].strip() == '1'}
            logger.info(f"✅ NRC chargé: {len(self.nrc_emotions)} émotions")
        except Exception as e:
            logger.error(f"NRC error: {e}")

    def preprocess_text(self, text, lang):
        text_lower = text.lower()
        emojis = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]').findall(text)
        text_no_emojis = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]').sub('', text_lower)
        tokens = word_tokenize(text_no_emojis, language='french' if lang in ['french', 'tunisian'] else 'english')
        tokens = [t for t in tokens if t not in self.stop_words.get(lang, set()) and len(t) >= 2]
        tokens.extend([unidecode(t) for t in tokens])
        return list(set(tokens)), emojis

    def detect_language(self, text):
        tokens, _ = self.preprocess_text(text, 'french')
        french_count = sum(1 for w in tokens if w in self.french_keywords or unidecode(w) in self.french_keywords)
        tunisian_count = sum(1 for w in tokens if w in self.tunisian_keywords)
        english_count = sum(1 for w in tokens if w in self.english_keywords)
        return 'tunisian' if tunisian_count > 0 else 'french' if french_count > english_count else 'english'

    def analyze_sentiment(self, text):
        lang = self.detect_language(text)
        words, emojis = self.preprocess_text(text, lang)
        emotions = Counter()

        if lang == 'tunisian':
            for word in words:
                word_no_accent = unidecode(word)
                if word in self.tunisian_words or word_no_accent in self.tunisian_words:
                    emotions.update(self.tunisian_words.get(word, []) or self.tunisian_words.get(word_no_accent, []))
        else:
            for word in words:
                word_no_accent = unidecode(word)
                for emo in self.emotions_list:
                    if lang == 'english' and word in self.nrc_emotions.get(emo, set()) or word_no_accent in self.nrc_emotions.get(emo, set()):
                        emotions[emo] += 1
                    elif word in self.emolex_words[emo].get(lang, []) or word_no_accent in self.emolex_words[emo].get(lang, []):
                        emotions[emo] += 1

        for emoji in emojis:
            if emoji in self.emoji_emotions:
                emotions.update(self.emoji_emotions[emoji])

        compound = (emotions.get('positive', 0) + emotions.get('joy', 0) - (emotions.get('negative', 0) + emotions.get('anger', 0) + emotions.get('sadness', 0) + emotions.get('fear', 0))) / max(sum(emotions.values()), 1)
        return 'positive' if compound > 0.2 else 'negative' if compound < -0.2 else 'neutral'

# Initialisation de l'analyseur
analyzer = LexiconAnalyzer(data_path="C:\\ShopHub\\ShopHub\\FastAPI\\data")

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

# Endpoint pour filtrer les avis via une question naturelle
# Endpoint pour filtrer les avis via une question naturelle
# Endpoint pour filtrer les avis via une question naturelle
# Endpoint pour filtrer les avis via une question naturelle
# Endpoint pour filtrer les avis via une question naturelle
# Endpoint pour filtrer les avis via une question naturelle
@app.post("/filter-avis")
async def filter_avis(query: NaturalQuery):
    product_uri = query.product_uri
    question = query.question.lower().strip()

    # Analyse avec SpaCy
    doc = nlp(question)
    entities = [ent.text for ent in doc.ents]
    tokens = [token.text for token in doc if not token.is_stop]

    # Détection de l'intention (logique améliorée)
    if any(phrase in question for phrase in ["tous les avis", "all avis", "all reviews"]):
        filter_type = "all"
    elif any(word in tokens for word in ["positif", "positive"]):
        filter_type = "positive"
    elif any(word in tokens for word in ["négatif", "negative"]):
        filter_type = "negative"
    else:
        return {"avis": []}  # Liste vide par défaut si aucun filtre valide

    # Construction de la requête SPARQL en fonction du filtre
    if filter_type == "all":
        sparql_query_text = f"""
            PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT ?avis ?note ?commentaire ?type
            WHERE {{
                {{
                    ?avis a ns:Avis_positif .
                    BIND(ns:Avis_positif AS ?type)
                }} UNION {{
                    ?avis a ns:Avis_négatif .
                    BIND(ns:Avis_négatif AS ?type)
                }} UNION {{
                    ?avis a ns:Avis .
                    BIND(ns:Avis AS ?type)
                }}
                ?avis ns:aAvisProduit <{product_uri}> .
                ?avis ns:aNote ?note .
                ?avis ns:aCommentaire ?commentaire .
            }}
        """
        print("Requête SPARQL pour 'tous les avis':", sparql_query_text)  # Débogage
    else:
        avis_type = {
            "positive": "ns:Avis_positif",
            "negative": "ns:Avis_négatif"
        }[filter_type]
        sparql_query_text = f"""
            PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            SELECT ?avis ?note ?commentaire ?type
            WHERE {{
                ?avis a {avis_type} .
                ?avis ns:aAvisProduit <{product_uri}> .
                ?avis ns:aNote ?note .
                ?avis ns:aCommentaire ?commentaire .
            }}
        """
        print("Requête SPARQL pour", filter_type, ":", sparql_query_text)  # Débogage

    sparql_query.setQuery(sparql_query_text)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        print("Résultats bruts:", results)  # Débogage
        avis_list = results.get("results", {}).get("bindings", [])
        return {"avis": avis_list}  # Retourne explicitement la liste des bindings
    except Exception as e:
        print("Erreur:", str(e))  # Débogage
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
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT ?avis ?note ?commentaire ?type
        WHERE {{
            {{
                ?avis a ns:Avis_positif .
            }} UNION {{
                ?avis a ns:Avis_négatif .
            }} UNION {{
                ?avis a ns:Avis .
            }}
            ?avis ns:aAvisProduit <{product_uri}> .
            ?avis ns:aNote ?note .
            ?avis ns:aCommentaire ?commentaire .
            OPTIONAL {{ ?avis a ?type . }}
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
    sentiment = analyzer.analyze_sentiment(avis.commentaire)
    avis_class = {
        'positive': "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Avis_positif>",
        'negative': "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Avis_négatif>",
        'neutral': "<http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Avis>"
    }[sentiment]

    insert_query = f"""
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        INSERT DATA {{
            {avis_uri} a {avis_class} .
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
        return {"message": "Avis ajouté avec succès", "avis_uri": avis_uri, "sentiment": sentiment}
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

# Endpoint pour la recherche NLP (Langage Naturel)
@app.post("/search-products-nlp")
async def search_products_nlp(question: str):
    """
    Recherche de produits en utilisant le traitement du langage naturel (NLP).
    L'utilisateur peut poser une question en français et le système la convertit en SPARQL.
    
    Exemples de questions :
    - "Quels sont les produits de la catégorie lave-vaisselle ?"
    - "Montre-moi les réfrigérateurs Samsung"
    - "Je cherche des lave-linge avec un prix inférieur à 600 euros"
    """
    try:
        # Analyser la question avec SpaCy
        analyse = analyser_question_nlp(question)
        
        if "error" in analyse:
            return {"error": analyse["error"]}
        
        # Exécuter la requête SPARQL générée
        sparql_query.setQuery(analyse["sparql_query"])
        sparql_query.setReturnFormat(JSON)
        
        results = sparql_query.query().convert()
        
        return {
            "question": question,
            "entites_detectees": analyse["entites"],
            "sparql_genere": analyse["sparql_query"],
            "results": results["results"]["bindings"]

# Nouveau endpoint pour les statistiques des avis
@app.get("/dashboard/avis-stats")
async def get_avis_stats():
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT ?type ?note
        WHERE {
            {
                ?avis a ns:Avis_positif .
                BIND(ns:Avis_positif AS ?type)
            } UNION {
                ?avis a ns:Avis_négatif .
                BIND(ns:Avis_négatif AS ?type)
            } UNION {
                ?avis a ns:Avis .
                BIND(ns:Avis AS ?type)
            }
            ?avis ns:aNote ?note .
        }
    """
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        bindings = results["results"]["bindings"]
        
        # Compter les avis par type
        avis_counts = {"positive": 0, "negative": 0, "neutral": 0}
        total_notes = 0
        note_count = 0
        
        for binding in bindings:
            note = float(binding["note"]["value"])
            if "Avis_positif" in binding["type"]["value"]:
                avis_counts["positive"] += 1
            elif "Avis_négatif" in binding["type"]["value"]:
                avis_counts["negative"] += 1
            else:
                avis_counts["neutral"] += 1
            total_notes += note
            note_count += 1
        
        # Calculer la moyenne des notes
        average_note = total_notes / note_count if note_count > 0 else 0
        
        return {
            "total_avis": sum(avis_counts.values()),
            "avis_positive": avis_counts["positive"],
            "avis_negative": avis_counts["negative"],
            "avis_neutral": avis_counts["neutral"],
            "average_note": round(average_note, 2)
        }
    except Exception as e:
        return {"error": str(e)}

# Endpoint pour la recherche NLP des Fournisseurs
@app.post("/search-suppliers-nlp")
async def search_suppliers_nlp(question: str):
    """
    Recherche de fournisseurs en utilisant le traitement du langage naturel (NLP).
    L'utilisateur peut poser une question en français et le système la convertit en SPARQL.
    
    Exemples de questions :
    - "Quels sont les fournisseurs en Tunisie ?"
    - "Montre-moi les fournisseurs Samsung"
    - "Fournisseur Samsung en Tunisie"
    """
    try:
        # Analyser la question avec SpaCy
        analyse = analyser_question_fournisseur(question)
        
        if "error" in analyse:
            return {"error": analyse["error"]}
        
        # Exécuter la requête SPARQL générée
        sparql_query.setQuery(analyse["sparql_query"])
        sparql_query.setReturnFormat(JSON)
        
        results = sparql_query.query().convert()
        
        return {
            "question": question,
            "entites_detectees": analyse["entites"],
            "sparql_genere": analyse["sparql_query"],
            "results": results["results"]["bindings"]
        }
    except Exception as e:
        return {"error": str(e)}

# Endpoint pour la recherche NLP du Stock
@app.post("/search-stock-nlp")
async def search_stock_nlp(question: str):
    """
    Recherche de stock en utilisant le traitement du langage naturel (NLP).
    L'utilisateur peut poser une question en français et le système la convertit en SPARQL.
    
    Exemples de questions :
    - "Quels sont les produits en rupture de stock ?"
    - "Montre-moi le stock des lave-linge Samsung"
    - "Produits avec stock faible"
    - "Tous les produits avec un stock supérieur à 50 unités"
    """
    try:
        # Analyser la question avec SpaCy
        analyse = analyser_question_stock(question)
        
        if "error" in analyse:
            return {"error": analyse["error"]}
        
        # Exécuter la requête SPARQL générée
        sparql_query.setQuery(analyse["sparql_query"])
        sparql_query.setReturnFormat(JSON)
        
        results = sparql_query.query().convert()
        
        return {
            "question": question,
            "entites_detectees": analyse["entites"],
            "sparql_genere": analyse["sparql_query"],
            "results": results["results"]["bindings"]
        }
    except Exception as e:
        return {"error": str(e)}

# Endpoint pour la recherche NLP des Clients
@app.post("/search-clients-nlp")
async def search_clients_nlp(question: str):
    """
    Recherche de clients en utilisant le traitement du langage naturel (NLP).
    L'utilisateur peut poser une question en français et le système la convertit en SPARQL.
    
    Exemples de questions :
    - "Quels sont les clients en Tunisie ?"
    - "Montre-moi les clients de Paris"
    - "Client Jean Dupont"
    - "Liste des clients français"
    """
    try:
        # Analyser la question avec SpaCy
        analyse = analyser_question_client(question)
        
        if "error" in analyse:
            return {"error": analyse["error"]}
        
        # Exécuter la requête SPARQL générée
        sparql_query.setQuery(analyse["sparql_query"])
        sparql_query.setReturnFormat(JSON)
        
        results = sparql_query.query().convert()
        
        return {
            "question": question,
            "entites_detectees": analyse["entites"],
            "sparql_genere": analyse["sparql_query"],
            "results": results["results"]["bindings"]
        }
# Nouveau endpoint pour les produits par catégorie
@app.get("/dashboard/products-by-category")
async def get_products_by_category():
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?categorie (COUNT(?produit) AS ?count)
        WHERE {
            ?produit a ns:Produit .
            ?produit ns:aSousCatégorie ?categorie .
        }
        GROUP BY ?categorie
    """
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        bindings = results["results"]["bindings"]
        categories = {}
        for binding in bindings:
            cat_name = binding["categorie"]["value"].split("#")[1]
            count = int(binding["count"]["value"])
            categories[cat_name] = count
        return categories
    except Exception as e:
        return {"error": str(e)}

# Nouveau endpoint pour les produits par marque
@app.get("/dashboard/products-by-brand")
async def get_products_by_brand():
    query = """
        PREFIX ns: <http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#>
        SELECT ?marque (COUNT(?produit) AS ?count)
        WHERE {
            ?produit a ns:Produit .
            ?produit ns:aProduitMarque ?marque .
        }
        GROUP BY ?marque
    """
    sparql_query.setQuery(query)
    sparql_query.setReturnFormat(JSON)
    try:
        results = sparql_query.query().convert()
        bindings = results["results"]["bindings"]
        brands = {}
        for binding in bindings:
            brand_name = binding["marque"]["value"].split("#")[1]
            count = int(binding["count"]["value"])
            brands[brand_name] = count
        return brands

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)