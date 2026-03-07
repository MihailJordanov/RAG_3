"use client";

type Props = {
  projectName: string | null;
  onUpload: (file: File) => void | Promise<void>;
};

export default function UploadCard({ projectName, onUpload }: Props) {
  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    await onUpload(file);
    e.target.value = "";
  }

  return (
    <div className="right-card upload-card">
      <div className="card-header">
        <p className="eyebrow">Documents</p>
        <h3 className="card-title glow-text">Upload Files</h3>
      </div>

      <div className="upload-zone">
        <div className="upload-icon">✦</div>
        <p className="upload-title">
          {projectName ? `Drop files into ${projectName}` : "Select a project first"}
        </p>
        <p className="upload-subtitle">
          PDF, DOCX, TXT and other supported sources
        </p>

        <label className="neon-button secondary-button" style={{ display: "inline-block" }}>
          Choose File
            <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            style={{ display: "none" }}
            disabled={!projectName}
            />
        </label>
      </div>
    </div>
  );
}