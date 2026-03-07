"use client";

import { useState } from "react";
import type { ChatMessage } from "@/lib/types";

type Props = {
  projectName: string;
  messages: ChatMessage[];
  isGenerating: boolean;
  onSend: (text: string) => void | Promise<void>;
};

export default function ChatWindow({
  projectName,
  messages,
  isGenerating,
  onSend,
}: Props) {
  const [input, setInput] = useState("");
  const isEmptyChat = messages.length === 0;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const trimmed = input.trim();
    if (!trimmed || isGenerating) return;

    setInput("");
    await onSend(trimmed);
  }

  return (
    <div className="chat-window">
      {isEmptyChat ? (
        <section className="chat-hero">
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

          <div className={`status-pill ${isGenerating ? "live" : ""}`}>
            {isGenerating ? "Generating..." : "Ready"}
          </div>
        </header>
      )}

      <div className={`messages-area custom-scroll ${isEmptyChat ? "messages-empty" : ""}`}>
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
          disabled={!projectName || projectName === "No project selected"}
        />
        <button
          type="submit"
          className="send-button"
          disabled={isGenerating || !projectName || projectName === "No project selected"}
        >
          Send
        </button>
      </form>
    </div>
  );
}