'use client'

import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

interface LaboratoryData {
  examen: string
  total: number
  nouveaux: number
  positifs: number
}

interface LaboratoryChartProps {
  data: LaboratoryData[]
}

export default function LaboratoryChart({ data }: LaboratoryChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!data || data.length === 0 || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const margin = { top: 60, right: 80, bottom: 60, left: 80 }
    const width = 800 - margin.left - margin.right
    const height = 500 - margin.bottom - margin.top

    const container = svg
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // Calcul du taux de positivité
    const processedData = data.map(d => ({
      ...d,
      positivityRate: (d.positifs / d.total) * 100
    }))

    // Graphique en secteurs pour la répartition des examens
    const pieRadius = Math.min(width, height) / 4
    const pie = d3.pie<LaboratoryData>()
      .value(d => d.total)
      .sort(null)

    const arc = d3.arc<d3.PieArcDatum<LaboratoryData>>()
      .outerRadius(pieRadius)
      .innerRadius(pieRadius * 0.4) // Donut chart

    const colorScale = d3.scaleOrdinal(d3.schemeCategory10)

    const pieContainer = container.append("g")
      .attr("transform", `translate(${width/4}, ${height/2})`)

    const arcs = pieContainer.selectAll(".arc")
      .data(pie(data))
      .enter()
      .append("g")
      .attr("class", "arc")

    // Arcs du graphique en secteurs
    arcs.append("path")
      .style("fill", (d, i) => colorScale(i.toString()))
      .style("stroke", "#fff")
      .style("stroke-width", 2)
      .style("cursor", "pointer")
      .transition()
      .delay((d, i) => i * 100)
      .duration(500)
      .attrTween("d", function(d) {
        const interpolate = d3.interpolate({ startAngle: 0, endAngle: 0 }, d)
        return function(t) {
          return arc(interpolate(t)) ?? ""
        }
      })

    // Ajout des événements après l'animation
    setTimeout(() => {
      arcs.selectAll("path")
        .on("mouseover", function(event, d: any) {
          const tooltip = d3.select("body")
            .append("div")
            .attr("class", "tooltip")
            .style("position", "absolute")
            .style("background", "rgba(0, 0, 0, 0.8)")
            .style("color", "white")
            .style("padding", "12px")
            .style("border-radius", "6px")
            .style("font-size", "13px")
            .style("pointer-events", "none")

          tooltip
            .html(`<strong>${d.data.examen}</strong><br/>
                   Total: ${d.data.total.toLocaleString()}<br/>
                   Positifs: ${d.data.positifs.toLocaleString()}<br/>
                   Taux: ${((d.data.positifs / d.data.total) * 100).toFixed(1)}%`)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 10) + "px")

          d3.select(this)
            .style("opacity", 0.8)
            .style("stroke-width", 3)
        })
        .on("mouseout", function() {
          d3.selectAll(".tooltip").remove()
          d3.select(this)
            .style("opacity", 1)
            .style("stroke-width", 2)
        })
    }, 1000)

    // Texte central du donut
    pieContainer.append("text")
      .attr("text-anchor", "middle")
      .style("font-size", "14px")
      .style("font-weight", "bold")
      .style("fill", "#333")
      .text("Examens")

    pieContainer.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "1.2em")
      .style("font-size", "12px")
      .style("fill", "#666")
      .text("de laboratoire")

    // Graphique en barres pour les taux de positivité
    const barChart = container.append("g")
      .attr("transform", `translate(${width/2 + 50}, 50)`)

    const barWidth = width/2 - 100
    const barHeight = height - 100

    const xScale = d3.scaleBand()
      .domain(processedData.map(d => d.examen))
      .range([0, barWidth])
      .padding(0.1)

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(processedData, d => d.positivityRate) || 0])
      .range([barHeight, 0])

    // Barres
    barChart.selectAll(".bar")
      .data(processedData)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", d => xScale(d.examen) || 0)
      .attr("y", barHeight)
      .attr("width", xScale.bandwidth())
      .attr("height", 0)
      .style("fill", (d, i) => colorScale(i.toString()))
      .style("cursor", "pointer")
      .transition()
      .delay((d, i) => i * 100)
      .duration(800)
      .attr("y", d => yScale(d.positivityRate))
      .attr("height", d => barHeight - yScale(d.positivityRate))

    // Ajout des événements pour les barres
    setTimeout(() => {
      barChart.selectAll(".bar")
        .on("mouseover", function(event, d: any) {
          const tooltip = d3.select("body")
            .append("div")
            .attr("class", "tooltip")
            .style("position", "absolute")
            .style("background", "rgba(0, 0, 0, 0.8)")
            .style("color", "white")
            .style("padding", "12px")
            .style("border-radius", "6px")
            .style("font-size", "13px")
            .style("pointer-events", "none")

          tooltip
            .html(`<strong>${d.examen}</strong><br/>
                   Taux positivité: <strong>${d.positivityRate.toFixed(1)}%</strong><br/>
                   Positifs: ${d.positifs} / ${d.total}`)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 10) + "px")

          d3.select(this)
            .style("opacity", 0.8)
        })
        .on("mouseout", function() {
          d3.selectAll(".tooltip").remove()
          d3.select(this)
            .style("opacity", 1)
        })
    }, 1200)

    // Axes pour le graphique en barres
    barChart.append("g")
      .attr("transform", `translate(0,${barHeight})`)
      .call(d3.axisBottom(xScale))
      .selectAll("text")
      .style("font-size", "10px")
      .style("fill", "#666")
      .attr("transform", "rotate(-45)")
      .style("text-anchor", "end")

    barChart.append("g")
      .call(d3.axisLeft(yScale)
        .tickFormat(d => `${d}%`))
      .selectAll("text")
      .style("font-size", "11px")
      .style("fill", "#666")

    // Titre principal
    container.append("text")
      .attr("x", width/2)
      .attr("y", -20)
      .style("text-anchor", "middle")
      .style("font-size", "18px")
      .style("font-weight", "bold")
      .style("fill", "#333")
      .text("Activités de laboratoire - Volume et taux de positivité")

    // Sous-titres
    container.append("text")
      .attr("x", width/4)
      .attr("y", 20)
      .style("text-anchor", "middle")
      .style("font-size", "14px")
      .style("font-weight", "600")
      .style("fill", "#555")
      .text("Répartition des examens")

    container.append("text")
      .attr("x", width * 3/4)
      .attr("y", 20)
      .style("text-anchor", "middle")
      .style("font-size", "14px")
      .style("font-weight", "600")
      .style("fill", "#555")
      .text("Taux de positivité (%)")

  }, [data])

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <svg ref={svgRef} className="w-full overflow-visible"></svg>
    </div>
  )
}