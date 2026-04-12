// =============================================
// VibeFuel GTM Simulator - Client-side JS
// =============================================

let currentSessionId = null;

// Utility: Get URL parameter
function getUrlParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// =============================================
// 1. Strategy Form Handling
// =============================================
function initStrategyForm() {
    const form = document.getElementById('strategy-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const textarea = form.querySelector('textarea');
        const submitBtn = form.querySelector('button');
        
        if (!textarea.value.trim()) {
            alert("Please enter your go-to-market strategy.");
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <i class="fa-solid fa-spinner animate-spin"></i> 
            Analyzing Strategy...
        `;

        try {
            const formData = new FormData();
            formData.append('text', textarea.value.trim());

            const response = await fetch('/api/strategy', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.session_id) {
                currentSessionId = result.session_id;
                // Redirect to decisions page
                window.location.href = `/decisions?session=${result.session_id}`;
            } else {
                throw new Error("No session returned");
            }
        } catch (err) {
            console.error(err);
            alert("Failed to submit strategy. Please try again.");
            submitBtn.disabled = false;
            submitBtn.innerHTML = `Submit Strategy & Continue <i class="fa-solid fa-arrow-right"></i>`;
        }
    });
}

// =============================================
// 2. Decisions Form Handling
// =============================================
function initDecisionsForm() {
    const form = document.getElementById('decisions-form');
    if (!form) return;

    const sessionId = getUrlParam('session');
    if (sessionId) {
        const hiddenInput = form.querySelector('input[name="session_id"]');
        if (hiddenInput) hiddenInput.value = sessionId;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = form.querySelector('button');
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <i class="fa-solid fa-spinner animate-spin"></i> 
            Launching Simulation...
        `;

        try {
            const formData = new FormData(form);
            
            const response = await fetch('/api/decisions', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const sessionId = formData.get('session_id');
                window.location.href = `/simulation?session=${sessionId}`;
            } else {
                throw new Error("Server error");
            }
        } catch (err) {
            console.error(err);
            alert("Failed to save decisions.");
            submitBtn.disabled = false;
            submitBtn.textContent = "Launch Simulation →";
        }
    });
}

// =============================================
// 3. Simulation Page - SSE Streaming + Live Updates
// =============================================
function initSimulation() {
    const startBtn = document.getElementById('start-simulation-btn');
    if (!startBtn) return;

    const sessionId = getUrlParam('session');
    if (!sessionId) {
        console.error("No session ID found");
        return;
    }

    currentSessionId = sessionId;

    startBtn.addEventListener('click', () => {
        startBtn.disabled = true;
        startBtn.innerHTML = `
            <i class="fa-solid fa-spinner animate-spin mr-3"></i>
            Running Live Simulation...
        `;

        const eventSource = new EventSource(`/api/simulation/stream/${sessionId}`);

        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);

            // Update progress bar
            if (data.stage) {
                const progressPercent = (data.stage / 4) * 100;
                const progressBar = document.getElementById('simulation-progress');
                if (progressBar) progressBar.style.width = `${progressPercent}%`;
            }

            // Update stage name
            if (data.stage_name) {
                const stageEl = document.getElementById('current-stage');
                if (stageEl) stageEl.textContent = `Stage ${data.stage}/4 • ${data.stage_name}`;
            }

            // Update KPI cards
            if (data.kpis) {
                Object.keys(data.kpis).forEach(key => {
                    const el = document.getElementById(`kpi-${key}`);
                    if (el) {
                        let displayValue = data.kpis[key];

                        if (key === 'cac') displayValue = '$' + Math.round(displayValue);
                        else if (key === 'roas') displayValue = displayValue.toFixed(1) + 'x';
                        else if (['conversion', 'awareness', 'marketShare'].includes(key)) {
                            displayValue = displayValue.toFixed(1) + '%';
                        } else if (key === 'sales') {
                            displayValue = Math.round(displayValue) + 'k';
                        } else {
                            displayValue = Math.round(displayValue);
                        }

                        el.textContent = displayValue;
                    }
                });
            }

            // Update insight / narrative
            if (data.narrative) {
                const insightPanel = document.getElementById('insight-panel');
                if (insightPanel) {
                    insightPanel.innerHTML = `
                        <div class="flex items-start gap-4">
                            <i class="fa-solid fa-lightbulb text-amber-400 mt-1"></i>
                            <p class="text-zinc-200 leading-relaxed">${data.narrative}</p>
                        </div>
                    `;
                }
            }

            // Competitor event
            if (data.competitor) {
                const compPanel = document.getElementById('competitor-panel');
                if (compPanel) {
                    compPanel.innerHTML = `
                        <div class="bg-red-950 border border-red-800 rounded-3xl p-8">
                            <div class="flex items-center gap-3 mb-4">
                                <i class="fa-solid fa-bolt text-red-400"></i>
                                <span class="uppercase text-red-400 text-sm font-semibold tracking-widest">
                                    ${data.competitor.event}
                                </span>
                            </div>
                            <p class="text-red-200">${data.competitor.commentary}</p>
                        </div>
                    `;
                }
            }

            // Simulation finished
            if (data.complete) {
                eventSource.close();
                setTimeout(() => {
                    window.location.href = `/results?session=${sessionId}`;
                }, 1500);
            }
        };

        eventSource.onerror = function() {
            eventSource.close();
            alert("Simulation stream encountered an error. Showing final results.");
            window.location.href = `/results?session=${sessionId}`;
        };
    });
}

// =============================================
// 4. Global Initialization
// =============================================
function initializeApp() {
    initStrategyForm();
    initDecisionsForm();
    initSimulation();

    // Display session ID in navbar if available
    const sessionId = getUrlParam('session');
    if (sessionId) {
        const sessionDisplay = document.getElementById('session-id-display');
        if (sessionDisplay) {
            sessionDisplay.textContent = sessionId.substring(0, 8).toUpperCase();
        }
    }
}

// Boot the app when DOM is ready
document.addEventListener('DOMContentLoaded', initializeApp);
