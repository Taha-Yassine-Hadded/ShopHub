import React from 'react';
import { CheckCircle, X, Package, Calendar, CreditCard, User, MapPin, Phone, Mail } from 'lucide-react';

const OrderSuccessModal = ({ isOpen, onClose, orderData }) => {
  if (!isOpen || !orderData) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b bg-green-50">
          <div className="flex items-center">
            <CheckCircle className="text-green-600 mr-3" size={32} />
            <div>
              <h2 className="text-2xl font-bold text-green-800">Commande confirmée!</h2>
              <p className="text-green-600">Votre commande a été créée avec succès</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <div className="p-6">
          {/* Order Summary */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center">
                <Package className="mr-2" size={20} />
                Détails de la commande
              </h3>
              <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                ID: {orderData.order_id}
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center">
                <Calendar className="text-gray-400 mr-2" size={16} />
                <span className="text-sm text-gray-600">Date:</span>
                <span className="ml-2 font-medium">{new Date().toLocaleDateString('fr-FR')}</span>
              </div>
              <div className="flex items-center">
                <Package className="text-gray-400 mr-2" size={16} />
                <span className="text-sm text-gray-600">Articles:</span>
                <span className="ml-2 font-medium">{orderData.total_items}</span>
              </div>
              <div className="flex items-center md:col-span-2">
                <CreditCard className="text-gray-400 mr-2" size={16} />
                <span className="text-sm text-gray-600">Montant total:</span>
                <span className="ml-2 font-bold text-lg text-green-600">{orderData.total_amount?.toFixed(2)} €</span>
              </div>
            </div>
          </div>

          {/* Customer Information */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <User className="mr-2" size={20} />
              Informations de livraison
            </h3>
            
            <div className="space-y-3">
              <div className="flex items-start">
                <User className="text-gray-400 mr-2 mt-1" size={16} />
                <div>
                  <span className="text-sm text-gray-600">Nom:</span>
                  <p className="font-medium">{orderData.order_details?.full_name}</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <Mail className="text-gray-400 mr-2 mt-1" size={16} />
                <div>
                  <span className="text-sm text-gray-600">Email:</span>
                  <p className="font-medium">{orderData.order_details?.email}</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <Phone className="text-gray-400 mr-2 mt-1" size={16} />
                <div>
                  <span className="text-sm text-gray-600">Téléphone:</span>
                  <p className="font-medium">{orderData.order_details?.phone}</p>
                </div>
              </div>
              
              <div className="flex items-start">
                <MapPin className="text-gray-400 mr-2 mt-1" size={16} />
                <div>
                  <span className="text-sm text-gray-600">Adresse de livraison:</span>
                  <p className="font-medium">{orderData.order_details?.delivery_address}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Next Steps */}
          <div className="bg-blue-50 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-3">Prochaines étapes</h3>
            <ul className="space-y-2 text-sm text-blue-700">
              <li className="flex items-center">
                <CheckCircle className="mr-2" size={16} />
                Votre commande est en cours de traitement
              </li>
              <li className="flex items-center">
                <CheckCircle className="mr-2" size={16} />
                Vous recevrez un email de confirmation à {orderData.order_details?.email}
              </li>
              <li className="flex items-center">
                <CheckCircle className="mr-2" size={16} />
                Nous vous contacterons au {orderData.order_details?.phone} pour la livraison
              </li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={onClose}
              className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-semibold"
            >
              Continuer mes achats
            </button>
            <button
              onClick={() => {
                // You can add order tracking functionality here
                onClose();
              }}
              className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 transition-colors font-semibold"
            >
              Suivre ma commande
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderSuccessModal;