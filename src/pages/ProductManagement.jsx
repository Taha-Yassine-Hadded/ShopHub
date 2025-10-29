import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";
import { Plus, Edit, Trash2, Save, X, Home as HomeIcon, BarChart3, FileDown } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

export default function ProductManagement() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [nlpQuestion, setNlpQuestion] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [detectedEntities, setDetectedEntities] = useState(null);
  const [showStats, setShowStats] = useState(false);
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

  // Calculer les statistiques
  const statistics = useMemo(() => {
    if (products.length === 0) return null;

    const prix = products.map(p => parseFloat(p.prix?.value || 0)).filter(p => p > 0);
    const total = products.length;
    const prixMoyen = prix.length > 0 ? (prix.reduce((a, b) => a + b, 0) / prix.length).toFixed(2) : 0;
    const prixMin = prix.length > 0 ? Math.min(...prix) : 0;
    const prixMax = prix.length > 0 ? Math.max(...prix) : 0;

    // Répartition par marque
    const marqueCount = {};
    products.forEach(p => {
      const marque = p.marque?.value.split("#")[1] || "Inconnu";
      marqueCount[marque] = (marqueCount[marque] || 0) + 1;
    });

    // Répartition par catégorie
    const categorieCount = {};
    products.forEach(p => {
      const categorie = p.categorie?.value.split("#")[1] || "Inconnu";
      categorieCount[categorie] = (categorieCount[categorie] || 0) + 1;
    });

    const marqueData = Object.entries(marqueCount).map(([name, value]) => ({ name, value }));
    const categorieData = Object.entries(categorieCount).map(([name, value]) => ({ name, value }));

    return {
      total,
      prixMoyen,
      prixMin,
      prixMax,
      marqueData,
      categorieData
    };
  }, [products]);

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

  // RECHERCHE NLP (Langage Naturel)
  const handleNLPSearch = async () => {
    if (!nlpQuestion.trim()) {
      alert("Veuillez poser une question");
      return;
    }

    setIsSearching(true);
    try {
      const response = await axios.post(
        "http://localhost:9000/search-products-nlp",
        null,
        { params: { question: nlpQuestion } }
      );
      
      if (response.data.error) {
        alert("Erreur: " + response.data.error);
      } else {
        setProducts(response.data.results || []);
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

  // EXPORT PDF
  const exportToPDF = () => {
    const doc = new jsPDF();
    
    // En-tête
    doc.setFontSize(20);
    doc.setTextColor(59, 130, 246); // Bleu
    doc.text("ShopHub - Rapport des Produits", 14, 20);
    
    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(`Date: ${new Date().toLocaleDateString('fr-FR')}`, 14, 28);
    
    // Statistiques
    if (statistics) {
      doc.setFontSize(14);
      doc.setTextColor(0);
      doc.text("Statistiques", 14, 40);
      
      doc.setFontSize(10);
      doc.text(`Total de produits: ${statistics.total}`, 20, 48);
      doc.text(`Prix moyen: ${statistics.prixMoyen} €`, 20, 55);
      doc.text(`Prix minimum: ${statistics.prixMin} €`, 20, 62);
      doc.text(`Prix maximum: ${statistics.prixMax} €`, 20, 69);
    }
    
    // Tableau des produits
    const tableData = products.map((product, index) => [
      index + 1,
      product.produit?.value.split("#")[1] || "N/A",
      `${product.prix?.value || "N/A"} €`,
      product.categorie?.value.split("#")[1] || "N/A",
      product.marque?.value.split("#")[1] || "N/A"
    ]);
    
    // Utiliser autoTable correctement
    autoTable(doc, {
      startY: 80,
      head: [['N°', 'Produit', 'Prix', 'Catégorie', 'Marque']],
      body: tableData,
      theme: 'striped',
      headStyles: { fillColor: [59, 130, 246] },
      styles: { fontSize: 9 }
    });
    
    // Pied de page
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(150);
      doc.text(
        `Page ${i} sur ${pageCount}`,
        doc.internal.pageSize.width / 2,
        doc.internal.pageSize.height - 10,
        { align: 'center' }
      );
    }
    
    // Télécharger
    doc.save(`ShopHub_Produits_${new Date().toISOString().split('T')[0]}.pdf`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800">Gestion des Produits</h1>
          <div className="flex gap-3">
            <button
              onClick={() => setShowStats(!showStats)}
              className="bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-xl font-semibold transition-all flex items-center gap-2"
            >
              <BarChart3 size={20} /> {showStats ? "Masquer Stats" : "Statistiques"}
            </button>
            <button
              onClick={exportToPDF}
              disabled={products.length === 0}
              className="bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-xl font-semibold transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileDown size={20} /> Export PDF
            </button>
            <button
              onClick={() => navigate("/")}
              className="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded-xl font-semibold transition-all flex items-center gap-2"
            >
              <HomeIcon size={20} /> Retour à l'accueil
            </button>
          </div>
        </div>

        {/* Recherche par filtres */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-2xl font-bold text-gray-800">Recherche de Produits</h2>
          </div>
          <p className="text-gray-600 mb-4">
            Recherchez des produits en utilisant des critères spécifiques.
          </p>
          
          <div className="flex gap-3">
            <input
              type="text"
              value={nlpQuestion}
              onChange={(e) => setNlpQuestion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleNLPSearch()}
              placeholder='Ex: "Quels sont les lave-vaisselle Samsung ?" ou "Produits moins de 600 euros"'
              className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:outline-none"
              disabled={isSearching}
            />
            <button
              onClick={handleNLPSearch}
              disabled={isSearching}
              className="bg-purple-600 hover:bg-purple-700 text-white px-8 py-3 rounded-xl font-semibold transition-all shadow-md disabled:opacity-50"
            >
              {isSearching ? "Recherche..." : "Rechercher"}
            </button>
            <button
              onClick={fetchProducts}
              className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-xl font-semibold transition-all"
              title="Réinitialiser et afficher tous les produits"
            >
              Tout afficher
            </button>
          </div>

          {/* Affichage des entités détectées - Masqué pour la démo */}
          {false && detectedEntities && (
            <div className="mt-4 p-4 bg-purple-50 rounded-xl border border-purple-200">
              <p className="font-semibold text-purple-900 mb-2">🎯 Entités détectées :</p>
              <div className="flex flex-wrap gap-2">
                {detectedEntities.categorie && (
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                    📦 Catégorie: {detectedEntities.categorie}
                  </span>
                )}
                {detectedEntities.marque && (
                  <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                    🏷️ Marque: {detectedEntities.marque}
                  </span>
                )}
                {detectedEntities.prix_max && (
                  <span className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm font-medium">
                    💰 Prix max: {detectedEntities.prix_max}€
                  </span>
                )}
                {detectedEntities.prix_min && (
                  <span className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm font-medium">
                    💰 Prix min: {detectedEntities.prix_min}€
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Section Statistiques */}
        {showStats && statistics && (
          <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl shadow-xl p-8 mb-6">
            <h2 className="text-3xl font-bold text-gray-800 mb-6 flex items-center gap-3">
              <BarChart3 className="text-purple-600" size={32} />
              Statistiques des Produits
            </h2>

            {/* Cartes statistiques */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-white rounded-xl p-6 shadow-md">
                <div className="text-gray-600 text-sm mb-1">Total Produits</div>
                <div className="text-3xl font-bold text-blue-600">{statistics.total}</div>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-md">
                <div className="text-gray-600 text-sm mb-1">Prix Moyen</div>
                <div className="text-3xl font-bold text-green-600">{statistics.prixMoyen}€</div>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-md">
                <div className="text-gray-600 text-sm mb-1">Prix Min</div>
                <div className="text-3xl font-bold text-orange-600">{statistics.prixMin}€</div>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-md">
                <div className="text-gray-600 text-sm mb-1">Prix Max</div>
                <div className="text-3xl font-bold text-red-600">{statistics.prixMax}€</div>
              </div>
            </div>

            {/* Graphiques */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Graphique par Marque */}
              <div className="bg-white rounded-xl p-6 shadow-md">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Répartition par Marque</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={statistics.marqueData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {statistics.marqueData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][index % 5]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Graphique par Catégorie */}
              <div className="bg-white rounded-xl p-6 shadow-md">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Répartition par Catégorie</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={statistics.categorieData}>
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" fill="#3b82f6" name="Nombre" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

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