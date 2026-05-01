import PRList from "@/components/PRList";
import DemoReviewer from "@/components/DemoReviewer";
import { api } from "@/lib/api";

async function SummaryStats() {
  try {
    const stats = await api.getAnalyticsSummary();
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Total PRs", value: stats.total_prs },
          { label: "Reviewed", value: stats.reviewed_prs },
          { label: "Comments Posted", value: stats.total_comments },
          { label: "Acceptance Rate", value: `${(stats.overall_acceptance_rate * 100).toFixed(0)}%` },
        ].map(({ label, value }) => (
          <div key={label} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <p className="text-xs text-gray-500 mb-1">{label}</p>
            <p className="text-2xl font-bold text-white">{value}</p>
          </div>
        ))}
      </div>
    );
  } catch {
    return null;
  }
}

export default function HomePage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-1">ReviewBot</h1>
        <p className="text-gray-400">GitHub pull request review dashboard</p>
      </div>

      <SummaryStats />

      <div className="mb-8">
        <DemoReviewer />
      </div>

      <PRList />
    </div>
  );
}
