"use client";

type Props = {
  projectName: string | null;
};

export default function UploadCard({ projectName }: Props) {
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

        <button className="neon-button secondary-button" type="button">
          Choose File
        </button>
      </div>
    </div>
  );
}