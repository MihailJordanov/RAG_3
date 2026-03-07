export type Project = {
  id: string;
  name: string;
  created_at?: string;
};

export type Job = {
  id: string;
  project_id?: string;
  status: "queued" | "running" | "succeeded" | "failed" | "not_found" | string;
  progress?: number;
  error?: string | null;
};

export type ChatMessage = {
  id?: number;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
};

export type ChatResponse = {
  answer: string;
  sources: Array<{ score: number; preview?: string }>;
};

