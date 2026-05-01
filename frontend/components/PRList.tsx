"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { api, PR } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";

const STATUS_STYLES: Record<string, string> = {
  reviewed: "bg-green-900 text-green-300",
  reviewing: "bg-blue-900 text-blue-300 animate-pulse",
  pending: "bg-gray-800 text-gray-400",
  error: "bg-red-900 text-red-300",
};

function PRRow({ pr }: { pr: PR }) {
  return (
    <Link href={`/pr/${pr.id}`} className="block">
      <div className="flex items-center gap-4 px-5 py-4 hover:bg-gray-800 transition-colors border-b border-gray-800 cursor-pointer">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-gray-500 font-mono">{pr.repo_full_name}#{pr.pr_number}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[pr.status] || STATUS_STYLES.pending}`}>
              {pr.status}
            </span>
          </div>
          <p className="text-sm font-medium text-white truncate">{pr.title}</p>
          <p className="text-xs text-gray-500 mt-0.5">by {pr.author}</p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-sm font-semibold text-blue-400">{pr.comment_count}</p>
          <p className="text-xs text-gray-500">comments</p>
        </div>
        <div className="text-right shrink-0 hidden sm:block">
          <p className="text-xs text-gray-400">
            {formatDistanceToNow(new Date(pr.created_at), { addSuffix: true })}
          </p>
        </div>
      </div>
    </Link>
  );
}

export default function PRList() {
  const [prs, setPrs] = useState<PR[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  const load = useCallback((silent = false) => {
    if (!silent) setLoading(true);
    api
      .listPRs(page * limit, limit, statusFilter || undefined)
      .then(({ total, items }) => {
        setTotal(total);
        setPrs(items);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [page, statusFilter]);

  // Initial load
  useEffect(() => { load(); }, [load]);

  // Auto-refresh every 4s so new reviews appear without manual refresh
  useEffect(() => {
    const interval = setInterval(() => load(true), 4000);
    return () => clearInterval(interval);
  }, [load]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">
            Past Reviews <span className="text-gray-500 text-sm">({total})</span>
          </h2>
          <span className="flex items-center gap-1 text-xs text-gray-600">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-600 animate-pulse" />
            live
          </span>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
          className="bg-gray-800 text-gray-300 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500"
        >
          <option value="">All statuses</option>
          <option value="reviewed">Reviewed</option>
          <option value="reviewing">Reviewing</option>
          <option value="pending">Pending</option>
          <option value="error">Error</option>
        </select>
      </div>

      <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
        {loading && prs.length === 0 ? (
          <div className="py-16 text-center text-gray-500">Loading...</div>
        ) : prs.length === 0 ? (
          <div className="py-16 text-center text-gray-500">
            <p className="text-lg">No reviews yet</p>
            <p className="text-sm mt-1">Paste a PR URL above and hit Review PR</p>
          </div>
        ) : (
          prs.map((pr) => <PRRow key={pr.id} pr={pr} />)
        )}
      </div>

      {total > limit && (
        <div className="flex justify-center gap-3 mt-4">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-4 py-2 text-sm bg-gray-800 rounded disabled:opacity-40 hover:bg-gray-700"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-gray-400">
            Page {page + 1} of {Math.ceil(total / limit)}
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={(page + 1) * limit >= total}
            className="px-4 py-2 text-sm bg-gray-800 rounded disabled:opacity-40 hover:bg-gray-700"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
