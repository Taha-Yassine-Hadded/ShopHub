import React, { useState, useEffect } from "react";
import axios from "axios";
import { Plus, Edit, Trash2, Save, X, Home as HomeIcon } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function SupplierManagement() {
  const navigate = useNavigate();
  const [suppliers, setSuppliers] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState(null);
  const [nlpQuestion, setNlpQuestion] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [detectedEntities, setDetectedEntities] = useState(null);
  const [formData, setFormData] = useState({
    nom: "",
    adresse: "",
    telephone: "",
    email: "",
    pays: ""
  });

  // Charger tous les fournisseurs
  useEffect(() => {
    fetchSuppliers();
  }, []);

  const fetchSuppliers = async () => {
    try {
      const response = await axios.get("http://localhost:9000/fournisseurs");
      setSuppliers(response.data.fournisseurs || []);
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors du chargement des fournisseurs");
    }
  };

  // AJOUTER un fournisseur
  const handleAddSupplier = async (e) => {
    e.preventDefault();
    try {
      await axios.post("http://localhost:9000/add-fournisseur", {
        nom: formData.nom,
        adresse: formData.adresse,
        telephone: formData.telephone,
        email: formData.email,
        pays: formData.pays
      });
      alert("Fournisseur ajouté avec succès!");
      resetForm();
      fetchSuppliers();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de l'ajout: " + (error.response?.data?.error || error.message));
    }
  };

  // MODIFIER un fournisseur
  const handleUpdateSupplier = async (e) => {
    e.preventDefault();
    try {
      const updateData = {
        fournisseur_uri: editingSupplier.fournisseur.value,
      };
      
      if (formData.adresse) updateData.adresse = formData.adresse;
      if (formData.telephone) updateData.telephone = formData.telephone;
      if (formData.email) updateData.email = formData.email;
      if (formData.pays) updateData.pays = formData.pays;

      await axios.put("http://localhost:9000/update-fournisseur", updateData);
      alert("Fournisseur modifié avec succès!");
      resetForm();
      fetchSuppliers();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de la modification: " + (error.response?.data?.error || error.message));
    }
  };

  // SUPPRIMER un fournisseur
  const handleDeleteSupplier = async (supplierUri) => {
    if (!window.confirm("Voulez-vous vraiment supprimer ce fournisseur?")) return;
    
    try {
      await axios.delete(`http://localhost:9000/delete-fournisseur?fournisseur_uri=${encodeURIComponent(supplierUri)}`);
      alert("Fournisseur supprimé avec succès!");
      fetchSuppliers();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de la suppression: " + (error.response?.data?.error || error.message));
    }
  };

  // Préparer le formulaire de modification
  const handleEditClick = (supplier) => {
    setEditingSupplier(supplier);
    setFormData({
      nom: supplier.fournisseur?.value.split("#")[1] || "",
      adresse: supplier.adresse?.value || "",
      telephone: supplier.telephone?.value || "",
      email: supplier.email?.value || "",
      pays: supplier.pays?.value || ""
    });
    setShowAddForm(true);
  };

  // Réinitialiser le formulaire
  const resetForm = () => {
    setFormData({
      nom: "",
      adresse: "",
      telephone: "",
      email: "",
      pays: ""
    });
    setShowAddForm(false);
    setEditingSupplier(null);
  };

  // RECHERCHE NLP (Langage Naturel) pour Fournisseurs
  const handleNLPSearch = async () => {
    if (!nlpQuestion.trim()) {
      alert("Veuillez poser une question");
      return;
    }

    setIsSearching(true);
    try {
      const response = await axios.post(
        "http://localhost:9000/search-suppliers-nlp",
        null,
        { params: { question: nlpQuestion } }
      );
      
      if (response.data.error) {
        alert("Erreur: " + response.data.error);
      } else {
        setSuppliers(response.data.results || []);
        setDetectedEntities(response.data.entites_detectees);
        console.log("SPARQL généré:", response.data.sparql_genere);
      }
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de la recherche: " + (error.response?.data?.error || error.message));
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800">Gestion des Fournisseurs</h1>
          <button
            onClick={() => navigate("/")}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded-xl font-semibold transition-all flex items-center gap-2"
          >
            <HomeIcon size={20} /> Retour à l'accueil
          </button>
        </div>

        {/* Recherche de Fournisseurs */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-2xl font-bold text-gray-800">Recherche de Fournisseurs</h2>
          </div>
          <p className="text-gray-600 mb-4">
            Recherchez des fournisseurs par nom, pays ou ville.
          </p>
          
          <div className="flex gap-3">
            <input
              type="text"
              value={nlpQuestion}
              onChange={(e) => setNlpQuestion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleNLPSearch()}
              placeholder='Ex: "Fournisseurs en Tunisie" ou "Fournisseur Samsung"'
              className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
              disabled={isSearching}
            />
            <button
              onClick={handleNLPSearch}
              disabled={isSearching}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-semibold transition-all shadow-md disabled:opacity-50"
            >
              {isSearching ? "Recherche..." : "Rechercher"}
            </button>
            <button
              onClick={fetchSuppliers}
              className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-xl font-semibold transition-all"
              title="Réinitialiser et afficher tous les fournisseurs"
            >
              Tout afficher
            </button>
          </div>

          {/* Affichage des entités détectées - Masqué pour la démo */}
          {false && detectedEntities && (
            <div className="mt-4 p-4 bg-green-50 rounded-xl border border-green-200">
              <p className="font-semibold text-green-900 mb-2">🎯 Entités détectées :</p>
              <div className="flex flex-wrap gap-2">
                {detectedEntities.nom_fournisseur && (
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                    🏢 Fournisseur: {detectedEntities.nom_fournisseur}
                  </span>
                )}
                {detectedEntities.pays && (
                  <span className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm font-medium">
                    🌍 Pays: {detectedEntities.pays}
                  </span>
                )}
                {detectedEntities.ville && (
                  <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium">
                    🏙️ Ville: {detectedEntities.ville}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Bouton Ajouter */}
        {!showAddForm && (
          <button
            onClick={() => setShowAddForm(true)}
            className="mb-6 bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-xl font-semibold transition-all flex items-center gap-2 shadow-md"
          >
            <Plus size={20} /> Ajouter un fournisseur
          </button>
        )}

        {/* Formulaire d'ajout/modification */}
        {showAddForm && (
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">
              {editingSupplier ? "Modifier le fournisseur" : "Nouveau fournisseur"}
            </h2>
            <form onSubmit={editingSupplier ? handleUpdateSupplier : handleAddSupplier}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Nom du fournisseur</label>
                  <input
                    type="text"
                    value={formData.nom}
                    onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    required={!editingSupplier}
                    disabled={editingSupplier}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Téléphone</label>
                  <input
                    type="tel"
                    value={formData.telephone}
                    onChange={(e) => setFormData({ ...formData, telephone: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    placeholder="+33 1 23 45 67 89"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    placeholder="contact@fournisseur.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Pays</label>
                  <input
                    type="text"
                    value={formData.pays}
                    onChange={(e) => setFormData({ ...formData, pays: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    placeholder="France"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Adresse</label>
                  <textarea
                    value={formData.adresse}
                    onChange={(e) => setFormData({ ...formData, adresse: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none resize-y min-h-[100px]"
                    placeholder="123 Rue Example, 75001 Paris"
                  />
                </div>
              </div>

              <div className="flex gap-4 mt-6">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
                >
                  <Save size={20} /> {editingSupplier ? "Enregistrer" : "Ajouter"}
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

        {/* Liste des fournisseurs */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Nom</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Téléphone</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Email</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Pays</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {suppliers.map((supplier, index) => (
                  <tr key={index} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">
                        {supplier.fournisseur?.value.split("#")[1]?.replace(/_/g, " ") || "N/A"}
                      </div>
                      <div className="text-sm text-gray-500 truncate max-w-xs">
                        {supplier.adresse?.value || "Pas d'adresse"}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {supplier.telephone?.value || "N/A"}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {supplier.email?.value || "N/A"}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {supplier.pays?.value || "N/A"}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex justify-center gap-3">
                        <button
                          onClick={() => handleEditClick(supplier)}
                          className="text-blue-600 hover:text-blue-800 transition-colors"
                          title="Modifier"
                        >
                          <Edit size={20} />
                        </button>
                        <button
                          onClick={() => handleDeleteSupplier(supplier.fournisseur.value)}
                          className="text-red-600 hover:text-red-800 transition-colors"
                          title="Supprimer"
                        >
                          <Trash2 size={20} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {suppliers.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            Aucun fournisseur disponible
          </div>
        )}
      </main>
    </div>
  );
}

