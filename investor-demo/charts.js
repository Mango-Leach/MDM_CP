// charts.js
// Handles rendering of Chart.js graphs for trends and UV forecast

let trendsChartInstance = null;
let uvChartInstance = null;

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { labels: { color: '#94a3b8', font: { family: 'Outfit' } } }
    },
    scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
    }
};

function renderTrendChart(readings) {
    const ctx = document.getElementById('trendsChart').getContext('2d');
    
    // Sort chronologically
    const sorted = [...readings].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    
    const labels = sorted.map(r => new Date(r.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }));
    const hydrationData = sorted.map(r => r.hydration);
    const scoreData = sorted.map(r => r.skin_score);

    if (trendsChartInstance) {
        trendsChartInstance.destroy();
    }

    trendsChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Skin Score',
                    data: scoreData,
                    borderColor: '#00f3ff',
                    backgroundColor: 'rgba(0, 243, 255, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Hydration %',
                    data: hydrationData,
                    borderColor: '#00ff88',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    tension: 0.4,
                    borderDash: [5, 5]
                }
            ]
        },
        options: chartOptions
    });
}

function renderUVForecast(forecastData) {
    const ctx = document.getElementById('uvForecastChart').getContext('2d');
    
    const hourly = forecastData.hourly || [];
    const labels = hourly.map(h => {
        const d = new Date(h.time);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });
    const uvData = hourly.map(h => h.uv_index);

    if (uvChartInstance) {
        uvChartInstance.destroy();
    }

    uvChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Predicted UV Index',
                data: uvData,
                backgroundColor: uvData.map(val => 
                    val >= 8 ? '#ff4757' : 
                    val >= 6 ? '#ff7b00' : 
                    val >= 3 ? '#f1c40f' : 'rgba(255,255,255,0.2)'
                ),
                borderRadius: 4
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: { ...chartOptions.scales.y, beginAtZero: true, max: 12 }
            }
        }
    });

    // Update warning text
    const warningContainer = document.getElementById('uv-warning-container');
    if (warningContainer) {
        const level = forecastData.warning_level;
        let icon = 'fa-sun';
        let colorClass = 'text-muted';
        
        if (level === 'extreme') { icon = 'fa-triangle-exclamation'; colorClass = 'state-bad'; }
        else if (level === 'high') { icon = 'fa-temperature-arrow-up'; colorClass = 'state-warn'; }
        else if (level === 'moderate') { icon = 'fa-cloud-sun'; colorClass = 'state-warn'; }
        else { icon = 'fa-cloud'; colorClass = 'state-good'; }

        warningContainer.innerHTML = `
            <div class="uv-alert ${colorClass}">
                <i class="fa-solid ${icon}"></i> 
                <span>${forecastData.warning_message || 'UV Data unavailable'}</span>
            </div>
        `;
    }
}

function renderInsights(insights) {
    const container = document.getElementById('insights-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (!insights || insights.length === 0) {
        container.innerHTML = `<div class="insight-item info"><i class="fa-solid fa-circle-info"></i> No recent insights available.</div>`;
        return;
    }
    
    insights.forEach(insight => {
        let icon = 'fa-circle-info';
        let colorClass = 'info';
        
        if (insight.type === 'positive') { icon = 'fa-circle-check'; colorClass = 'positive'; }
        else if (insight.type === 'warning') { icon = 'fa-triangle-exclamation'; colorClass = 'warning'; }
        else if (insight.type === 'alert') { icon = 'fa-bell'; colorClass = 'alert'; }
        
        const el = document.createElement('div');
        el.className = `insight-item ${colorClass}`;
        el.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${insight.message}</span>`;
        container.appendChild(el);
    });
}
