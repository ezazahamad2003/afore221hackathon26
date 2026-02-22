const PIPELINE_STEPS = [
  { label: "Intent parsed",        detail: "Indian restaurant · 2 people · 9:00 PM · rating ≥ 4.5" },
  { label: "Location extracted",   detail: "501 Folsom St, San Francisco, CA" },
  { label: "Preferences applied",  detail: "Quiet ambiance · window seat · within 10 min" },
  { label: "Restaurants found",    detail: "5 results scraped via rtrvr.ai" },
  { label: "Top candidate selected", detail: "Copper Chimney · 4.7★ · 0.4 mi away" },
  { label: "Calling restaurant",   detail: "Outbound call via Vapi + MiniMax voice" },
  { label: "Booking confirmed",    detail: "Table for 2 at 9:00 PM under your name" },
  { label: "Calendar event created", detail: "Added to Google Calendar" },
];

const MEMORY_NODES = [
  { label: "Indian food", x: 50, y: 50, r: 38, main: true },
  { label: "Rating ≥ 4.5", x: 75, y: 28, r: 26 },
  { label: "2 people", x: 78, y: 68, r: 22 },
  { label: "Quiet ambiance", x: 28, y: 20, r: 24 },
  { label: "Window seat", x: 22, y: 72, r: 20 },
  { label: "Downtown", x: 55, y: 80, r: 18 },
  { label: "9 PM dinner", x: 32, y: 48, r: 16 },
];

let taskRunning = false;

function showPage(id) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.getElementById(id).classList.add("active");
  window.scrollTo(0, 0);
  if (id === "page-dashboard") renderMemoryGraph();
}

function connectService(service) {
  const btn = document.getElementById(`btn-${service}`);
  btn.classList.add("connected");
  btn.innerHTML = btn.innerHTML.replace("Connect", "✓ Connected");
}

function setupComplete() {
  const name  = document.getElementById("input-name").value.trim() || "User";
  const phone = document.getElementById("input-phone").value.trim();

  document.getElementById("nav-name").textContent = name;
  document.getElementById("nav-avatar").textContent = name[0].toUpperCase();

  showPage("page-dashboard");
  addBooking("Copper Chimney", "Tonight · 9:00 PM · 2 people", "Confirmed");
}

function renderMemoryGraph() {
  const container = document.getElementById("memory-graph");
  if (!container || container.dataset.rendered) return;
  container.dataset.rendered = "1";

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", "100%");
  svg.setAttribute("viewBox", "0 0 100 100");

  const cx = 50, cy = 50;
  MEMORY_NODES.forEach((node, i) => {
    if (i > 0) {
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", cx); line.setAttribute("y1", cy);
      line.setAttribute("x2", node.x); line.setAttribute("y2", node.y);
      line.setAttribute("stroke", "rgba(124,111,247,0.2)");
      line.setAttribute("stroke-width", "0.8");
      svg.appendChild(line);
    }
  });

  MEMORY_NODES.forEach((node, i) => {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", node.x);
    circle.setAttribute("cy", node.y);
    circle.setAttribute("r", node.r / 2.5);
    circle.setAttribute("fill", i === 0 ? "rgba(124,111,247,0.35)" : "rgba(79,195,247,0.18)");
    circle.setAttribute("stroke", i === 0 ? "rgba(124,111,247,0.7)" : "rgba(79,195,247,0.4)");
    circle.setAttribute("stroke-width", "0.8");

    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", node.x);
    text.setAttribute("y", node.y + 0.5);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("dominant-baseline", "middle");
    text.setAttribute("font-size", i === 0 ? "4" : "3.2");
    text.setAttribute("fill", "rgba(232,234,242,0.9)");
    text.setAttribute("font-family", "system-ui");
    text.textContent = node.label;

    g.appendChild(circle);
    g.appendChild(text);
    svg.appendChild(g);
  });

  container.appendChild(svg);
}

function simulateTask() {
  if (taskRunning) return;
  taskRunning = true;

  const pipeline = document.getElementById("task-pipeline");
  const badge    = document.getElementById("task-badge");

  badge.textContent = "Running";
  badge.className = "task-status running";
  pipeline.innerHTML = "";

  const stepEls = PIPELINE_STEPS.map((step, i) => {
    const div = document.createElement("div");
    div.className = "pipeline-step";
    div.innerHTML = `
      <div class="p-icon pending" id="picon-${i}">○</div>
      <div>
        <div class="p-label">${step.label}</div>
        <div class="p-detail" id="pdetail-${i}" style="opacity:0">${step.detail}</div>
      </div>
    `;
    pipeline.appendChild(div);
    return div;
  });

  let i = 0;
  function advance() {
    if (i > 0) {
      const prev = document.getElementById(`picon-${i - 1}`);
      prev.className = "p-icon done";
      prev.textContent = "✓";
    }
    if (i < PIPELINE_STEPS.length) {
      const icon   = document.getElementById(`picon-${i}`);
      const detail = document.getElementById(`pdetail-${i}`);
      icon.className = "p-icon running";
      icon.innerHTML = `<span class="pulse-dot" style="width:8px;height:8px;display:block"></span>`;
      detail.style.opacity = "1";
      i++;
      const delay = i === 6 ? 3200 : 700;
      setTimeout(advance, delay);
    } else {
      badge.textContent = "Done";
      badge.className = "task-status done";
      addBooking("Copper Chimney", "Tonight · 9:00 PM · 2 people", "Just confirmed");
      taskRunning = false;
    }
  }
  advance();
}

function addBooking(name, meta, status) {
  const list = document.getElementById("bookings-list");
  const empty = list.querySelector(".empty-state");
  if (empty) empty.remove();

  const already = [...list.querySelectorAll(".booking-name")]
    .find(el => el.textContent === name);
  if (already) return;

  const item = document.createElement("div");
  item.className = "booking-item";
  item.innerHTML = `
    <div class="booking-icon">🍽️</div>
    <div>
      <div class="booking-name">${name}</div>
      <div class="booking-meta">${meta}</div>
    </div>
    <div class="booking-badge">${status}</div>
  `;
  list.prepend(item);
}
