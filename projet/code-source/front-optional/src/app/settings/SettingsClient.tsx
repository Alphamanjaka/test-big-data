"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Settings, User, Mail, Lock, Save } from "lucide-react";
import { toast } from "react-toastify";

interface SettingsClientProps {
  userName: string;
}

export default function SettingsClient({ userName }: SettingsClientProps) {
  const { data: session, update } = useSession();
  const [form, setForm] = useState({
    firstName: (session?.user as any)?.firstName || "",
    lastName: (session?.user as any)?.lastName || "",
    email: session?.user?.email || "",
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [saving, setSaving] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      // Mise à jour via l'API (simulation pour données fictives)
      await new Promise(resolve => setTimeout(resolve, 800));
      toast.success("Profil mis à jour avec succès !");
      setForm({ ...form, currentPassword: "", newPassword: "", confirmPassword: "" });
    } catch (error) {
      toast.error("Erreur lors de la mise à jour du profil");
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.newPassword !== form.confirmPassword) {
      toast.error("Les mots de passe ne correspondent pas");
      return;
    }
    if (form.newPassword.length < 6) {
      toast.error("Le mot de passe doit contenir au moins 6 caractères");
      return;
    }
    setSaving(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      toast.success("Mot de passe modifié avec succès !");
      setForm({ ...form, currentPassword: "", newPassword: "", confirmPassword: "" });
    } catch (error) {
      toast.error("Erreur lors de la modification du mot de passe");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="w-5 h-5 text-blue-600" />
            <span>Paramètres</span>
          </CardTitle>
          <CardDescription>
            Gérez votre profil et vos préférences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-8">
          {/* Informations du profil */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <User className="w-4 h-4" />
              Informations du profil
            </h3>
            <form onSubmit={handleSaveProfile} className="space-y-4 max-w-lg">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nom</label>
                  <input
                    type="text"
                    name="firstName"
                    value={form.firstName}
                    onChange={handleChange}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Votre nom"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Prénom</label>
                  <input
                    type="text"
                    name="lastName"
                    value={form.lastName}
                    onChange={handleChange}
                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Votre prénom"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Mail className="w-3 h-3 inline mr-1" />
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="votre@email.com"
                />
              </div>
              <button
                type="submit"
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                <Save className="w-4 h-4" />
                {saving ? "Enregistrement..." : "Enregistrer le profil"}
              </button>
            </form>
          </div>

          <hr className="border-gray-200" />

          {/* Modification du mot de passe */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Lock className="w-4 h-4" />
              Modifier le mot de passe
            </h3>
            <form onSubmit={handleChangePassword} className="space-y-4 max-w-lg">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mot de passe actuel</label>
                <input
                  type="password"
                  name="currentPassword"
                  value={form.currentPassword}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="••••••••"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nouveau mot de passe</label>
                <input
                  type="password"
                  name="newPassword"
                  value={form.newPassword}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="••••••••"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Confirmer le mot de passe</label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={form.confirmPassword}
                  onChange={handleChange}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="••••••••"
                />
              </div>
              <button
                type="submit"
                disabled={saving}
                className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-md hover:bg-gray-900 disabled:opacity-50 transition-colors"
              >
                <Lock className="w-4 h-4" />
                {saving ? "Enregistrement..." : "Modifier le mot de passe"}
              </button>
            </form>
          </div>

          <hr className="border-gray-200" />

          {/* Informations de session */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Informations de session</h3>
            <div className="bg-gray-50 p-4 rounded-lg space-y-2 max-w-lg">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Connecté en tant que :</span>
                <span className="text-sm font-medium">{session?.user?.email}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Rôle :</span>
                <span className="text-sm font-medium px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                  {(session?.user as any)?.role || "MEDECIN"}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
