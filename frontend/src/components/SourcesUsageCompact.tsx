"use client";

import type { ProjectLimits, ProjectSource } from "@/lib/types";

function formatMb(bytes: number) {
  return (bytes / (1024 * 1024)).toFixed(1);
}

type SourcesHeaderProps = {
  sources: ProjectSource[];
  limits: ProjectLimits | null;
};

export default function SourcesUsageCompact({
  sources,
  limits,
}: SourcesHeaderProps) {
  const maxFiles = limits?.max_files_per_project ?? 0;
  const maxFileSizeMb = limits?.max_file_size_mb ?? 0;
  const maxTotalProjectSizeMb = limits?.max_total_project_size_mb ?? 0;
  const maxTotalProjectSizeBytes = limits?.max_total_project_size_bytes ?? 0;

  const fileCount = limits?.current_file_count ?? sources.length;
  const totalBytes =
    limits?.current_total_size_bytes ??
    sources.reduce((sum, source) => sum + (source.size_bytes ?? 0), 0);

  const remainingFiles = limits?.remaining_file_slots ?? 0;
  const remainingMb =
    limits?.remaining_total_size_bytes != null
      ? formatMb(limits.remaining_total_size_bytes)
      : "0.0";

  const filesPercent =
    maxFiles > 0 ? Math.min((fileCount / maxFiles) * 100, 100) : 0;

  const storagePercent =
    maxTotalProjectSizeBytes > 0
      ? Math.min((totalBytes / maxTotalProjectSizeBytes) * 100, 100)
      : 0;

  return (
    <div className="sources-usage-compact">
      <div className="sources-usage-topline">
        <span>
          {fileCount}/{maxFiles} files
        </span>
        <span>
          {formatMb(totalBytes)}/{maxTotalProjectSizeMb} MB
        </span>
      </div>

      <div className="sources-usage-bars">
        <div className="mini-progress">
          <div
            className="mini-progress-fill"
            style={{ width: `${filesPercent}%` }}
          />
        </div>
        <div className="mini-progress">
          <div
            className="mini-progress-fill"
            style={{ width: `${storagePercent}%` }}
          />
        </div>
      </div>

      <div className="sources-usage-meta">
        <span>{remainingFiles} slots left</span>
        <span>{remainingMb} MB left</span>
        <span>{maxFileSizeMb} MB/file</span>
      </div>
    </div>
  );
}