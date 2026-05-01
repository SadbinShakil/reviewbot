"use client";

import { useState, useEffect } from "react";
import { api, CategoryCount, SeverityCount, AcceptanceRate, TimelinePoint } from "@/lib/api";
import {
  CategoryBarChart,
  SeverityPieChart,
  AcceptanceRateChart,
  PRTimelineChart,
} from "@/components/AnalyticsCharts";

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
      <p className="text-xs text-gray-500 mb-1 uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">{title}</h3>
      {children}
    </div>
  );
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<Awaited<ReturnType<typeof api.getAnalyticsSummary>> | null>(null);
  const [byCategory, setByCategory] = useState<CategoryCount[]>([]);
  const [bySeverity, setBySeverity] = useState<SeverityCount[]>([]);
  const [acceptanceRates, setAcceptanceRates] = useState<AcceptanceRate[]>([]);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getAnalyticsSummary(),
      api.getByCategory(),
      api.getBySeverity(),
      api.getAcceptanceRates(),
      api.getPRTimeline(30),
    ])
      .then(([sum, cat, sev, rates, tl]) => {
        setSummary(sum);
        setByCategory(cat);
        setBySeverity(sev);
        setAcceptanceRates(rates);
        setTimeline(tl);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32 text-gray-500">Loading analytics...</div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Analytics</h1>
        <p className="text-gray-400">Review quality and feedback metrics</p>
      </div>

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total PRs" value={summary.total_prs} />
          <StatCard label="Total Comments" value={summary.total_comments} />
          <StatCard label="Feedback Logged" value={summary.total_feedback} />
          <StatCard
            label="Overall Acceptance"
            value={`${(summary.overall_acceptance_rate * 100).toFixed(0)}%`}
            sub="comments accepted by authors"
          />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <ChartCard title="Comments by Category">
          {byCategory.length > 0 ? (
            <CategoryBarChart data={byCategory} />
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-600">No data yet</div>
          )}
        </ChartCard>

        <ChartCard title="Comments by Severity">
          {bySeverity.length > 0 ? (
            <SeverityPieChart data={bySeverity} />
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-600">No data yet</div>
          )}
        </ChartCard>

        <ChartCard title="Acceptance Rate by Category">
          {acceptanceRates.length > 0 ? (
            <AcceptanceRateChart data={acceptanceRates} />
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-600">
              Need at least 1 feedback entry
            </div>
          )}
        </ChartCard>

        <ChartCard title="PRs Reviewed (Last 30 Days)">
          {timeline.length > 0 ? (
            <PRTimelineChart data={timeline} />
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-600">No data yet</div>
          )}
        </ChartCard>
      </div>
    </div>
  );
}
