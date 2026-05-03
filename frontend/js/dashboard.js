let dashboardProjects = [];
let projectRolesById = {};
let currentUserId = null;
let taskFilters = {
    projectId: "",
    userId: ""
};

document.addEventListener("DOMContentLoaded", async () => {
    const logoutBtn = document.getElementById("logout-btn");
    const taskFilterForm = document.getElementById("task-filter-form");
    const clearFilterBtn = document.getElementById("clear-filter-btn");

    if (!getToken()) {
        window.location.href = "index.html";
        return;
    }

    logoutBtn.style.display = "inline-block";
    logoutBtn.addEventListener("click", () => {
        clearTokens();
        window.location.href = "index.html";
    });

    await loadCurrentUser();
    dashboardProjects = await loadProjects();
    updateProjectSelectOptions(dashboardProjects);
    applyMemberAccessControls(dashboardProjects);
    await loadDashboardStats(dashboardProjects.length);
    await loadTasks();

    taskFilterForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        taskFilters.projectId = document.getElementById("filter-project-id").value;
        taskFilters.userId = document.getElementById("filter-user-id").value.trim();
        await loadTasks(taskFilters);
    });

    clearFilterBtn.addEventListener("click", async () => {
        taskFilters = { projectId: "", userId: "" };
        taskFilterForm.reset();
        await loadTasks();
    });

    document.addEventListener("project:created", async (event) => {
        const createdProjectId = event?.detail?.project?.id ? String(event.detail.project.id) : null;
        await refreshProjectDependentUI(createdProjectId);
    });

    document.addEventListener("project:member-added", async () => {
        await loadTasks(taskFilters);
    });

    document.addEventListener("task:created", async () => {
        await loadTasks(taskFilters);
        await loadDashboardStats(dashboardProjects.length);
    });

    document.addEventListener("task:updated", async () => {
        await loadTasks(taskFilters);
        await loadDashboardStats(dashboardProjects.length);
    });
});

async function refreshProjectDependentUI(selectProjectId = null) {
    dashboardProjects = await loadProjects();
    updateProjectSelectOptions(dashboardProjects);
    if (selectProjectId) {
        selectProjectInForms(selectProjectId);
    }
    applyMemberAccessControls(dashboardProjects);
    await loadDashboardStats(dashboardProjects.length);
    await loadTasks(taskFilters);
}

async function loadCurrentUser() {
    try {
        const res = await apiFetch("/users/me");
        if (!res.ok) return;
        const responseData = await res.json();
        currentUserId = responseData?.data?.id ?? null;
    } catch (err) {
        console.error(err);
    }
}

async function loadDashboardStats(totalProjects = 0) {
    try {
        const res = await apiFetch("/dashboard");
        if (!res.ok) return;

        const responseData = await res.json();
        const stats = responseData.data;
        const container = document.getElementById("stats-container");
        container.innerHTML = `
            <div class="stat-card">
                <h3>Total Tasks</h3>
                <p>${stats.total_tasks}</p>
            </div>
            <div class="stat-card">
                <h3>Completed</h3>
                <p>${stats.completed_tasks}</p>
            </div>
            <div class="stat-card">
                <h3>Pending</h3>
                <p>${stats.pending_tasks}</p>
            </div>
            <div class="stat-card">
                <h3 style="color: #d9534f;">Overdue</h3>
                <p style="color: #d9534f;">${stats.overdue_tasks}</p>
            </div>
            <div class="stat-card">
                <h3>Total Projects</h3>
                <p>${totalProjects}</p>
            </div>
        `;
    } catch (err) {
        console.error(err);
    }
}

function updateProjectSelectOptions(projects) {
    const projectSelectIds = ["member-project-id", "task-project-id", "filter-project-id"];
    const byId = Object.fromEntries(projects.map((p) => [String(p.id), p]));

    projectSelectIds.forEach((selectId) => {
        const select = document.getElementById(selectId);
        if (!select) return;

        const previousValue = select.value;
        const placeholder = selectId === "filter-project-id"
            ? `<option value="">All Projects</option>`
            : `<option value="">Select Project</option>`;

        let options = placeholder;
        for (const project of projects) {
            const roleLabel = resolveProjectRole(project);
            options += `<option value="${project.id}">${project.name} (${roleLabel})</option>`;
        }
        select.innerHTML = options;
        select.disabled = projects.length === 0;

        if (previousValue && byId[previousValue]) {
            select.value = previousValue;
        } else if (selectId === "filter-project-id") {
            select.value = "";
        }
    });
}

function selectProjectInForms(projectId) {
    const targetSelectIds = ["member-project-id", "task-project-id", "filter-project-id"];
    targetSelectIds.forEach((selectId) => {
        const select = document.getElementById(selectId);
        if (!select) return;
        const hasOption = Array.from(select.options).some((option) => option.value === projectId);
        if (hasOption) {
            select.value = projectId;
        }
    });
}

