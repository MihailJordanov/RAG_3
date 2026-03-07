"use client";

import { useEffect, useMemo, useState } from "react";
import ProjectList from "./ProjectList";
import ChatWindow from "./ChatWindow";
import UploadCard from "./UploadCard";
import SourcesPanel from "./SourcesPanel";
import { api } from "@/lib/api";

type Project = {
  id: string;
  name: string;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export default function Shell() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  const [messagesByProject, setMessagesByProject] = useState<
    Record<string, Message[]>
  >({});

  async function load() {
    const data = await api.listProjects();
    setProjects(data);

    if (!activeProjectId && data.length > 0) {
      setActiveProjectId(data[0].id);
    }

    if (activeProjectId && !data.find((p) => p.id === activeProjectId)) {
      setActiveProjectId(data[0]?.id ?? "");
    }
  }

  useEffect(() => {
    load().catch(console.error);
  }, []);

  const activeProject = useMemo(
    () => projects.find((p) => p.id === activeProjectId) ?? null,
    [projects, activeProjectId]
  );

  const activeMessages = activeProject
    ? messagesByProject[activeProject.id] ?? []
    : [];

  async function handleCreateProject() {
    const name = prompt("Project name:");
    const trimmed = name?.trim();
    if (!trimmed) return;

    await api.createProject(trimmed);
    await load();
  }

  async function handleDeleteProject(projectId: string) {
    const p = projects.find((x) => x.id === projectId);
    const label = p ? `"${p.name}"` : "this project";

    if (
      !confirm(
        `Delete ${label}? This will remove its messages, jobs, uploads and vector DB.`
      )
    ) {
      return;
    }

    try {
      setBusyId(projectId);
      await api.deleteProject(projectId);

      if (activeProjectId === projectId) {
        const remaining = projects.filter((p) => p.id !== projectId);
        setActiveProjectId(remaining[0]?.id ?? "");
      }

      await load();
    } catch (e) {
      console.error(e);
      alert("Failed to delete project. Check backend logs.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleSendMessage(text: string) {
    if (!activeProject) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };

    setMessagesByProject((prev) => ({
      ...prev,
      [activeProject.id]: [...(prev[activeProject.id] ?? []), userMessage],
    }));

    setIsGenerating(true);

    setTimeout(() => {
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content:
          "This is a placeholder assistant response. Next step is connecting this UI to your backend chat endpoint.",
      };

      setMessagesByProject((prev) => ({
        ...prev,
        [activeProject.id]: [...(prev[activeProject.id] ?? []), assistantMessage],
      }));

      setIsGenerating(false);
    }, 1800);
  }

  return (
    <main className="workspace-page">
      <div className="workspace-bg-orb workspace-bg-orb-1" />
      <div className="workspace-bg-orb workspace-bg-orb-2" />

      <section className="workspace-shell">
        <aside className="panel sidebar-panel">
          <ProjectList
            projects={projects}
            activeProjectId={activeProjectId}
            busyId={busyId}
            onSelect={setActiveProjectId}
            onCreate={handleCreateProject}
            onDelete={handleDeleteProject}
          />
        </aside>

        <section className="panel chat-panel">
          <ChatWindow
            projectName={activeProject?.name ?? "No project selected"}
            messages={activeMessages}
            isGenerating={isGenerating}
            onSend={handleSendMessage}
          />
        </section>

        <aside className="panel right-panel">
          <UploadCard projectName={activeProject?.name ?? null} />
          <SourcesPanel />
        </aside>
      </section>
    </main>
  );
}