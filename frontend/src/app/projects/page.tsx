"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Link from "next/link";
import type { Project } from "@/lib/types";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);

  async function load() {
    setProjects(await api.listProjects());
  }

  useEffect(() => {
    load().catch(console.error);
  }, []);

  async function create() {
    const n = name.trim();
    if (!n) return;
    await api.createProject(n);
    setName("");
    await load();
  }

  async function remove(projectId: string) {
    const p = projects.find((x) => x.id === projectId);
    const label = p ? `"${p.name}"` : "this project";
    if (!confirm(`Delete ${label}? This will remove its messages, jobs, uploads and vector DB.`)) return;

    try {
      setBusyId(projectId);
      await api.deleteProject(projectId);
      await load();
    } catch (e) {
      console.error(e);
      alert("Failed to delete project. Check backend logs.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <main style={{ maxWidth: 900, margin: "0 auto", padding: 24 }}>
      <h1 style={{ fontSize: 28, marginBottom: 12 }}>Projects</h1>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Project name..."
          style={{ flex: 1, padding: 10 }}
        />
        <button onClick={create}>Create</button>
      </div>

      <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 10 }}>
        {projects.map((p) => (
          <li
            key={p.id}
            style={{ border: "1px solid #ddd", borderRadius: 10, padding: 14 }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: 10,
              }}
            >
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 700 }}>{p.name}</div>
                <div style={{ fontSize: 12, opacity: 0.7, wordBreak: "break-all" }}>
                  {p.id}
                </div>
              </div>

              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <Link href={`/projects/${p.id}`}>Open →</Link>
                <button
                  onClick={() => remove(p.id)}
                  disabled={busyId === p.id}
                  style={{
                    padding: "8px 10px",
                    borderRadius: 8,
                    border: "1px solid #f3b2b2",
                    background: busyId === p.id ? "#f8d7da" : "#ffe6e6",
                  }}
                >
                  {busyId === p.id ? "Deleting..." : "Delete"}
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}