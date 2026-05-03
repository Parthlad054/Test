async function createProject(name, description) {
    try {
        const res = await apiFetch("/projects", {
            method: "POST",
            body: JSON.stringify({ name, description })
        });
        if (res.ok) {
            const responseData = await res.json();
            const newProject = responseData?.data || null;
            alert("Project created!");
            document.dispatchEvent(new CustomEvent("project:created", { detail: { project: newProject } }));
        } else {
            const data = await res.json();
            alert("Error: " + data.message);
        }
    } catch (err) {
        console.error(err);
    }
}

async function addProjectMember(projectId, userId, role) {
    try {
        const res = await apiFetch(`/projects/${projectId}/members`, {
            method: "POST",
            body: JSON.stringify({
                user_id: Number(userId),
                role
            })
        });

        if (res.ok) {
            alert("Member added to project.");
            document.dispatchEvent(new CustomEvent("project:member-added"));
            return true;
        }

        const data = await res.json();
        alert("Error: " + (data.message || "Failed to add member."));
        return false;
    } catch (err) {
        console.error(err);
        return false;
    }
}

// Add event listener to project form if it exists
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("create-project-form");
    const addMemberForm = document.getElementById("add-member-form");

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const name = document.getElementById("project-name").value;
            const desc = document.getElementById("project-desc").value;
            await createProject(name, desc);
            form.reset();
        });
    }

    if (addMemberForm) {
        addMemberForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const projectId = document.getElementById("member-project-id").value;
            const userId = document.getElementById("member-user-id").value;
            const role = document.getElementById("member-role").value;

            const ok = await addProjectMember(projectId, userId, role);
            if (ok) {
                addMemberForm.reset();
            }
        });
    }
});
