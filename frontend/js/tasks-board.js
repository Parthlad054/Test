let selectedProjectId = "";
let currentMembers = [];

document.addEventListener("DOMContentLoaded", async () => {
    const logoutBtn = document.getElementById("logout-btn");
    const projectFilter = document.getElementById("project-filter");
    const applyFilterBtn = document.getElementById("apply-filter-btn");
    const clearFilterBtn = document.getElementById("clear-filter-btn");
    const toggleAddTaskBtn = document.getElementById("toggle-add-task-btn");
    const addTaskForm = document.getElementById("add-task-form");
    const closeDetailBtn = document.getElementById("close-detail-btn");

    if (!getToken()) {
        window.location.href = "index.html";
        return;
    }

    logoutBtn.style.display = "inline-block";
    logoutBtn.addEventListener("click", () => {
        clearTokens();
        window.location.href = "index.html";
    });

    await loadProjects();
    await applyTaskPageQueryParams();
    projectFilter.addEventListener("change", async () => {
        selectedProjectId = projectFilter.value;
        await loadProjectMembers(selectedProjectId);
        await loadTasks();
    });

    applyFilterBtn.addEventListener("click", async () => {
        await loadTasks();
    });

    clearFilterBtn.addEventListener("click", async () => {
        document.getElementById("status-filter").value = "";
        document.getElementById("priority-filter").value = "";
        document.getElementById("assignee-filter").value = "";
        await loadTasks();
    });

    toggleAddTaskBtn.addEventListener("click", () => {
        addTaskForm.style.display = addTaskForm.style.display === "none" ? "flex" : "none";
    });

    addTaskForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!selectedProjectId) {
            alert("Please select a project first.");
            return;
        }

        const payload = {
            title: document.getElementById("task-title").value.trim(),
            description: document.getElementById("task-description").value.trim() || null,
            assigned_to: document.getElementById("task-assigned-to").value
                ? Number(document.getElementById("task-assigned-to").value)
                : null,
            priority: document.getElementById("task-priority").value,
            due_date: document.getElementById("task-due-date").value || null
        };

        const res = await apiFetch(`/api/v1/projects/${selectedProjectId}/tasks`, {
            method: "POST",
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            alert(data.message || "Could not create task.");
            return;
        }

        addTaskForm.reset();
        addTaskForm.style.display = "none";
        await loadTasks();
    });

    closeDetailBtn.addEventListener("click", () => {
        document.getElementById("task-detail-panel").classList.remove("open");
    });
});

async function applyTaskPageQueryParams() {
    const params = new URLSearchParams(window.location.search);
    const queryProject = params.get("project");
    const queryTask = params.get("task");
    const projectFilter = document.getElementById("project-filter");

    if (queryProject) {
        selectedProjectId = queryProject;
        projectFilter.value = queryProject;
        await loadProjectMembers(selectedProjectId);
        await loadTasks();
    }
    if (queryTask) {
        await openTaskDetail(queryTask);
    }
}

async function loadProjects() {
    const res = await apiFetch("/api/v1/projects");
    const projectFilter = document.getElementById("project-filter");
    if (!res.ok) {
        projectFilter.innerHTML = `<option value="">No projects</option>`;
        return;
    }

    const data = await res.json();
    const projects = Array.isArray(data.data) ? data.data : [];
    projectFilter.innerHTML = `<option value="">Select Project</option>`;
    projects.forEach((project) => {
        projectFilter.innerHTML += `<option value="${project.id}">${project.name}</option>`;
    });

    if (projects.length > 0) {
        selectedProjectId = projects[0].id;
        projectFilter.value = selectedProjectId;
        await loadProjectMembers(selectedProjectId);
        await loadTasks();
    }
}

async function loadProjectMembers(projectId) {
    const assigneeFilter = document.getElementById("assignee-filter");
    const taskAssignedTo = document.getElementById("task-assigned-to");
    assigneeFilter.innerHTML = `<option value="">All Assignees</option>`;
    taskAssignedTo.innerHTML = `<option value="">Unassigned</option>`;
    currentMembers = [];

    if (!projectId) return;

    const res = await apiFetch(`/api/v1/projects/${projectId}`);
    if (!res.ok) return;
    const data = await res.json();
    const members = data?.data?.members || [];
    currentMembers = members;
    for (const member of members) {
        assigneeFilter.innerHTML += `<option value="${member.user_id}">${member.email}</option>`;
        taskAssignedTo.innerHTML += `<option value="${member.user_id}">${member.email}</option>`;
    }
}

