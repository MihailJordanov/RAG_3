import { Project, Job, ChatMessage, ChatResponse, ProjectSource } from "./types";

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

type IngestResponse = {
  job_id: string;
  status: string;
  file: string;
};

function ingestPdfWithProgress(
  projectId: string,
  file: File,
  onProgress: (progress: number) => void
): Promise<IngestResponse> {
  return new Promise((resolve, reject) => {
    const form = new FormData();
    form.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${BASE}/projects/${projectId}/ingest/file`);

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable) return;
      const percent = Math.round((event.loaded / event.total) * 100);
      onProgress(percent);
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const parsed = JSON.parse(xhr.responseText) as IngestResponse;
          resolve(parsed);
        } catch {
          reject(new Error("Invalid JSON response from upload endpoint."));
        }
      } else {
        reject(new Error(xhr.responseText || `Upload failed with status ${xhr.status}`));
      }
    };

    xhr.onerror = () => {
      reject(new Error("Network error during file upload."));
    };

    xhr.send(form);
  });
}

export const api = {
  // projects
  listProjects: () => http<Project[]>("/projects"),

  createProject: (name: string) =>
    http<Project>("/projects", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  deleteProject: (projectId: string) =>
    http<{ status: string }>(`/projects/${projectId}`, {
      method: "DELETE",
    }),

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
    return res.json() as Promise<IngestResponse>;
  },

  ingestPdfWithProgress,

  // jobs
  getJob: (jobId: string) => http<Job>(`/jobs/${jobId}`),

  getIngestJobStatus: (jobId: string) => http<Job>(`/jobs/${jobId}`),

  // chat
  chat: (projectId: string, message: string) =>
    http<ChatResponse>(`/projects/${projectId}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  // history
  listMessages: (projectId: string) =>
    http<ChatMessage[]>(`/projects/${projectId}/messages`),

  // sources
  listSources: (projectId: string) =>
    http<ProjectSource[]>(`/projects/${projectId}/sources`),
};