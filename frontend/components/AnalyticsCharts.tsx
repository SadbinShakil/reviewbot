"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend,
} from "recharts";

const CATEGORY_COLORS: Record<string, string> = {
  bug: "#ef4444",
  security: "#f97316",
  performance: "#eab308",
  style: "#3b82f6",
  testing: "#8b5cf6",
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#ef4444",
  warning: "#f59e0b",
  suggestion: "#3b82f6",
};

interface CategoryChartProps {
  data: { category: string; count: number }[];
}

export function CategoryBarChart({ data }: CategoryChartProps) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <XAxis dataKey="category" tick={{ fill: "#9ca3af", fontSize: 12 }} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 12 }} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: 8 }}
          labelStyle={{ color: "#f3f4f6" }}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((entry) => (
            <Cell key={entry.category} fill={CATEGORY_COLORS[entry.category] || "#6b7280"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

interface SeverityChartProps {
  data: { severity: string; count: number }[];
}

export function SeverityPieChart({ data }: SeverityChartProps) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="severity"
          cx="50%"
          cy="50%"
          outerRadius={80}
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          labelLine={{ stroke: "#4b5563" }}
        >
          {data.map((entry) => (
            <Cell key={entry.severity} fill={SEVERITY_COLORS[entry.severity] || "#6b7280"} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: 8 }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

interface AcceptanceChartProps {
  data: { category: string; acceptance_rate: number }[];
}

export function AcceptanceRateChart({ data }: AcceptanceChartProps) {
  const formatted = data.map((d) => ({ ...d, pct: Math.round(d.acceptance_rate * 100) }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={formatted} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fill: "#9ca3af", fontSize: 12 }} />
        <YAxis type="category" dataKey="category" tick={{ fill: "#9ca3af", fontSize: 12 }} width={80} />
        <Tooltip
          formatter={(value: number) => [`${value}%`, "Acceptance Rate"]}
          contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: 8 }}
        />
        <Bar dataKey="pct" radius={[0, 4, 4, 0]} fill="#22c55e" />
      </BarChart>
    </ResponsiveContainer>
  );
}

interface TimelineChartProps {
  data: { day: string; count: number }[];
}

export function PRTimelineChart({ data }: TimelineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis dataKey="day" tick={{ fill: "#9ca3af", fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
        <YAxis tick={{ fill: "#9ca3af", fontSize: 12 }} />
        <Tooltip
          contentStyle={{ backgroundColor: "#111827", border: "1px solid #374151", borderRadius: 8 }}
          labelStyle={{ color: "#f3f4f6" }}
        />
        <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={false} name="PRs" />
      </LineChart>
    </ResponsiveContainer>
  );
}
