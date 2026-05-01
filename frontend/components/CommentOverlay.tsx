"use client";

import { PRComment } from "@/lib/api";
import clsx from "clsx";

const SEVERITY_CONFIG = {
  critical: { emoji: "🔴", label: "Critical", classes: "border-red-800 bg-red-950/50 text-red-300" },
  warning: { emoji: "🟡", label: "Warning", classes: "border-yellow-800 bg-yellow-950/50 text-yellow-300" },
  suggestion: { emoji: "🔵", label: "Suggestion", classes: "border-blue-800 bg-blue-950/50 text-blue-300" },
};

const OUTCOME_BADGE: Record<string, string> = {
  accepted: "bg-green-900 text-green-300",
  dismissed: "bg-gray-800 text-gray-400",
  modified: "bg-purple-900 text-purple-300",
};

interface Props {
  comments: PRComment[];
  groupByFile?: boolean;
}

function CommentCard({ comment }: { comment: PRComment }) {
  const config = SEVERITY_CONFIG[comment.severity] || SEVERITY_CONFIG.suggestion;

  return (
    <div className={clsx("border rounded-lg p-4 mb-3", config.classes)}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <span>{config.emoji}</span>
          <span className="text-xs font-semibold uppercase tracking-wide">{config.label}</span>
          <span className="text-xs px-2 py-0.5 rounded bg-black/20 text-current">{comment.category}</span>
          <span className="text-xs text-gray-500 font-mono">line {comment.line_number}</span>
        </div>
        {comment.feedback && (
          <span className={clsx("text-xs px-2 py-0.5 rounded-full font-medium", OUTCOME_BADGE[comment.feedback.outcome])}>
            {comment.feedback.outcome}
          </span>
        )}
      </div>
      <p className="text-sm text-gray-200 leading-relaxed">{comment.comment_text}</p>
      {comment.suggestion && (
        <div className="mt-3">
          <p className="text-xs text-gray-400 mb-1 font-medium">Suggestion:</p>
          <pre className="text-xs bg-black/30 rounded p-3 overflow-x-auto text-gray-300 whitespace-pre-wrap">
            {comment.suggestion}
          </pre>
        </div>
      )}
    </div>
  );
}

export default function CommentOverlay({ comments, groupByFile = true }: Props) {
  if (comments.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">No comments found</p>
        <p className="text-sm mt-1">This PR either has no issues or hasn&#39;t been reviewed yet</p>
      </div>
    );
  }

  if (!groupByFile) {
    return (
      <div>
        {comments.map((c) => (
          <CommentCard key={c.id} comment={c} />
        ))}
      </div>
    );
  }

  const byFile: Record<string, PRComment[]> = {};
  for (const c of comments) {
    if (!byFile[c.file_path]) byFile[c.file_path] = [];
    byFile[c.file_path].push(c);
  }

  return (
    <div>
      {Object.entries(byFile).map(([filePath, fileComments]) => (
        <div key={filePath} className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <span className="font-mono text-sm text-gray-300 bg-gray-800 px-3 py-1 rounded">
              {filePath}
            </span>
            <span className="text-xs text-gray-500">{fileComments.length} comment{fileComments.length !== 1 ? "s" : ""}</span>
          </div>
          {fileComments
            .sort((a, b) => a.line_number - b.line_number)
            .map((c) => (
              <CommentCard key={c.id} comment={c} />
            ))}
        </div>
      ))}
    </div>
  );
}
