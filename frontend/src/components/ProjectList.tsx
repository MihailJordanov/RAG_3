"use client";

type Project = {
  id: string;
  name: string;
};

type Props = {
  projects: Project[];
  activeProjectId: string;
  busyId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
};

export default function ProjectList({
  projects,
  activeProjectId,
  busyId,
  onSelect,
  onCreate,
  onDelete,
}: Props) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div>
          <p className="eyebrow">Workspace</p>
          <h1 className="sidebar-title glow-text">RAG Projects</h1>
        </div>

        <button className="neon-button" onClick={onCreate}>
          + New
        </button>
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
                  <span className="project-name">{project.name}</span>
                  <span className="project-subtitle">Open project chat</span>
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