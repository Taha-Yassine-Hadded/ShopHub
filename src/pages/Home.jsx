import React, { useState, useEffect } from "react";
import axios from "axios";
import { ShoppingCart, Search, Package, Info } from "lucide-react";

export default function Home() {
  const [products, setProducts] = useState([]);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generatedSparql, setGeneratedSparql] = useState("");

  useEffect(() => {
    // load default list on mount
    fetchProducts("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // unified fetch using NLQ endpoint (POST /nlq)
  const fetchProducts = async (nlQuery = "") => {
    setLoading(true);
    setError(null);
    setGeneratedSparql("");
    try {
      const body = { question: nlQuery && nlQuery.trim() ? nlQuery.trim() : "liste des produits" };
      const response = await axios.post("http://localhost:9000/nlq", body, {
        headers: { "Content-Type": "application/json" },
      });

      // backend returns { sparql, results }
      if (response.data?.sparql) {
        setGeneratedSparql(response.data.sparql);
      } else {
        setGeneratedSparql("");
      }

      if (response.data?.results) {
        setProducts(response.data.results);
      } else if (response.data?.results === undefined && response.data?.error) {
        setProducts([]);
        setError(response.data.error);
      } else {
        setProducts([]);
      }
    } catch (err) {
      // handle axios errors and backend error payloads
      const serverDetail = err?.response?.data?.detail || err?.response?.data?.error;
      setError(serverDetail || "Erreur lors de la récupération des produits.");
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = () => {
    fetchProducts(query);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleFilter();
    }
  };

  const addToCart = (product, event) => {
    setCart((prev) => [...prev, product]);

    // Animation feedback (safe guard if event absent)
    try {
      if (event && event.currentTarget) {
        const btn = event.currentTarget;
        btn.classList.add("scale-95");
        setTimeout(() => btn.classList.remove("scale-95"), 200);
      }
    } catch (err) {
      // ignore animation errors
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-800 mb-4">Découvrez Nos Électroménagers</h2>
          <p className="text-gray-600 text-lg">
            Les meilleurs produits pour votre maison au meilleur prix
          </p>
        </div>

        {/* Search Bar */}
        <div className="max-w-3xl mx-auto mb-6">
          <div className="relative flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ex: 'liste des produits', 'produits par categorie Lave-vaisselle', 'products with price less than 500'"
                className="w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition-colors shadow-sm"
              />
            </div>
            <button
              onClick={handleFilter}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-xl font-semibold transition-all shadow-md hover:shadow-lg flex items-center gap-2"
            >
              <Search size={20} />
              Rechercher
            </button>
          </div>
        </div>

        {/* Loading / SPARQL preview */}
        {loading && (
          <div className="max-w-3xl mx-auto mb-4 text-center text-gray-600">Recherche en cours…</div>
        )}

        {generatedSparql && (
          <div className="max-w-3xl mx-auto mb-6 bg-gray-50 border p-3 rounded-lg text-sm text-gray-700">
            <strong>SPARQL généré:</strong>
            <pre className="whitespace-pre-wrap text-xs mt-2">{generatedSparql}</pre>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="max-w-3xl mx-auto mb-8 bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-lg">
            <p className="font-semibold">{error}</p>
          </div>
        )}

        {/* Products Grid */}
        {products.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-gray-800">Produits Disponibles ({products.length})</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {products.map((product, index) => (
                <div
                  key={index}
                  className="bg-white rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden group"
                >
                  {/* Product Image */}
                  <div className="relative h-64 bg-gray-100 overflow-hidden">
                    {product.image ? (
                      <img
                        src={product.image.value}
                        alt={product.produit?.value?.split("#")[1] || "Produit"}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Package size={64} className="text-gray-300" />
                      </div>
                    )}
                    {product.categorie && (
                      <span className="absolute top-4 left-4 bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                        {product.categorie.value.split("#")[1]}
                      </span>
                    )}
                  </div>

                  {/* Product Info */}
                  <div className="p-6">
                    <h4 className="text-xl font-bold text-gray-800 mb-2 line-clamp-1">
                      {product.produit?.value.split("#")[1] || "Produit"}
                    </h4>

                    {product.marque && (
                      <p className="text-sm text-gray-500 mb-3">
                        Marque: <span className="font-semibold text-gray-700">{product.marque.value.split("#")[1]}</span>
                      </p>
                    )}

                    {product.description && (
                      <p className="text-gray-600 text-sm mb-4 line-clamp-2">{product.description.value}</p>
                    )}

                    <div className="flex items-center justify-between mb-4">
                      <span className="text-3xl font-bold text-blue-600">{product.prix?.value || "N/A"} €</span>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => setSelectedProduct(product)}
                        className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-800 py-3 rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
                      >
                        <Info size={18} />
                        Détails
                      </button>
                      <button
                        onClick={(e) => addToCart(product, e)}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
                      >
                        <ShoppingCart size={18} />
                        Ajouter
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {products.length === 0 && !error && !loading && (
          <div className="text-center py-16">
            <Package size={80} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500 text-lg">Aucun produit trouvé. Essayez une autre recherche.</p>
          </div>
        )}
      </main>

      {/* Product Details Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedProduct(null)}>
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="relative">
              {selectedProduct.image && (
                <img src={selectedProduct.image.value} alt={selectedProduct.produit?.value.split("#")[1]} className="w-full h-80 object-cover" />
              )}
              <button onClick={() => setSelectedProduct(null)} className="absolute top-4 right-4 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100">
                ✕
              </button>
            </div>

            <div className="p-8">
              <h3 className="text-3xl font-bold text-gray-800 mb-4">{selectedProduct.produit?.value.split("#")[1]}</h3>

              <div className="space-y-4 mb-6">
                {selectedProduct.marque && (
                  <div>
                    <span className="text-sm text-gray-500">Marque:</span>
                    <p className="text-lg font-semibold text-gray-800">{selectedProduct.marque.value.split("#")[1]}</p>
                  </div>
                )}

                {selectedProduct.categorie && (
                  <div>
                    <span className="text-sm text-gray-500">Catégorie:</span>
                    <p className="text-lg font-semibold text-gray-800">{selectedProduct.categorie.value.split("#")[1]}</p>
                  </div>
                )}

                {selectedProduct.description && (
                  <div>
                    <span className="text-sm text-gray-500">Description:</span>
                    <p className="text-gray-700 leading-relaxed">{selectedProduct.description.value}</p>
                  </div>
                )}

                <div>
                  <span className="text-sm text-gray-500">Prix:</span>
                  <p className="text-4xl font-bold text-blue-600">{selectedProduct.prix?.value || "N/A"} €</p>
                </div>
              </div>

              <button
                onClick={(e) => {
                  addToCart(selectedProduct, e);
                  setSelectedProduct(null);
                }}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-3 shadow-lg hover:shadow-xl"
              >
                <ShoppingCart size={24} />
                Ajouter au Panier
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
