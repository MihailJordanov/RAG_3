"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import ProjectList from "./ProjectList";
import ChatWindow from "./ChatWindow";
import UploadCard from "./UploadCard";
import SourcesPanel from "./SourcesPanel";
import type { Project, ChatMessage, ProjectSource } from "@/lib/types";

export default function Shell() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string>("");
  const [newProjectName, setNewProjectName] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [sources, setSources] = useState<ProjectSource[]>([]);
  const [isLoadingSources, setIsLoadingSources] = useState(false);

  const [uploadState, setUploadState] = useState<{
    fileName: string;
    phase: "idle" | "uploading" | "processing" | "done" | "error";
    progress: number;
    message?: string;
  } | null>(null);

  async function loadProjects() {
    const data = await api.listProjects();
    setProjects(data);

    setActiveProjectId((current) => {
      if (current && data.some((p) => p.id === current)) return current;
      return data[0]?.id ?? "";
    });
  }

  useEffect(() => {
    loadProjects().catch(console.error);
  }, []);

  useEffect(() => {
    if (!activeProjectId) {
      setSources([]);
      return;
    }

    loadSources(activeProjectId).catch(console.error);
  }, [activeProjectId]);

  useEffect(() => {
    if (!activeProjectId) {
      setMessages([]);
      return;
    }

    async function loadMessages() {
      try {
        setIsLoadingMessages(true);
        const data = await api.listMessages(activeProjectId);
        setMessages(data);
      } catch (err) {
        console.error(err);
        setMessages([]);
      } finally {
        setIsLoadingMessages(false);
      }
    }

    loadMessages().catch(console.error);
  }, [activeProjectId]);

  const activeProject = useMemo(
    () => projects.find((p) => p.id === activeProjectId) ?? null,
    [projects, activeProjectId]
  );

  const hasSelectedProject = !!activeProject;

  async function handleCreateProject() {
    const name = newProjectName.trim();
    if (!name) return;

    try {
      const created = await api.createProject(name);
      setNewProjectName("");
      await loadProjects();
      setActiveProjectId(created.id);
    } catch (err) {
      console.error(err);
      alert("Failed to create project.");
    }
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

      const remaining = projects.filter((p) => p.id !== projectId);
      if (activeProjectId === projectId) {
        setActiveProjectId(remaining[0]?.id ?? "");
      }

      await loadProjects();
    } catch (e) {
      console.error(e);
      alert("Failed to delete project. Check backend logs.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleSendMessage(text: string) {
    if (!activeProjectId) return;

    const optimisticUserMessage: ChatMessage = {
      role: "user",
      content: text,
    };

    setMessages((prev) => [...prev, optimisticUserMessage]);
    setIsGenerating(true);

    try {
      const response = await api.chat(activeProjectId, text);

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.answer,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error(err);

      const assistantError: ChatMessage = {
        role: "assistant",
        content: "Failed to get response from backend.",
      };

      setMessages((prev) => [...prev, assistantError]);
    } finally {
      setIsGenerating(false);
    }
  }

  async function loadSources(projectId: string) {
    try {
      setIsLoadingSources(true);
      const data = await api.listSources(projectId);
      setSources(data);
    } catch (err) {
      console.error(err);
      setSources([]);
    } finally {
      setIsLoadingSources(false);
    }
  }

  async function pollIngestJob(jobId: string, fileName: string) {
    let done = false;

    while (!done) {
        const status = await api.getIngestJobStatus(jobId);

        if (status.status === "queued" || status.status === "running") {
        setUploadState({
            fileName,
            phase: "processing",
            progress:
            typeof status.progress === "number"
                ? status.progress
                : status.status === "queued"
                ? 15
                : 65,
            message: status.message ?? "Processing document...",
        });
        }

        if (status.status === "succeeded") {
        setUploadState({
            fileName,
            phase: "done",
            progress: 100,
            message: "File uploaded and indexed successfully.",
        });

        await loadSources(activeProjectId);
        done = true;
        break;
        }

        if (status.status === "failed" || status.status === "not_found") {
        setUploadState({
            fileName,
            phase: "error",
            progress: 0,
            message:
            status.error ??
            status.message ??
            "Document processing failed.",
        });
        done = true;
        break;
        }

        await new Promise((resolve) => setTimeout(resolve, 1200));
    }
  }

  async function handleUpload(file: File) {
    if (!activeProjectId) {
        alert("Please select a project first.");
        return;
    }

    setUploadState({
        fileName: file.name,
        phase: "uploading",
        progress: 0,
    });

    try {
      const result = await api.ingestPdfWithProgress(activeProjectId, file, (progress) => {
        setUploadState({
            fileName: file.name,
            phase: "uploading",
            progress,
        });
      });

        // Ако backend връща job_id за обработка
        if (result?.job_id) {
        setUploadState({
            fileName: file.name,
            phase: "processing",
            progress: 15,
            message: "Queued for processing...",
        });

        await pollIngestJob(result.job_id, file.name);
        } else {
        // fallback ако backend връща успех директно
        setUploadState({
            fileName: file.name,
            phase: "done",
            progress: 100,
        });

        await loadSources(activeProjectId);
        }
    } catch (err) {
        console.error(err);
        setUploadState({
        fileName: file.name,
        phase: "error",
        progress: 0,
        message: "Failed to upload file.",
        });
    }
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
            newProjectName={newProjectName}
            onNewProjectNameChange={setNewProjectName}
            onSelect={setActiveProjectId}
            onCreate={handleCreateProject}
            onDelete={handleDeleteProject}
          />
        </aside>

        <section className="panel chat-panel">
          <ChatWindow
            projectName={activeProject?.name ?? "No project selected"}
            projectId={activeProject?.id ?? null}
            hasSelectedProject={hasSelectedProject}
            messages={messages}
            isGenerating={isGenerating || isLoadingMessages}
            onSend={handleSendMessage}
            newProjectName={newProjectName}
            onNewProjectNameChange={setNewProjectName}
            onCreateProject={handleCreateProject}
          />
        </section>

        <aside className="panel right-panel">
          {hasSelectedProject ? (
            <>
              <UploadCard
                projectName={activeProject?.name ?? null}
                uploadState={uploadState}
                onUpload={handleUpload}
              />
              <SourcesPanel
                projectName={activeProject?.name ?? null}
                sources={sources}
                isLoading={isLoadingSources}
              />
            </>
          ) : (
            <div className="right-card empty-right-card">
              <div className="card-header">
                <p className="eyebrow">Getting Started</p>
                <h3 className="card-title glow-text">How it works</h3>
              </div>

              <div className="empty-right-content">
                <div className="empty-step">
                  <span className="empty-step-number">1</span>
                  <div>
                    <div className="empty-step-title">Create a project</div>
                    <div className="empty-step-text">
                      Start by creating a workspace for your files and chats.
                    </div>
                  </div>
                </div>

                <div className="empty-step">
                  <span className="empty-step-number">2</span>
                  <div>
                    <div className="empty-step-title">Upload documents</div>
                    <div className="empty-step-text">
                      Add PDFs and build a searchable knowledge base.
                    </div>
                  </div>
                </div>

                <div className="empty-step">
                  <span className="empty-step-number">3</span>
                  <div>
                    <div className="empty-step-title">Ask questions</div>
                    <div className="empty-step-text">
                      Chat with your project and retrieve answers from your data.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </aside>
      </section>
    </main>
  );
}