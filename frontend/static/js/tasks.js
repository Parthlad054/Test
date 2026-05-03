let selectedProjectId = "";
let taskFilters = { status: "", priority: "", assigned_to: "" };
let projectMembers = [];

async function initTasksPage() {
    if (!requireAuth()) return;
    applyNavActive();
    await setupTopbar();
    await loadProjectOptions();
    bindTaskEvents();
    await applyUrlState();
}

async function loadProjectOptions() {
    const response = await apiFetch("/api/v1/projects");
    const payload = await response.json();
    if (!response.ok) {
        showToast(payload.message || "Could not load projects", "error");
        return;
    }

    const select = document.getElementById("project-select");
    select.innerHTML = `<option value="">Select project</option>`;
    (payload.data || []).forEach((project) => {
        select.innerHTML += `<option value="${project.id}">${project.name}</option>`;
    });
}

function bindTaskEvents() {
    document.getElementById("project-select").addEventListener("change", async (event) => {
        selectedProjectId = event.target.value;
        await loadMembers();
        await loadTasksBoard();
    });

    document.getElementById("apply-filters").addEventListener("click", async () => {
        taskFilters.status = document.getElementById("filter-status").value;
        taskFilters.priority = document.getElementById("filter-priority").value;
        taskFilters.assigned_to = document.getElementById("filter-assignee").value;
        await loadTasksBoard();
    });

    document.getElementById("clear-filters").addEventListener("click", async () => {
        document.getElementById("filter-status").value = "";
        document.getElementById("filter-priority").value = "";
        document.getElementById("filter-assignee").value = "";
        taskFilters = { status: "", priority: "", assigned_to: "" };
        await loadTasksBoard();
    });

    document.getElementById("toggle-add-task").addEventListener("click", () => {
        const form = document.getElementById("add-task-form");
        form.style.display = form.style.display === "none" ? "block" : "none";
    });

    document.getElementById("add-task-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!selectedProjectId) {
            showToast("Select a project first", "error");
            return;
        }

        const payload = {
            title: document.getElementById("task-title").value.trim(),
            description: document.getElementById("task-description").value.trim() || null,
            assigned_to: document.getElementById("task-assignee").value || null,
            priority: document.getElementById("task-priority").value,
            due_date: document.getElementById("task-due-date").value || null
        };
        if (payload.title.length < 3 || payload.title.length > 200) {
            showToast("Task title must be 3-200 chars", "error");
            return;
        }

        const submit = document.getElementById("add-task-submit");
        submit.classList.add("loading");
        submit.disabled = true;
        try {
            const response = await apiFetch(`/api/v1/projects/${selectedProjectId}/tasks`, {
                method: "POST",
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (!response.ok) {
                showToast(result.message || "Failed to add task", "error");
                return;
            }
            showToast("Task created", "success");
            event.target.reset();
            await loadTasksBoard();
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            submit.classList.remove("loading");
            submit.disabled = false;
        }
    });
}

async function applyUrlState() {
    const params = new URLSearchParams(window.location.search);
    const project = params.get("project");
    const task = params.get("task");
    if (project) {
        selectedProjectId = project;
        document.getElementById("project-select").value = project;
        await loadMembers();
        await loadTasksBoard(task);
    }
}

async function loadMembers() {
    projectMembers = [];
    const assigneeControls = ["filter-assignee", "task-assignee"];
    assigneeControls.forEach((id) => {
        const select = document.getElementById(id);
        const label = id === "filter-assignee" ? "All assignees" : "Unassigned";
        select.innerHTML = `<option value="">${label}</option>`;
    });
    if (!selectedProjectId) return;

    const response = await apiFetch(`/api/v1/projects/${selectedProjectId}`);
    const payload = await response.json();
    if (!response.ok) return;
    projectMembers = payload.data.members || [];
    assigneeControls.forEach((id) => {
        const select = document.getElementById(id);
        projectMembers.forEach((member) => {
            select.innerHTML += `<option value="${member.user_id}">${member.email}</option>`;
        });
    });
}

async function loadTasksBoard(focusTaskId = null) {
    if (!selectedProjectId) {
        renderEmptyKanban();
        return;
    }
    const params = new URLSearchParams();
    if (taskFilters.status) params.set("status", taskFilters.status);
    if (taskFilters.priority) params.set("priority", taskFilters.priority);
    if (taskFilters.assigned_to) params.set("assigned_to", taskFilters.assigned_to);
    const query = params.toString();

    const response = await apiFetch(`/api/v1/projects/${selectedProjectId}/tasks${query ? `?${query}` : ""}`);
    const payload = await response.json();
    if (!response.ok) {
        showToast(payload.message || "Failed to load tasks", "error");
        return;
    }
    renderKanban(payload.data || [], focusTaskId);
}

function renderEmptyKanban() {
    ["todo", "in_progress", "in_review", "done"].forEach((status) => {
        document.getElementById(`col-${status}`).innerHTML = `
            <div class="empty-state">
                <div class="emoji">📭</div>
                <div class="title">No tasks yet.</div>
                <div>Create your first task</div>
            </div>
        `;
    });
}

function renderKanban(tasks, focusTaskId = null) {
    const groups = { todo: [], in_progress: [], in_review: [], done: [] };
    tasks.forEach((task) => {
        if (groups[task.status]) groups[task.status].push(task);
    });

    Object.keys(groups).forEach((status) => {
        const col = document.getElementById(`col-${status}`);
        if (!groups[status].length) {
            col.innerHTML = `
                <div class="empty-state">
                    <div class="emoji">📭</div>
                    <div class="title">No tasks yet.</div>
                    <div>Create your first task</div>
                </div>
            `;
            return;
        }
        col.innerHTML = groups[status].map((task) => `
            <div class="kanban-card ${task.is_overdue ? "overdue" : ""}" id="task-${task.id}">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px">
                    <strong>${task.title}</strong>
                    <span class="badge priority-${task.priority}">${task.priority}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                    <span>${avatarMarkup(task.assigned_user_name || "Unassigned")}</span>
                    <span style="font-size:12px;color:var(--gray-600)">${task.due_date || "No due date"}</span>
                </div>
                ${task.is_overdue ? `<div class="overdue-indicator"><span class="overdue-dot"></span>${Math.abs(task.days_until_due)} days overdue</div>` : ""}
                <div style="margin-top:8px">
                    <select class="select" data-task-status="${task.id}">
                        <option value="todo" ${task.status === "todo" ? "selected" : ""}>Todo</option>
                        <option value="in_progress" ${task.status === "in_progress" ? "selected" : ""}>In Progress</option>
                        <option value="in_review" ${task.status === "in_review" ? "selected" : ""}>In Review</option>
                        <option value="done" ${task.status === "done" ? "selected" : ""}>Done</option>
                    </select>
                </div>
            </div>
        `).join("");
    });

    document.querySelectorAll("[data-task-status]").forEach((select) => {
        select.addEventListener("change", async (event) => {
            const taskId = event.target.getAttribute("data-task-status");
            const status = event.target.value;
            const response = await apiFetch(`/api/v1/tasks/${taskId}/status`, {
                method: "PATCH",
                body: JSON.stringify({ status })
            });
            const payload = await response.json();
            if (!response.ok) {
                showToast(payload.message || "Status update failed", "error");
                return;
            }
            showToast("Task status updated", "success");
            await loadTasksBoard(taskId);
        });
    });

    if (focusTaskId) {
        const target = document.getElementById(`task-${focusTaskId}`);
        if (target) target.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

document.addEventListener("DOMContentLoaded", initTasksPage);
