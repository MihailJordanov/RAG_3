"use client";

import type { ProjectSource, ProjectLimits } from "@/lib/types";
import SourcesUsageCompact from "./SourcesUsageCompact";

type Props = {
  projectName: string | null;
  sources: ProjectSource[];
  limits: ProjectLimits | null;
  isLoading?: boolean;
};

function formatFileSize(bytes?: number | null) {
  if (!bytes || bytes <= 0) return null;

  const mb = bytes / (1024 * 1024);
  if (mb >= 1) return `${mb.toFixed(1)} MB`;

  const kb = bytes / 1024;
  if (kb >= 1) return `${kb.toFixed(1)} KB`;

  return `${bytes} B`;
}

export default function SourcesPanel({
  projectName,
  sources,
  limits,
  isLoading = false,
}: Props) {
  const isEmpty = !isLoading && sources.length === 0;

  return (
    <div className="right-card sources-card">
      <div className="card-header compact-card-header">
        <p className="eyebrow compact-eyebrow">Knowledge Base</p>
        <h3 className="card-title compact-card-title glow-text">Sources</h3>
      </div>

      <SourcesUsageCompact sources={sources} limits={limits} />

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
          sources.map((source, index) => {
            const extension =
              source.name.split(".").pop()?.toUpperCase() ?? "FILE";
            const sizeLabel = formatFileSize(source.size_bytes);

            return (
              <div className="source-item compact-source-item" key={`${source.name}-${index}`}>
                <div className="source-icon compact-source-icon">{extension}</div>

                <div className="source-content">
                  <div className="source-name" title={source.name}>
                    {source.name}
                  </div>

                  <div className="source-meta compact-source-meta">
                    <span>{source.status ?? "Ready"}</span>
                    {sizeLabel && <span>• {sizeLabel}</span>}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}