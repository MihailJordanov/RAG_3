export type User = {
  id: string;
  name?: string | null;
  email?: string | null;
  is_guest: boolean;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer" | string;
  user: User;
};

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
  message?: string;
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

export type ProjectSource = {
  name: string;
  status?: string;
  size_bytes?: number;
};

export type ProjectLimits = {
  max_files_per_project: number;
  max_file_size_mb: number;
  max_total_project_size_mb: number;
  max_file_size_bytes: number;
  max_total_project_size_bytes: number;
  current_file_count: number;
  current_total_size_bytes: number;
  remaining_file_slots: number;
  remaining_total_size_bytes: number;
};