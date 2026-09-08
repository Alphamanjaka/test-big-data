"use client";

import { createContext, useContext, useState, ReactNode, useCallback, JSX } from "react";

interface Filters {
    dateRange: { start: string | null; end: string | null };
    gender: string;
    ageRange: string;
}

interface FiltersContextType {
    filters: Filters;
    updateCount: number; // Trigger pour "Voir" (incrémenté manuellement)
    setDateRange: (range: { start: string | null; end: string | null }) => void;
    setGender: (gender: string) => void;
    setAgeRange: (ageRange: string) => void;
    resetFilters: () => void;
    triggerUpdate: () => void;
}

const defaultFilters: Filters = {
    dateRange: { start: null, end: null },
    gender: "all",
    ageRange: "all",
};

const FiltersContext = createContext<FiltersContextType | undefined>(undefined);

export function FiltersProvider({ children }: { children: ReactNode }): JSX.Element {
    const [filters, setFilters] = useState<Filters>(defaultFilters);
    const [updateCount, setUpdateCount] = useState<number>(0); // Trigger manuel pour "Voir"

    const setDateRange = useCallback((newRange: { start: string | null; end: string | null }) => {
        setFilters((prev) => ({ ...prev, dateRange: newRange }));
    }, []);

    const setGender = useCallback((newGender: string) => {
        setFilters((prev) => ({ ...prev, gender: newGender }));
    }, []);

    const setAgeRange = useCallback((newAgeRange: string) => {
        setFilters((prev) => ({ ...prev, ageRange: newAgeRange }));
    }, []);

    const resetFilters = useCallback(() => {
        setFilters(defaultFilters);
    }, []);

    // Trigger "Voir" : Incrémente pour notifier pages (manuel, pas auto)
    const triggerUpdate = useCallback(() => {
        setUpdateCount((prev) => prev + 1);
    }, []);

    const value: FiltersContextType = {
        filters,
        updateCount,
        setDateRange,
        setGender,
        setAgeRange,
        resetFilters,
        triggerUpdate,
    };

    // JSX correctement fermé : <Provider> ouvert + </Provider> fermé
    return (
        <FiltersContext.Provider value={value}>
            {children}
        </FiltersContext.Provider>
    );
}

export function useFilters() {
    const context = useContext(FiltersContext);
    if (context === undefined) {
        throw new Error("useFilters doit être utilisé dans un FiltersProvider");
    }
    return context;
}
