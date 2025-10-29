import React, { useState, useEffect } from "react";
import { BarChart, PieChart, TrendingUp, Star, MessageSquare, Package } from "lucide-react";

export default function Dashboard() {
  const [avisStats, setAvisStats] = useState(null);
  const [categoryData, setCategoryData] = useState(null);
  const [brandData, setBrandData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [avisResponse, categoryResponse, brandResponse] = await Promise.all([
        fetch("http://localhost:9000/dashboard/avis-stats"),
        fetch("http://localhost:9000/dashboard/products-by-category"),
        fetch("http://localhost:9000/dashboard/products-by-brand")
      ]);

      const avisData = await avisResponse.json();
      const categoryDataJson = await categoryResponse.json();
      const brandDataJson = await brandResponse.json();

      setAvisStats(avisData);
      setCategoryData(categoryDataJson);
      setBrandData(brandDataJson);
      setError(null);
    } catch (err) {
      setError("Erreur lors du chargement des données du dashboard");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
    <div className={`bg-white rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 p-6 border-l-4 ${color}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-600 text-sm font-semibold mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-800">{value}</p>
          {subtitle && <p className="text-sm text-gray-500 mt-2">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl ${color.replace('border-', 'bg-').replace('-500', '-100')}`}>
          <Icon className={color.replace('border-', 'text-')} size={24} />
        </div>
      </div>
    </div>
  );

  const BarChartComponent = ({ data, title, color, allItems }) => {
    if (!data) return null;
    
    // Si allItems est fourni, créer un objet complet avec toutes les valeurs
    let completeData = { ...data };
    if (allItems) {
      allItems.forEach(item => {
        if (!(item in completeData)) {
          completeData[item] = 0;
        }
      });
    }
    
    const entries = Object.entries(completeData).sort((a, b) => b[1] - a[1]);
    const maxValue = Math.max(...entries.map(([, value]) => value), 1);

    return (
      <div className="bg-white rounded-2xl shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
          <BarChart size={24} className="text-blue-600" />
          {title}
        </h3>
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {entries.map(([name, value]) => (
            <div key={name}>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-semibold text-gray-700">{name}</span>
                <span className={`text-sm font-bold ${value === 0 ? 'text-gray-400' : 'text-gray-800'}`}>
                  {value} {value === 0 && '(vide)'}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${value === 0 ? 'bg-gray-300' : color}`}
                  style={{ width: `${(value / maxValue) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const PieChartComponent = ({ positive, negative, neutral }) => {
    const total = positive + negative + neutral;
    if (total === 0) return null;

    const positivePercent = (positive / total) * 100;
    const negativePercent = (negative / total) * 100;
    const neutralPercent = (neutral / total) * 100;

    return (
      <div className="bg-white rounded-2xl shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
          <PieChart size={24} className="text-blue-600" />
          Répartition des Avis
        </h3>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between mb-2">
                <span className="text-sm font-semibold text-green-700">Positifs</span>
                <span className="text-sm font-bold text-gray-800">{positive} ({positivePercent.toFixed(1)}%)</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div className="bg-green-500 h-full rounded-full transition-all duration-500" style={{ width: `${positivePercent}%` }} />
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between mb-2">
                <span className="text-sm font-semibold text-red-700">Négatifs</span>
                <span className="text-sm font-bold text-gray-800">{negative} ({negativePercent.toFixed(1)}%)</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div className="bg-red-500 h-full rounded-full transition-all duration-500" style={{ width: `${negativePercent}%` }} />
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between mb-2">
                <span className="text-sm font-semibold text-gray-700">Neutres</span>
                <span className="text-sm font-bold text-gray-800">{neutral} ({neutralPercent.toFixed(1)}%)</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div className="bg-gray-500 h-full rounded-full transition-all duration-500" style={{ width: `${neutralPercent}%` }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg font-semibold">Chargement des données...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center">
        <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-6 rounded-lg max-w-md">
          <p className="font-semibold">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-800 mb-4">Tableau de Bord</h2>
          <p className="text-gray-600 text-lg">Vue d'ensemble des statistiques et analyses</p>
        </div>

        {/* Stats Cards */}
        {avisStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              title="Total des Avis"
              value={avisStats.total_avis}
              icon={MessageSquare}
              color="border-blue-500"
            />
            <StatCard
              title="Avis Positifs"
              value={avisStats.avis_positive}
              icon={TrendingUp}
              color="border-green-500"
            />
            <StatCard
              title="Avis Négatifs"
              value={avisStats.avis_negative}
              icon={MessageSquare}
              color="border-red-500"
            />
            <StatCard
              title="Note Moyenne"
              value={avisStats.average_note}
              icon={Star}
              color="border-yellow-500"
              subtitle="Sur 5 étoiles"
            />
          </div>
        )}

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {avisStats && (
            <PieChartComponent
              positive={avisStats.avis_positive}
              negative={avisStats.avis_negative}
              neutral={avisStats.avis_neutral}
            />
          )}
          {categoryData && (
            <BarChartComponent
              data={categoryData}
              title="Produits par Catégorie"
              color="bg-blue-500"
            />
          )}
        </div>

        {/* Brand Chart */}
        {brandData && (
          <div className="mb-8">
            <BarChartComponent
              data={brandData}
              title="Produits par Marque"
              color="bg-purple-500"
            />
          </div>
        )}

        {/* Summary Section */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl shadow-xl p-8 text-white">
          <div className="flex items-center gap-4 mb-4">
            <Package size={32} />
            <h3 className="text-2xl font-bold">Résumé Global</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-blue-200 text-sm mb-1">Total Produits</p>
              <p className="text-3xl font-bold">
                {categoryData ? Object.values(categoryData).reduce((a, b) => a + b, 0) : 0}
              </p>
            </div>
            <div>
              <p className="text-blue-200 text-sm mb-1">Catégories</p>
              <p className="text-3xl font-bold">
                {categoryData ? Object.keys(categoryData).length : 0}
              </p>
            </div>
            <div>
              <p className="text-blue-200 text-sm mb-1">Marques</p>
              <p className="text-3xl font-bold">
                {brandData ? Object.keys(brandData).length : 0}
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}