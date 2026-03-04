"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Link from "next/link";
import type { Project } from "@/lib/types";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");

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
          <li key={p.id} style={{ border: "1px solid #ddd", borderRadius: 10, padding: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontWeight: 700 }}>{p.name}</div>
                <div style={{ fontSize: 12, opacity: 0.7 }}>{p.id}</div>
              </div>
              <Link href={`/projects/${p.id}`}>Open →</Link>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}