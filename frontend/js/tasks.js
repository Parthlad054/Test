async function createTask(taskPayload) {
    try {
        const res = await apiFetch("/tasks", {
            method: "POST",
            body: JSON.stringify(taskPayload)
        });

        if (res.ok) {
            alert("Task created!");
            document.dispatchEvent(new CustomEvent("task:created"));
            return true;
        }

        const data = await res.json();
        alert("Error: " + (data.message || "Failed to create task."));
        return false;
    } catch (err) {
        console.error(err);
        return false;
    }
}

async function updateTaskStatus(taskId, status) {
    try {
        const res = await apiFetch(`/tasks/${taskId}/status`, {
            method: "PATCH",
            body: JSON.stringify({ status })
        });
        if (res.ok) {
            document.dispatchEvent(new CustomEvent("task:updated"));
            return true;
        } else {
            const data = await res.json();
            alert("Error: " + data.message);
            return false;
        }
    } catch (err) {
        console.error(err);
        return false;
    }
}

async function assignTask(taskId, assignedToId) {
    try {
        const payload = { assigned_to_id: assignedToId ? Number(assignedToId) : null };
        const res = await apiFetch(`/tasks/${taskId}/assign`, {
            method: "PATCH",
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            document.dispatchEvent(new CustomEvent("task:updated"));
            return true;
        }

        const data = await res.json();
        alert("Error: " + (data.message || "Failed to re-assign task."));
        return false;
    } catch (err) {
        console.error(err);
        return false;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const createTaskForm = document.getElementById("create-task-form");

    if (createTaskForm) {
        createTaskForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const title = document.getElementById("task-title").value.trim();
            const description = document.getElementById("task-desc").value.trim();
            const projectId = document.getElementById("task-project-id").value;
            const assignedToId = document.getElementById("task-assigned-user-id").value;
            const dueDate = document.getElementById("task-due-date").value;

            const payload = {
                title,
                description: description || null,
                project_id: projectId,
                assigned_to_id: assignedToId ? Number(assignedToId) : null,
                due_date: dueDate ? new Date(dueDate).toISOString() : null
            };

            const ok = await createTask(payload);
            if (ok) {
                createTaskForm.reset();
            }
        });
    }
});
