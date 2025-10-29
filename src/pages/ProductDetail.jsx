import React, { useState } from "react";
import { ShoppingCart, Star, Trash2, Edit } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios";

const ProductDetail = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const product = state?.product;

  // États pour la note, le commentaire, les avis, l'alerte et le filtre
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [comments, setComments] = useState([]); // Initialement vide
  const [editComment, setEditComment] = useState(null);
  const [editRating, setEditRating] = useState(0);
  const [editText, setEditText] = useState("");
  const [alert, setAlert] = useState({ message: "", type: "", show: false });
  const [filterQuery, setFilterQuery] = useState(""); // Nouvel état pour la question de filtrage

  // Appliquer le filtre basé sur la question
  const handleFilterAvis = async () => {
    if (product?.produit?.value && filterQuery.trim()) {
      try {
        const response = await axios.post("http://localhost:9000/filter-avis", {
          question: filterQuery,
          product_uri: product.produit.value,
        });
        setComments(response.data.avis || []);
        setFilterQuery(""); // Réinitialiser après filtrage
      } catch (error) {
        console.error("Erreur lors du filtrage des avis:", error);
        window.alert("Erreur lors du filtrage des avis.");
      }
    } else {
      window.alert("Veuillez entrer une question de filtrage.");
    }
  };

  // Soumettre un nouvel avis
  const handleSubmitReview = async (e) => {
    e.preventDefault();
    if (rating > 0 && comment.trim() && product?.produit?.value) {
      const productUri = product.produit.value;
      try {
        const response = await axios.post("http://localhost:9000/add-avis", {
          product_uri: productUri,
          note: rating,
          commentaire: comment,
        }, {
          headers: { "Content-Type": "application/json" },
        });
        setComments([...comments, { avis: { value: response.data.avis_uri }, note: { value: rating }, commentaire: { value: comment } }]);
        setRating(0);
        setComment("");

        const sentiment = response.data.sentiment;
        if (sentiment === "positive" || sentiment === "neutral") {
          setAlert({ message: "Merci de votre réactivité", type: "success", show: true });
        } else if (sentiment === "negative") {
          setAlert({ message: "Votre commentaire risque d'être supprimé par l'admin", type: "danger", show: true });
        }
        setTimeout(() => setAlert({ ...alert, show: false }), 7000);
        window.alert("Avis ajouté avec succès !");
      } catch (error) {
        console.error("Erreur lors de l'ajout de l'avis:", error.response?.data || error.message);
        window.alert("Erreur lors de l'ajout de l'avis: " + (error.response?.data?.detail || error.message));
      }
    } else {
      window.alert("Veuillez entrer une note et un commentaire valides.");
    }
  };

  // Supprimer un avis
  const handleDeleteAvis = async (avisUri) => {
    if (window.confirm("Voulez-vous vraiment supprimer cet avis ?")) {
      try {
        await axios.delete("http://localhost:9000/delete-avis", {
          params: { avis_uri: avisUri },
        });
        setComments(comments.filter(c => c.avis.value !== avisUri));
        window.alert("Avis supprimé avec succès !");
      } catch (error) {
        console.error("Erreur lors de la suppression:", error.response?.data || error.message);
        window.alert("Erreur lors de la suppression de l'avis: " + (error.response?.data?.detail || error.message));
      }
    }
  };

  // Modifier un avis
  const handleEditAvis = (avis) => {
    setEditComment(avis.avis.value);
    setEditRating(parseFloat(avis.note.value));
    setEditText(avis.commentaire.value);
  };

  const handleSaveEdit = async () => {
    if (editComment && editRating > 0 && editText.trim()) {
      try {
        await axios.put("http://localhost:9000/update-avis", {
          avis_uri: editComment,
          note: editRating,
          commentaire: editText,
        }, {
          headers: { "Content-Type": "application/json" },
        });
        setComments(comments.map(c =>
          c.avis.value === editComment ? { ...c, note: { value: editRating }, commentaire: { value: editText } } : c
        ));
        setEditComment(null);
        setEditRating(0);
        setEditText("");
        window.alert("Avis modifié avec succès !");
      } catch (error) {
        console.error("Erreur lors de la modification:", error);
        window.alert("Erreur lors de la modification de l'avis.");
      }
    } else {
      window.alert("Veuillez entrer une note et un commentaire valides.");
    }
  };

  // Générer les étoiles pour le rating
  const renderStars = (ratingToShow = 0) => {
    const totalStars = 5;
    return (
      <div className="flex gap-1">
        {[...Array(totalStars)].map((_, index) => (
          <Star
            key={index}
            size={20}
            className={index < Math.floor(ratingToShow) ? "text-yellow-400 fill-yellow-400" : "text-gray-300"}
            onClick={() => (editComment ? setEditRating(index + 1) : setRating(index + 1))}
            style={{ cursor: "pointer" }}
          />
        ))}
        {ratingToShow % 1 !== 0 && (
          <Star
            size={20}
            className="text-yellow-400 fill-yellow-400"
            style={{ clipPath: `inset(0 ${100 - (ratingToShow % 1) * 100}% 0 0)`, cursor: "pointer" }}
            onClick={() => (editComment ? setEditRating(Math.ceil(ratingToShow)) : setRating(Math.ceil(ratingToShow)))}
          />
        )}
        <span className="ml-2 text-gray-600">({ratingToShow}/5)</span>
      </div>
    );
  };

  if (!product) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <p className="text-red-500">Produit non trouvé.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      {/* Alerte temporaire */}
      {alert.show && (
        <div className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 px-6 py-3 rounded-xl text-white shadow-lg transition-opacity duration-300 ${alert.type === "success" ? "bg-green-600" : "bg-red-600"}`}>
          {alert.message}
        </div>
      )}

      <main className="container mx-auto px-4 py-8">
        <button
          onClick={() => navigate("/")}
          className="mb-6 bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded-xl font-semibold transition-all"
        >
          Retour
        </button>

        {/* Layout à deux colonnes */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Carte Détails du Produit - 2/3 de l'espace */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-2xl overflow-hidden h-full">
              <div className="relative">
                {product.image && product.image.value ? (
                  <img
                    src={product.image.value}
                    alt={product.produit?.value.split("#")[1] || "Produit"}
                    className="w-full h-96 object-cover"
                  />
                ) : (
                  <div className="w-full h-96 bg-gray-200 flex items-center justify-center">
                    <span className="text-gray-500">Aucune image disponible</span>
                  </div>
                )}
              </div>

              <div className="p-8">
                <h3 className="text-3xl font-bold text-gray-800 mb-6">
                  {product.produit?.value.split("#")[1] || "Produit inconnu"}
                </h3>

                <div className="space-y-4 mb-6">
                  <div>
                    <span className="text-sm text-gray-500 uppercase tracking-wide">Marque</span>
                    <p className="text-lg font-semibold text-gray-800">
                      {product.marque ? product.marque.value.split("#")[1] : "Non spécifiée"}
                    </p>
                  </div>

                  <div>
                    <span className="text-sm text-gray-500 uppercase tracking-wide">Catégorie</span>
                    <p className="text-lg font-semibold text-gray-800">
                      {product.categorie ? product.categorie.value.split("#")[1] : "Non spécifiée"}
                    </p>
                  </div>

                  <div>
                    <span className="text-sm text-gray-500 uppercase tracking-wide">Description</span>
                    <p className="text-gray-700 leading-relaxed mt-2">
                      {product.description ? product.description.value : "Aucune description disponible"}
                    </p>
                  </div>

                  <div className="pt-4 border-t">
                    <span className="text-sm text-gray-500 uppercase tracking-wide">Prix</span>
                    <p className="text-5xl font-bold text-blue-600 mt-2">{product.prix?.value || "N/A"} €</p>
                  </div>
                </div>

                <button
                  onClick={() => {
                    addToCart(product);
                    navigate("/");
                  }}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-3 shadow-lg hover:shadow-xl"
                >
                  <ShoppingCart size={24} /> Ajouter au Panier
                </button>
              </div>
            </div>
          </div>

          {/* Carte Avis - 1/3 de l'espace */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-2xl p-6 sticky top-6">
              <h4 className="text-2xl font-bold text-gray-800 mb-4">Avis & Évaluations</h4>

              {/* Formulaire d'ajout d'avis */}
              <div className="mb-6 pb-6 border-b">
                <h5 className="text-lg font-semibold text-gray-700 mb-3">Donnez votre avis</h5>
                <form onSubmit={handleSubmitReview}>
                  <div className="mb-3">{renderStars(rating)}</div>
                  <textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Votre commentaire..."
                    className="w-full p-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none resize-y min-h-[100px] text-sm"
                  />
                  <button
                    type="submit"
                    className="mt-3 w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-xl font-semibold transition-all"
                  >
                    Publier
                  </button>
                </form>
              </div>

              {/* Champ de filtrage des avis */}
              <div className="mb-6 pb-6 border-b">
                <h5 className="text-lg font-semibold text-gray-700 mb-3">Filtrer les avis</h5>
                <input
                  type="text"
                  value={filterQuery}
                  onChange={(e) => setFilterQuery(e.target.value)}
                  placeholder="Ex: 'tous les avis', 'avis positifs', 'avis négatifs'"
                  className="w-full p-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none text-sm"
                />
                <button
                  onClick={handleFilterAvis}
                  className="mt-3 w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-xl font-semibold transition-all"
                >
                  Filtrer
                </button>
              </div>

              {/* Liste des commentaires */}
              <div>
                <h5 className="text-lg font-semibold text-gray-700 mb-4">
                  Commentaires ({comments.length})
                </h5>
                <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                  {comments.length === 0 ? (
                    <p className="text-gray-500 text-sm text-center py-8">Aucun avis pour le moment</p>
                  ) : (
                    comments.map((comment) => (
                      <div key={comment.avis.value} className="border-b pb-4 last:border-b-0">
                        {editComment === comment.avis.value ? (
                          <div>
                            <div className="mb-2">{renderStars(editRating)}</div>
                            <textarea
                              value={editText}
                              onChange={(e) => setEditText(e.target.value)}
                              className="w-full p-2 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none resize-y min-h-[80px] text-sm"
                            />
                            <div className="flex gap-2 mt-2">
                              <button
                                onClick={handleSaveEdit}
                                className="flex-1 bg-green-600 hover:bg-green-700 text-white py-1.5 px-3 rounded-lg text-sm font-semibold transition-all"
                              >
                                Sauvegarder
                              </button>
                              <button
                                onClick={() => setEditComment(null)}
                                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-1.5 px-3 rounded-lg text-sm font-semibold transition-all"
                              >
                                Annuler
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-semibold text-gray-800 text-sm">Utilisateur</span>
                              <div className="flex gap-2">
                                <Edit
                                  size={16}
                                  className="text-blue-600 cursor-pointer hover:text-blue-700"
                                  onClick={() => handleEditAvis(comment)}
                                />
                                <Trash2
                                  size={16}
                                  className="text-red-600 cursor-pointer hover:text-red-700"
                                  onClick={() => handleDeleteAvis(comment.avis.value)}
                                />
                              </div>
                            </div>
                            <div className="mb-2">{renderStars(parseFloat(comment.note.value))}</div>
                            <p className="text-gray-600 text-sm leading-relaxed">{comment.commentaire.value}</p>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

// Fonction addToCart manquante (à implémenter selon ton contexte)
const addToCart = (product) => {
  console.log("Produit ajouté au panier:", product);
  // Logique pour ajouter au panier ici
};

export default ProductDetail;