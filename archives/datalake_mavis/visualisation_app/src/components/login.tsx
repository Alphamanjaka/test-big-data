'use client';

import { signIn } from "next-auth/react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Activity } from "lucide-react";

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErrorMessage("");

    const res = await signIn("credentials", {
      redirect: false,
      email,
      password,
    });

    setLoading(false);

    if (res?.error) {
      setErrorMessage("Échec de connexion : email ou mot de passe invalide.");
      console.error("Erreur NextAuth:", res.error);
    } else {
      router.push("/dashboard");
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-5 bg-white p-6 rounded shadow-md"
      >

        <div className="p-3 border-b border-gray-700 text-center">
          <div className="flex items-center justify-center space-x-1">
            <Activity className="h-6 w-6 text-blue-400" />
            <h1 className="font-semibold tracking-wide">RMA DataViz</h1>
          </div>
          <div className="text-sm text-gray-100">
            <h1 className="text-2xl font-bold text-center text-gray-800">Connexion</h1>
          </div>
        </div>

        {/* Email */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Adresse email
          </label>
          <input
            type="email"
            id="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Password */}
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">
            Mot de passe
          </label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-2 flex items-center px-2 text-sm text-gray-600 hover:text-gray-900"
            >
              {showPassword ? "🙈" : "👁️"}
            </button>
          </div>
        </div>

        {/* Error */}
        {errorMessage && (
          <p className="text-red-600 text-sm text-center">{errorMessage}</p>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || !email || !password}
          className={`w-full text-white p-2 rounded transition ${loading || !email || !password
            ? "bg-blue-300 cursor-not-allowed"
            : "bg-blue-600 hover:bg-blue-700"
            }`}
        >
          {loading ? "Connexion..." : "Se connecter"}
        </button>

      </form>
    </div>
  );
}
