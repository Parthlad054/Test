async function loadDashboardPage() {
    if (!requireAuth()) return;
    applyNavActive();
    await setupTopbar();

    const response = await apiFetch("/api/v1/dashboard");
    const payload = await response.json();
    if (!response.ok) {
        showToast(payload.message || "Failed to load dashboard", "error");
        return;
    }

    const data = payload.data;
    renderSummary(data.summary || {});
    renderMyTasks(data.my_tasks || []);
    renderProjects(data.recent_projects || []);
    renderQuickAddProjects(data.recent_projects || []);
    bindQuickAdd();

    const overdue = data.overdue_tasks || [];
    renderList("overdue-list", overdue, taskRowMarkup, "No overdue tasks.");

    const adminPanel = document.getElementById("admin-panel");
    if (data.team_summary) {
        adminPanel.style.display = "block";
        renderTeamSummary(data.team_summary);
        renderList("all-overdue-list", data.all_overdue_tasks || [], taskRowMarkup, "No overdue tasks.");
    } else {
        adminPanel.style.display = "none";
    }
}

function renderSummary(summary) {
    document.getElementById("stat-open").textContent = summary.my_open_tasks || 0;
    document.getElementById("stat-overdue").textContent = summary.overdue_tasks || 0;
    document.getElementById("stat-overdue").classList.toggle("stat-danger", (summary.overdue_tasks || 0) > 0);
    document.getElementById("stat-done-week").textContent = summary.tasks_completed_this_week || 0;
    document.getElementById("stat-projects").textContent = summary.total_projects || 0;
}

function taskRowMarkup(task) {
    const overdueText = task.is_overdue
        ? `<span class="overdue-indicator"><span class="overdue-dot"></span>${Math.abs(task.days_until_due)} days overdue</span>`
        : "";
    return `
        <a class="row ${task.is_overdue ? "overdue" : ""}" href="tasks.html?project=${task.project_id}&task=${task.id}">
            <div>
                <div><strong>${task.title}</strong></div>
                <div style="font-size:12px;color:var(--gray-600)">${task.project_name}</div>
            </div>
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:flex-end">
                <span class="badge priority-${task.priority}">${task.priority}</span>
                <span style="font-size:12px">${task.due_date || "No due date"}</span>
                ${overdueText}
            </div>
        </a>
    `;
}

function renderMyTasks(tasks) {
    const sorted = [...tasks].sort((a, b) => {
        if (!a.due_date) return 1;
        if (!b.due_date) return -1;
        return new Date(a.due_date) - new Date(b.due_date);
    });
    renderList("my-tasks-list", sorted, taskRowMarkup, "No tasks yet.", "Create your first task");
}

function renderProjects(projects) {
    renderList(
        "my-projects-list",
        projects,
        (project) => {
            const total = project.task_count || 0;
            const done = Math.max(total - (project.open_task_count || 0), 0);
            const percent = total ? Math.round((done / total) * 100) : 0;
            return `
                <div class="row" style="display:block">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <strong>${project.name}</strong>
                        <span style="font-size:12px;color:var(--gray-600)">${done}/${total}</span>
                    </div>
                    <div class="progress"><span style="width:${percent}%"></span></div>
                </div>
            `;
        },
        "No projects yet."
    );
}

function renderQuickAddProjects(projects) {
    const select = document.getElementById("quick-project");
    select.innerHTML = `<option value="">Select project</option>`;
    projects.forEach((project) => {
        select.innerHTML += `<option value="${project.id}">${project.name}</option>`;
    });
}

function bindQuickAdd() {
    const form = document.getElementById("quick-add-form");
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const projectId = document.getElementById("quick-project").value;
        const title = document.getElementById("quick-title").value.trim();
        const dueDate = document.getElementById("quick-due-date").value || null;
        if (!projectId || title.length < 3) {
            showToast("Select project and enter a valid title", "error");
            return;
        }
        const button = document.getElementById("quick-submit");
        button.classList.add("loading");
        button.disabled = true;
        try {
            const response = await apiFetch(`/api/v1/projects/${projectId}/tasks`, {
                method: "POST",
                body: JSON.stringify({ title, due_date: dueDate })
            });
            const payload = await response.json();
            if (!response.ok) {
                showToast(payload.message || "Could not create task", "error");
                return;
            }
            showToast("Task created", "success");
            form.reset();
            await loadDashboardPage();
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            button.classList.remove("loading");
            button.disabled = false;
        }
    });
}

function renderTeamSummary(team) {
    const el = document.getElementById("team-summary");
    el.innerHTML = `
        <div class="grid-2">
            <div class="row"><span>Total Users</span><strong>${team.total_users}</strong></div>
            <div class="row"><span>Active Projects</span><strong>${team.active_projects}</strong></div>
            <div class="row"><span>Total Open Tasks</span><strong>${team.total_open_tasks}</strong></div>
            <div class="row"><span>Critical Tasks</span><strong>${team.critical_tasks}</strong></div>
        </div>
    `;
}

function renderList(containerId, items, renderer, emptyTitle, emptySubtitle = "") {
    const container = document.getElementById(containerId);
    if (!items.length) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="emoji">📭</div>
                <div class="title">${emptyTitle}</div>
                <div>${emptySubtitle}</div>
            </div>
        `;
        return;
    }
    container.innerHTML = `<div class="list">${items.map(renderer).join("")}</div>`;
}

document.addEventListener("DOMContentLoaded", loadDashboardPage);
