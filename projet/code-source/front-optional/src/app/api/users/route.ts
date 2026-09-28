import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import bcrypt from "bcryptjs";
import { checkRole } from "@/lib/rbac";

export async function GET() {
  const guard = await checkRole(["ADMIN"]);
  if (!guard.ok) return guard.response;

  const users = await prisma.user.findMany({
    select: { id: true, firstName: true, lastName: true, email: true, role: true, createdAt: true, updatedAt: true },
  });
  return NextResponse.json(users);
}

export async function POST(req: Request) {
  const guard = await checkRole(["ADMIN"]);
  if (!guard.ok) return guard.response;

  const data = await req.json();
  const { firstName, lastName, email, password, role } = data;

  const hashed = await bcrypt.hash(password, 10);

  const user = await prisma.user.create({
    data: {
      firstName,
      lastName,
      email,
      password: hashed,
      role: role || "MEDECIN",
    },
  });

  const { password: _, ...userSafe } = user;
  return NextResponse.json(userSafe);
}
