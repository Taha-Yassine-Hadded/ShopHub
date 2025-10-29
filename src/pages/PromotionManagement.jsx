import React, { useState, useEffect } from "react";
import axios from "axios";
import { Plus, Edit, Trash2, Save, X, Home as HomeIcon, Calendar, Percent, DollarSign, Tag, TrendingUp } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function PromotionManagement() {
  const navigate = useNavigate();
  const [promotions, setPromotions] = useState([]);
  const [promotionsActives, setPromotionsActives] = useState([]);
  const [produits, setProduits] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingPromotion, setEditingPromotion] = useState(null);
  const [formData, setFormData] = useState({
    nom_promotion: "",
    date_debut: "",
    date_fin: "",
    pourcentage_reduction: 0,
    reduction_fixe: 0,
    produit_uri: ""
  });

  // Charger les données
  useEffect(() => {
    fetchPromotions();
    fetchPromotionsActives();
    fetchProduits();
  }, []);

  const fetchPromotions = async () => {
    try {
      const response = await axios.get("http://localhost:9000/promotions");
      setPromotions(response.data.promotions || []);
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors du chargement des promotions");
    }
  };

  const fetchPromotionsActives = async () => {
    try {
      const response = await axios.get("http://localhost:9000/promotions/actives");
      setPromotionsActives(response.data.promotions_actives || []);
    } catch (error) {
      console.error("Erreur:", error);
    }
  };

  const fetchProduits = async () => {
    try {
      const response = await axios.get("http://localhost:9000/stock/all");
      setProduits(response.data.produits || []);
    } catch (error) {
      console.error("Erreur:", error);
    }
  };

  // AJOUTER une promotion
  const handleAddPromotion = async (e) => {
    e.preventDefault();
    try {
      await axios.post("http://localhost:9000/add-promotion", {
        nom_promotion: formData.nom_promotion,
        date_debut: formData.date_debut,
        date_fin: formData.date_fin,
        pourcentage_reduction: parseFloat(formData.pourcentage_reduction),
        reduction_fixe: parseFloat(formData.reduction_fixe),
        produit_uri: formData.produit_uri
      });
      alert("Promotion ajoutée avec succès!");
      resetForm();
      fetchPromotions();
      fetchPromotionsActives();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de l'ajout: " + (error.response?.data?.error || error.message));
    }
  };

  // MODIFIER une promotion
  const handleUpdatePromotion = async (e) => {
    e.preventDefault();
    try {
      const updateData = {
        promotion_uri: editingPromotion.promotion.value,
      };
      
      if (formData.date_debut) updateData.date_debut = formData.date_debut;
      if (formData.date_fin) updateData.date_fin = formData.date_fin;
      if (formData.pourcentage_reduction !== undefined) 
        updateData.pourcentage_reduction = parseFloat(formData.pourcentage_reduction);
      if (formData.reduction_fixe !== undefined) 
        updateData.reduction_fixe = parseFloat(formData.reduction_fixe);

      await axios.put("http://localhost:9000/update-promotion", updateData);
      alert("Promotion modifiée avec succès!");
      resetForm();
      fetchPromotions();
      fetchPromotionsActives();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de la modification: " + (error.response?.data?.error || error.message));
    }
  };

  // SUPPRIMER une promotion
  const handleDeletePromotion = async (promotionUri) => {
    if (!window.confirm("Voulez-vous vraiment supprimer cette promotion?")) return;
    
    try {
      await axios.delete(`http://localhost:9000/delete-promotion?promotion_uri=${encodeURIComponent(promotionUri)}`);
      alert("Promotion supprimée avec succès!");
      fetchPromotions();
      fetchPromotionsActives();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de la suppression: " + (error.response?.data?.error || error.message));
    }
  };

  // Préparer le formulaire de modification
  const handleEditClick = (promotion) => {
    setEditingPromotion(promotion);
    setFormData({
      nom_promotion: promotion.promotion?.value.split("#")[1] || "",
      date_debut: promotion.dateDebut?.value ? promotion.dateDebut.value.split("T")[0] + "T" + promotion.dateDebut.value.split("T")[1] : "",
      date_fin: promotion.dateFin?.value ? promotion.dateFin.value.split("T")[0] + "T" + promotion.dateFin.value.split("T")[1] : "",
      pourcentage_reduction: promotion.pourcentage?.value || 0,
      reduction_fixe: promotion.reduction?.value || 0,
      produit_uri: promotion.produit?.value || ""
    });
    setShowAddForm(true);
  };

  // Réinitialiser le formulaire
  const resetForm = () => {
    setFormData({
      nom_promotion: "",
      date_debut: "",
      date_fin: "",
      pourcentage_reduction: 0,
      reduction_fixe: 0,
      produit_uri: ""
    });
    setShowAddForm(false);
    setEditingPromotion(null);
  };

  // Vérifier si une promotion est active
  const isActive = (dateDebut, dateFin) => {
    const now = new Date();
    const debut = new Date(dateDebut);
    const fin = new Date(dateFin);
    return now >= debut && now <= fin;
  };

  // Formater la date
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString("fr-FR", { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100">
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800">🎉 Gestion des Promotions</h1>
          <button
            onClick={() => navigate("/")}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded-xl font-semibold transition-all flex items-center gap-2"
          >
            <HomeIcon size={20} /> Retour à l'accueil
          </button>
        </div>

        {/* Statistiques */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 shadow-md text-white">
            <div className="flex items-center justify-between mb-2">
              <div className="text-blue-100 text-sm">Promotions Actives</div>
              <TrendingUp className="text-blue-200" size={24} />
            </div>
            <div className="text-3xl font-bold">{promotionsActives.length}</div>
            <div className="text-blue-100 text-xs mt-1">en cours</div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6 shadow-md text-white">
            <div className="flex items-center justify-between mb-2">
              <div className="text-blue-100 text-sm">Total Promotions</div>
              <Tag className="text-blue-200" size={24} />
            </div>
            <div className="text-3xl font-bold">{promotions.length}</div>
            <div className="text-blue-100 text-xs mt-1">créées</div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-700 to-blue-800 rounded-xl p-6 shadow-md text-white">
            <div className="flex items-center justify-between mb-2">
              <div className="text-blue-100 text-sm">Réduction Moyenne</div>
              <Percent className="text-blue-200" size={24} />
            </div>
            <div className="text-3xl font-bold">
              {promotions.length > 0 
                ? Math.round(promotions.reduce((acc, p) => acc + parseFloat(p.pourcentage?.value || 0), 0) / promotions.length)
                : 0}%
            </div>
            <div className="text-blue-100 text-xs mt-1">moyenne</div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-400 to-blue-500 rounded-xl p-6 shadow-md text-white">
            <div className="flex items-center justify-between mb-2">
              <div className="text-blue-100 text-sm">Produits en Promo</div>
              <DollarSign className="text-blue-200" size={24} />
            </div>
            <div className="text-3xl font-bold">
              {new Set(promotions.map(p => p.produit?.value).filter(Boolean)).size}
            </div>
            <div className="text-blue-100 text-xs mt-1">produits</div>
          </div>
        </div>

        {/* Bouton Ajouter */}
        {!showAddForm && (
          <button
            onClick={() => setShowAddForm(true)}
            className="mb-6 bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-xl font-semibold transition-all flex items-center gap-2 shadow-md"
          >
            <Plus size={20} /> Créer une promotion
          </button>
        )}

        {/* Formulaire d'ajout/modification */}
        {showAddForm && (
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">
              {editingPromotion ? "Modifier la promotion" : "Nouvelle promotion"}
            </h2>
            <form onSubmit={editingPromotion ? handleUpdatePromotion : handleAddPromotion}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Nom de la promotion</label>
                  <input
                    type="text"
                    value={formData.nom_promotion}
                    onChange={(e) => setFormData({ ...formData, nom_promotion: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    required={!editingPromotion}
                    disabled={editingPromotion}
                    placeholder="Ex: Soldes d'Hiver 2025"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Produit</label>
                  <select
                    value={formData.produit_uri}
                    onChange={(e) => setFormData({ ...formData, produit_uri: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    required={!editingPromotion}
                    disabled={editingPromotion}
                  >
                    <option value="">Sélectionner un produit</option>
                    {produits.map((produit, index) => (
                      <option key={index} value={produit.produit?.value}>
                        {produit.produit?.value.split("#")[1]} - {produit.prix?.value}€
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Date de début</label>
                  <input
                    type="datetime-local"
                    value={formData.date_debut}
                    onChange={(e) => setFormData({ ...formData, date_debut: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    required={!editingPromotion}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Date de fin</label>
                  <input
                    type="datetime-local"
                    value={formData.date_fin}
                    onChange={(e) => setFormData({ ...formData, date_fin: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    required={!editingPromotion}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Pourcentage de réduction (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    value={formData.pourcentage_reduction}
                    onChange={(e) => setFormData({ ...formData, pourcentage_reduction: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    placeholder="Ex: 20"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Réduction fixe (€)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.reduction_fixe}
                    onChange={(e) => setFormData({ ...formData, reduction_fixe: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    placeholder="Ex: 50"
                  />
                </div>
              </div>

              <div className="flex gap-4 mt-6">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
                >
                  <Save size={20} /> {editingPromotion ? "Enregistrer" : "Créer"}
                </button>
                <button
                  type="button"
                  onClick={resetForm}
                  className="flex-1 bg-gray-500 hover:bg-gray-600 text-white py-3 rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
                >
                  <X size={20} /> Annuler
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Liste des promotions */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b">
            <h2 className="text-xl font-bold text-gray-800">Liste des Promotions ({promotions.length})</h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Promotion</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Produit</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Réduction</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Période</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Statut</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {promotions.map((promotion, index) => {
                  const active = isActive(promotion.dateDebut?.value, promotion.dateFin?.value);
                  return (
                    <tr key={index} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {promotion.promotion?.value.split("#")[1] || "N/A"}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">
                        {promotion.produit?.value.split("#")[1] || "N/A"}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex flex-col items-center gap-1">
                          {promotion.pourcentage?.value && parseFloat(promotion.pourcentage.value) > 0 && (
                            <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-bold">
                              -{promotion.pourcentage.value}%
                            </span>
                          )}
                          {promotion.reduction?.value && parseFloat(promotion.reduction.value) > 0 && (
                            <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-bold">
                              -{promotion.reduction.value}€
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center text-xs text-gray-600">
                        <div>{formatDate(promotion.dateDebut?.value)}</div>
                        <div className="text-gray-400">au</div>
                        <div>{formatDate(promotion.dateFin?.value)}</div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        {active ? (
                          <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-bold">
                            ✅ Active
                          </span>
                        ) : (
                          <span className="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-xs font-bold">
                            ⏸️ Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex justify-center gap-3">
                          <button
                            onClick={() => handleEditClick(promotion)}
                            className="text-blue-600 hover:text-blue-800 transition-colors"
                            title="Modifier"
                          >
                            <Edit size={20} />
                          </button>
                          <button
                            onClick={() => handleDeletePromotion(promotion.promotion.value)}
                            className="text-red-600 hover:text-red-800 transition-colors"
                            title="Supprimer"
                          >
                            <Trash2 size={20} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {promotions.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            Aucune promotion disponible
          </div>
        )}
      </main>
    </div>
  );
}

