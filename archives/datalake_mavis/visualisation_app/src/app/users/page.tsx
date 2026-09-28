// app/dashboard/page.tsx
import UserClient from "./UserClient";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth"
import { redirect } from "next/navigation";

export default async function UserPage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/login");
  }

  if (session.user.role !== "ADMIN") {
    redirect("/dashboard?denied=1");
  }

  // return <UserClient userName={session.user.email ?? "Utilisateur"} />;
  return <UserClient />;
}