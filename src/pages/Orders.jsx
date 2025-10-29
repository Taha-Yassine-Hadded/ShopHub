import React, { useState, useEffect } from 'react';
import { Package, Calendar, CreditCard, User, MapPin, X, AlertCircle, CheckCircle, Trash2 } from 'lucide-react';
import axios from 'axios';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [cancellingOrder, setCancellingOrder] = useState(null);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:9000/orders');
      setOrders(response.data);
      setError('');
    } catch (error) {
      console.error('Error fetching orders:', error);
      setError('Erreur lors du chargement des commandes');
    } finally {
      setLoading(false);
    }
  };

  const cancelOrder = async (orderId) => {
    try {
      setCancellingOrder(orderId);
      await axios.delete(`http://localhost:9000/orders/${orderId}`);
      
      // Update the orders list by removing the cancelled order
      setOrders(orders.filter(order => order.id !== orderId));
      
      // Show success message (you could add a toast notification here)
      console.log('Commande annulée avec succès');
    } catch (error) {
      console.error('Error cancelling order:', error);
      setError('Erreur lors de l\'annulation de la commande');
    } finally {
      setCancellingOrder(null);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'pending':
      case 'en_attente':
        return 'bg-yellow-100 text-yellow-800';
      case 'confirmed':
      case 'confirmee':
        return 'bg-green-100 text-green-800';
      case 'shipped':
      case 'expediee':
        return 'bg-blue-100 text-blue-800';
      case 'delivered':
      case 'livree':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
      case 'annulee':
      case 'annule':
      case 'annulée':
        return 'bg-red-500 text-white';
      case 'en_cours':
        return 'bg-green-500 text-white';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status?.toLowerCase()) {
      case 'pending':
      case 'en_attente':
        return 'En attente';
      case 'confirmed':
      case 'confirmee':
        return 'Confirmée';
      case 'shipped':
      case 'expediee':
        return 'Expédiée';
      case 'delivered':
      case 'livree':
        return 'Livrée';
      case 'cancelled':
      case 'annulee':
      case 'annule':
      case 'annulée':
        return 'Annulée';
      case 'en_cours':
        return 'En cours';
      default:
        return status || 'Statut inconnu';
    }
  };

  const canCancelOrder = (status) => {
    const cancelableStatuses = ['pending', 'en_attente', 'confirmed', 'confirmee'];
    return cancelableStatuses.includes(status?.toLowerCase());
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement de vos commandes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Mes Commandes</h1>
          <p className="text-gray-600">Consultez et gérez vos commandes</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-lg flex items-center">
            <AlertCircle className="mr-2" size={20} />
            <p>{error}</p>
          </div>
        )}

        {/* Orders List */}
        {orders.length === 0 ? (
          <div className="text-center py-16">
            <Package size={80} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-xl font-semibold text-gray-600 mb-2">Aucune commande trouvée</h3>
            <p className="text-gray-500 mb-6">Vous n'avez pas encore passé de commande.</p>
            <a 
              href="/" 
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center"
            >
              <Package className="mr-2" size={20} />
              Commencer mes achats
            </a>
          </div>
        ) : (
          <div className="space-y-6">
            {orders
              .sort((a, b) => {
                // Priority order: "En cours" first, then "Annulée"/cancelled, then others
                const getPriority = (status) => {
                  const statusLower = status?.toLowerCase();
                  if (statusLower === 'en cours') return 0; // Highest priority (first)
                  if (['cancelled', 'annulee', 'annule', 'annulée'].includes(statusLower)) return 1; // Second priority
                  return 2; // Lowest priority (last)
                };
                return getPriority(a.status) - getPriority(b.status);
              })
              .map((order) => (
              <div key={order.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                {/* Order Header */}
                <div className="bg-gray-50 px-6 py-4 border-b">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                    <div className="flex items-center space-x-4 mb-2 md:mb-0">
                      <h3 className="text-lg font-semibold text-gray-900">
                        Commande #{order.id}
                      </h3>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
                        {getStatusText(order.status)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <div className="flex items-center">
                        <Calendar className="mr-1" size={16} />
                        {new Date(order.order_date || order.created_at).toLocaleDateString('fr-FR')}
                      </div>
                      <div className="flex items-center">
                        <CreditCard className="mr-1" size={16} />
                        {order.total_amount?.toFixed(2)} €
                      </div>
                    </div>
                  </div>
                </div>

                {/* Order Content */}
                <div className="p-6">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Customer Information */}
                    <div>
                      <h4 className="text-lg font-semibold mb-4 flex items-center">
                        <User className="mr-2" size={20} />
                        Informations de livraison
                      </h4>
                      <div className="space-y-2 text-sm">
                        <p><span className="font-medium">Nom:</span> {order.full_name}</p>
                        <p><span className="font-medium">Email:</span> {order.email}</p>
                        <p><span className="font-medium">Téléphone:</span> {order.phone}</p>
                        <div className="flex items-start">
                          <MapPin className="mr-1 mt-0.5 flex-shrink-0" size={16} />
                          <div>
                            <span className="font-medium">Adresse:</span>
                            <p className="text-gray-600">{order.delivery_address}</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Order Summary */}
                    <div>
                      <h4 className="text-lg font-semibold mb-4 flex items-center">
                        <Package className="mr-2" size={20} />
                        Résumé de la commande
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Total articles:</span>
                          <span className="font-medium">{order.total_items}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Livraison:</span>
                          <span className="text-green-600 font-medium">Gratuite</span>
                        </div>
                        <hr className="my-2" />
                        <div className="flex justify-between text-lg font-bold">
                          <span>Total:</span>
                          <span className="text-blue-600">{order.total_amount?.toFixed(2)} €</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  {!['cancelled', 'annulee', 'annule', 'annulée'].includes(order.status?.toLowerCase()) && (
                    <div className="mt-6 pt-4 border-t flex flex-col sm:flex-row gap-3">
                      <button
                        onClick={() => cancelOrder(order.id)}
                        disabled={cancellingOrder === order.id}
                        className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center"
                      >
                        {cancellingOrder === order.id ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Suppression...
                          </>
                        ) : (
                          <>
                            <Trash2 className="mr-2" size={18} />
                            Supprimer
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Orders;