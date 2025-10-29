import React from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import ProductDetail from "./pages/ProductDetail";
import ProductManagement from "./pages/ProductManagement";
import SupplierManagement from "./pages/SupplierManagement";
import StockManagement from "./pages/StockManagement";
import ClientManagement from "./pages/ClientManagement";
import PromotionManagement from "./pages/PromotionManagement";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/product/:id" element={<ProductDetail />} />
        <Route path="/manage-products" element={<ProductManagement />} />
        <Route path="/manage-suppliers" element={<SupplierManagement />} />
        <Route path="/manage-stock" element={<StockManagement />} />
        <Route path="/manage-clients" element={<ClientManagement />} />
        <Route path="/manage-promotions" element={<PromotionManagement />} />
      </Route>
    </Routes>
  );
}
