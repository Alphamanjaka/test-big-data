'use client'

import { useEffect, useState } from 'react'
import MalariaKPI from '@/components/rma/MalariaKPI'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Bug, Activity } from 'lucide-react'
import { useFilters } from '@/context/FiltersContext'
import { getMalaria, MalariaData } from '@/lib/api'

export default function PaludismePage() {
  const { filters, updateCount } = useFilters()
  const [malariaData, setMalariaData] = useState<MalariaData | null>(null)
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    setLoading(true)
    try {
      setMalariaData(await getMalaria({
        start: filters.dateRange.start,
        end: filters.dateRange.end,
        sex: filters.gender === "all" ? undefined : filters.gender,
      }))
    } catch (error) {
      console.error('Erreur chargement paludisme:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [updateCount])

  if (loading || !malariaData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Chargement des données de paludisme...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Bug className="w-5 h-5 text-yellow-600" />
            <span>Tableau 25 - Prise en charge Paludisme</span>
          </CardTitle>
          <CardDescription>
            Indicateurs clés et évolution de la prise en charge du paludisme
          </CardDescription>
        </CardHeader>
        <CardContent>
          <MalariaKPI data={malariaData} />
        </CardContent>
      </Card>
    </div>
  )
}