async function loadTasks() {
    if (!selectedProjectId) return;

    const status = document.getElementById("status-filter").value;
    const priority = document.getElementById("priority-filter").value;
    const assignedTo = document.getElementById("assignee-filter").value;

    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (priority) params.set("priority", priority);
    if (assignedTo) params.set("assigned_to", assignedTo);

    const endpoint = `/api/v1/projects/${selectedProjectId}/tasks${params.toString() ? `?${params.toString()}` : ""}`;
    const res = await apiFetch(endpoint);
    const data = await res.json();
    if (!res.ok) {
        alert(data.message || "Could not load tasks.");
        return;
    }

    const tasks = Array.isArray(data.data) ? data.data : [];
    renderKanban(tasks);
}

function renderKanban(tasks) {
    const columns = ["todo", "in_progress", "in_review", "done"];
    columns.forEach((status) => {
        const column = document.getElementById(`column-${status}`);
        column.innerHTML = "";
    });

    tasks.forEach((task) => {
        const column = document.getElementById(`column-${task.status}`);
        if (!column) return;

        const overdueClass = task.is_overdue ? "task-overdue" : "";
        const dueDateLabel = task.due_date ? task.due_date : "No due date";
        const initials = getInitials(task.assigned_user_name || "Unassigned");
        const priorityClass = `priority-${task.priority}`;

        column.innerHTML += `
            <div class="kanban-card ${overdueClass}" onclick="openTaskDetail('${task.id}')">
                <div class="kanban-card-header">
                    <strong>${task.title}</strong>
                    <span class="priority-badge ${priorityClass}">${task.priority}</span>
                </div>
                <div class="task-meta-row">
                    <span class="avatar-circle">${initials}</span>
                    <span>${task.assigned_user_name || "Unassigned"}</span>
                </div>
                <div class="task-meta-row">
                    <span>Due: ${dueDateLabel}</span>
                    ${task.is_overdue ? "<span class='overdue-label'>Overdue</span>" : ""}
                </div>
                <div class="task-meta-row">
                    <select onclick="event.stopPropagation()" onchange="updateStatus('${task.id}', this.value)">
                        <option value="todo" ${task.status === "todo" ? "selected" : ""}>Todo</option>
                        <option value="in_progress" ${task.status === "in_progress" ? "selected" : ""}>In Progress</option>
                        <option value="in_review" ${task.status === "in_review" ? "selected" : ""}>In Review</option>
                        <option value="done" ${task.status === "done" ? "selected" : ""}>Done</option>
                    </select>
                </div>
            </div>
        `;
    });
}

async function updateStatus(taskId, status) {
    const res = await apiFetch(`/api/v1/tasks/${taskId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status })
    });
    const data = await res.json();
    if (!res.ok) {
        alert(data.message || "Status update failed.");
        return;
    }
    await loadTasks();
}

async function openTaskDetail(taskId) {
    const panel = document.getElementById("task-detail-panel");
    const content = document.getElementById("task-detail-content");
    const res = await apiFetch(`/api/v1/tasks/${taskId}`);
    const data = await res.json();
    if (!res.ok) {
        alert(data.message || "Could not load task detail.");
        return;
    }

    const task = data.data;
    content.innerHTML = `
        <h3>${task.title}</h3>
        <p>${task.description || "No description"}</p>
        <p><strong>Status:</strong> ${task.status}</p>
        <p><strong>Priority:</strong> ${task.priority}</p>
        <p><strong>Due Date:</strong> ${task.due_date || "N/A"}</p>
        <p><strong>Creator:</strong> ${task.creator?.email || "N/A"}</p>
        <p><strong>Assignee:</strong> ${task.assignee?.email || "Unassigned"}</p>
        <p><strong>Days Until Due:</strong> ${task.days_until_due ?? "N/A"}</p>
    `;
    panel.classList.add("open");
}

function getInitials(name) {
    if (!name) return "NA";
    const parts = name.split("@")[0].split(/[.\s_-]+/).filter(Boolean);
    const first = parts[0]?.[0] || "N";
    const second = parts[1]?.[0] || parts[0]?.[1] || "A";
    return `${first}${second}`.toUpperCase();
}
