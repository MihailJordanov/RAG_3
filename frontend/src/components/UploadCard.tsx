"use client";

type UploadState = {
  fileName: string;
  phase: "idle" | "uploading" | "processing" | "done" | "error";
  progress: number;
  message?: string;
};

type Props = {
  projectName: string | null;
  uploadState: UploadState | null;
  onUpload: (file: File) => void | Promise<void>;
};

export default function UploadCard({ projectName, uploadState, onUpload }: Props) {
  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    await onUpload(file);
    e.target.value = "";
  }

  const isBusy =
    uploadState?.phase === "uploading" || uploadState?.phase === "processing";

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

        <p className="upload-subtitle">
          PDF and supported sources
        </p>

        <label htmlFor="file-upload" className="neon-button secondary-button upload-button">
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
                {uploadState.phase === "uploading" && `${uploadState.progress}%`}
                {uploadState.phase === "processing" && `${uploadState.progress}%`}
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
                File uploaded and indexed successfully.
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