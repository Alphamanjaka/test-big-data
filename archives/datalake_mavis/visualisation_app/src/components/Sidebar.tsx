"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "next-auth/react";
import { Home, Users, Settings, ChevronDown, ChevronRight, Table, Activity } from "lucide-react";
import { useEffect, useState } from "react";
import { getLastSync } from "@/lib/api";

export default function Sidebar() {
    const pathname = usePathname();
    const { data: session } = useSession();
    const isAdmin = session?.user?.role === "ADMIN";
    const [openRMA, setOpenRMA] = useState(false);
    const [lastSync, setLastSync] = useState("Vendredi 26 Septembre 2025 05:00");

    useEffect(() => {
        getLastSync().then((sync) => {
            if (sync) {
                const date = new Date(sync);
                if (!isNaN(date.getTime())) {
                    const options: Intl.DateTimeFormatOptions = {
                        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
                    };
                    setLastSync(date.toLocaleDateString('fr-FR', options));
                }
            }
        }).catch((err) => console.error("Erreur fetch last sync:", err));
    }, []);

    const menuItems = [
        { href: "/dashboard", label: "Accueil", icon: Home },
        ...(isAdmin ? [{ href: "/users", label: "Gestion des utilisateurs", icon: Users }] : []),
        { href: "/settings", label: "Paramètres", icon: Settings },
    ];

    const rmaTables = [
        { href: "/rma", label: "Tableau 5 - Diagnostics consultations externes" },
        { href: "/rma/morbidite", label: "Tableau 9 : Morbidité & Mortalité hospitalière" },
        { href: "/rma/maternite", label: "Tableaux 11 & 12 : CPN & Maternité" },
        { href: "/rma/laboratoire", label: "Tableau 16 - Activité de laboratoires" },
        { href: "/rma/paludisme", label: "Tableau 25 : Paludisme" },
    ];

    return (
        <div className="w-60 h-screen bg-gray-900 text-gray-200 fixed left-0 top-0 z-50 flex flex-col">
            {/* Header compact */}
            <div className="p-3 border-b border-gray-700 text-center">
                <div className="flex items-center justify-center space-x-2">
                    <Activity className="h-6 w-6 text-blue-400" />
                    <h1 className="font-semibold tracking-wide">RMA DataViz</h1>
                </div>
                <div className="text-sm text-gray-100">
                    Dernière synchro : <span className="font-medium">{lastSync}</span>
                </div>
            </div>

            {/* Menu principal */}
            <nav className="flex-1 overflow-y-auto px-2 py-2 text-sm">
                <ul className="space-y-1">
                    {menuItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = pathname === item.href;
                        return (
                            <li key={item.href}>
                                <Link
                                    href={item.href}
                                    className={`flex items-center py-1.5 px-2 rounded-md transition ${isActive ? "bg-blue-600 text-white" : "hover:bg-gray-800"
                                        }`}
                                >
                                    <Icon size={16} className="mr-2" />
                                    {item.label}
                                </Link>
                            </li>
                        );
                    })}

                    {/* Section RMA */}
                    <li className="mt-3">
                        <button
                            onClick={() => setOpenRMA(!openRMA)}
                            className="flex items-center w-full py-1.5 px-2 rounded-md hover:bg-gray-800 transition text-sm"
                        >
                            {openRMA ? (
                                <ChevronDown size={14} className="mr-2" />
                            ) : (
                                <ChevronRight size={14} className="mr-2" />
                            )}
                            Rapports RMA
                        </button>

                        {openRMA && (
                            <ul className="ml-4 mt-1 space-y-0.5">
                                {rmaTables.map((table) => {
                                    const isActive = pathname === table.href;
                                    return (
                                        <li key={table.href}>
                                            <Link
                                                href={table.href}
                                                className={`flex items-center py-1 px-2 rounded-md text-xs ${isActive ? "bg-blue-600 text-white" : "hover:bg-gray-800"
                                                    }`}
                                            >
                                                <Table size={14} className="mr-2" />
                                                {table.label}
                                            </Link>
                                        </li>
                                    );
                                })}
                            </ul>
                        )}
                    </li>
                </ul>
            </nav>
        </div>
    );
}
