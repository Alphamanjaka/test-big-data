import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import type { Session } from "next-auth"
import { authOptions } from "@/lib/auth"
import type { AppRole } from "@/type/Role"

type GuardOk = { ok: true; session: Session }
type GuardKo = { ok: false; response: NextResponse }
export type GuardResult = GuardOk | GuardKo

export async function checkRole(allowedRoles: AppRole[]): Promise<GuardResult> {
  const session = await getServerSession(authOptions)

  if (!session?.user) {
    return {
      ok: false,
      response: NextResponse.json({ error: "Non authentifié" }, { status: 401 }),
    }
  }

  if (!allowedRoles.includes(session.user.role)) {
    return {
      ok: false,
      response: NextResponse.json(
        { error: `Accès refusé : rôle requis (${allowedRoles.join(" ou ")})` },
        { status: 403 }
      ),
    }
  }

  return { ok: true, session }
}
