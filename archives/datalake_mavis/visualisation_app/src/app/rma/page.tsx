'use client'

import { useEffect, useState } from 'react'
import DiagnosticsHeatmap from '@/components/rma/DiagnosticsHeatmap'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { BarChart3, Activity, Table as TableIcon, BarChart2, ChevronLeft, ChevronRight } from 'lucide-react'
import { useFilters } from "@/context/FiltersContext"
import { getDiagnosticsHeatmap, getDiagnosticsList, Diagnostic } from '@/lib/api'

const AGE_COLUMNS = [
  { field: "age_0_28j" as const, label: "0-28 j" },
  { field: "age_29_59j" as const, label: "29-59 j" },
  { field: "age_2_11m" as const, label: "2-11 m" },
  { field: "age_1_4a" as const, label: "1-4 ans" },
  { field: "age_5_14a" as const, label: "5-14 ans" },
  { field: "age_15_24a" as const, label: "15-24 ans" },
  { field: "age_25_59a" as const, label: "25-59 ans" },
  { field: "age_60plus" as const, label: "60 ans et plus" },
];
const ageColumns = AGE_COLUMNS.map(c => c.label)

const rowsPerPage = 10

export default function RmaTableau5() {
  const { filters, updateCount } = useFilters()

  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart")
  const [currentPage, setCurrentPage] = useState(1)
  const [diagnosticsData, setDiagnosticsData] = useState<Diagnostic[]>([])
  const [diagnosticsDataTableau, setDiagnosticsDataTableau] = useState<Diagnostic[]>([])

  // Mount : fetch initial
  useEffect(() => {
    loadData()
  }, [])

  // Re-fetch sur "Voir" ou changement de vue
  useEffect(() => {
    if (updateCount > 0) {
      loadData()
    }
  }, [updateCount, viewMode])

  const loadData = async () => {
    setLoading(true)
    const sex = filters.gender === "all" ? undefined : filters.gender
    const common = { start: filters.dateRange.start, end: filters.dateRange.end, sex }
    try {
      if (viewMode === "chart") {
        setDiagnosticsData(await getDiagnosticsHeatmap({ ...common, limit: 15 }))
      }

      if (viewMode === "table") {
        setDiagnosticsDataTableau(await getDiagnosticsList({ ...common, page: currentPage, limit: rowsPerPage }))
      }
    } catch (err) {
      console.error("Erreur loadData Tableau 5 :", err)
      setDiagnosticsData([])
      setDiagnosticsDataTableau([])
    } finally {
      setLoading(false)
      setCurrentPage(1) // Reset pagination au nouveau fetch
    }
  }

  // 🧮 Pagination locale
  const totalItems = diagnosticsDataTableau.length
  const totalPages = Math.ceil(totalItems / rowsPerPage)
  const startIndex = (currentPage - 1) * rowsPerPage
  const endIndex = startIndex + rowsPerPage
  const currentPageData = diagnosticsDataTableau.slice(startIndex, endIndex)

  const handlePrevPage = () => setCurrentPage(prev => Math.max(prev - 1, 1))
  const handleNextPage = () => setCurrentPage(prev => Math.min(prev + 1, totalPages))

  const handleChangeView = (mode: "chart" | "table") => {
    if (viewMode !== mode) {
      setViewMode(mode)
      setLoading(true)
      // Rechargement déclenché via useEffect
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">
            Chargement des diagnostics RMA (Tableau 5) – {viewMode === "chart" ? "Graphique" : "Tableau"} en cours...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              <span>Tableau 5 - Diagnostics consultations externes (CIM-10)</span>
            </CardTitle>
            <CardDescription>
              Distribution des diagnostics par tranche d'âge entre {filters.dateRange.start || "?"} et {filters.dateRange.end || "?"}
            </CardDescription>
          </div>
          <div className="flex space-x-2">
            <Button
              variant={viewMode === "chart" ? "default" : "outline"}
              size="sm"
              onClick={() => handleChangeView("chart")}
            >
              <BarChart2 className="w-4 h-4 mr-1" /> Chart
            </Button>
            <Button
              variant={viewMode === "table" ? "default" : "outline"}
              size="sm"
              onClick={() => handleChangeView("table")}
            >
              <TableIcon className="w-4 h-4 mr-1" /> Tableau
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {viewMode === "chart" ? (
            <DiagnosticsHeatmap data={diagnosticsData} />
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full border">
                  <thead className="bg-gray-100 text-gray-700 text-sm">
                    <tr>
                      <th className="px-4 py-2 border text-left">Diagnostic</th>
                      {ageColumns.map(col => (
                        <th key={col} className="px-4 py-2 border text-center">{col}</th>
                      ))}
                      <th className="px-4 py-2 border text-center">Total</th>
                      {/* <th className="px-4 py-2 border text-center">Référés</th> */}
                    </tr>
                  </thead>
                  <tbody>
                    {currentPageData.map((diag, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-4 py-2 border">{diag.diagnosis_code + '-' + diag.diagnosis || 'N/A'}</td>
                        {AGE_COLUMNS.map(col => (
                          <td key={col.field} className="px-4 py-2 border text-center">
                            {diag[col.field] ?? 0}
                          </td>
                        ))}

                        <td className="px-4 py-2 border text-center">{diag.total || 0}</td>
                        {/* <td className="px-4 py-2 border text-center">{diag.refered || 0}</td> */}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination locale */}
              <div className="flex justify-end items-center space-x-2 mt-2">
                <Button onClick={handlePrevPage} disabled={currentPage === 1} size="sm">
                  <ChevronLeft className="w-4 h-4 mr-1" /> Précédent
                </Button>
                <span className="text-sm">
                  Page {currentPage} / {totalPages || 1}
                </span>
                <Button onClick={handleNextPage} disabled={currentPage === totalPages || totalPages === 0} size="sm">
                  Suivant <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
