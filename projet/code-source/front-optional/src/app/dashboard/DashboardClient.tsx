'use client'

import { useEffect, useState } from 'react'
import { BarChart3, HeartPulse, Venus, Activity } from 'lucide-react'
import { useFilters } from "@/context/FiltersContext";
import { getAdmissionsSummary, getTopDiagnostics } from "@/lib/api";

interface TopDiagnostic {
  diagnosis_code: string
  diagnosis: string
  total: number
}

export default function Dashboard() {
  const { filters, updateCount } = useFilters();
  const [loading, setLoading] = useState(true)
  const [kpiData, setKpiData] = useState([
    { title: "Total Admissions", value: 0, icon: BarChart3, color: "#a73d1dff" },
    { title: "Taux de Mortalité infantile", value: 0, icon: HeartPulse, color: "#10B981" },
    { title: "Taux de Mortalité maternelle", value: 0, icon: Venus, color: "#F59E0B" },
  ]);
  const [topDiagnostics, setTopDiagnostics] = useState<TopDiagnostic[]>([]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const sex = filters.gender === "all" ? undefined : filters.gender;
      const summary = await getAdmissionsSummary({
        start: filters.dateRange.start,
        end: filters.dateRange.end,
        sex,
      });
      const top = await getTopDiagnostics({
        start: filters.dateRange.start,
        end: filters.dateRange.end,
        sex,
        limit: 5,
      });

      setKpiData([
        { title: "Total Admissions", value: summary.total_admissions, icon: BarChart3, color: "#a73d1dff" },
        { title: "Taux de Mortalité infantile", value: summary.mortalite_infantile ?? 0, icon: HeartPulse, color: "#10B981" },
        { title: "Taux de Mortalité maternelle", value: summary.mortalite_maternelle ?? 0, icon: Venus, color: "#F59E0B" },
      ]);
      setTopDiagnostics(top);
    } catch (err) {
      console.error("Erreur fetch dashboard :", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchDashboardData();
  }, [updateCount]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Chargement des données...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-0">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiData.map((kpi, index) => {
          const Icon = kpi.icon
          return (
            <div key={index} className="bg-white p-6 rounded-lg shadow-lg border-l-4"
              style={{ borderLeftColor: kpi.color }}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{kpi.title}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {typeof kpi.value === 'number' && kpi.value < 10
                      ? `${kpi.value}%`
                      : kpi.value.toLocaleString()
                    }
                  </p>
                </div>
                <div className="p-3 rounded-full" style={{ backgroundColor: `${kpi.color}20` }}>
                  <Icon className="w-6 h-6" style={{ color: kpi.color }} />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Top 5 maladies */}
      <div className="mt-10">
        <h2 className="text-xl font-bold text-gray-800 mb-4">
          Top 5 des pathologies
          {filters.dateRange.start && filters.dateRange.end
            ? ` du ${filters.dateRange.start} au ${filters.dateRange.end}`
            : ""
          }
        </h2>
        <div className="overflow-x-auto bg-white rounded-lg shadow-md">
          <table className="min-w-full border">
            <thead className="bg-gray-100 text-gray-700 text-sm">
              <tr>
                <th className="px-4 py-2 border text-left">Code CIM-10</th>
                <th className="px-4 py-2 border text-left">Pathologie</th>
                <th className="px-4 py-2 border text-center">Nombre de cas</th>
              </tr>
            </thead>
            <tbody>
              {topDiagnostics.map((diag, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-2 border font-medium">{diag.diagnosis_code}</td>
                  <td className="px-4 py-2 border font-medium">{diag.diagnosis}</td>
                  <td className="px-4 py-2 border text-center">{diag.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
