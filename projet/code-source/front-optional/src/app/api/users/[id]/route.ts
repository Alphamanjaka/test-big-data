import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import bcrypt from "bcryptjs";
import { checkRole } from "@/lib/rbac";

export async function PUT(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const guard = await checkRole(["ADMIN"]);
  if (!guard.ok) return guard.response;

  const data = await req.json();
  const { firstName, lastName, email, password, role } = data;

  const user = await prisma.user.update({
    where: { id },
    data: {
      firstName,
      lastName,
      email,
      role,
      ...(password ? { password: await bcrypt.hash(password, 10) } : {}),
    },
  });

  const { password: _, ...userSafe } = user;
  return NextResponse.json(userSafe);
}

export async function DELETE(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const guard = await checkRole(["ADMIN"]);
  if (!guard.ok) return guard.response;

  await prisma.user.delete({ where: { id } });
  return NextResponse.json({ message: "Utilisateur supprimé" });
}
