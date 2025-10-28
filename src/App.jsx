import React from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import ProductDetail from "./pages/ProductDetail";
import ProductManagement from "./pages/ProductManagement"; // ← NOUVELLE LIGNE

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/product/:id" element={<ProductDetail />} />
        <Route path="/manage-products" element={<ProductManagement />} />
      </Route>
    </Routes>
  );
}
