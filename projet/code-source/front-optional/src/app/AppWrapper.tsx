// src/app/AppWrapper.tsx (ou où il est)
"use client";

import { usePathname } from "next/navigation";
import { ToastContainer } from "react-toastify";
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";
import { FiltersProvider } from "@/context/FiltersContext"; // Import ici

export default function AppWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const MainContent = (
    <FiltersProvider> {/* Wrap seulement le contenu principal (hors login) */}
      <div className="ml-60">
        <Header /> {/* Accède aux filtres via useFilters() */}
      </div>
      <main className="ml-62 pt-6"> {/* ml-60 ? Vérifiez cohérence avec Sidebar */}
        {children} {/* Pages accèdent aux filtres */}
      </main>
    </FiltersProvider>
  );

  return (
    <>
      {pathname !== "/login" ? (
        <>
          <Sidebar /> {/* Peut aussi utiliser useFilters() si besoin (ex: menu filtres) */}
          {MainContent}
        </>
      ) : (
        <main>{children}</main> // Login sans filtres/Sidebar
      )}
      <ToastContainer />
    </>
  );
}
