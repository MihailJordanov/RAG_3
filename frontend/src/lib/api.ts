import { Project, Job, ChatMessage, ChatResponse } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL!;

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // projects
  listProjects: () => http<Project[]>("/projects"),
  createProject: (name: string) =>
    http<Project>("/projects", { method: "POST", body: JSON.stringify({ name }) }),

  deleteProject: (projectId: string) =>
    http<{ status: string }>(`/projects/${projectId}`, { method: "DELETE" }),

  // ingest
  ingestPdf: async (projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);

    const res = await fetch(`${BASE}/projects/${projectId}/ingest/file`, {
      method: "POST",
      body: form,
      cache: "no-store",
    });

    if (!res.ok) throw new Error(await res.text());
    return res.json() as Promise<{ job_id: string; status: string; file: string }>;
  },

  // jobs
  getJob: (jobId: string) => http<Job>(`/jobs/${jobId}`),

  // chat
  chat: (projectId: string, message: string) =>
    http<ChatResponse>(`/projects/${projectId}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  // history
  listMessages: (projectId: string) =>
    http<ChatMessage[]>(`/projects/${projectId}/messages`),
};