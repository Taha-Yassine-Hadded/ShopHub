import React, { useState, useEffect } from "react";
import axios from "axios";
import { Plus, Edit, Trash2, Save, X, Home as HomeIcon, Search, Users, Globe, Mail, Phone } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function ClientManagement() {
  const navigate = useNavigate();
  const [clients, setClients] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [nlpQuestion, setNlpQuestion] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [formData, setFormData] = useState({
    nom: "",
    prenom: "",
    adresse: "",
    telephone: "",
    email: "",
    pays: ""
  });

  // Charger tous les clients
  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await axios.get("http://localhost:9000/clients");
      setClients(response.data.clients || []);
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors du chargement des clients");
    }
  };

  // AJOUTER un client
  const handleAddClient = async (e) => {
    e.preventDefault();
    try {
      await axios.post("http://localhost:9000/add-client", {
        nom: formData.nom,
        prenom: formData.prenom,
        adresse: formData.adresse,
        telephone: formData.telephone,
        email: formData.email,
        pays: formData.pays
      });
      alert("Client ajouté avec succès!");
      resetForm();
      fetchClients();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de l'ajout: " + (error.response?.data?.error || error.message));
    }
  };

  // MODIFIER un client
  const handleUpdateClient = async (e) => {
    e.preventDefault();
    try {
      const updateData = {
        client_uri: editingClient.client.value,
      };
      
      if (formData.adresse) updateData.adresse = formData.adresse;
      if (formData.telephone) updateData.telephone = formData.telephone;
      if (formData.email) updateData.email = formData.email;
      if (formData.pays) updateData.pays = formData.pays;

      await axios.put("http://localhost:9000/update-client", updateData);
      alert("Client modifié avec succès!");
      resetForm();
      fetchClients();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de la modification: " + (error.response?.data?.error || error.message));
    }
  };

  // SUPPRIMER un client
  const handleDeleteClient = async (clientUri) => {
    if (!window.confirm("Voulez-vous vraiment supprimer ce client?")) return;
    
    try {
      await axios.delete(`http://localhost:9000/delete-client?client_uri=${encodeURIComponent(clientUri)}`);
      alert("Client supprimé avec succès!");
      fetchClients();
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de la suppression: " + (error.response?.data?.error || error.message));
    }
  };

  // Préparer le formulaire de modification
  const handleEditClick = (client) => {
    setEditingClient(client);
    const fullName = client.client?.value.split("#")[1] || "";
    const nameParts = fullName.split("_");
    
    setFormData({
      nom: nameParts[0] || "",
      prenom: nameParts.slice(1).join(" ") || "",
      adresse: client.adresse?.value || "",
      telephone: client.telephone?.value || "",
      email: client.email?.value || "",
      pays: client.pays?.value || ""
    });
    setShowAddForm(true);
  };

  // Réinitialiser le formulaire
  const resetForm = () => {
    setFormData({
      nom: "",
      prenom: "",
      adresse: "",
      telephone: "",
      email: "",
      pays: ""
    });
    setShowAddForm(false);
    setEditingClient(null);
  };

  // RECHERCHE NLP (Langage Naturel) pour Clients
  const handleNLPSearch = async () => {
    if (!nlpQuestion.trim()) {
      alert("Veuillez poser une question");
      return;
    }

    setIsSearching(true);
    try {
      const response = await axios.post(
        "http://localhost:9000/search-clients-nlp",
        null,
        { params: { question: nlpQuestion } }
      );
      
      if (response.data.error) {
        alert("Erreur: " + response.data.error);
      } else {
        setClients(response.data.results || []);
        console.log("SPARQL généré:", response.data.sparql_genere);
      }
    } catch (error) {
      console.error("Erreur:", error);
      alert("Erreur lors de la recherche: " + (error.response?.data?.error || error.message));
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800">Gestion des Clients</h1>
          <button
            onClick={() => navigate("/")}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 py-2 px-4 rounded-xl font-semibold transition-all flex items-center gap-2"
          >
            <HomeIcon size={20} /> Retour à l'accueil
          </button>
        </div>

        {/* Statistiques des Clients */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 shadow-md text-white">
            <div className="flex items-center justify-between mb-2">
              <div className="text-blue-100 text-sm">Total Clients</div>
              <Users className="text-blue-200" size={24} />
            </div>
            <div className="text-3xl font-bold">{clients.length}</div>
            <div className="text-blue-100 text-xs mt-1">clients enregistrés</div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6 shadow-md text-white">
            <div className="flex items-center justify-between mb-2">
              <div className="text-blue-100 text-sm">Pays</div>
              <Globe className="text-blue-200" size={24} />
            </div>
            <div className="text-3xl font-bold">
              {new Set(clients.map(c => c.pays?.value).filter(Boolean)).size}
            </div>
            <div className="text-blue-100 text-xs mt-1">pays différents</div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-700 to-blue-800 rounded-xl p-6 shadow-md text-white">
            <div className="flex items-center justify-between mb-2">
              <div className="text-blue-100 text-sm">Avec Email</div>
              <Mail className="text-blue-200" size={24} />
            </div>
            <div className="text-3xl font-bold">
              {clients.filter(c => c.email?.value && c.email.value.trim() !== "").length}
            </div>
            <div className="text-blue-100 text-xs mt-1">emails renseignés</div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-400 to-blue-500 rounded-xl p-6 shadow-md text-white">
            <div className="flex items-center justify-between mb-2">
              <div className="text-blue-100 text-sm">Avec Téléphone</div>
              <Phone className="text-blue-200" size={24} />
            </div>
            <div className="text-3xl font-bold">
              {clients.filter(c => c.telephone?.value && c.telephone.value.trim() !== "").length}
            </div>
            <div className="text-blue-100 text-xs mt-1">téléphones renseignés</div>
          </div>
        </div>

        {/* Recherche de Clients */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-2xl font-bold text-gray-800">Recherche de Clients</h2>
          </div>
          <p className="text-gray-600 mb-4">
            Recherchez des clients par nom, pays ou ville.
          </p>
          
          <div className="flex gap-3">
            <input
              type="text"
              value={nlpQuestion}
              onChange={(e) => setNlpQuestion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleNLPSearch()}
              placeholder='Ex: "Clients en Tunisie" ou "Clients de Paris"'
              className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
              disabled={isSearching}
            />
            <button
              onClick={handleNLPSearch}
              disabled={isSearching}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-semibold transition-all shadow-md disabled:opacity-50"
            >
              {isSearching ? "Recherche..." : "Rechercher"}
            </button>
            <button
              onClick={fetchClients}
              className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-xl font-semibold transition-all"
              title="Réinitialiser et afficher tous les clients"
            >
              Tout afficher
            </button>
          </div>
        </div>

        {/* Bouton Ajouter */}
        {!showAddForm && (
          <button
            onClick={() => setShowAddForm(true)}
            className="mb-6 bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-xl font-semibold transition-all flex items-center gap-2 shadow-md"
          >
            <Plus size={20} /> Ajouter un client
          </button>
        )}

        {/* Formulaire d'ajout/modification */}
        {showAddForm && (
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">
              {editingClient ? "Modifier le client" : "Nouveau client"}
            </h2>
            <form onSubmit={editingClient ? handleUpdateClient : handleAddClient}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Nom</label>
                  <input
                    type="text"
                    value={formData.nom}
                    onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    required={!editingClient}
                    disabled={editingClient}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Prénom</label>
                  <input
                    type="text"
                    value={formData.prenom}
                    onChange={(e) => setFormData({ ...formData, prenom: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    required={!editingClient}
                    disabled={editingClient}
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Téléphone</label>
                  <input
                    type="tel"
                    value={formData.telephone}
                    onChange={(e) => setFormData({ ...formData, telephone: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    placeholder="+33 1 23 45 67 89"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    placeholder="client@exemple.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Pays</label>
                  <input
                    type="text"
                    value={formData.pays}
                    onChange={(e) => setFormData({ ...formData, pays: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none"
                    placeholder="France"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Adresse</label>
                  <textarea
                    value={formData.adresse}
                    onChange={(e) => setFormData({ ...formData, adresse: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none resize-y min-h-[100px]"
                    placeholder="123 Rue Example, 75001 Paris"
                  />
                </div>
              </div>

              <div className="flex gap-4 mt-6">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
                >
                  <Save size={20} /> {editingClient ? "Enregistrer" : "Ajouter"}
                </button>
                <button
                  type="button"
                  onClick={resetForm}
                  className="flex-1 bg-gray-500 hover:bg-gray-600 text-white py-3 rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
                >
                  <X size={20} /> Annuler
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Liste des clients */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Nom complet</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Téléphone</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Email</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Pays</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {clients.map((client, index) => {
                  const fullName = client.client?.value.split("#")[1] || "";
                  const nameParts = fullName.split("_");
                  const displayName = nameParts.join(" ");
                  
                  return (
                    <tr key={index} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {displayName}
                        </div>
                        <div className="text-sm text-gray-500 truncate max-w-xs">
                          {client.adresse?.value || "Pas d'adresse"}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {client.telephone?.value || "N/A"}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">
                        {client.email?.value || "N/A"}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">
                        {client.pays?.value || "N/A"}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex justify-center gap-3">
                          <button
                            onClick={() => handleEditClick(client)}
                            className="text-blue-600 hover:text-blue-800 transition-colors"
                            title="Modifier"
                          >
                            <Edit size={20} />
                          </button>
                          <button
                            onClick={() => handleDeleteClient(client.client.value)}
                            className="text-red-600 hover:text-red-800 transition-colors"
                            title="Supprimer"
                          >
                            <Trash2 size={20} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {clients.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            Aucun client disponible
          </div>
        )}
      </main>
    </div>
  );
}

