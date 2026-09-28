"use client"

import * as React from "react"
import { CalendarIcon } from "@radix-ui/react-icons"
import { addDays, format, parseISO, isValid } from "date-fns"
import { DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

// Interface (inchangée)
interface DatePickerWithRangeProps {
  onPaste?: (values: { from: string; to: string }) => void
  onChange?: (values: { start: string | null; end: string | null }) => void
  initialDateFrom?: string
  initialDateTo?: string
  align?: "start" | "center" | "end"
  locale?: string
  showCompare?: boolean
  className?: string
}

export function DatePickerWithRange({
  onPaste,
  onChange,
  initialDateFrom,
  initialDateTo,
  align = "start",
  locale = "en-GB",
  showCompare = false,
  className,
}: DatePickerWithRangeProps) {
  // État initial : Basé sur props (undefined si pas d'initial)
  const [date, setDate] = React.useState<DateRange | undefined>(() => {
    const from = initialDateFrom ? parseISO(initialDateFrom) : undefined
    const to = initialDateTo ? parseISO(initialDateTo) : undefined
    // Retourne {from, to} seulement si valides ; sinon undefined (défaut "tous mois" pour RMA)
    return (from && isValid(from) && to && isValid(to)) ? { from, to } : undefined
  })

  // Sync avec props changeantes (ex: reset via Context)
  React.useEffect(() => {
    const newFrom = initialDateFrom ? parseISO(initialDateFrom) : undefined
    const newTo = initialDateTo ? parseISO(initialDateTo) : undefined
    
    // Évite setState si identique (prévention re-renders)
    const hasChange = 
      (date?.from?.getTime() !== newFrom?.getTime()) || 
      (date?.to?.getTime() !== newTo?.getTime())
    
    if (hasChange) {
      const newDateRange = (newFrom && isValid(newFrom) && newTo && isValid(newTo)) 
        ? { from: newFrom, to: newTo } 
        : undefined
      setDate(newDateRange)
      
      // Notifie immédiatement le reset si undefined
      if (onChange && !newDateRange) {
        onChange({ start: null, end: null })
      }
    }
  }, [initialDateFrom, initialDateTo, onChange]) // Dépendances : props + onChange pour reset

  // Notification parents sur changement interne (sélection user)
  React.useEffect(() => {
    if (date?.from && date?.to && isValid(date.from) && isValid(date.to)) {
      const formattedDates = {
        from: format(date.from, "yyyy-MM-dd"),
        to: format(date.to, "yyyy-MM-dd"),
      }
      
      if (onPaste) onPaste(formattedDates)
      if (onChange) onChange({ start: formattedDates.from, end: formattedDates.to })
    } else if (onChange && (date === undefined || (!date.from && !date.to))) {
      // Reset si pas de dates valides
      onChange({ start: null, end: null })
    }
  }, [date?.from, date?.to, onPaste, onChange]) // Dépend de dates seulement (optimisé)

  return (
    <div className={cn("grid gap-2", className)}>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            id="date"
            variant={"outline"}
            className={cn(
              "w-[280px] justify-start text-left font-normal", // Largeur fixe pour stabilité UI
              !date && "text-muted-foreground" // Style muted si undefined
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {date?.from ? (
              date.to ? (
                <> {/* Affichage range : ex: "Jan 01, 2025 - Jan 31, 2025" */}
                  {format(date.from, "LLL dd, y")} - {format(date.to, "LLL dd, y")}
                </>
              ) : (
                format(date.from, "LLL dd, y") // Single date
              )
            ) : (
              <span>Choisir une plage de dates</span> // Texte par défaut (FR pour RMA)
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align={align}>
          <Calendar
            initialFocus
            mode="range"
            selected={date} // Contrôlé par état interne
            onSelect={setDate} // Met à jour sur sélection
            defaultMonth={date?.from ?? new Date()} // Ouvre sur from ou aujourd'hui
            fromDate={new Date(2020, 0, 1)} // Min : 2020 pour RMA historiques
            toDate={addDays(new Date(), 365)} // Max : +1 an
            numberOfMonths={2} // 2 mois visibles
          />
        </PopoverContent>
      </Popover>
    </div>
  )
}