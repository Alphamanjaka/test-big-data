// app/dashboard/page.tsx
import SettingsClient from "./SettingsClient";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth"
import { redirect } from "next/navigation";

export default async function SettingsPage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    // Rediriger vers la page login si pas connecté
    redirect("/login");
  }

  return <SettingsClient userName={session.user.email ?? "Utilisateur"} />;
}