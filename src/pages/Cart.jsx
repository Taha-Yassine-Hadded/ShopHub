import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Trash2, Plus, Minus, ShoppingBag, CreditCard } from 'lucide-react';
import CheckoutModal from '../components/CheckoutModal';
import OrderSuccessModal from '../components/OrderSuccessModal';

const Cart = () => {
  const [cartItems, setCartItems] = useState([]);
  const [cartSummary, setCartSummary] = useState({ totalItems: 0, totalAmount: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [orderData, setOrderData] = useState(null);

  const CLIENT_ID = 1; // Static client ID as requested

  // Fetch cart data
  const fetchCart = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:9000/cart/${CLIENT_ID}`);
      setCartItems(response.data.items || []);
      setCartSummary(response.data.summary || { totalItems: 0, totalAmount: 0 });
      setError('');
    } catch (err) {
      console.error('Error fetching cart:', err);
      setError('Erreur lors du chargement du panier');
    } finally {
      setLoading(false);
    }
  };

  // Remove item from cart
  const removeFromCart = async (productUri) => {
    try {
      await axios.delete(`http://localhost:9000/cart/${CLIENT_ID}/remove`, {
        data: { product_uri: productUri }
      });
      fetchCart(); // Refresh cart
      window.dispatchEvent(new CustomEvent('cartUpdated')); // Update cart count in layout
      toast.success('Produit retiré du panier');
    } catch (err) {
      console.error('Error removing from cart:', err);
      setError('Erreur lors de la suppression du produit');
      toast.error('Erreur lors de la suppression du produit');
    }
  };

  // Update quantity of item in cart
  const updateQuantity = async (productUri, newQuantity) => {
    if (newQuantity < 1) return;
    
    try {
      await axios.put(`http://localhost:9000/cart/${CLIENT_ID}/update-quantity`, {
        product_uri: productUri,
        quantity: newQuantity
      });
      fetchCart(); // Refresh cart
      window.dispatchEvent(new CustomEvent('cartUpdated')); // Update cart count in layout
      toast.success('Quantité mise à jour');
    } catch (err) {
      console.error('Error updating quantity:', err);
      setError('Erreur lors de la mise à jour de la quantité');
      toast.error('Erreur lors de la mise à jour de la quantité');
    }
  };

  // Clear entire cart
  const clearCart = async () => {
    try {
      await axios.delete(`http://localhost:9000/cart/${CLIENT_ID}/clear`);
      fetchCart(); // Refresh cart
      window.dispatchEvent(new CustomEvent('cartUpdated')); // Update cart count in layout
      toast.success('Panier vidé avec succès');
    } catch (err) {
      console.error('Error clearing cart:', err);
      setError('Erreur lors de la suppression du panier');
      toast.error('Erreur lors de la suppression du panier');
    }
  };

  // Checkout cart
  const handleCheckoutClick = () => {
    setShowCheckoutModal(true);
  };

  const handleConfirmOrder = async (orderDetails) => {
    try {
      setCheckoutLoading(true);
      const response = await axios.post(`http://localhost:9000/cart/${CLIENT_ID}/checkout`, orderDetails);
      if (response.data.success) {
        // Store order data for success modal
        setOrderData(response.data);
        
        // Show success modal instead of toast
        setShowCheckoutModal(false);
        setShowSuccessModal(true);
        
        fetchCart(); // Refresh cart (should be empty now)
        window.dispatchEvent(new CustomEvent('cartUpdated')); // Update cart count in layout
      }
    } catch (err) {
      console.error('Error during checkout:', err);
      setError('Erreur lors de la commande');
      toast.error('Erreur lors de la commande');
    } finally {
      setCheckoutLoading(false);
    }
  };

  // Extract product name from URI
  const getProductName = (uri) => {
    if (!uri) return 'Produit inconnu';
    const parts = uri.split('#');
    return parts[parts.length - 1] || 'Produit';
  };

  // Extract brand name from URI
  const getBrandName = (uri) => {
    if (!uri) return '';
    const parts = uri.split('#');
    return parts[parts.length - 1] || '';
  };

  // Extract category name from URI
  const getCategoryName = (uri) => {
    if (!uri) return '';
    const parts = uri.split('#');
    return parts[parts.length - 1] || '';
  };

  useEffect(() => {
    fetchCart();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Chargement du panier...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-16">
        <div className="container mx-auto px-4 text-center">
          <ShoppingBag className="mx-auto mb-4" size={64} />
          <h1 className="text-4xl font-bold mb-4">Mon Panier</h1>
          <p className="text-xl opacity-90">
            {cartSummary.totalItems} article{cartSummary.totalItems !== 1 ? 's' : ''} - 
            {cartSummary.totalAmount.toFixed(2)} €
          </p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {cartItems.length === 0 ? (
          <div className="text-center py-16">
            <ShoppingBag className="mx-auto mb-4 text-gray-400" size={64} />
            <h2 className="text-2xl font-semibold text-gray-600 mb-4">Votre panier est vide</h2>
            <p className="text-gray-500 mb-8">Découvrez nos produits et ajoutez-les à votre panier</p>
            <a 
              href="/" 
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center"
            >
              <ShoppingBag className="mr-2" size={20} />
              Continuer mes achats
            </a>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Cart Items */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-semibold">Articles dans votre panier</h2>
                  <button
                    onClick={clearCart}
                    className="text-red-600 hover:text-red-800 flex items-center"
                  >
                    <Trash2 className="mr-1" size={16} />
                    Vider le panier
                  </button>
                </div>

                <div className="space-y-4">
                  {cartItems.map((item, index) => (
                    <div key={index} className="border-b pb-4 last:border-b-0">
                      <div className="flex items-center space-x-4">
                        {/* Product Image */}
                        <div className="w-20 h-20 bg-gray-200 rounded-lg flex-shrink-0 overflow-hidden">
                          {item.image ? (
                            <img
                              src={item.image}
                              alt={getProductName(item.product_uri)}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                e.target.style.display = 'none';
                              }}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-gray-400">
                              <ShoppingBag size={24} />
                            </div>
                          )}
                        </div>

                        {/* Product Details */}
                        <div className="flex-1">
                          <h3 className="font-semibold text-lg">
                            {getProductName(item.product_uri)}
                          </h3>
                          {item.brand && (
                            <p className="text-gray-600">
                              Marque: {getBrandName(item.brand)}
                            </p>
                          )}
                          {item.category && (
                            <p className="text-gray-600">
                              Catégorie: {getCategoryName(item.category)}
                            </p>
                          )}
                          {item.description && (
                            <p className="text-gray-500 text-sm mt-1 line-clamp-2">
                              {item.description}
                            </p>
                          )}
                          
                          {/* Quantity Controls */}
                          <div className="flex items-center mt-3 space-x-3">
                            <span className="text-gray-600 text-sm">Quantité:</span>
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => updateQuantity(item.product_uri, item.quantity - 1)}
                                disabled={item.quantity <= 1}
                                className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                              >
                                <Minus size={14} />
                              </button>
                              <span className="w-8 text-center font-medium">{item.quantity}</span>
                              <button
                                onClick={() => updateQuantity(item.product_uri, item.quantity + 1)}
                                className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 transition-colors"
                              >
                                <Plus size={14} />
                              </button>
                            </div>
                          </div>
                        </div>

                        {/* Price and Actions */}
                        <div className="text-right">
                          <div className="mb-2">
                            <p className="text-sm text-gray-500">Prix unitaire</p>
                            <p className="text-lg font-semibold text-gray-700">
                              {item.price ? `${parseFloat(item.price).toFixed(2)} €` : 'N/A'}
                            </p>
                          </div>
                          <div className="mb-3">
                            <p className="text-sm text-gray-500">Total</p>
                            <p className="text-xl font-bold text-blue-600">
                              {item.price ? `${(parseFloat(item.price) * item.quantity).toFixed(2)} €` : 'Prix non disponible'}
                            </p>
                          </div>
                          <button
                            onClick={() => removeFromCart(item.product_uri)}
                            className="text-red-600 hover:text-red-800 flex items-center justify-end w-full"
                          >
                            <Trash2 className="mr-1" size={16} />
                            Supprimer
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Cart Summary */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
                <h3 className="text-xl font-semibold mb-4">Résumé de la commande</h3>
                
                <div className="space-y-3 mb-6">
                  <div className="flex justify-between">
                    <span>Articles ({cartSummary.totalItems})</span>
                    <span>{cartSummary.totalAmount.toFixed(2)} €</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Livraison</span>
                    <span className="text-green-600">Gratuite</span>
                  </div>
                  <hr />
                  <div className="flex justify-between text-xl font-bold">
                    <span>Total</span>
                    <span>{cartSummary.totalAmount.toFixed(2)} €</span>
                  </div>
                </div>

                <button
                  onClick={handleCheckoutClick}
                  disabled={checkoutLoading || cartItems.length === 0}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {checkoutLoading ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  ) : (
                    <>
                      <CreditCard className="mr-2" size={20} />
                      Passer la commande
                    </>
                  )}
                </button>

                <a 
                  href="/" 
                  className="w-full mt-3 border border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center"
                >
                  Continuer mes achats
                </a>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Checkout Modal */}
      <CheckoutModal
        isOpen={showCheckoutModal}
        onClose={() => setShowCheckoutModal(false)}
        cartItems={cartItems}
        cartSummary={cartSummary}
        onConfirmOrder={handleConfirmOrder}
      />

      {/* Order Success Modal */}
      <OrderSuccessModal
        isOpen={showSuccessModal}
        onClose={() => {
          setShowSuccessModal(false);
          setOrderData(null);
        }}
        orderData={orderData}
      />
    </div>
  );
};

export default Cart;