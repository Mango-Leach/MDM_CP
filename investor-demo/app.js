document.addEventListener('DOMContentLoaded', () => {
    const syncBtn = document.getElementById('sync-btn');
    const valHydration = document.getElementById('val-hydration');
    const valUv = document.getElementById('val-uv');
    const valScore = document.getElementById('val-score');
    const valState = document.getElementById('val-state');
    const scoreRing = document.getElementById('score-ring');
    const resultsContainer = document.getElementById('product-results');
    const loadingSpinner = document.getElementById('loading-spinner');

    const API_URL = 'http://localhost:8000/api/latest';
    let pollingInterval = null;
    let lastRenderedScore = null;

    // SVG Ring properties
    const radius = scoreRing.r.baseVal.value;
    const circumference = radius * 2 * Math.PI;
    scoreRing.style.strokeDasharray = `${circumference} ${circumference}`;
    scoreRing.style.strokeDashoffset = `${circumference}`;

    function setProgress(percent) {
        const offset = circumference - (percent / 100) * circumference;
        scoreRing.style.strokeDashoffset = offset;
    }

    async function pollLatestData() {
        try {
            const response = await fetch(API_URL);
            if (!response.ok) return;

            const result = await response.json();
            if (result.status === "active" && result.data) {
                const data = result.data;
                loadingSpinner.classList.add('hidden');

                // Prevent re-animating if data hasn't changed
                if (lastRenderedScore === data.skin_score) return;
                lastRenderedScore = data.skin_score;

                // Animate metrics rolling up
                animateValue(valHydration, 0, data.hydration_percentage, 1000, '%');
                animateValue(valUv, 0, data.uv_index, 1000, ' UVI', true);
                animateValue(valScore, 0, data.skin_score, 1500, '');
                
                setTimeout(() => {
                    setProgress(data.skin_score);
                    valState.textContent = data.state_detected;
                    
                    // Color logic
                    if(data.state_detected === "Optimal") valState.className = "state-good";
                    else if(data.state_detected === "UV-Stressed") valState.className = "state-warn";
                    else valState.className = "state-bad";
                }, 500);

                renderProducts(data.recommendations);
            }
        } catch (error) {
            console.log("Polling error (Server might be down)");
        }
    }

    function toggleHardwareSync() {
        if(pollingInterval) {
            // Disable Sync
            clearInterval(pollingInterval);
            pollingInterval = null;
            syncBtn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i> Connect to Node';
            syncBtn.style.border = "1px solid rgba(0, 243, 255, 0.4)";
        } else {
            // Enable Sync
            syncBtn.innerHTML = '<i class="fa-solid fa-satellite-dish fa-spin"></i> Live Streaming...';
            syncBtn.style.border = "1px solid #00ff88"; // Green means active
            lastRenderedScore = null; // Reset
            resultsContainer.innerHTML = '';
            loadingSpinner.classList.remove('hidden');
            
            // Start Polling every 2 seconds
            pollLatestData();
            pollingInterval = setInterval(pollLatestData, 2000);
        }
    }

    function renderProducts(products) {
        resultsContainer.innerHTML = '';
        if (!products || products.length === 0) {
            resultsContainer.innerHTML = '<div class="empty-state"><p>No specific interventions found.</p></div>';
            return;
        }

        products.forEach((prod, index) => {
            const card = document.createElement('div');
            card.className = 'product-card';
            card.style.animationDelay = `${index * 0.15}s`;

            const ingredientsHTML = prod.key_ingredients.map(i => 
                `<span class="ingredient-tag">${i}</span>`
            ).join('');

            card.innerHTML = `
                <div class="product-brand">${prod.brand}</div>
                <div class="product-name">${prod.product_name}</div>
                <div class="product-confidence">
                    <i class="fa-solid fa-check-double"></i> Match Confidence: ${Math.round(prod.match_confidence * 100)}%
                </div>
                <div class="ingredients-list">
                    ${ingredientsHTML}
                </div>
            `;
            resultsContainer.appendChild(card);
        });
    }

    // Utility animate numbers
    function animateValue(obj, start, end, duration, suffix, isFloat=false) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            
            let current = progress * (end - start) + start;
            if(!isFloat) current = Math.floor(current);
            else current = current.toFixed(1);

            obj.innerHTML = current + suffix;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    syncBtn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i> Connect to Node';
    syncBtn.addEventListener('click', toggleHardwareSync);
});
