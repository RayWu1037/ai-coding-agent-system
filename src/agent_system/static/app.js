const form = document.getElementById("task-form");
const statusPill = document.getElementById("status-pill");
const statusMessage = document.getElementById("status-message");
const timeline = document.getElementById("timeline");
const jobs = document.getElementById("jobs");
const planOutput = document.getElementById("plan-output");
const reviewOutput = document.getElementById("review-output");
const codeOutput = document.getElementById("code-output");

let activeJobId = null;
let pollTimer = null;

function setStatus(stage, message) {
  statusPill.textContent = stage || "idle";
  statusPill.dataset.state = stage || "idle";
  statusMessage.textContent = message || "No active run.";
}

function renderTimeline(items) {
  timeline.innerHTML = "";
  if (!items || items.length === 0) {
    timeline.innerHTML = "<li class='muted'>No events yet.</li>";
    return;
  }

  items.forEach((item) => {
    const li = document.createElement("li");
    li.className = "timeline-item";
    li.innerHTML = `<strong>${item.stage}</strong><span>${item.message}</span>`;
    timeline.appendChild(li);
  });
}

function renderJobList(jobItems) {
  jobs.innerHTML = "";
  if (!jobItems.length) {
    jobs.innerHTML = "<p class='muted'>No jobs submitted yet.</p>";
    return;
  }

  jobItems
    .slice()
    .reverse()
    .forEach((job) => {
      const button = document.createElement("button");
      button.className = "job-card";
      button.type = "button";
      button.innerHTML = `
        <span class="job-status" data-state="${job.status}">${job.status}</span>
        <strong>${job.task}</strong>
        <small>${job.message}</small>
      `;
      button.addEventListener("click", () => {
        activeJobId = job.id;
        refreshJob(job.id);
      });
      jobs.appendChild(button);
    });
}

function renderOutputs(job) {
  planOutput.textContent = job.plan || "";
  reviewOutput.textContent = job.review || "";
  codeOutput.textContent = job.final_code || "";
  setStatus(job.status, job.error || job.message);
  renderTimeline(job.timeline || []);
}

async function refreshJobs() {
  const response = await fetch("/api/jobs");
  const data = await response.json();
  renderJobList(data.jobs || []);
}

async function refreshJob(jobId) {
  const response = await fetch(`/api/jobs/${jobId}`);
  const job = await response.json();
  renderOutputs(job);
  await refreshJobs();

  const activeStates = new Set(["queued", "starting", "planning", "coding", "executing", "debugging", "reviewing"]);
  if (activeStates.has(job.status)) {
    schedulePoll();
  } else {
    clearTimeout(pollTimer);
    pollTimer = null;
  }
}

function schedulePoll() {
  clearTimeout(pollTimer);
  pollTimer = setTimeout(() => {
    if (activeJobId) {
      refreshJob(activeJobId).catch((error) => {
        setStatus("failed", error.message);
      });
    }
  }, 1500);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const task = String(formData.get("task") || "").trim();
  const iterationsValue = String(formData.get("iterations") || "").trim();

  if (!task) {
    setStatus("invalid", "Task is required.");
    return;
  }

  setStatus("submitting", "Submitting job.");
  renderTimeline([]);
  planOutput.textContent = "";
  reviewOutput.textContent = "";
  codeOutput.textContent = "";

  const payload = {
    task,
    iterations: iterationsValue ? Number(iterationsValue) : null,
  };

  const response = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    setStatus("failed", errorText);
    return;
  }

  const job = await response.json();
  activeJobId = job.id;
  await refreshJob(job.id);
});

refreshJobs().catch((error) => {
  setStatus("failed", error.message);
});
