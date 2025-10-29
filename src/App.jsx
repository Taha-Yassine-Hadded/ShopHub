import React from "react";
import { Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Cart from "./pages/Cart";
import Orders from "./pages/Orders";
import ProductDetail from "./pages/ProductDetail";
import ProductManagement from "./pages/ProductManagement";
import SupplierManagement from "./pages/SupplierManagement";
import StockManagement from "./pages/StockManagement";
import ClientManagement from "./pages/ClientManagement";
import PromotionManagement from "./pages/PromotionManagement";
import Dashboard from "./pages/Dashboard";

export default function App() {
  return (
    <>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/manage-products" element={<ProductManagement />} />
          <Route path="/manage-suppliers" element={<SupplierManagement />} />
          <Route path="/manage-stock" element={<StockManagement />} />
          <Route path="/manage-clients" element={<ClientManagement />} />
          <Route path="/manage-promotions" element={<PromotionManagement />} />
        </Route>
      </Routes>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            theme: {
              primary: 'green',
              secondary: 'black',
            },
          },
        }}
      />
    </>
  );
}
