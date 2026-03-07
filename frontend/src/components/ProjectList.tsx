"use client";

import type { Project } from "@/lib/types";
import CreateProjectForm from "./CreateProjectForm";

type Props = {
  projects: Project[];
  activeProjectId: string;
  busyId: string | null;
  newProjectName: string;
  onNewProjectNameChange: (value: string) => void;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
};

export default function ProjectList({
  projects,
  activeProjectId,
  busyId,
  newProjectName,
  onNewProjectNameChange,
  onSelect,
  onCreate,
  onDelete,
}: Props) {
  function truncateProjectName(name: string, max = 12) {
    return name.length > max ? `${name.slice(0, max)}...` : name;
  }
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div>
          <p className="eyebrow">Workspace</p>
          <h1 className="sidebar-title glow-text">RAG Projects</h1>
        </div>
      </div>

      <div className="project-create-box">
        <CreateProjectForm
          newProjectName={newProjectName}
          onNewProjectNameChange={onNewProjectNameChange}
          onCreate={onCreate}
        />
      </div>

      <div className="project-list custom-scroll">
        {projects.map((project) => {
          const active = project.id === activeProjectId;
          const deleting = busyId === project.id;

          return (
            <div
              key={project.id}
              className={`project-item ${active ? "active" : ""}`}
            >
              <button
                className="project-main"
                onClick={() => onSelect(project.id)}
                type="button"
              >
                <span className="project-dot" />
                <div className="project-meta">
                  <span className="project-name" title={project.name}>
                    {truncateProjectName(project.name)}
                  </span>
                  <span className="project-subtitle">{project.id}</span>
                </div>
              </button>

              <button
                type="button"
                className={`delete-project-button ${deleting ? "deleting" : ""}`}
                onClick={() => onDelete(project.id)}
                disabled={deleting}
                title="Delete project"
              >
                {deleting ? "..." : "✕"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}