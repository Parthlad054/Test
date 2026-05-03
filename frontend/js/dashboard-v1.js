let dashboardData = null;

document.addEventListener("DOMContentLoaded", async () => {
    const logoutBtn = document.getElementById("logout-btn");
    const quickAddTaskForm = document.getElementById("quick-add-task-form");

    if (!getToken()) {
        window.location.href = "index.html";
        return;
    }

    logoutBtn.style.display = "inline-block";
    logoutBtn.addEventListener("click", () => {
        clearTokens();
        window.location.href = "index.html";
    });

    await loadDashboard();

    quickAddTaskForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        await submitQuickTask();
    });
});

async function loadDashboard() {
    const res = await apiFetch("/api/v1/dashboard");
    const data = await res.json();
    if (!res.ok) {
        alert(data.message || "Could not load dashboard.");
        return;
    }

    dashboardData = data.data;
    renderSummary(dashboardData.summary);
    renderMyTasks(dashboardData.my_tasks || []);
    renderOverdueTasks("overdue-tasks-list", dashboardData.overdue_tasks || []);
    renderRecentProjects(dashboardData.recent_projects || []);
    await populateQuickProjectOptions();
    renderAdminSections(dashboardData);
}

function renderSummary(summary) {
    document.getElementById("metric-open").textContent = summary.my_open_tasks;
    document.getElementById("metric-overdue").textContent = summary.overdue_tasks;
    document.getElementById("metric-done-week").textContent = summary.tasks_completed_this_week;
    document.getElementById("metric-projects").textContent = summary.total_projects;

    const overdueEl = document.getElementById("metric-overdue");
    overdueEl.classList.toggle("metric-danger", summary.overdue_tasks > 0);
    const doneEl = document.getElementById("metric-done-week");
    doneEl.classList.add("metric-success");
}

function renderMyTasks(tasks) {
    const container = document.getElementById("my-tasks-list");
    if (!tasks.length) {
        container.innerHTML = "<p>No personal tasks found.</p>";
        return;
    }

    const sortedTasks = [...tasks].sort((a, b) => {
        if (!a.due_date) return 1;
        if (!b.due_date) return -1;
        return new Date(a.due_date) - new Date(b.due_date);
    });

    container.innerHTML = sortedTasks.map((task) => {
        const overdueClass = task.is_overdue ? "task-row-overdue" : "";
        const overdueText = task.is_overdue ? `<span class="overdue-dot"></span><span class="overdue-text">${Math.abs(task.days_until_due)} days overdue</span>` : "";
        return `
            <a class="task-row ${overdueClass}" href="tasks.html?project=${task.project_id}&task=${task.id}">
                <div>
                    <strong>${task.title}</strong>
                    <div class="task-subtext">${task.project_name}</div>
                </div>
                <div class="task-row-right">
                    <span class="priority-badge priority-${task.priority}">${task.priority}</span>
                    <span>${task.due_date || "No due date"}</span>
                    <span>${overdueText}</span>
                </div>
            </a>
        `;
    }).join("");
}

function renderOverdueTasks(containerId, tasks) {
    const container = document.getElementById(containerId);
    if (!tasks.length) {
        container.innerHTML = "<p>No overdue tasks.</p>";
        return;
    }

    container.innerHTML = tasks.map((task) => `
        <div class="task-row task-row-overdue">
            <div>
                <strong>${task.title}</strong>
                <div class="task-subtext">${task.project_name}</div>
            </div>
            <div class="task-row-right">
                <span class="priority-badge priority-${task.priority}">${task.priority}</span>
                <span class="overdue-dot"></span>
                <span class="overdue-text">${Math.abs(task.days_until_due)} days overdue</span>
            </div>
        </div>
    `).join("");
}

function renderRecentProjects(projects) {
    const container = document.getElementById("my-projects-list");
    if (!projects.length) {
        container.innerHTML = "<p>No recent projects.</p>";
        return;
    }

    container.innerHTML = projects.map((project) => {
        const doneCount = Math.max(project.task_count - project.open_task_count, 0);
        const percent = project.task_count > 0 ? Math.round((doneCount / project.task_count) * 100) : 0;
        return `
            <div class="project-progress-item">
                <div class="project-progress-top">
                    <strong>${project.name}</strong>
                    <span>${doneCount}/${project.task_count}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-value" style="width:${percent}%"></div>
                </div>
            </div>
        `;
    }).join("");
}

async function populateQuickProjectOptions() {
    const select = document.getElementById("quick-project-id");
    select.innerHTML = `<option value="">Select Project</option>`;
    const res = await apiFetch("/api/v1/projects");
    if (!res.ok) return;
    const data = await res.json();
    const projects = Array.isArray(data.data) ? data.data : [];
    for (const project of projects) {
        select.innerHTML += `<option value="${project.id}">${project.name}</option>`;
    }
}

function renderAdminSections(data) {
    const adminPanel = document.getElementById("admin-panel");
    if (!data.team_summary) {
        adminPanel.style.display = "none";
        return;
    }

    adminPanel.style.display = "block";
    document.getElementById("team-summary").innerHTML = `
        <div class="team-summary-grid">
            <div class="summary-chip">Users: ${data.team_summary.total_users}</div>
            <div class="summary-chip">Active Projects: ${data.team_summary.active_projects}</div>
            <div class="summary-chip">Open Tasks: ${data.team_summary.total_open_tasks}</div>
            <div class="summary-chip">Critical Tasks: ${data.team_summary.critical_tasks}</div>
        </div>
    `;
    renderOverdueTasks("all-overdue-tasks-list", data.all_overdue_tasks || []);
}

async function submitQuickTask() {
    const projectId = document.getElementById("quick-project-id").value;
    const title = document.getElementById("quick-task-title").value.trim();
    const dueDate = document.getElementById("quick-task-due-date").value;

    if (!projectId || !title) {
        alert("Project and title are required.");
        return;
    }

    const res = await apiFetch(`/api/v1/projects/${projectId}/tasks`, {
        method: "POST",
        body: JSON.stringify({
            title,
            due_date: dueDate || null
        })
    });
    const data = await res.json();
    if (!res.ok) {
        alert(data.message || "Quick add failed.");
        return;
    }
    document.getElementById("quick-add-task-form").reset();
    await loadDashboard();
}
