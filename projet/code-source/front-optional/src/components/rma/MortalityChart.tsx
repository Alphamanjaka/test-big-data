'use client'

import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

interface MortalityData {
  service: string
  code: string
  diagnostic: string
  cas: number
  deces: number
}

interface MortalityChartProps {
  data: MortalityData[]
}

export default function MortalityChart({ data }: MortalityChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!data || data.length === 0 || !svgRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const margin = { top: 60, right: 80, bottom: 100, left: 150 }
    const width = 700 - margin.left - margin.right
    const height = 500 - margin.bottom - margin.top

    const container = svg
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // Calcul du taux de mortalité
    const processedData = data.map(d => ({
      ...d,
      mortalityRate: (d.deces / d.cas) * 100
    })).sort((a, b) => b.mortalityRate - a.mortalityRate)

    // Échelles
    const xScale = d3.scaleLinear()
      .domain([0, d3.max(processedData, d => d.mortalityRate) || 0])
      .range([0, width])

    const yScale = d3.scaleBand()
      .domain(processedData.map(d => d.diagnostic))
      .range([0, height])
      .padding(0.1)

    // Échelle de couleurs par service
    const colorScale = d3.scaleOrdinal<string>()
      .domain([...new Set(data.map(d => d.service))])
      .range(['#3B82F6', '#10B981', '#F59E0B', '#EF4444'])

    // Barres
    container.selectAll(".bar")
      .data(processedData)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", 0)
      .attr("y", d => yScale(d.diagnostic) || 0)
      .attr("width", 0)
      .attr("height", yScale.bandwidth())
      .style("fill", d => colorScale(d.service))
      .style("cursor", "pointer")
      .transition()
      .duration(1000)
      .attr("width", d => xScale(d.mortalityRate))

    // Ajout des événements après la transition
    setTimeout(() => {
      container.selectAll(".bar")
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
            .style("box-shadow", "0 4px 6px rgba(0, 0, 0, 0.1)")

          tooltip
            .html(`<strong>${d.diagnostic}</strong><br/>
                   Service: ${d.service}<br/>
                   Cas: ${d.cas}<br/>
                   Décès: ${d.deces}<br/>
                   Taux mortalité: <strong>${d.mortalityRate.toFixed(1)}%</strong>`)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 10) + "px")

          d3.select(this)
            .style("opacity", 0.8)
            .style("stroke", "#333")
            .style("stroke-width", 2)
        })
        .on("mouseout", function() {
          d3.selectAll(".tooltip").remove()
          d3.select(this)
            .style("opacity", 1)
            .style("stroke", "none")
        })
    }, 1000)

    // Labels des valeurs
    container.selectAll(".value-label")
      .data(processedData)
      .enter()
      .append("text")
      .attr("class", "value-label")
      .attr("x", d => xScale(d.mortalityRate) + 5)
      .attr("y", d => (yScale(d.diagnostic) || 0) + yScale.bandwidth()/2)
      .attr("dy", "0.35em")
      .style("font-size", "11px")
      .style("fill", "#666")
      .style("opacity", 0)
      .text(d => `${d.mortalityRate.toFixed(1)}%`)
      .transition()
      .delay(1000)
      .duration(500)
      .style("opacity", 1)

    // Axe X
    container.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickFormat(d => `${d}%`))
      .selectAll("text")
      .style("font-size", "12px")
      .style("fill", "#666")

    // Axe Y
    container.append("g")
      .call(d3.axisLeft(yScale))
      .selectAll("text")
      .style("font-size", "11px")
      .style("fill", "#666")

    // Labels des axes
    container.append("text")
      .attr("transform", `translate(${width/2}, ${height + 40})`)
      .style("text-anchor", "middle")
      .style("font-size", "14px")
      .style("fill", "#333")
      .text("Taux de mortalité (%)")

    container.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -margin.left + 20)
      .attr("x", -height/2)
      .style("text-anchor", "middle")
      .style("font-size", "14px")
      .style("fill", "#333")
      .text("Diagnostics")

    // Titre
    container.append("text")
      .attr("x", width/2)
      .attr("y", -20)
      .style("text-anchor", "middle")
      .style("font-size", "18px")
      .style("font-weight", "bold")
      .style("fill", "#333")
      .text("Taux de mortalité par diagnostic")

    // Légende des services
    const legend = container.append("g")
      .attr("transform", `translate(${width - 200}, 20)`)

    const services = [...new Set(data.map(d => d.service))]
    
    legend.selectAll(".legend-item")
      .data(services)
      .enter()
      .append("g")
      .attr("class", "legend-item")
      .attr("transform", (d, i) => `translate(0, ${i * 25})`)
      .each(function(d, i) {
        const item = d3.select(this)
        
        item.append("rect")
          .attr("width", 18)
          .attr("height", 18)
          .style("fill", colorScale(d))

        item.append("text")
          .attr("x", 25)
          .attr("y", 9)
          .attr("dy", "0.35em")
          .style("font-size", "12px")
          .style("fill", "#333")
          .text(d)
      })

  }, [data])

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <svg ref={svgRef} className="w-full overflow-visible"></svg>
    </div>
  )
}