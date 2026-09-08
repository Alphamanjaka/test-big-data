import type { DefaultSession, DefaultUser } from "next-auth"
import type { AppRole } from "./src/type/Role"

declare module "next-auth" {
  interface User extends DefaultUser {
    id: string
    firstName?: string | null
    lastName?: string | null
    role: AppRole
  }

  interface Session {
    user: {
      id: string
      firstName?: string | null
      lastName?: string | null
      role: AppRole
    } & DefaultSession["user"]
    jwt?: any // <-- ajouter ce champ
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string
    firstName?: string | null
    lastName?: string | null
    role: AppRole
  }
}
