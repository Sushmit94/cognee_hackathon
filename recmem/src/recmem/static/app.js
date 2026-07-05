async function updateDashboard() {
    try {
        const response = await fetch('/api/events');
        const data = await response.json();

        const log = document.getElementById('log');
        log.innerHTML = data.events.slice(-15).map(e =>
            `<div class="event">[${e.layer_source}] ${e.summary}</div>`
        ).join('');
        log.scrollTop = log.scrollHeight;

        const activeList = document.getElementById('active-list');
        const resolvedList = document.getElementById('resolved-list');
        activeList.innerHTML = data.constraints.filter(c => c.status === 'active')
            .map(c => `<li class="constraint-active">${c.constraint}</li>`).join('');
        resolvedList.innerHTML = data.constraints.filter(c => c.status === 'resolved')
            .map(c => `<li class="constraint-resolved">${c.constraint}</li>`).join('');

        const healthList = document.getElementById('health-list');
        healthList.innerHTML = data.facts_health.map(h => `<div>${h.id.slice(0,5)}: ${h.score}%</div>`).join('');

        const cogneeList = document.getElementById('cognee-list');
        cogneeList.innerHTML = Object.entries(data.cognee_calls)
            .map(([k, v]) => `<div>${k}: ${v} calls</div>`).join('');

    } catch (err) {
        console.error("Dashboard update failed:", err);
    }
}

updateDashboard();
setInterval(updateDashboard, 2000);