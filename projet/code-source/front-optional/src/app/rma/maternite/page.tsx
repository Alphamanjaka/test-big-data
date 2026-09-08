"use client";

import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { useFilters } from "@/context/FiltersContext";
import { getMaternity, MaternityPoint } from "@/lib/api";
import { Activity, Baby } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface MaterniteRow {
  month: string;
  CPN1: number;
  CPN4: number;
  Accouchements: number;
  Avortements: number;
  DecesMaternels: number;
  MortsNes: number;
  VisitesPostnatales: number;
}

export default function MaternitePage() {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const { filters, updateCount } = useFilters();
  const [data, setData] = useState<MaterniteRow[]>([]);
  const [loading, setLoading] = useState(true);

  // KPIs calculés
  const totalCPN1 = data.reduce((s, d) => s + d.CPN1, 0);
  const totalCPN4 = data.reduce((s, d) => s + d.CPN4, 0);
  const totalAccouchements = data.reduce((s, d) => s + d.Accouchements, 0);
  const totalDecesMaternels = data.reduce((s, d) => s + d.DecesMaternels, 0);
  const totalAvortements = data.reduce((s, d) => s + d.Avortements, 0);
  const tauxCPN4 = totalCPN1 > 0 ? ((totalCPN4 / totalCPN1) * 100).toFixed(1) : "0";

  const loadData = async () => {
    setLoading(true);
    try {
      const raw: MaternityPoint[] = await getMaternity({
        start: filters.dateRange.start,
        end: filters.dateRange.end,
        sex: filters.gender === "all" ? undefined : filters.gender,
      });

      // Le backend renvoie [{ month, total, accouchements, deces_maternels, live_births_total }]
      // On adapte au format du graphique { month, CPN1, Accouchements, ... }
      const mapped: MaterniteRow[] = raw.map((r) => ({
        month: r.month,
        CPN1: r.total ?? 0,
        CPN4: 0,
        Accouchements: r.accouchements ?? 0,
        Avortements: 0,
        DecesMaternels: r.deces_maternels ?? 0,
        MortsNes: 0,
        VisitesPostnatales: 0,
      }));

      setData(mapped);
    } catch (error) {
      console.error("Erreur chargement maternité:", error);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [updateCount]);

  useEffect(() => {
    if (!svgRef.current || loading) return;
    const width = 700, height = 380, margin = { top: 40, right: 30, bottom: 50, left: 60 };
    d3.select(svgRef.current).selectAll("*").remove();
    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("preserveAspectRatio", "xMidYMid meet");

    const x = d3.scalePoint().domain(data.map((d) => d.month))
      .range([margin.left, width - margin.right]);
    const y = d3.scaleLinear().domain([0, d3.max(data, (d) => Math.max(d.CPN1, d.Accouchements))!])
      .nice().range([height - margin.bottom, margin.top]);

    // Axes
    svg.append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .style("font-size", "10px")
      .attr("transform", "rotate(-35)")
      .style("text-anchor", "end");

    svg.append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y));

    // Ligne CPN1
    const cpn1Line = d3.line<any>().x((d) => x(d.month)!).y((d) => y(d.CPN1)).curve(d3.curveMonotoneX);
    svg.append("path").datum(data).attr("fill", "none")
      .attr("stroke", "#3b82f6").attr("stroke-width", 2.5).attr("d", cpn1Line(data));

    // Ligne Accouchements
    const accLine = d3.line<any>().x((d) => x(d.month)!).y((d) => y(d.Accouchements)).curve(d3.curveMonotoneX);
    svg.append("path").datum(data).attr("fill", "none")
      .attr("stroke", "#ef4444").attr("stroke-width", 2.5).attr("d", accLine(data));

    // Points CPN1
    svg.selectAll(".dot-cpn1").data(data).enter().append("circle")
      .attr("cx", (d) => x(d.month)!)
      .attr("cy", (d) => y(d.CPN1))
      .attr("r", 4).style("fill", "#3b82f6");

    // Points Accouchements
    svg.selectAll(".dot-acc").data(data).enter().append("circle")
      .attr("cx", (d) => x(d.month)!)
      .attr("cy", (d) => y(d.Accouchements))
      .attr("r", 4).style("fill", "#ef4444");

    // Légende
    const legend = svg.append("g").attr("transform", `translate(${width - 180}, 20)`);
    legend.append("line").attr("x1", 0).attr("x2", 20).attr("y1", 0).attr("y2", 0).style("stroke", "#3b82f6").style("stroke-width", 3);
    legend.append("text").attr("x", 25).attr("y", 0).attr("dy", "0.35em").style("font-size", "11px").text("CPN1");
    legend.append("line").attr("x1", 0).attr("x2", 20).attr("y1", 18).attr("y2", 18).style("stroke", "#ef4444").style("stroke-width", 3);
    legend.append("text").attr("x", 25).attr("y", 18).attr("dy", "0.35em").style("font-size", "11px").text("Accouchements");

    // Labels axes
    svg.append("text")
      .attr("transform", `translate(${width/2}, ${height - 5})`)
      .style("text-anchor", "middle").style("font-size", "12px").text("Mois");
    svg.append("text")
      .attr("transform", "rotate(-90)").attr("y", 15).attr("x", -height / 2)
      .style("text-anchor", "middle").style("font-size", "12px").text("Nombre");
  }, [data, loading]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Chargement des données de maternité...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Baby className="w-5 h-5 text-pink-600" />
            <span>Tableaux 11 & 12 - Consultations prénatales & Maternité</span>
          </CardTitle>
          <CardDescription>
            Évolution des CPN (1ère visite) et des accouchements mensuels
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-xs text-blue-600 font-medium">Taux CPN ≥ 4</p>
              <p className="text-2xl font-bold text-blue-700">{tauxCPN4}%</p>
              <p className="text-xs text-gray-500">{totalCPN4} / {totalCPN1} femmes suivies</p>
            </div>
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <p className="text-xs text-red-600 font-medium">Décès maternels</p>
              <p className="text-2xl font-bold text-red-700">{totalDecesMaternels}</p>
              <p className="text-xs text-gray-500">sur {totalAccouchements} accouchements</p>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <p className="text-xs text-yellow-600 font-medium">Avortements</p>
              <p className="text-2xl font-bold text-yellow-700">{totalAvortements}</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-xs text-green-600 font-medium">Accouchements totaux</p>
              <p className="text-2xl font-bold text-green-700">{totalAccouchements}</p>
            </div>
          </div>

          {/* Graphique */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">Évolution mensuelle</h3>
            <svg ref={svgRef}></svg>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
