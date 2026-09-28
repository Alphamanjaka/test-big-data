// src/app/AppWrapper.tsx
"use client";

import { usePathname } from "next/navigation";
import { ToastContainer } from "react-toastify";
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";

export default function AppWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const MainContent = (
    <>
      <div className="ml-60">
        <Header />
      </div>
      <main className="ml-62 pt-6">
        {children}
      </main>
    </>
  );

  return (
    <>
      {pathname !== "/login" ? (
        <>
          <Sidebar />
          {MainContent}
        </>
      ) : (
        <main>{children}</main>
      )}
      <ToastContainer />
    </>
  );
}