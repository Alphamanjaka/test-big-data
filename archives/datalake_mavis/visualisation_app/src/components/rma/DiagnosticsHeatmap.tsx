'use client'

import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import type { Diagnostic } from '@/lib/api'

interface DiagnosticsHeatmapProps {
  data: Diagnostic[]
}

export default function DiagnosticsHeatmap({ data }: DiagnosticsHeatmapProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  
  useEffect(() => {
    if (!data || !Array.isArray(data) || data.length === 0 || !svgRef.current) return;
    
    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const margin = { top: 60, right: 150, bottom: 100, left: 200 }
    const width = 800 - margin.left - margin.right
    const height = 500 - margin.bottom - margin.top

    const container = svg
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    // Préparation des données pour la heatmap
    const ageGroups = ['0-28j', '29-59j', '2-11m', '1-4a', '5-14a', '15-24a', '25-59a', '60+']
    const ageKeys: Array<keyof Diagnostic> = ['age_0_28j', 'age_29_59j', 'age_2_11m', 'age_1_4a', 'age_5_14a', 'age_15_24a', 'age_25_59a', 'age_60plus']
    
    const heatmapData: Array<{
      diagnostic: string
      ageGroup: string
      value: number
      row: number
      col: number
    }> = []

    data.forEach((d, i) => {
      ageKeys.forEach((key, j) => {
        heatmapData.push({
          diagnostic: d.diagnosis,
          ageGroup: ageGroups[j],
          value: Number(d[key]) || 0,
          row: i,
          col: j
        })
      })
    })

    // Échelles
    const xScale = d3.scaleBand()
      .domain(ageGroups)
      .range([0, width])
      .padding(0.02)

    const yScale = d3.scaleBand()
      .domain(data.map(d => d.diagnosis))
      .range([0, height])
      .padding(0.02)

    const colorScale = d3.scaleSequential(d3.interpolateYlOrRd)
      .domain([0, d3.max(heatmapData, d => d.value) || 0])

    // Création des rectangles
    container.selectAll(".cell")
      .data(heatmapData)
      .enter()
      .append("rect")
      .attr("class", "cell")
      .attr("x", d => xScale(d.ageGroup) || 0)
      .attr("y", d => yScale(d.diagnostic) || 0)
      .attr("width", xScale.bandwidth())
      .attr("height", yScale.bandwidth())
      .style("fill", d => d.value === 0 ? "#f5f5f5" : colorScale(d.value))
      .style("stroke", "#fff")
      .style("stroke-width", 1)
      .style("cursor", "pointer")
      .on("mouseover", function(event, d) {
        // Tooltip
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

        tooltip
          .html(`<strong>${d.diagnostic}</strong><br/>
                 Âge: ${d.ageGroup}<br/>
                 Cas: ${d.value.toLocaleString()}`)
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 10) + "px")

        d3.select(this)
          .style("stroke", "#333")
          .style("stroke-width", 2)
      })
      .on("mouseout", function() {
        d3.selectAll(".tooltip").remove()
        d3.select(this)
          .style("stroke", "#fff")
          .style("stroke-width", 1)
      })

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
      .style("font-size", "11px")
      .style("fill", "#666")
      .call(wrap, 180)

    // Labels des axes
    container.append("text")
      .attr("transform", `translate(${width/2}, ${height + 50})`)
      .style("text-anchor", "middle")
      .style("font-size", "14px")
      .style("fill", "#333")
      .text("Tranches d'âge")

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
      .text("Heatmap des diagnostics par tranche d'âge")

    // Légende
    const legend = container.append("g")
      .attr("transform", `translate(${width + 20}, 20)`)

    const legendScale = d3.scaleLinear()
      .domain(colorScale.domain())
      .range([100, 0])

    const legendAxis = d3.axisRight(legendScale)
      .tickFormat(d3.format(".0f"))

    const legendGradient = svg.append("defs")
      .append("linearGradient")
      .attr("id", "legend-gradient")
      .attr("gradientUnits", "userSpaceOnUse")
      .attr("x1", 0).attr("y1", 100)
      .attr("x2", 0).attr("y2", 0)

    legendGradient.selectAll("stop")
      .data(d3.range(0, 1.1, 0.1))
      .enter().append("stop")
      .attr("offset", d => `${d * 100}%`)
      .attr("stop-color", d => colorScale(d * (colorScale.domain()[1] || 1)))

    legend.append("rect")
      .attr("width", 20)
      .attr("height", 100)
      .style("fill", "url(#legend-gradient)")

    legend.append("g")
      .attr("transform", "translate(20, 0)")
      .call(legendAxis)

    // Fonction pour wrap le texte
    function wrap(text: any, width: number) {
      text.each(function(this: SVGTextElement) {
        const text = d3.select(this)
        const words = text.text().split(/\s+/).reverse()
        let word
        let line: string[] = []
        let lineNumber = 0
        const lineHeight = 1.1
        const y = text.attr("y")
        const dy = parseFloat(text.attr("dy")) || 0
        let tspan = text.text(null).append("tspan")
          .attr("x", -10)
          .attr("y", y)
          .attr("dy", dy + "em")

        while (word = words.pop()) {
          line.push(word)
          tspan.text(line.join(" "))
          if (tspan.node()?.getComputedTextLength()! > width) {
            line.pop()
            tspan.text(line.join(" "))
            line = [word]
            tspan = text.append("tspan")
              .attr("x", -10)
              .attr("y", y)
              .attr("dy", ++lineNumber * lineHeight + dy + "em")
              .text(word)
          }
        }
      })
    }

  }, [data])

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <svg ref={svgRef} className="w-full overflow-visible"></svg>
    </div>
  )
}