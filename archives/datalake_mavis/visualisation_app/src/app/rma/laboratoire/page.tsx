'use client'

import { useEffect, useState } from 'react'
import LaboratoryChart from '@/components/rma/LaboratoryChart'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TestTube, Activity } from 'lucide-react'
import { useFilters } from '@/context/FiltersContext'
import { getLaboratory, LaboratoryRow } from '@/lib/api'

export default function LaboratoirePage() {
  const { filters, updateCount } = useFilters()
  const [laboratoryData, setLaboratoryData] = useState<LaboratoryRow[]>([])
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    setLoading(true)
    try {
      setLaboratoryData(await getLaboratory({
        start: filters.dateRange.start,
        end: filters.dateRange.end,
        sex: filters.gender === "all" ? undefined : filters.gender,
      }))
    } catch (error) {
      console.error('Erreur chargement laboratoire:', error)
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
          <p className="text-gray-600">Chargement des données de laboratoire...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TestTube className="w-5 h-5 text-green-600" />
            <span>Tableau 16 - Activité de laboratoires</span>
          </CardTitle>
          <CardDescription>
            Volume d&apos;examens et taux de positivité par type d&apos;examen
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LaboratoryChart data={laboratoryData} />
        </CardContent>
      </Card>
    </div>
  )
}
