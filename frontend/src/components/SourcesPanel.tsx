"use client";

export default function SourcesPanel() {
  return (
    <div className="right-card sources-card">
      <div className="card-header">
        <p className="eyebrow">Knowledge Base</p>
        <h3 className="card-title glow-text">Sources</h3>
      </div>

      <div className="sources-list custom-scroll">
        <div className="source-item">
          <div className="source-icon">PDF</div>
          <div>
            <div className="source-name">example_document.pdf</div>
            <div className="source-meta">Indexed • Ready</div>
          </div>
        </div>

        <div className="source-item">
          <div className="source-icon">TXT</div>
          <div>
            <div className="source-name">notes.txt</div>
            <div className="source-meta">Indexed • 12 chunks</div>
          </div>
        </div>

        <div className="source-item">
          <div className="source-icon">DOC</div>
          <div>
            <div className="source-name">paper_summary.docx</div>
            <div className="source-meta">Processing complete</div>
          </div>
        </div>
      </div>
    </div>
  );
}