const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export interface PR {
  id: number;
  repo_full_name: string;
  pr_number: number;
  title: string;
  author: string;
  status: string;
  pr_url: string;
  created_at: string;
  reviewed_at: string | null;
  comment_count: number;
}

export interface PRComment {
  id: number;
  github_comment_id: number | null;
  file_path: string;
  line_number: number;
  severity: "critical" | "warning" | "suggestion";
  category: "bug" | "security" | "performance" | "style" | "testing";
  comment_text: string;
  suggestion: string;
  created_at: string;
  feedback: { outcome: string; logged_at: string } | null;
}

export interface PRDetail extends PR {
  head_sha: string;
  comments: PRComment[];
}

export interface AnalyticsSummary {
  total_prs: number;
  reviewed_prs: number;
  total_comments: number;
  total_feedback: number;
  overall_acceptance_rate: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface SeverityCount {
  severity: string;
  count: number;
}

export interface AcceptanceRate {
  category: string;
  acceptance_rate: number;
}

export interface TimelinePoint {
  day: string;
  count: number;
}

export const api = {
  listPRs: (skip = 0, limit = 20, status?: string) => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (status) params.set("status", status);
    return apiFetch<{ total: number; items: PR[] }>(`/reviews?${params}`);
  },

  getPR: (id: number) => apiFetch<PRDetail>(`/reviews/${id}`),

  rerunReview: (id: number) =>
    apiFetch<{ status: string }>(`/reviews/${id}/rerun`, { method: "POST" }),

  getAnalyticsSummary: () => apiFetch<AnalyticsSummary>("/analytics/summary"),
  getByCategory: () => apiFetch<CategoryCount[]>("/analytics/by-category"),
  getBySeverity: () => apiFetch<SeverityCount[]>("/analytics/by-severity"),
  getAcceptanceRates: () => apiFetch<AcceptanceRate[]>("/analytics/acceptance-rates"),
  getPRTimeline: (days = 30) => apiFetch<TimelinePoint[]>(`/analytics/pr-timeline?days=${days}`),
  getFeedbackStats: () => apiFetch<Record<string, unknown>>("/analytics/feedback-stats"),
};
