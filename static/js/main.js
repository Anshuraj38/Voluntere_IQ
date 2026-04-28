async function fetchJson(path, options = {}) {
  const response = await fetch(path, options);
  const text = await response.text();
  try {
    const data = JSON.parse(text || "{}");
    if (!response.ok) {
      return {
        success: false,
        message: data.message || `Server error ${response.status}`,
        details: data,
      };
    }
    return data;
  } catch (error) {
    return {
      success: false,
      message: `Invalid server response (${response.status})`,
      details: text,
    };
  }
}

function getUrgencyBadge(score) {
  if (score >= 8) return "badge-urgency-critical";
  if (score >= 5) return "badge-urgency-high";
  return "badge-urgency-normal";
}

async function loadDashboard() {
  const statsResult = await fetchJson("/api/stats");
  const needsResult = await fetchJson("/api/get-needs");
  const volunteersResult = await fetchJson("/api/get-volunteers");

  if (statsResult.success) {
    document.getElementById("totalNeeds").innerText = statsResult.data.total_needs;
    document.getElementById("resolvedNeeds").innerText = statsResult.data.resolved;
    document.getElementById("pendingNeeds").innerText = statsResult.data.pending;
    document.getElementById("activeVolunteers").innerText = statsResult.data.active_volunteers;
  }

  if (needsResult.success) {
    const tbody = document.getElementById("needsTableBody");
    tbody.innerHTML = "";
    needsResult.data.forEach((need) => {
      const badgeClass = getUrgencyBadge(need.urgency_score);
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${need.id}</td>
        <td>${need.need_type}</td>
        <td>${need.location}</td>
        <td><span class="badge ${badgeClass}">${need.urgency_score}</span></td>
        <td>${need.people_affected}</td>
        <td>${need.skills_required.join(", ")}</td>
        <td>${need.status}</td>
        <td>${need.created_at}</td>
      `;
      tbody.appendChild(row);
    });
  }

  if (volunteersResult.success) {
    const tbody = document.getElementById("volunteersTableBody");
    tbody.innerHTML = "";
    volunteersResult.data.forEach((volunteer) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${volunteer.id}</td>
        <td>${volunteer.name}</td>
        <td>${volunteer.location}</td>
        <td>${volunteer.skills.join(", ")}</td>
        <td>${volunteer.availability}</td>
        <td>${volunteer.created_at}</td>
      `;
      tbody.appendChild(row);
    });
  }
}

async function submitNeed(event) {
  event.preventDefault();
  const form = document.getElementById("needForm");
  const formData = new FormData(form);
  const message = document.getElementById("needFormMessage");

  try {
    const response = await fetchJson("/api/submit-need", {
      method: "POST",
      body: formData,
    });

    if (response.success) {
      message.innerText = "Need submitted successfully.";
      message.className = "text-success mt-3";
      form.reset();
    } else {
      message.innerText = response.message || "Unable to submit need.";
      message.className = "text-danger mt-3";
    }
  } catch (error) {
    message.innerText = error.message || "Unable to submit need.";
    message.className = "text-danger mt-3";
  }
}

async function registerVolunteer(event) {
  event.preventDefault();
  const form = document.getElementById("volunteerForm");
  const formData = new FormData(form);
  const skills = [];
  document.querySelectorAll("input[name='skills']:checked").forEach((checkbox) => skills.push(checkbox.value));

  const payload = {
    name: formData.get("name"),
    phone: formData.get("phone"),
    location: formData.get("location"),
    availability: formData.get("availability"),
    skills,
  };

  const response = await fetchJson("/api/register-volunteer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const message = document.getElementById("volunteerFormMessage");
  if (response.success) {
    message.innerText = "Volunteer registered successfully.";
    message.className = "text-success mt-3";
    form.reset();
  } else {
    message.innerText = response.message || "Unable to register volunteer.";
    message.className = "text-danger mt-3";
  }
}

function attachPageHandlers() {
  const needForm = document.getElementById("needForm");
  if (needForm) {
    needForm.addEventListener("submit", submitNeed);
  }

  const volunteerForm = document.getElementById("volunteerForm");
  if (volunteerForm) {
    volunteerForm.addEventListener("submit", registerVolunteer);
  }

  const dashboard = document.getElementById("dashboardRoot");
  if (dashboard) {
    loadDashboard();
  }
}

document.addEventListener("DOMContentLoaded", attachPageHandlers);
