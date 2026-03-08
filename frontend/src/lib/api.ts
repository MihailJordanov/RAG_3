import {
  Project,
  Job,
  ChatMessage,
  ChatResponse,
  ProjectSource,
  ProjectLimits,
  AuthResponse,
  User,
} from "./types";
import { getAccessToken } from "./storage";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL!;

type ApiErrorBody =
  | { detail?: string | Array<{ msg?: string }> }
  | Record<string, unknown>;

async function extractErrorMessageFromResponse(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as ApiErrorBody;

    if (typeof data?.detail === "string") {
      return data.detail;
    }

    if (Array.isArray(data?.detail)) {
      const messages = data.detail
        .map((item) => item?.msg)
        .filter((msg): msg is string => typeof msg === "string" && msg.trim().length > 0);

      if (messages.length > 0) {
        return messages.join(", ");
      }
    }

    return `HTTP ${res.status} ${res.statusText}`;
  } catch {
    const text = await res.text().catch(() => "");
    return text || `HTTP ${res.status} ${res.statusText}`;
  }
}

function extractErrorMessageFromXhr(xhr: XMLHttpRequest): string {
  const fallback = `Upload failed with status ${xhr.status}`;

  try {
    const data = JSON.parse(xhr.responseText) as ApiErrorBody;

    if (typeof data?.detail === "string") {
      return data.detail;
    }

    if (Array.isArray(data?.detail)) {
      const messages = data.detail
        .map((item) => item?.msg)
        .filter((msg): msg is string => typeof msg === "string" && msg.trim().length > 0);

      if (messages.length > 0) {
        return messages.join(", ");
      }
    }

    return fallback;
  } catch {
    return xhr.responseText || fallback;
  }
}

function buildHeaders(init?: RequestInit): HeadersInit {
  const token = getAccessToken();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(init?.headers || {}),
  };
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: buildHeaders(init),
    cache: "no-store",
  });

  if (!res.ok) {
    const message = await extractErrorMessageFromResponse(res);
    throw new Error(message);
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

    const token = getAccessToken();
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

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
        reject(new Error(extractErrorMessageFromXhr(xhr)));
      }
    };

    xhr.onerror = () => {
      reject(new Error("Network error during file upload."));
    };

    xhr.send(form);
  });
}

export const api = {
  authGuest: () =>
    http<AuthResponse>("/auth/guest", {
      method: "POST",
    }),

  authGoogle: (credential: string) =>
    http<AuthResponse>("/auth/google", {
      method: "POST",
      body: JSON.stringify({ credential }),
    }),

  me: () => http<User>("/auth/me"),

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

    const token = getAccessToken();

    const res = await fetch(`${BASE}/projects/${projectId}/ingest/file`, {
      method: "POST",
      body: form,
      cache: "no-store",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });

    if (!res.ok) {
      const message = await extractErrorMessageFromResponse(res);
      throw new Error(message);
    }

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

  // limits
  getProjectLimits: (projectId: string) =>
    http<ProjectLimits>(`/projects/${projectId}/limits`),
};