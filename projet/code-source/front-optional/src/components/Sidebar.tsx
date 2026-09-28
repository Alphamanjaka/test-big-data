"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "next-auth/react";
import { Users, Settings, Table, CopyCheck, ShieldCheck, Layers, PlayCircle, UserRound } from "lucide-react";

export default function Sidebar() {
    const pathname = usePathname();
    const { data: session } = useSession();
    const isAdmin = session?.user?.role === "ADMIN";

    const menuItems = [
        { href: "/synthese", label: "Synthèse", icon: Layers },
        { href: "/doublons", label: "Doublons", icon: CopyCheck },
        { href: "/gouvernance", label: "Gouvernance", icon: ShieldCheck },
        { href: "/patients", label: "Patients", icon: UserRound },
        { href: "/pipeline", label: "Pipeline ELT", icon: PlayCircle },
        ...(isAdmin ? [{ href: "/users", label: "Gestion des utilisateurs", icon: Users }] : []),
        { href: "/settings", label: "Paramètres", icon: Settings },
    ];

    return (
        <div className="w-60 h-screen bg-gray-900 text-gray-200 fixed left-0 top-0 z-50 flex flex-col">
            {/* Header compact */}
            <div className="p-3 border-b border-gray-700 text-center">
                <div className="flex items-center justify-center space-x-2">
                    <Table className="h-6 w-6 text-blue-400" />
                    <h1 className="font-semibold tracking-wide">DataViz Gouvernance</h1>
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
                </ul>
            </nav>
        </div>
    );
}