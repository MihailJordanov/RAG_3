"use client";

import { useState } from "react";
import type { ChatMessage } from "@/lib/types";
import CreateProjectForm from "./CreateProjectForm";

type Props = {
  projectName: string;
  projectId: string | null;
  hasSelectedProject: boolean;
  messages: ChatMessage[];
  isGenerating: boolean;
  onSend: (text: string) => void | Promise<void>;
  newProjectName: string;
  onNewProjectNameChange: (value: string) => void;
  onCreateProject: () => void;
};

export default function ChatWindow({
  projectName,
  projectId,
  hasSelectedProject,
  messages,
  isGenerating,
  onSend,
  newProjectName,
  onNewProjectNameChange,
  onCreateProject,
}: Props) {
  const [input, setInput] = useState("");
  const [showProjectIdPanel, setShowProjectIdPanel] = useState(false);
  const [copied, setCopied] = useState(false);

  const isEmptyChat = messages.length === 0;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const trimmed = input.trim();
    if (!trimmed || isGenerating || !hasSelectedProject) return;

    setInput("");
    await onSend(trimmed);
  }

  async function handleCopyProjectId() {
    if (!projectId) return;

    try {
      await navigator.clipboard.writeText(projectId);
      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 1200);
    } catch (err) {
      console.error(err);
      alert("Failed to copy project ID.");
    }
  }

  if (!hasSelectedProject) {
    return (
      <div className="chat-window no-project-chat">
        <section className="no-project-state">
          <div className="no-project-icon">✦</div>

          <p className="eyebrow">RAG Workspace</p>
          <h1 className="no-project-title glow-text">No project selected</h1>
          <p className="no-project-subtitle">
            Create your first project to start uploading documents, building a
            knowledge base, and chatting with your files.
          </p>

          <div className="no-project-actions">
            <CreateProjectForm
              newProjectName={newProjectName}
              onNewProjectNameChange={onNewProjectNameChange}
              onCreate={onCreateProject}
            />
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="chat-window">
      {isEmptyChat ? (
        <section className="chat-hero chat-hero-empty">
          <div className="chat-topbar">
            <div />
            <div className="project-id-tools">
              <button
                type="button"
                className="project-id-toggle"
                onClick={() => {
                  setShowProjectIdPanel((prev) => !prev);
                  setCopied(false);
                }}
              >
                {showProjectIdPanel ? "Hide ID" : "ID"}
              </button>

              {showProjectIdPanel && projectId && (
                <div className="project-id-panel">
                  <div className="project-id-label">Project ID</div>
                  <div className="project-id-value">{projectId}</div>

                  <div className="project-id-actions">
                    <button
                      type="button"
                      className="secondary-button project-id-copy-btn"
                      onClick={handleCopyProjectId}
                    >
                      {copied ? "Copied!" : "Copy"}
                    </button>

                    <button
                      type="button"
                      className="neon-button project-id-done-btn"
                      onClick={() => {
                        setShowProjectIdPanel(false);
                        setCopied(false);
                      }}
                    >
                      Done
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          <p className="eyebrow">AI Workspace</p>
          <h1 className="chat-hero-title glow-text">RAG 3</h1>
          <p className="chat-hero-subtitle">{projectName}</p>

          <div className={`status-pill ${isGenerating ? "live" : ""}`}>
            {isGenerating ? "Generating..." : "Ready"}
          </div>
        </section>
      ) : (
        <header className="chat-header">
          <div>
            <p className="eyebrow">AI Workspace</p>
            <h2 className="chat-title glow-text">RAG 3</h2>
            <p className="chat-project-name">{projectName}</p>
          </div>

          <div className="chat-header-actions">
            <div className={`status-pill ${isGenerating ? "live" : ""}`}>
              {isGenerating ? "Generating..." : "Ready"}
            </div>

            <div className="project-id-tools">
              <button
                type="button"
                className="project-id-toggle"
                onClick={() => {
                  setShowProjectIdPanel((prev) => !prev);
                  setCopied(false);
                }}
              >
                {showProjectIdPanel ? "Hide ID" : "ID"}
              </button>

              {showProjectIdPanel && projectId && (
                <div className="project-id-panel">
                  <div className="project-id-label">Project ID</div>
                  <div className="project-id-value">{projectId}</div>

                  <div className="project-id-actions">
                    <button
                      type="button"
                      className="secondary-button project-id-copy-btn"
                      onClick={handleCopyProjectId}
                    >
                      {copied ? "Copied!" : "Copy"}
                    </button>

                    <button
                      type="button"
                      className="neon-button project-id-done-btn"
                      onClick={() => {
                        setShowProjectIdPanel(false);
                        setCopied(false);
                      }}
                    >
                      Done
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>
      )}

      <div
        className={`messages-area custom-scroll ${
          isEmptyChat ? "messages-empty" : ""
        }`}
      >
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message-row ${
              message.role === "user" ? "user-row" : "assistant-row"
            }`}
          >
            <div
              className={`message-bubble ${
                message.role === "user" ? "user-bubble" : "assistant-bubble"
              }`}
            >
              <span className="message-role">
                {message.role === "user" ? "You" : "Assistant"}
              </span>
              <p>{message.content}</p>
            </div>
          </div>
        ))}

        {isGenerating && (
          <div className="message-row assistant-row">
            <div className="message-bubble assistant-bubble typing-bubble">
              <span className="message-role">Assistant</span>
              <div className="typing-dots">
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>
        )}
      </div>

      <form
        className={`composer ${isGenerating ? "composer-generating" : ""}`}
        onSubmit={handleSubmit}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something about your project documents..."
          className="composer-input"
          disabled={!hasSelectedProject}
        />
        <button
          type="submit"
          className="send-button"
          disabled={isGenerating || !hasSelectedProject}
        >
          Send
        </button>
      </form>
    </div>
  );
}