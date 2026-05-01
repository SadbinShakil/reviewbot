"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import clsx from "clsx";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type LogLine = {
  type: "status" | "pr_found" | "comment" | "done" | "error";
  message?: string;
  file_path?: string;
  line?: number;
  severity?: "critical" | "warning" | "suggestion";
  category?: string;
  comment?: string;
  suggestion?: string;
  posted_to_github?: boolean;
  pr_id?: number;
  total?: number;
};

const SEVERITY_COLOR = {
  critical: "text-red-400",
  warning: "text-yellow-400",
  suggestion: "text-blue-400",
};

const SEVERITY_EMOJI = {
  critical: "🔴",
  warning: "🟡",
  suggestion: "🔵",
};

export default function DemoReviewer() {
  const [url, setUrl] = useState("");
  const [running, setRunning] = useState(false);
  const [log, setLog] = useState<LogLine[]>([]);
  const [prId, setPrId] = useState<number | null>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [log]);

  const handleReview = async () => {
    if (!url.trim() || running) return;
    setRunning(true);
    setLog([]);
    setPrId(null);

    try {
      const res = await fetch(`${API_BASE}/demo/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pr_url: url.trim() }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        setLog([{ type: "error", message: err.detail || "Request failed" }]);
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const parsed: LogLine = JSON.parse(line.slice(6));
            setLog((prev) => [...prev, parsed]);
            if (parsed.pr_id) setPrId(parsed.pr_id);
          } catch {
            // ignore malformed SSE line
          }
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Connection failed";
      setLog((prev) => [...prev, { type: "error", message: msg }]);
    } finally {
      setRunning(false);
    }
  };

  const isDone = log.some((l) => l.type === "done");
  const hasError = log.some((l) => l.type === "error");
  const comments = log.filter((l) => l.type === "comment");

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800">
        <h2 className="text-base font-semibold text-white">Try ReviewBot on any public PR</h2>
        <p className="text-xs text-gray-500 mt-0.5">Paste a GitHub pull request URL to run a live AI review</p>
      </div>

      {/* Input */}
      <div className="px-6 py-4 flex gap-3">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleReview()}
          placeholder="https://github.com/owner/repo/pull/123"
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono"
          disabled={running}
        />
        <button
          onClick={handleReview}
          disabled={running || !url.trim()}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-sm font-semibold text-white transition-colors shrink-0"
        >
          {running ? (
            <span className="flex items-center gap-2">
              <span className="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Reviewing...
            </span>
          ) : (
            "Review PR"
          )}
        </button>
      </div>

      {/* Live log */}
      {log.length > 0 && (
        <div className="px-6 pb-6">
          <div
            ref={logRef}
            className="bg-gray-950 rounded-lg border border-gray-800 p-4 max-h-96 overflow-y-auto font-mono text-xs space-y-2"
          >
            {log.map((line, i) => {
              if (line.type === "status") {
                return (
                  <div key={i} className="text-gray-400 flex items-center gap-2">
                    <span className="text-gray-600">›</span> {line.message}
                  </div>
                );
              }
              if (line.type === "pr_found") {
                return (
                  <div key={i} className="text-green-400 flex items-center gap-2">
                    <span>✓</span> {line.message}
                  </div>
                );
              }
              if (line.type === "comment") {
                const sev = line.severity ?? "suggestion";
                return (
                  <div key={i} className={clsx("border-l-2 pl-3 py-1", {
                    "border-red-600": sev === "critical",
                    "border-yellow-600": sev === "warning",
                    "border-blue-600": sev === "suggestion",
                  })}>
                    <div className={clsx("font-semibold", SEVERITY_COLOR[sev])}>
                      {SEVERITY_EMOJI[sev]} [{line.category?.toUpperCase()}] {line.file_path}:{line.line}
                    </div>
                    <div className="text-gray-300 mt-0.5 whitespace-pre-wrap">{line.comment}</div>
                    {line.suggestion && (
                      <div className="text-gray-500 mt-1">↳ {line.suggestion}</div>
                    )}
                    {line.posted_to_github && (
                      <div className="text-green-500 mt-0.5">✓ Posted to GitHub</div>
                    )}
                  </div>
                );
              }
              if (line.type === "done") {
                return (
                  <div key={i} className="text-green-400 font-semibold border-t border-gray-800 pt-2 mt-2">
                    ✓ {line.message}
                  </div>
                );
              }
              if (line.type === "error") {
                return (
                  <div key={i} className="text-red-400 flex items-center gap-2">
                    <span>✗</span> {line.message}
                  </div>
                );
              }
              return null;
            })}

            {running && (
              <div className="text-gray-600 animate-pulse">analyzing...</div>
            )}
          </div>

          {/* Summary bar */}
          {(isDone || hasError) && (
            <div className="mt-3 flex items-center justify-between">
              <div className="flex gap-4 text-xs">
                {comments.filter((c) => c.severity === "critical").length > 0 && (
                  <span className="text-red-400">
                    🔴 {comments.filter((c) => c.severity === "critical").length} critical
                  </span>
                )}
                {comments.filter((c) => c.severity === "warning").length > 0 && (
                  <span className="text-yellow-400">
                    🟡 {comments.filter((c) => c.severity === "warning").length} warnings
                  </span>
                )}
                {comments.filter((c) => c.severity === "suggestion").length > 0 && (
                  <span className="text-blue-400">
                    🔵 {comments.filter((c) => c.severity === "suggestion").length} suggestions
                  </span>
                )}
                {comments.length === 0 && isDone && (
                  <span className="text-green-400">No issues found</span>
                )}
              </div>
              {prId && (
                <button
                  onClick={() => router.push(`/pr/${prId}`)}
                  className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded border border-gray-700 text-gray-300 transition-colors"
                >
                  View full report →
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
