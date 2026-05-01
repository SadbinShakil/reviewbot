"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, PRDetail } from "@/lib/api";
import CommentOverlay from "@/components/CommentOverlay";
import { formatDistanceToNow } from "date-fns";

const SEVERITY_ORDER = { critical: 0, warning: 1, suggestion: 2 };

export default function PRDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const [pr, setPr] = useState<PRDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [rerunning, setRerunning] = useState(false);
  const [sortBy, setSortBy] = useState<"file" | "severity" | "line">("file");
  const [filterSeverity, setFilterSeverity] = useState("");
  const [filterCategory, setFilterCategory] = useState("");

  const load = () => {
    setLoading(true);
    api
      .getPR(id)
      .then(setPr)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(load, [id]);

  const handleRerun = async () => {
    setRerunning(true);
    try {
      await api.rerunReview(id);
      load();
    } catch (e) {
      console.error(e);
    } finally {
      setRerunning(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center py-32 text-gray-500">Loading...</div>;
  }

  if (!pr) {
    return (
      <div className="text-center py-32">
        <p className="text-gray-500 text-lg">PR not found</p>
        <Link href="/" className="text-blue-400 hover:underline mt-2 inline-block">Back to dashboard</Link>
      </div>
    );
  }

  const filteredComments = pr.comments
    .filter((c) => (!filterSeverity || c.severity === filterSeverity))
    .filter((c) => (!filterCategory || c.category === filterCategory))
    .sort((a, b) => {
      if (sortBy === "severity") return SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
      if (sortBy === "line") return a.line_number - b.line_number;
      return a.file_path.localeCompare(b.file_path);
    });

  const criticalCount = pr.comments.filter((c) => c.severity === "critical").length;
  const warningCount = pr.comments.filter((c) => c.severity === "warning").length;
  const suggestionCount = pr.comments.filter((c) => c.severity === "suggestion").length;

  return (
    <div>
      <div className="mb-6">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-300 flex items-center gap-1 mb-4">
          ← Back to PRs
        </Link>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-mono text-gray-500">{pr.repo_full_name}#{pr.pr_number}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  pr.status === "reviewed" ? "bg-green-900 text-green-300" :
                  pr.status === "reviewing" ? "bg-blue-900 text-blue-300" :
                  "bg-gray-800 text-gray-400"
                }`}>{pr.status}</span>
              </div>
              <h1 className="text-xl font-bold text-white">{pr.title}</h1>
              <p className="text-sm text-gray-400 mt-1">
                by <span className="text-gray-300">{pr.author}</span>
                {pr.created_at && ` · ${formatDistanceToNow(new Date(pr.created_at), { addSuffix: true })}`}
              </p>
            </div>
            <div className="flex gap-3">
              {pr.pr_url && (
                <a
                  href={pr.pr_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded border border-gray-700 transition-colors"
                >
                  View on GitHub ↗
                </a>
              )}
              <button
                onClick={handleRerun}
                disabled={rerunning}
                className="text-sm px-4 py-2 bg-blue-700 hover:bg-blue-600 rounded transition-colors disabled:opacity-50"
              >
                {rerunning ? "Re-reviewing..." : "Re-run Review"}
              </button>
            </div>
          </div>

          <div className="flex gap-4 mt-5 pt-4 border-t border-gray-800">
            <div className="text-center">
              <p className="text-xl font-bold text-red-400">{criticalCount}</p>
              <p className="text-xs text-gray-500">Critical</p>
            </div>
            <div className="text-center">
              <p className="text-xl font-bold text-yellow-400">{warningCount}</p>
              <p className="text-xs text-gray-500">Warnings</p>
            </div>
            <div className="text-center">
              <p className="text-xl font-bold text-blue-400">{suggestionCount}</p>
              <p className="text-xs text-gray-500">Suggestions</p>
            </div>
          </div>
        </div>
      </div>

      {pr.comments.length > 0 && (
        <div className="flex flex-wrap gap-3 mb-5">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "file" | "severity" | "line")}
            className="bg-gray-800 text-gray-300 border border-gray-700 rounded px-3 py-1.5 text-sm"
          >
            <option value="file">Sort by file</option>
            <option value="severity">Sort by severity</option>
            <option value="line">Sort by line</option>
          </select>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-gray-800 text-gray-300 border border-gray-700 rounded px-3 py-1.5 text-sm"
          >
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="suggestion">Suggestion</option>
          </select>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="bg-gray-800 text-gray-300 border border-gray-700 rounded px-3 py-1.5 text-sm"
          >
            <option value="">All categories</option>
            <option value="bug">Bug</option>
            <option value="security">Security</option>
            <option value="performance">Performance</option>
            <option value="style">Style</option>
            <option value="testing">Testing</option>
          </select>
          <span className="text-sm text-gray-500 py-1.5">
            {filteredComments.length} of {pr.comments.length} comments
          </span>
        </div>
      )}

      <CommentOverlay comments={filteredComments} groupByFile={sortBy === "file"} />
    </div>
  );
}
