import React, { useState, useEffect } from "react";
import axios from "axios";
import { Home as HomeIcon, AlertTriangle, Package, TrendingUp, Edit2, Search, MessageCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function StockManagement() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [alerts, setAlerts] = useState({ rupture: [], stock_faible: [] });
  const [statistics, setStatistics] = useState(null);
  const [editingStock, setEditingStock] = useState(null);
  const [newStockValue, setNewStockValue] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);

  // Charger toutes les données au démarrage
  useEffect(() => {
    fetchAllStock();
    fetchAlerts();
    fetchStatistics();
  }, []);

  // Récupérer tous les produits avec leur stock
  const fetchAllStock = async () => {
    try {
      const response = await axios.get("http://localhost:9000/stock/all");
      setProducts(response.data.produits || []);
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors du chargement du stock");
    }
  };

  // Récupérer les alertes
  const fetchAlerts = async () => {
    try {
      const response = await axios.get("http://localhost:9000/stock/alerts");
      setAlerts(response.data);
    } catch (error) {
      console.error("Erreur:", error);
    }
  };

  // Récupérer les statistiques
  const fetchStatistics = async () => {
    try {
      const response = await axios.get("http://localhost:9000/stock/statistics");
      setStatistics(response.data);
    } catch (error) {
      console.error("Erreur:", error);
    }
  };

  // Modifier le stock d'un produit
  const handleUpdateStock = async (productUri) => {
    if (!newStockValue || newStockValue < 0) {
      alert("Veuillez entrer une quantité valide");
      return;
    }

    try {
      await axios.put("http://localhost:9000/stock/update", {
        produit_uri: productUri,
        quantite: parseInt(newStockValue)
      });
      alert("Stock mis à jour avec succès!");
      setEditingStock(null);
      setNewStockValue("");
      // Rafraîchir toutes les données
      fetchAllStock();
      fetchAlerts();
      fetchStatistics();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de la mise à jour: " + (error.response?.data?.error || error.message));
    }
  };

  // Préparer l'édition du stock
  const handleEditStock = (product) => {
    setEditingStock(product.produit?.value);
    setNewStockValue(product.stock?.value || "0");
  };

  // Annuler l'édition
  const cancelEdit = () => {
    setEditingStock(null);
    setNewStockValue("");
  };

  // Recherche NLP du stock
  const handleSearchNLP = async () => {
    if (!searchQuery.trim()) {
      alert("Veuillez entrer une question");
      return;
    }

    setSearching(true);
    try {
      const response = await axios.post("http://localhost:9000/search-stock-nlp", null, {
        params: { question: searchQuery }
      });
      
      if (response.data.error) {
        alert("Erreur: " + response.data.error);
        setSearching(false);
        return;
      }

      setSearchResults(response.data.results);
      setSearching(false);
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de la recherche: " + (error.response?.data?.error || error.message));
      setSearching(false);
    }
  };

  // Réinitialiser la recherche
  const resetSearch = () => {
    setSearchQuery("");
    setSearchResults(null);
    fetchAllStock();
  };

  // Déterminer le badge de stock
  const getStockBadge = (stockValue) => {
    const stock = parseInt(stockValue || 0);
    if (stock === 0) {
      return <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-xs font-bold">🔴 RUPTURE</span>;
    } else if (stock < 10) {
      return <span className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-xs font-bold">🟠 {stock} unités</span>;
    } else {
      return <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-bold">🟢 {stock} unités</span>;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-indigo-50">
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800">Gestion du Stock</h1>
          <button
            onClick={() => navigate("/")}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded-xl font-semibold transition-all flex items-center gap-2"
          >
            <HomeIcon size={20} /> Retour à l'accueil
          </button>
        </div>

        {/* Statistiques du Stock */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 shadow-md text-white">
              <div className="text-blue-100 text-sm mb-1">Stock Total</div>
              <div className="text-3xl font-bold">{statistics.stock_total}</div>
              <div className="text-blue-100 text-xs mt-1">unités</div>
            </div>
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6 shadow-md text-white">
              <div className="text-blue-100 text-sm mb-1">En Stock</div>
              <div className="text-3xl font-bold">{statistics.produits_en_stock}</div>
              <div className="text-blue-100 text-xs mt-1">produits</div>
            </div>
            <div className="bg-gradient-to-br from-blue-700 to-blue-800 rounded-xl p-6 shadow-md text-white">
              <div className="text-blue-100 text-sm mb-1">Ruptures</div>
              <div className="text-3xl font-bold">{statistics.produits_rupture}</div>
              <div className="text-blue-100 text-xs mt-1">produits</div>
            </div>
            <div className="bg-gradient-to-br from-blue-400 to-blue-500 rounded-xl p-6 shadow-md text-white">
              <div className="text-blue-100 text-sm mb-1">Valeur Stock</div>
              <div className="text-3xl font-bold">{statistics.valeur_stock}€</div>
              <div className="text-blue-100 text-xs mt-1">total</div>
            </div>
          </div>
        )}

        {/* Alertes Stock */}
        {(alerts.rupture.length > 0 || alerts.stock_faible.length > 0) && (
          <div className="bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-red-500 rounded-2xl shadow-lg p-6 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="text-red-600" size={28} />
              <h2 className="text-2xl font-bold text-gray-800">
                Alertes Stock ({alerts.total_alertes || 0})
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Rupture de stock */}
              {alerts.rupture.length > 0 && (
                <div className="bg-white rounded-xl p-4 border-2 border-red-200">
                  <h3 className="font-bold text-red-700 mb-3 flex items-center gap-2">
                    <span className="bg-red-500 text-white px-2 py-1 rounded-full text-sm">
                      {alerts.rupture.length}
                    </span>
                    🔴 Rupture de stock
                  </h3>
                  <ul className="space-y-2">
                    {alerts.rupture.map((product, index) => (
                      <li key={index} className="text-sm text-gray-700 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                          <span>{product.produit?.value.split("#")[1] || "N/A"}</span>
                          <span className="text-gray-500">({product.marque?.value.split("#")[1] || "N/A"})</span>
                        </div>
                        <button
                          onClick={() => handleEditStock(product)}
                          className="text-blue-600 hover:text-blue-800 text-xs"
                        >
                          Réapprovisionner
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Stock faible */}
              {alerts.stock_faible.length > 0 && (
                <div className="bg-white rounded-xl p-4 border-2 border-orange-200">
                  <h3 className="font-bold text-orange-700 mb-3 flex items-center gap-2">
                    <span className="bg-orange-500 text-white px-2 py-1 rounded-full text-sm">
                      {alerts.stock_faible.length}
                    </span>
                    🟠 Stock faible ({"<"} 10 unités)
                  </h3>
                  <ul className="space-y-2">
                    {alerts.stock_faible.map((product, index) => (
                      <li key={index} className="text-sm text-gray-700 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
                          <span>{product.produit?.value.split("#")[1] || "N/A"}</span>
                          <span className="text-gray-500">({product.stock?.value || 0} unités)</span>
                        </div>
                        <button
                          onClick={() => handleEditStock(product)}
                          className="text-blue-600 hover:text-blue-800 text-xs"
                        >
                          Modifier
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Recherche NLP */}
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl shadow-xl p-6 mb-6 border-2 border-indigo-200">
          <div className="flex items-center gap-3 mb-4">
            <MessageCircle className="text-indigo-600" size={28} />
            <h2 className="text-2xl font-bold text-gray-800">Recherche Intelligente du Stock</h2>
          </div>
          
          <p className="text-sm text-gray-600 mb-4">
            Posez des questions en langage naturel pour rechercher dans le stock (ex: "Produits en rupture de stock", "Stock des lave-linge Samsung", "Produits avec moins de 10 unités")
          </p>
          
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Ex: Produits en rupture de stock..."
                className="w-full pl-10 pr-4 py-3 border-2 border-indigo-300 rounded-xl focus:border-indigo-500 focus:outline-none"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleSearchNLP();
                  }
                }}
              />
            </div>
            <button
              onClick={handleSearchNLP}
              disabled={searching}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-semibold transition-all flex items-center gap-2 disabled:opacity-50"
            >
              <Search size={20} />
              {searching ? "Recherche..." : "Rechercher"}
            </button>
            {searchResults !== null && (
              <button
                onClick={resetSearch}
                className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-3 rounded-xl font-semibold transition-all"
              >
                Réinitialiser
              </button>
            )}
          </div>
          
          {searchResults && (
            <div className="mt-4 text-sm text-indigo-700 font-semibold">
              {searchResults.length} résultat(s) trouvé(s)
            </div>
          )}
        </div>

        {/* Tableau de tous les produits */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b">
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <Package size={24} />
              Inventaire {searchResults !== null ? "Recherche" : "Complet"} ({searchResults !== null ? searchResults.length : products.length} produits)
            </h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Produit</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Catégorie</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Marque</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Prix Unitaire</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Stock</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Valeur</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {(searchResults !== null ? searchResults : products).map((product, index) => {
                  const stock = parseInt(product.stock?.value || 0);
                  const prix = parseFloat(product.prix?.value || 0);
                  const valeur = stock * prix;
                  const isEditing = editingStock === product.produit?.value;

                  return (
                    <tr key={index} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {product.produit?.value.split("#")[1] || "N/A"}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">
                        {product.categorie?.value.split("#")[1] || "N/A"}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">
                        {product.marque?.value.split("#")[1] || "N/A"}
                      </td>
                      <td className="px-6 py-4 text-center text-sm text-gray-900 font-semibold">
                        {prix.toFixed(2)}€
                      </td>
                      <td className="px-6 py-4 text-center">
                        {isEditing ? (
                          <div className="flex items-center justify-center gap-2">
                            <input
                              type="number"
                              value={newStockValue}
                              onChange={(e) => setNewStockValue(e.target.value)}
                              className="w-20 px-2 py-1 border-2 border-blue-500 rounded-lg text-center"
                              min="0"
                            />
                            <button
                              onClick={() => handleUpdateStock(product.produit?.value)}
                              className="bg-green-500 text-white px-2 py-1 rounded-lg text-xs font-bold hover:bg-green-600"
                            >
                              ✓
                            </button>
                            <button
                              onClick={cancelEdit}
                              className="bg-gray-500 text-white px-2 py-1 rounded-lg text-xs font-bold hover:bg-gray-600"
                            >
                              ✗
                            </button>
                          </div>
                        ) : (
                          getStockBadge(product.stock?.value)
                        )}
                      </td>
                      <td className="px-6 py-4 text-center text-sm text-gray-900 font-semibold">
                        {valeur.toFixed(2)}€
                      </td>
                      <td className="px-6 py-4 text-center">
                        {!isEditing && (
                          <button
                            onClick={() => handleEditStock(product)}
                            className="text-blue-600 hover:text-blue-800 transition-colors"
                            title="Modifier le stock"
                          >
                            <Edit2 size={18} />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {(searchResults !== null ? searchResults : products).length === 0 && (
          <div className="text-center py-12 text-gray-500">
            {searchResults !== null ? "Aucun résultat trouvé" : "Aucun produit disponible"}
          </div>
        )}
      </main>
    </div>
  );
}

