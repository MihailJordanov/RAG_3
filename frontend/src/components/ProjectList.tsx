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
  function truncateProjectName(name: string, max = 16) {
    return name.length > max ? `${name.slice(0, max)}...` : name;
  }

  const hasProjects = projects.length > 0;

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div>
          <p className="eyebrow">Workspace</p>
          <h1 className="sidebar-title glow-text">RAG Projects</h1>
        </div>
      </div>

      {projects.length > 0 && (
        <div className="project-create-box">
          <CreateProjectForm
            newProjectName={newProjectName}
            onNewProjectNameChange={onNewProjectNameChange}
            onCreate={onCreate}
          />
        </div>
      )}

      {hasProjects ? (
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
                  title={project.name}
                >
                  <span className="project-dot" />
                  <div className="project-meta">
                    <span className="project-name" title={project.name}>
                      {truncateProjectName(project.name)}
                    </span>
                  </div>
                </button>

                <button
                  type="button"
                  className={`delete-project-button ${
                    deleting ? "deleting" : ""
                  }`}
                  onClick={() => onDelete(project.id)}
                  disabled={deleting}
                  title="Delete project"
                  aria-label={`Delete project ${project.name}`}
                >
                  {deleting ? "..." : "✕"}
                </button>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="sidebar-empty-state">
          <div className="sidebar-empty-icon">✦</div>

          <div className="sidebar-empty-title">No projects yet</div>

          <div className="sidebar-empty-subtitle">
            Create your first project to start building a knowledge base and
            chatting with your documents.
          </div>

          <div className="project-create-box empty-create-box">
            <CreateProjectForm
              newProjectName={newProjectName}
              onNewProjectNameChange={onNewProjectNameChange}
              onCreate={onCreate}
            />
          </div>
        </div>
      )}
    </div>
  );
}