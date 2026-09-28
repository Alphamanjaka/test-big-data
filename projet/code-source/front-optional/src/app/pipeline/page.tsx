// app/pipeline/page.tsx
import PipelineClient from "./PipelineClient";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth"
import { redirect } from "next/navigation";

export default async function PipelinePage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/login");
  }

  const role = (session.user as any)?.role;
  return (
    <PipelineClient
      userName={session.user.email ?? "Utilisateur"}
      isAdmin={role === "ADMIN"}
    />
  );
}