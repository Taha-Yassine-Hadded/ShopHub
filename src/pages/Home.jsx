import React, { useState, useEffect } from "react";
import axios from "axios";
import { ShoppingCart, Search, Package, Info, Tag } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const [products, setProducts] = useState([]);
  const [promotions, setPromotions] = useState([]);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProducts();
    fetchPromotions();
  }, []);

  const fetchProducts = async (filter = "") => {
    try {
      const response = await axios.get(`http://localhost:9000/sparql?question=${encodeURIComponent(filter || "liste des produits")}`);
      if (response.data.error) {
        setError(response.data.error);
        setProducts([]);
      } else {
        setProducts(response.data.results || []);
        setError(null);
      }
    } catch (err) {
      setError("Erreur lors de la récupération des produits.");
      setProducts([]);
    }
  };

  const fetchPromotions = async () => {
    try {
      const response = await axios.get("http://localhost:9000/promotions/actives");
      setPromotions(response.data.promotions_actives || []);
    } catch (err) {
      console.error("Erreur lors de la récupération des promotions:", err);
    }
  };

  const getProductPromotion = (productUri) => {
    return promotions.find(promo => promo.produit?.value === productUri);
  };

  const calculatePromotionalPrice = (originalPrice, promotion) => {
    if (!promotion) return originalPrice;
    
    let finalPrice = originalPrice;
    
    // Appliquer la réduction en pourcentage
    if (promotion.pourcentage?.value) {
      const percentage = parseFloat(promotion.pourcentage.value);
      finalPrice = finalPrice * (1 - percentage / 100);
    }
    
    // Appliquer la réduction fixe
    if (promotion.reduction?.value) {
      const reduction = parseFloat(promotion.reduction.value);
      finalPrice = finalPrice - reduction;
    }
    
    return Math.max(0, finalPrice).toFixed(2);
  };

  const handleFilter = () => {
    fetchProducts(query);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleFilter();
    }
  };

  const addToCart = (product) => {
    setCart([...cart, product]);
    const btn = event.target.closest("button");
    btn.classList.add("scale-95");
    setTimeout(() => btn.classList.remove("scale-95"), 200);
  };

  const handleProductDetail = (product) => {
    console.log("Produit sélectionné:", product); // Débogage
    navigate(`/product/${encodeURIComponent(product.produit.value)}`, { state: { product } });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-800 mb-4">Découvrez Nos Électroménagers</h2>
          <p className="text-gray-600 text-lg mb-8">Les meilleurs produits pour votre maison au meilleur prix</p>
        </div>

        {/* Search Bar */}
        <div className="max-w-3xl mx-auto mb-12">
          <div className="relative flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ex: 'liste des produits', 'produits par categorie Lave-vaisselle', 'products with price less than 500'"
                className="w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition-colors shadow-sm"
              />
            </div>
            <button
              onClick={handleFilter}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-xl font-semibold transition-all shadow-md hover:shadow-lg flex items-center gap-2"
            >
              <Search size={20} /> Rechercher
            </button>
          </div>
        </div>

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
              {products.map((product, index) => {
                const promotion = getProductPromotion(product.produit?.value);
                const originalPrice = parseFloat(product.prix?.value || 0);
                const promotionalPrice = promotion ? calculatePromotionalPrice(originalPrice, promotion) : null;
                const discountPercentage = promotion && promotion.pourcentage?.value ? parseFloat(promotion.pourcentage.value) : null;

                return (
                  <div
                    key={index}
                    className="bg-white rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden group"
                  >
                    {/* Product Image */}
                    <div className="relative h-64 bg-gray-100 overflow-hidden">
                      {product.image ? (
                        <img
                          src={product.image.value}
                          alt={product.produit?.value.split("#")[1] || "Produit"}
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
                      {promotion && (
                        <span className="absolute top-4 right-4 bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold flex items-center gap-1 animate-pulse">
                          <Tag size={16} /> PROMO
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
                      
                      {/* Prix */}
                      <div className="flex items-center gap-3 mb-4">
                        {promotion ? (
                          <div className="flex flex-col">
                            <div className="flex items-center gap-2">
                              <span className="text-3xl font-bold text-red-600">{promotionalPrice} €</span>
                              {discountPercentage && (
                                <span className="bg-red-100 text-red-700 px-2 py-1 rounded-full text-xs font-bold">
                                  -{discountPercentage}%
                                </span>
                              )}
                            </div>
                            <span className="text-lg text-gray-400 line-through">{originalPrice.toFixed(2)} €</span>
                          </div>
                        ) : (
                          <span className="text-3xl font-bold text-blue-600">{originalPrice.toFixed(2)} €</span>
                        )}
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleProductDetail(product)}
                          className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-800 py-3 rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
                        >
                          <Info size={18} /> Détails
                        </button>
                        <button
                          onClick={() => addToCart(product)}
                          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
                        >
                          <ShoppingCart size={18} /> Ajouter
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Empty State */}
        {products.length === 0 && !error && (
          <div className="text-center py-16">
            <Package size={80} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500 text-lg">Aucun produit trouvé. Essayez une autre recherche.</p>
          </div>
        )}
      </main>
    </div>
  );
}