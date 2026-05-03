async function initProjectsPage() {
    if (!requireAuth()) return;
    applyNavActive();
    await setupTopbar();
    bindProjectModal();
    await loadProjects();
}

function bindProjectModal() {
    const modal = document.getElementById("create-project-modal");
    document.getElementById("open-create-project").addEventListener("click", () => {
        modal.classList.add("open");
    });
    document.getElementById("close-create-project").addEventListener("click", () => {
        modal.classList.remove("open");
    });
    modal.addEventListener("click", (event) => {
        if (event.target === modal) modal.classList.remove("open");
    });

    document.getElementById("create-project-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        document.getElementById("project-name-error").textContent = "";

        const name = document.getElementById("project-name").value.trim();
        const description = document.getElementById("project-description").value.trim();
        if (name.length < 3 || name.length > 100) {
            document.getElementById("project-name-error").textContent = "Name must be 3-100 characters.";
            return;
        }

        const submit = document.getElementById("submit-create-project");
        submit.classList.add("loading");
        submit.disabled = true;
        try {
            const response = await apiFetch("/api/v1/projects", {
                method: "POST",
                body: JSON.stringify({ name, description })
            });
            const payload = await response.json();
            if (!response.ok) {
                showToast(payload.message || "Could not create project", "error");
                return;
            }
            showToast("Project created", "success");
            event.target.reset();
            document.getElementById("create-project-modal").classList.remove("open");
            await loadProjects();
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            submit.classList.remove("loading");
            submit.disabled = false;
        }
    });
}

async function loadProjects() {
    const response = await apiFetch("/api/v1/projects");
    const payload = await response.json();
    const container = document.getElementById("projects-list");
    if (!response.ok) {
        showToast(payload.message || "Failed to load projects", "error");
        return;
    }

    const projects = payload.data || [];
    if (!projects.length) {
        container.innerHTML = `
            <div class="card empty-state">
                <div class="emoji">📁</div>
                <div class="title">No projects yet.</div>
                <div>Create your first project</div>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="list">
            ${projects.map((project) => `
                <article class="row">
                    <div>
                        <div><strong>${project.name}</strong></div>
                        <div style="font-size:12px;color:var(--gray-600)">${project.description || "No description"}</div>
                    </div>
                    <div style="display:flex;align-items:center;gap:8px">
                        <span class="badge status-${project.status}">${project.status}</span>
                        <span style="font-size:12px;color:var(--gray-600)">${project.task_count || 0} tasks</span>
                    </div>
                </article>
            `).join("")}
        </div>
    `;
}

document.addEventListener("DOMContentLoaded", initProjectsPage);
