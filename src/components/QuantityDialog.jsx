import React, { useState } from 'react';
import { X, Plus, Minus, ShoppingCart } from 'lucide-react';

const QuantityDialog = ({ isOpen, onClose, onConfirm, productName }) => {
  const [quantity, setQuantity] = useState(1);

  const handleIncrement = () => {
    setQuantity(prev => prev + 1);
  };

  const handleDecrement = () => {
    if (quantity > 1) {
      setQuantity(prev => prev - 1);
    }
  };

  const handleConfirm = () => {
    onConfirm(quantity);
    setQuantity(1); // Reset quantity
    onClose();
  };

  const handleClose = () => {
    setQuantity(1); // Reset quantity
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Ajouter au panier
          </h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Product Info */}
        <div className="mb-6">
          <p className="text-gray-700 mb-2">Produit :</p>
          <p className="font-medium text-gray-900">{productName}</p>
        </div>

        {/* Quantity Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quantité
          </label>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleDecrement}
              disabled={quantity <= 1}
              className="w-10 h-10 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Minus size={16} />
            </button>
            
            <div className="flex-1 text-center">
              <input
                type="number"
                min="1"
                value={quantity}
                onChange={(e) => {
                  const value = parseInt(e.target.value);
                  if (value >= 1) {
                    setQuantity(value);
                  }
                }}
                className="w-20 text-center border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <button
              onClick={handleIncrement}
              className="w-10 h-10 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 transition-colors"
            >
              <Plus size={16} />
            </button>
          </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-3">
          <button
            onClick={handleClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
          >
            Annuler
          </button>
          <button
            onClick={handleConfirm}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center"
          >
            <ShoppingCart className="mr-2" size={16} />
            Ajouter ({quantity})
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuantityDialog;