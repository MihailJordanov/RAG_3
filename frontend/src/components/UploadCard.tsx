"use client";

import type { ProjectSource, ProjectLimits } from "@/lib/types";

type UploadState = {
  fileName: string;
  phase: "idle" | "uploading" | "processing" | "done" | "error";
  progress: number;
  message?: string;
};

type Props = {
  projectName: string | null;
  uploadState: UploadState | null;
  sources: ProjectSource[];
  limits: ProjectLimits | null;
  onUpload: (file: File) => void | Promise<void>;
};

function formatMb(bytes: number) {
  return (bytes / (1024 * 1024)).toFixed(1);
}

export default function UploadCard({
  projectName,
  uploadState,
  sources,
  limits,
  onUpload,
}: Props) {
  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    await onUpload(file);
    e.target.value = "";
  }

  const isBusy =
    uploadState?.phase === "uploading" || uploadState?.phase === "processing";

  const maxFiles = limits?.max_files_per_project ?? 0;
  const maxFileSizeMb = limits?.max_file_size_mb ?? 0;
  const maxTotalProjectSizeMb = limits?.max_total_project_size_mb ?? 0;
  const maxTotalProjectSizeBytes = limits?.max_total_project_size_bytes ?? 0;

  const fileCount = limits?.current_file_count ?? sources.length;
  const totalBytes =
    limits?.current_total_size_bytes ??
    sources.reduce((sum, source) => sum + (source.size_bytes ?? 0), 0);

  const filesPercent =
    maxFiles > 0 ? Math.min((fileCount / maxFiles) * 100, 100) : 0;

  const storagePercent =
    maxTotalProjectSizeBytes > 0
      ? Math.min((totalBytes / maxTotalProjectSizeBytes) * 100, 100)
      : 0;

  const remainingFiles = limits?.remaining_file_slots ?? 0;
  const remainingMb =
    limits?.remaining_total_size_bytes != null
      ? Number(formatMb(limits.remaining_total_size_bytes))
      : 0;

  return (
    <div className="right-card upload-card">
      <div className="card-header">
        <p className="eyebrow">Documents</p>
        <h3 className="card-title glow-text">Upload Files</h3>
      </div>

      <div className="upload-zone">
        <div className="upload-icon">
          {uploadState?.phase === "processing" ? "◌" : "✦"}
        </div>

        <p className="upload-title">
          {projectName ? `Drop files into ${projectName}` : "Select a project first"}
        </p>

        <p className="upload-subtitle">PDF documents for your knowledge base</p>

        <div className="upload-limit-pills">
          <span className="upload-limit-pill">{maxFiles} files max</span>
          <span className="upload-limit-pill">{maxFileSizeMb} MB / file</span>
          <span className="upload-limit-pill">
            {maxTotalProjectSizeMb} MB / project
          </span>
        </div>

        {!!projectName && (
          <div className="limit-progress-group">
            <div className="limit-progress-label">
              <span>Files used</span>
              <span>
                {fileCount}/{maxFiles}
              </span>
            </div>
            <div className="limit-progress-bar">
              <div
                className="limit-progress-fill"
                style={{ width: `${filesPercent}%` }}
              />
            </div>

            <div className="limit-progress-meta">
              <span>{remainingFiles} file(s) remaining</span>
            </div>

            <div className="limit-progress-label">
              <span>Storage used</span>
              <span>
                {formatMb(totalBytes)}/{maxTotalProjectSizeMb} MB
              </span>
            </div>
            <div className="limit-progress-bar">
              <div
                className="limit-progress-fill"
                style={{ width: `${storagePercent}%` }}
              />
            </div>

            <div className="limit-progress-meta">
              <span>{remainingMb.toFixed(1)} MB remaining</span>
            </div>
          </div>
        )}

        <label
          htmlFor="file-upload"
          className="neon-button secondary-button upload-button"
        >
          Choose File
        </label>

        <input
          id="file-upload"
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileChange}
          style={{ display: "none" }}
          disabled={!projectName || isBusy}
        />

        {uploadState && (
          <div className={`upload-status-card upload-${uploadState.phase}`}>
            <div className="upload-status-top">
              <span className="upload-file-name" title={uploadState.fileName}>
                {uploadState.fileName}
              </span>
              <span className="upload-phase-label">
                {(uploadState.phase === "uploading" ||
                  uploadState.phase === "processing") &&
                  `${uploadState.progress}%`}
                {uploadState.phase === "done" && "Ready"}
                {uploadState.phase === "error" && "Failed"}
              </span>
            </div>

            {(uploadState.phase === "uploading" ||
              uploadState.phase === "processing") && (
              <>
                <div className="upload-progress-bar">
                  <div
                    className="upload-progress-fill"
                    style={{ width: `${uploadState.progress}%` }}
                  />
                </div>

                <div className="upload-status-message">
                  {uploadState.phase === "uploading"
                    ? "Uploading file..."
                    : uploadState.message || "Processing document..."}
                </div>
              </>
            )}

            {uploadState.phase === "done" && (
              <div className="upload-status-message success">
                {uploadState.message || "File uploaded and indexed successfully."}
              </div>
            )}

            {uploadState.phase === "error" && (
              <div className="upload-status-message error">
                {uploadState.message || "Upload failed."}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}