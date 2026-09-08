'use client'

import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { TrendingUp, Users, Activity, Shield } from 'lucide-react'

interface MalariaData {
  consultants_fievre: number
  tdr_effectues: number
  lames_effectuees: number
  tdr_positifs: number
  lames_positives: number
  traites: number
  moustiquaires_distribuees: number
  prevention: {
    enfants_0_5ans: number
    femmes_enceintes: number
    population_generale: number
  }
  evolution_mensuelle: Array<{
    mois: string
    cas: number
    traites: number
  }>
}

interface MalariaKPIProps {
  data: MalariaData
}

export default function MalariaKPI({ data }: MalariaKPIProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  const kpiData = [
    {
      title: "Consultants avec fièvre",
      value: data.consultants_fievre,
      icon: Users,
      color: "#3B82F6",
      trend: "+12%"
    },
    {
      title: "Tests effectués",
      value: data.tdr_effectues + data.lames_effectuees,
      icon: Activity,
      color: "#10B981",
      trend: "+8%"
    },
    {
      title: "Cas positifs",
      value: data.tdr_positifs + data.lames_positives,
      icon: TrendingUp,
      color: "#F59E0B",
      trend: "-5%"
    },
    {
      title: "Moustiquaires distribuées",
      value: data.moustiquaires_distribuees,
      icon: Shield,
      color: "#8B5CF6",
      trend: "+15%"
    }
  ]

  useEffect(() => {
    if (!data || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const margin = { top: 20, right: 30, bottom: 60, left: 60 }
    const width = 500 - margin.left - margin.right
    const height = 300 - margin.bottom - margin.top

    const container = svg
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // Échelles
    const xScale = d3.scaleBand()
      .domain(data.evolution_mensuelle.map(d => d.mois))
      .range([0, width])
      .padding(0.1)

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(data.evolution_mensuelle, d => Math.max(d.cas, d.traites)) || 0])
      .range([height, 0])

    // Ligne des cas
    const casLine = d3.line<{ mois: string; cas: number; traites: number }>()
      .x(d => (xScale(d.mois) || 0) + xScale.bandwidth() / 2)
      .y(d => yScale(d.cas))
      .curve(d3.curveMonotoneX)

    // Ligne des traités
    const traitesLine = d3.line<{ mois: string; cas: number; traites: number }>()
      .x(d => (xScale(d.mois) || 0) + xScale.bandwidth() / 2)
      .y(d => yScale(d.traites))
      .curve(d3.curveMonotoneX)

    // Ajout des lignes
    const casPath = container.append("path")
      .datum(data.evolution_mensuelle)
      .attr("fill", "none")
      .attr("stroke", "#EF4444")
      .attr("stroke-width", 3)
      .attr("d", casLine)

    const traitesPath = container.append("path")
      .datum(data.evolution_mensuelle)
      .attr("fill", "none")
      .attr("stroke", "#10B981")
      .attr("stroke-width", 3)
      .attr("d", traitesLine)

    // Animation des lignes
    const totalLength1 = casPath.node()?.getTotalLength() || 0
    const totalLength2 = traitesPath.node()?.getTotalLength() || 0

    casPath
      .attr("stroke-dasharray", totalLength1 + " " + totalLength1)
      .attr("stroke-dashoffset", totalLength1)
      .transition()
      .duration(2000)
      .attr("stroke-dashoffset", 0)

    traitesPath
      .attr("stroke-dasharray", totalLength2 + " " + totalLength2)
      .attr("stroke-dashoffset", totalLength2)
      .transition()
      .duration(2000)
      .attr("stroke-dashoffset", 0)

    // Points pour les cas
    container.selectAll(".dot-cas")
      .data(data.evolution_mensuelle)
      .enter()
      .append("circle")
      .attr("class", "dot-cas")
      .attr("cx", d => (xScale(d.mois) || 0) + xScale.bandwidth() / 2)
      .attr("cy", d => yScale(d.cas))
      .attr("r", 0)
      .style("fill", "#EF4444")
      .style("cursor", "pointer")
      .transition()
      .delay(1500)
      .duration(500)
      .attr("r", 5)

    // Points pour les traités
    container.selectAll(".dot-traites")
      .data(data.evolution_mensuelle)
      .enter()
      .append("circle")
      .attr("class", "dot-traites")
      .attr("cx", d => (xScale(d.mois) || 0) + xScale.bandwidth() / 2)
      .attr("cy", d => yScale(d.traites))
      .attr("r", 0)
      .style("fill", "#10B981")
      .style("cursor", "pointer")
      .transition()
      .delay(1500)
      .duration(500)
      .attr("r", 5)

    // Ajout des événements après l'animation
    setTimeout(() => {
      container.selectAll(".dot-cas, .dot-traites")
        .on("mouseover", function(event, d: any) {
          const tooltip = d3.select("body")
            .append("div")
            .attr("class", "tooltip")
            .style("position", "absolute")
            .style("background", "rgba(0, 0, 0, 0.8)")
            .style("color", "white")
            .style("padding", "8px")
            .style("border-radius", "4px")
            .style("font-size", "12px")
            .style("pointer-events", "none")

          const isCase = d3.select(this).attr("class") === "dot-cas"
          tooltip
            .html(`<strong>${d.mois}</strong><br/>
                   ${isCase ? 'Cas' : 'Traités'}: ${isCase ? d.cas : d.traites}`)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 10) + "px")

          d3.select(this)
            .transition()
            .duration(200)
            .attr("r", 8)
        })
        .on("mouseout", function() {
          d3.selectAll(".tooltip").remove()
          d3.select(this)
            .transition()
            .duration(200)
            .attr("r", 5)
        })
    }, 2000)

    // Axes
    container.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale))
      .selectAll("text")
      .style("font-size", "12px")
      .style("fill", "#666")

    container.append("g")
      .call(d3.axisLeft(yScale))
      .selectAll("text")
      .style("font-size", "12px")
      .style("fill", "#666")

    // Labels des axes
    container.append("text")
      .attr("transform", `translate(${width/2}, ${height + 40})`)
      .style("text-anchor", "middle")
      .style("font-size", "12px")
      .style("fill", "#333")
      .text("Mois")

    container.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -40)
      .attr("x", -height/2)
      .style("text-anchor", "middle")
      .style("font-size", "12px")
      .style("fill", "#333")
      .text("Nombre de cas")

    // Légende
    const legend = container.append("g")
      .attr("transform", `translate(${width - 120}, 20)`)

    legend.append("line")
      .attr("x1", 0)
      .attr("x2", 20)
      .attr("y1", 0)
      .attr("y2", 0)
      .style("stroke", "#EF4444")
      .style("stroke-width", 3)

    legend.append("text")
      .attr("x", 25)
      .attr("y", 0)
      .attr("dy", "0.35em")
      .style("font-size", "11px")
      .style("fill", "#333")
      .text("Cas")

    legend.append("line")
      .attr("x1", 0)
      .attr("x2", 20)
      .attr("y1", 15)
      .attr("y2", 15)
      .style("stroke", "#10B981")
      .style("stroke-width", 3)

    legend.append("text")
      .attr("x", 25)
      .attr("y", 15)
      .attr("dy", "0.35em")
      .style("font-size", "11px")
      .style("fill", "#333")
      .text("Traités")

  }, [data])

  return (
    <div className="space-y-6">

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Evolution Chart */}
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Évolution mensuelle - Paludisme
          </h3>
          <svg ref={svgRef} className="w-full"></svg>
        </div>

        {/* Prevention Stats */}
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Prévention et statistiques
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Taux de positivité TDR</span>
              <span className="text-lg font-bold text-blue-600">
                {((data.tdr_positifs / data.tdr_effectues) * 100).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Taux de traitement</span>
              <span className="text-lg font-bold text-green-600">
                {((data.traites / (data.tdr_positifs + data.lames_positives)) * 100).toFixed(1)}%
              </span>
            </div>
            <div className="mt-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Prévention par groupe</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Enfants 0-5 ans</span>
                  <span className="text-sm font-medium">{data.prevention.enfants_0_5ans}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Femmes enceintes</span>
                  <span className="text-sm font-medium">{data.prevention.femmes_enceintes}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Population générale</span>
                  <span className="text-sm font-medium">{data.prevention.population_generale}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}