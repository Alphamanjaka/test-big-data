// components/Header.tsx (basé sur votre code)
"use client";

import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Settings, LogOut, User } from "lucide-react";
import Link from "next/link";
import { signOut, useSession } from "next-auth/react";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import { useFilters } from "@/context/FiltersContext";
import { useCallback } from "react";

export default function Header() {
  const { data: session, status } = useSession(); 
  const {
    filters,
    setDateRange,
    setGender,
    setAgeRange,
    triggerUpdate,
    resetFilters,
  } = useFilters();

  const handleDateChange = useCallback((values: { start: string | null; end: string | null }) => {
    setDateRange(values); // Seulement update filtres (pas fetch)
  }, [setDateRange]);

  const handleGenderChange = useCallback((value: string) => {
    setGender(value);
  }, [setGender]);

  const handleAgeChange = useCallback((value: string) => {
    setAgeRange(value);
  }, [setAgeRange]);

  const handleSeeData = useCallback(() => {
    triggerUpdate(); // Incrémente pour notifier pages (chacune se re-fetch dans son loadData)
  }, [triggerUpdate]);

  const handleReset = useCallback(() => {
    resetFilters();
  }, [resetFilters]);

  return (
    <header className="w-full flex justify-between items-center pt-3 p-1 border-b shadow-sm bg-white">
      <div className="flex items-center gap-3">
        <DatePickerWithRange
          onChange={handleDateChange}
          initialDateFrom={filters.dateRange.start || undefined}
          initialDateTo={filters.dateRange.end || undefined}
          align="start"
          locale="fr-FR"
          showCompare={false}
          className="w-[280px]"
        />

        <Select value={filters.gender} onValueChange={handleGenderChange}>
          <SelectTrigger className="w-[120px]">
            <SelectValue placeholder="Sexe" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous</SelectItem>
            <SelectItem value="male">Homme</SelectItem>
            <SelectItem value="female">Femme</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filters.ageRange} onValueChange={handleAgeChange}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Âge" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les âges</SelectItem>
            <SelectItem value="0-28j">0-28 jours</SelectItem>
            <SelectItem value="29-59j">29-59 jours</SelectItem>
            <SelectItem value="2-11m">2-11 mois</SelectItem>
            <SelectItem value="1-4a">1-4 ans</SelectItem>
            <SelectItem value="5-14a">5-14 ans</SelectItem>
            <SelectItem value="15-24a">15-24 ans</SelectItem>
            <SelectItem value="25-59a">25-59 ans</SelectItem>
            <SelectItem value="60+">60+ ans</SelectItem>
          </SelectContent>
        </Select>

        <div className="flex gap-2">
          <Button variant="default" onClick={handleSeeData} size="sm">
            Voir {/* MANUEL : Trigger + fetch page active */}
          </Button>
          <Button variant="outline" onClick={handleReset} size="sm">
            Reset
          </Button>
        </div>
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
        <Button variant="ghost" size="icon" onClick={() => signOut({ callbackUrl: "/login" })} className="text-red-600 hover:bg-gray-50 rounded-full">
          <LogOut size={20} />
        </Button>
      </div>
    </header>
  );
}
