"use client";

import { useEffect, useRef, useState } from "react";
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
  isMobileProjectsOpen?: boolean;
  isMobileToolsOpen?: boolean;
  onToggleProjectsPanel?: () => void;
  onToggleToolsPanel?: () => void;
  projectsToggleRef?: React.RefObject<HTMLButtonElement | null>;
  toolsToggleRef?: React.RefObject<HTMLButtonElement | null>;
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
  isMobileProjectsOpen = false,
  isMobileToolsOpen = false,
  onToggleProjectsPanel,
  onToggleToolsPanel,
  projectsToggleRef,
  toolsToggleRef,
}: Props) {
  const [input, setInput] = useState("");
  const [showProjectIdPanel, setShowProjectIdPanel] = useState(false);
  const [copied, setCopied] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const projectIdPanelRef = useRef<HTMLDivElement | null>(null);
  const projectIdToggleRef = useRef<HTMLButtonElement | null>(null);

  const isEmptyChat = messages.length === 0;
  const EMPTY_MESSAGE = "Your workspace is empty. Upload a document from the Tools ✦ panel.";

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isGenerating]);

  useEffect(() => {
    function handlePointerDown(e: PointerEvent) {
      if (!showProjectIdPanel) return;

      const target = e.target as Node;

      const clickedInsidePanel =
        projectIdPanelRef.current?.contains(target) ?? false;
      const clickedToggle =
        projectIdToggleRef.current?.contains(target) ?? false;

      if (!clickedInsidePanel && !clickedToggle) {
        setShowProjectIdPanel(false);
        setCopied(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
    };
  }, [showProjectIdPanel]);

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
        <div className="mobile-chat-toolbar">
          <button
            ref={projectsToggleRef}
            type="button"
            className={`mobile-panel-toggle ${
              isMobileProjectsOpen ? "active" : ""
            }`}
            onClick={onToggleProjectsPanel}
            aria-label="Toggle projects panel"
          >
            <span className="mobile-toggle-icon">☰</span>
            <span className="mobile-toggle-text">Projects</span>
          </button>

          <div className="mobile-id-tools">
            <button
              ref={projectIdToggleRef}
              type="button"
              className="mobile-panel-toggle id-toggle-mobile"
              onClick={() => {
                setShowProjectIdPanel((prev) => !prev);
                setCopied(false);
              }}
              aria-label="Toggle project ID"
            >
              <span className="mobile-toggle-text">ID</span>
            </button>

            {showProjectIdPanel && projectId && (
              <div ref={projectIdPanelRef} className="project-id-panel mobile-project-id-panel">
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

          <button
            ref={toolsToggleRef}
            type="button"
            className={`mobile-panel-toggle ${
              isMobileToolsOpen ? "active" : ""
            }`}
            onClick={onToggleToolsPanel}
            aria-label="Toggle tools panel"
          >
            <span className="mobile-toggle-text">Tools</span>
            <span className="mobile-toggle-icon">✦</span>
          </button>
        </div>

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
      <div className="mobile-chat-toolbar">
        <button
          ref={projectsToggleRef}
          type="button"
          className={`mobile-panel-toggle ${
            isMobileProjectsOpen ? "active" : ""
          }`}
          onClick={onToggleProjectsPanel}
          aria-label="Toggle projects panel"
        >
          <span className="mobile-toggle-icon">☰</span>
          <span className="mobile-toggle-text">Projects</span>
        </button>

        <button
          ref={toolsToggleRef}
          type="button"
          className={`mobile-panel-toggle ${
            isMobileToolsOpen ? "active" : ""
          }`}
          onClick={onToggleToolsPanel}
          aria-label="Toggle tools panel"
        >
          <span className="mobile-toggle-text">Tools</span>
          <span className="mobile-toggle-icon">✦</span>
        </button>
      </div>

      {isEmptyChat ? (
        <section className="chat-hero chat-hero-empty">
          <div className="chat-topbar">
            <div />
            <div className="project-id-tools">
              <button
                ref={projectIdToggleRef}
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
                <div ref={projectIdPanelRef} className="project-id-panel">
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
                ref={projectIdToggleRef}
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
                <div ref={projectIdPanelRef} className="project-id-panel">
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
              <p
                dangerouslySetInnerHTML={{
                  __html:
                    message.content === EMPTY_MESSAGE
                      ? message.content.replace(
                          "Tools ✦",
                          '<span class="tools-highlight">Tools ✦</span>'
                        )
                      : message.content,
                }}
              />
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

        <div ref={messagesEndRef} />
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