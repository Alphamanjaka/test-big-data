// app/patients/page.tsx
import PatientsClient from "./PatientsClient";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth"
import { redirect } from "next/navigation";

export default async function PatientsPage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/login");
  }

  return (
    <PatientsClient
      userName={session.user.email ?? "Utilisateur"}
    />
  );
}