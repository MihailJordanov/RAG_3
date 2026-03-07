"use client";

import { useEffect, useState } from "react";

type Props = {
  newProjectName: string;
  onNewProjectNameChange: (value: string) => void;
  onCreate: () => void;
};

export default function CreateProjectForm({
  newProjectName,
  onNewProjectNameChange,
  onCreate,
}: Props) {
  const [open, setOpen] = useState(false);

  const closeModal = () => {
    setOpen(false);
    onNewProjectNameChange("");
  };

  const handleCreate = () => {
    if (!newProjectName.trim()) return;
    onCreate();
    setOpen(false);
  };

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (!open) return;

      if (e.key === "Escape") {
        closeModal();
      }

      if (e.key === "Enter") {
        handleCreate();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, newProjectName]);

  return (
    <>
      <button
        className="neon-button create-project-trigger"
        onClick={() => setOpen(true)}
        type="button"
      >
        + New
      </button>

      {open && (
        <div className="modal-overlay" onClick={closeModal}>
          <div
            className="create-project-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="modal-close-btn"
              onClick={closeModal}
              aria-label="Close"
            >
              ✕
            </button>

            <div className="create-project-modal-content">
              <p className="eyebrow">New project</p>
              <h2 className="create-project-title glow-text">
                Create RAG Project
              </h2>
              <p className="create-project-subtitle">
                Choose a name for your new workspace.
              </p>

              <input
                autoFocus
                value={newProjectName}
                onChange={(e) => onNewProjectNameChange(e.target.value)}
                placeholder="Enter project name..."
                className="project-modal-input"
              />

              <div className="create-project-actions">
                <button
                  type="button"
                  className="neon-button create-project-btn"
                  onClick={handleCreate}
                  disabled={!newProjectName.trim()}
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}