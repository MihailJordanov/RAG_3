"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ChatMessage, Job } from "@/lib/types";

export default function ProjectPage({ params }: { params: { projectId: string } }) {
  const projectId = params.projectId;

  const [file, setFile] = useState<File | null>(null);
  const [job, setJob] = useState<Job | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  // history (ако endpoint съществува)
  useEffect(() => {
    api.listMessages(projectId).then(setMessages).catch(() => {});
  }, [projectId]);

  async function uploadAndIngest() {
    if (!file) return;
    const r = await api.ingestPdf(projectId, file);
    const jobId = r.job_id;

    // simple polling
    const timer = setInterval(async () => {
      const j = await api.getJob(jobId);
      setJob(j);
      if (j.status === "succeeded" || j.status === "failed") clearInterval(timer);
    }, 1000);
  }

  async function send() {
    const q = input.trim();
    if (!q) return;
    setSending(true);
    setInput("");

    setMessages((m: ChatMessage[]) => [...m, { role: "user", content: q }]);

    try {
      const res = await api.chat(projectId, q);
      setMessages((m: ChatMessage[]) => [...m, { role: "assistant", content: res.answer }]);
    } finally {
      setSending(false);
    }
  }

  const ready = job?.status === "succeeded";

  return (
    <main style={{ maxWidth: 1100, margin: "0 auto", padding: 24, display: "grid", gap: 16 }}>
      <h1 style={{ fontSize: 22 }}>Project: {projectId}</h1>

      <section style={{ border: "1px solid #ddd", borderRadius: 12, padding: 14 }}>
        <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <button onClick={uploadAndIngest} disabled={!file} style={{ marginLeft: 8 }}>
          Upload & Ingest
        </button>

        {job && (
          <div style={{ marginTop: 10 }}>
            <b>Status:</b> {job.status} {typeof job.progress === "number" ? `(${job.progress}%)` : ""}
            {job.error ? <div style={{ color: "crimson" }}>{job.error}</div> : null}
          </div>
        )}
      </section>

      <section style={{ border: "1px solid #ddd", borderRadius: 12, padding: 14 }}>
        <div style={{ height: 420, overflow: "auto", padding: 8, background: "#fafafa", borderRadius: 10 }}>
          {messages.map((m, i) => (
            <div key={i} style={{ marginBottom: 10, whiteSpace: "pre-wrap" }}>
              <b>{m.role}:</b> {m.content}
            </div>
          ))}
        </div>

        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!ready || sending}
            placeholder={ready ? "Ask..." : "Upload & ingest first..."}
            style={{ flex: 1, padding: 10 }}
            onKeyDown={(e) => e.key === "Enter" && send()}
          />
          <button onClick={send} disabled={!ready || sending}>
            Send
          </button>
        </div>
      </section>
    </main>
  );
}