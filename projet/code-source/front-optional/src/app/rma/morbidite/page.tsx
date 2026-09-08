'use client'

import { useEffect, useState } from 'react'
import MortalityChart from '@/components/rma/MortalityChart'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Heart, Activity } from 'lucide-react'
import { useFilters } from '@/context/FiltersContext'
import { getMortality, MortalityRow } from '@/lib/api'

export default function MorbiditePage() {
  const { filters, updateCount } = useFilters()
  const [mortalityData, setMortalityData] = useState<MortalityRow[]>([])
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    setLoading(true)
    try {
      setMortalityData(await getMortality({
        start: filters.dateRange.start,
        end: filters.dateRange.end,
        sex: filters.gender === "all" ? undefined : filters.gender,
      }))
    } catch (error) {
      console.error('Erreur chargement mortalité:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [updateCount])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Chargement des données de morbidité...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Heart className="w-5 h-5 text-red-600" />
            <span>Tableau 9 - Morbidité et mortalité hospitalière</span>
          </CardTitle>
          <CardDescription>
            Taux de mortalité par diagnostic et service hospitalier
          </CardDescription>
        </CardHeader>
        <CardContent>
          <MortalityChart data={mortalityData} />
        </CardContent>
      </Card>
    </div>
  )
}
