// app/patients/[id]/page.tsx
import PatientDetailClient from "./PatientDetailClient";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth"
import { redirect } from "next/navigation";

export default async function PatientDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/login");
  }

  const { id } = await params;
  return <PatientDetailClient masterPatientId={decodeURIComponent(id)} />;
}