// components/Header.tsx
"use client";

import { Settings, LogOut, User } from "lucide-react";
import Link from "next/link";
import { signOut, useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";

export default function Header() {
  const { data: session, status } = useSession();

  return (
    <header className="w-full flex justify-between items-center pt-3 p-1 border-b shadow-sm bg-white">
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-500">
          Plateforme de gouvernance des données patients — données synthétiques et de démonstration.
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <User className="w-5 h-5" />
          <span className="text-sm font-medium">
            {status === "loading"
              ? "Chargement..."
              : session?.user?.email ?? "Non connecté"}
          </span>
        </div>
        <Link href="/settings" className="flex items-center justify-center w-5 h-5 text-gray-700 hover:bg-gray-50 rounded-full transition-colors">
          <Settings size={20} />
        </Link>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => signOut({ callbackUrl: "/login" })}
          className="text-red-600 hover:bg-gray-50 rounded-full"
          aria-label="Se déconnecter"
        >
          <LogOut size={20} />
        </Button>
      </div>
    </header>
  );
}