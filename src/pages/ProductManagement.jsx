import React, { useState, useEffect } from "react";
import axios from "axios";
import { Plus, Edit, Trash2, Save, X, Home as HomeIcon } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function ProductManagement() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState({
    nom: "",
    description: "",
    prix: "",
    categorie_uri: "",
    marque_uri: "",
    image: "",
    poids: "",
    stock_disponible: ""
  });

  // Catégories et marques disponibles
  const categories = [
    { label: "Lave-vaisselle", uri: "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Lave-vaisselle" },
    { label: "Lave-linge", uri: "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Lave-linge" },
    { label: "Réfrigérateurs", uri: "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Réfrigérateurs" },
    { label: "Aspirateurs", uri: "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Aspirateurs" },
  ];

  const marques = [
    { label: "Samsung", uri: "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Samsung" },
    { label: "LG", uri: "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#LG" },
    { label: "Beko", uri: "http://www.semanticweb.org/asus/ontologies/2025/9/untitled-ontology-10#Beko" },
  ];

  // Charger tous les produits
  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get("http://localhost:9000/sparql?question=liste des produits");
      setProducts(response.data.results || []);
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors du chargement des produits");
    }
  };

  // AJOUTER un produit
  const handleAddProduct = async (e) => {
    e.preventDefault();
    try {
      await axios.post("http://localhost:9000/add-produit", {
        nom: formData.nom,
        description: formData.description,
        prix: parseFloat(formData.prix),
        categorie_uri: formData.categorie_uri,
        marque_uri: formData.marque_uri,
        image: formData.image,
        poids: parseFloat(formData.poids) || 0,
        stock_disponible: parseInt(formData.stock_disponible) || 0
      });
      alert("Produit ajouté avec succès!");
      resetForm();
      fetchProducts();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de l'ajout: " + (error.response?.data?.error || error.message));
    }
  };

  // MODIFIER un produit
  const handleUpdateProduct = async (e) => {
    e.preventDefault();
    try {
      const updateData = {
        produit_uri: editingProduct.produit.value,
      };
      
      if (formData.description) updateData.description = formData.description;
      if (formData.prix) updateData.prix = parseFloat(formData.prix);
      if (formData.categorie_uri) updateData.categorie_uri = formData.categorie_uri;
      if (formData.marque_uri) updateData.marque_uri = formData.marque_uri;
      if (formData.image) updateData.image = formData.image;
      if (formData.poids) updateData.poids = parseFloat(formData.poids);
      if (formData.stock_disponible) updateData.stock_disponible = parseInt(formData.stock_disponible);

      await axios.put("http://localhost:9000/update-produit", updateData);
      alert("Produit modifié avec succès!");
      resetForm();
      fetchProducts();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de la modification: " + (error.response?.data?.error || error.message));
    }
  };

  // SUPPRIMER un produit
  const handleDeleteProduct = async (productUri) => {
    if (!window.confirm("Voulez-vous vraiment supprimer ce produit?")) return;
    
    try {
      await axios.delete(`http://localhost:9000/delete-produit?produit_uri=${encodeURIComponent(productUri)}`);
      alert("Produit supprimé avec succès!");
      fetchProducts();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de la suppression: " + (error.response?.data?.error || error.message));
    }
  };

  // Préparer le formulaire de modification
  const handleEditClick = (product) => {
    setEditingProduct(product);
    setFormData({
      nom: product.produit?.value.split("#")[1] || "",
      description: product.description?.value || "",
      prix: product.prix?.value || "",
      categorie_uri: product.categorie?.value || "",
      marque_uri: product.marque?.value || "",
      image: product.image?.value || "",
      poids: "",
      stock_disponible: ""
    });
    setShowAddForm(true);
  };

  // Réinitialiser le formulaire
  const resetForm = () => {
    setFormData({
      nom: "",
      description: "",
      prix: "",
      categorie_uri: "",
      marque_uri: "",
      image: "",
      poids: "",
      stock_disponible: ""
    });
    setShowAddForm(false);
    setEditingProduct(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800">Gestion des Produits</h1>
          <button
            onClick={() => navigate("/")}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded-xl font-semibold transition-all flex items-center gap-2"
          >
            <HomeIcon size={20} /> Retour à l'accueil
          </button>
        </div>

        {/* Bouton Ajouter */}
        {!showAddForm && (
          <button
            onClick={() => setShowAddForm(true)}
            className="mb-6 bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-xl font-semibold transition-all flex items-center gap-2 shadow-md"
          >
            <Plus size={20} /> Ajouter un produit
          </button>
        )}

        {/* Formulaire d'ajout/modification */}
        {showAddForm && (
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">
              {editingProduct ? "Modifier le produit" : "Nouveau produit"}
            </h2>
            <form onSubmit={editingProduct ? handleUpdateProduct : handleAddProduct}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Nom du produit</label>
                  <input
                    type="text"
                    value={formData.nom}
                    onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    required={!editingProduct}
                    disabled={editingProduct}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Prix (€)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.prix}
                    onChange={(e) => setFormData({ ...formData, prix: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    required={!editingProduct}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Catégorie</label>
                  <select
                    value={formData.categorie_uri}
                    onChange={(e) => setFormData({ ...formData, categorie_uri: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    required={!editingProduct}
                  >
                    <option value="">Sélectionner une catégorie</option>
                    {categories.map((cat) => (
                      <option key={cat.uri} value={cat.uri}>{cat.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Marque</label>
                  <select
                    value={formData.marque_uri}
                    onChange={(e) => setFormData({ ...formData, marque_uri: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    required={!editingProduct}
                  >
                    <option value="">Sélectionner une marque</option>
                    {marques.map((marque) => (
                      <option key={marque.uri} value={marque.uri}>{marque.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Poids (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.poids}
                    onChange={(e) => setFormData({ ...formData, poids: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Stock disponible</label>
                  <input
                    type="number"
                    value={formData.stock_disponible}
                    onChange={(e) => setFormData({ ...formData, stock_disponible: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">URL de l'image</label>
                  <input
                    type="url"
                    value={formData.image}
                    onChange={(e) => setFormData({ ...formData, image: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none resize-y min-h-[100px]"
                    required={!editingProduct}
                  />
                </div>
              </div>

              <div className="flex gap-4 mt-6">
                <button
                  type="submit"
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
                >
                  <Save size={20} /> {editingProduct ? "Enregistrer" : "Ajouter"}
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

        {/* Liste des produits */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Produit</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Prix</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Catégorie</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Marque</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {products.map((product, index) => (
                  <tr key={index} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">
                        {product.produit?.value.split("#")[1] || "N/A"}
                      </div>
                      <div className="text-sm text-gray-500 truncate max-w-xs">
                        {product.description?.value || "Pas de description"}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 font-semibold">
                      {product.prix?.value || "N/A"} €
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {product.categorie?.value.split("#")[1] || "N/A"}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {product.marque?.value.split("#")[1] || "N/A"}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex justify-center gap-3">
                        <button
                          onClick={() => handleEditClick(product)}
                          className="text-blue-600 hover:text-blue-800 transition-colors"
                          title="Modifier"
                        >
                          <Edit size={20} />
                        </button>
                        <button
                          onClick={() => handleDeleteProduct(product.produit.value)}
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

        {products.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            Aucun produit disponible
          </div>
        )}
      </main>
    </div>
  );
}