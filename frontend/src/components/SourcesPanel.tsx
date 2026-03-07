"use client";

import type { ProjectSource } from "@/lib/types";

type Props = {
  projectName: string | null;
  sources: ProjectSource[];
  isLoading?: boolean;
};

export default function SourcesPanel({
  projectName,
  sources,
  isLoading = false,
}: Props) {
  const isEmpty = !isLoading && sources.length === 0;

  return (
    <div className="right-card sources-card">
      <div className="card-header">
        <p className="eyebrow">Knowledge Base</p>
        <h3 className="card-title glow-text">Sources</h3>
      </div>

      <div className="sources-list custom-scroll">
        {isLoading ? (
          <div className="sources-empty-state">
            <div className="source-empty-title">Loading sources...</div>
            <div className="source-empty-subtitle">
              Please wait a moment.
            </div>
          </div>
        ) : isEmpty ? (
          <div className="sources-empty-state">
            <div className="source-empty-title">
              {projectName ? "No files uploaded yet" : "No project selected"}
            </div>
            <div className="source-empty-subtitle">
              {projectName
                ? "Upload a file to start building this project's knowledge base."
                : "Choose a project from the left panel first."}
            </div>
          </div>
        ) : (
          sources.map((source, index) => (
            <div className="source-item" key={`${source.name}-${index}`}>
              <div className="source-icon">
                {source.name.split(".").pop()?.toUpperCase() ?? "FILE"}
              </div>
              <div>
                <div className="source-name">{source.name}</div>
                <div className="source-meta">
                  {source.status ?? "Ready"}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}