function applyMemberAccessControls(projects) {
    const addMemberForm = document.getElementById("add-member-form");
    const createTaskForm = document.getElementById("create-task-form");
    const hasAdminAccess = projects.some((project) => resolveProjectRole(project) === "admin");

    projectRolesById = Object.fromEntries(
        projects.map((project) => [String(project.id), resolveProjectRole(project)])
    );

    if (addMemberForm) {
        addMemberForm.style.display = hasAdminAccess ? "flex" : "none";
    }
    if (createTaskForm) {
        createTaskForm.style.display = hasAdminAccess ? "flex" : "none";
    }
}

function resolveProjectRole(project) {
    if (project.my_role) return project.my_role;
    if (currentUserId !== null && Number(project.owner_id) === Number(currentUserId)) {
        return "admin";
    }
    return "member";
}

async function loadProjects() {
    try {
        const res = await apiFetch("/projects");
        const listContainer = document.getElementById("projects-list");
        if (!res.ok) {
            const data = await res.json();
            listContainer.innerHTML = `<p>${data.message || "Unable to load projects."}</p>`;
            return [];
        }
        const responseData = await res.json();
        const projects = Array.isArray(responseData.data) ? responseData.data : [];

        if (!projects.length) {
            listContainer.innerHTML = `<p>No projects yet. Create your first project above.</p>`;
            return [];
        }

        let html = `<ul>`;
        for (let p of projects) {
            const roleLabel = resolveProjectRole(p);
            html += `<li><strong>${p.name}</strong> (ID: ${p.id}) - Role: ${roleLabel} - ${p.description || "No description"}</li>`;
        }
        html += `</ul>`;
        listContainer.innerHTML = html;
        return projects;
    } catch(err) {
        console.error(err);
        return [];
    }
}

async function loadTasks(filters = {}) {
    try {
        const section = document.getElementById("tasks-list");
        const params = new URLSearchParams();
        if (filters.projectId) {
            params.set("project_id", filters.projectId);
        }
        if (filters.userId && /^\d+$/.test(String(filters.userId))) {
            params.set("user_id", filters.userId);
        }
        const queryString = params.toString();
        const endpoint = queryString ? `/tasks?${queryString}` : "/tasks";

        const res = await apiFetch(endpoint);
        if (!res.ok) {
            const data = await res.json();
            section.innerHTML = `<p>${data.message || "Unable to load tasks."}</p>`;
            return;
        }
        const responseData = await res.json();
        const tasks = Array.isArray(responseData.data) ? responseData.data : [];

        if (!tasks.length) {
            section.innerHTML = `<p>No tasks found for the selected criteria.</p>`;
            return;
        }

        let html = "";
        for (let t of tasks) {
            const dueDate = t.due_date ? new Date(t.due_date).toLocaleString() : "none";
            const canAssign = projectRolesById[String(t.project_id)] === "admin";
            html += `
                <div class="task-item">
                    <strong>${t.title}</strong>
                    <div class="task-meta">
                        Project ID: ${t.project_id} | Assigned To: ${t.assigned_to ?? "Unassigned"} | Due: ${dueDate}
                    </div>
                    <div class="task-meta">Status: ${t.status}</div>
                    <div class="task-actions">
                        <select id="status-select-${t.id}">
                            <option value="todo" ${t.status === "todo" ? "selected" : ""}>Todo</option>
                            <option value="in_progress" ${t.status === "in_progress" ? "selected" : ""}>In Progress</option>
                            <option value="in_review" ${t.status === "in_review" ? "selected" : ""}>In Review</option>
                            <option value="done" ${t.status === "done" ? "selected" : ""}>Done</option>
                        </select>
                        <button class="btn-primary btn-inline" onclick="handleStatusUpdate(${t.id})">Update Status</button>

                        <input type="number" min="1" id="assign-input-${t.id}" placeholder="User ID">
                        <button class="btn-primary btn-inline" onclick="handleAssignTask(${t.id})" ${canAssign ? "" : "disabled"}>
                            ${canAssign ? "Assign" : "Assign (Admin only)"}
                        </button>
                    </div>
                </div>
            `;
        }
        section.innerHTML = html;
    } catch(err) {
        console.error(err);
    }
}

async function handleStatusUpdate(taskId) {
    const statusSelect = document.getElementById(`status-select-${taskId}`);
    if (!statusSelect) return;
    await updateTaskStatus(taskId, statusSelect.value);
}

async function handleAssignTask(taskId) {
    const assignInput = document.getElementById(`assign-input-${taskId}`);
    if (!assignInput) return;
    await assignTask(taskId, assignInput.value.trim());
}
