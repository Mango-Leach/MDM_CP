document.addEventListener('DOMContentLoaded', () => {
    // ─── ROUTING & VIEW LOGIC ───
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.view');

    function switchView(viewId) {
        // Update nav active state
        navItems.forEach(item => {
            if (item.getAttribute('data-view') === viewId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Hide all views, show selected
        views.forEach(view => {
            if (view.id === `view-${viewId}`) {
                view.classList.add('active');
                // Trigger animation reset
                view.style.animation = 'none';
                view.offsetHeight; /* trigger reflow */
                view.style.animation = null; 
            } else {
                view.classList.remove('active');
            }
        });

        // Update URL hash
        window.location.hash = viewId;
    }

    // Handle hash change for browser back/forward
    window.addEventListener('hashchange', () => {
        const hash = window.location.hash.substring(1) || 'dashboard';
        switchView(hash);
    });

    // Handle initial load
    const initialHash = window.location.hash.substring(1) || 'dashboard';
    switchView(initialHash);

    // Nav click handlers
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const viewId = item.getAttribute('data-view');
            switchView(viewId);
        });
    });

    // ─── BACKGROUND PARTICLES INTERACTIVITY ───
    const particlesContainer = document.getElementById('particles');
    const particleCount = 30;
    const particles = [];

    for (let i = 0; i < particleCount; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        const size = Math.random() * 5 + 2;
        p.style.width = `${size}px`;
        p.style.height = `${size}px`;
        p.style.left = `${Math.random() * 100}vw`;
        p.style.top = `${Math.random() * 100}vh`;
        p.dataset.speedX = (Math.random() - 0.5) * 2;
        p.dataset.speedY = (Math.random() - 0.5) * 2;
        particlesContainer.appendChild(p);
        particles.push(p);
    }

    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;

    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    function animateParticles() {
        particles.forEach(p => {
            const rect = p.getBoundingClientRect();
            const dx = mouseX - (rect.left + rect.width / 2);
            const dy = mouseY - (rect.top + rect.height / 2);
            const dist = Math.sqrt(dx * dx + dy * dy);

            // Move away from mouse if close
            if (dist < 150) {
                p.style.transform = `translate(${dx * -0.2}px, ${dy * -0.2}px)`;
            } else {
                p.style.transform = `translate(0, 0)`;
            }
        });
        requestAnimationFrame(animateParticles);
    }
    animateParticles();

    // ─── DASHBOARD LOGIC (Adapted from existing) ───
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

    if (scoreRing) {
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

                    if (lastRenderedScore === data.skin_score) return;
                    lastRenderedScore = data.skin_score;

                    animateValue(valHydration, parseFloat(valHydration.innerText) || 0, data.hydration_percentage, 500, '%');
                    animateValue(valUv, parseFloat(valUv.innerText) || 0, data.uv_index, 500, ' UVI', true);
                    animateValue(valScore, parseFloat(valScore.innerText) || 0, data.skin_score, 500, '');
                    
                    setProgress(data.skin_score);
                    valState.textContent = data.state_detected;
                    
                    if(data.state_detected === "Optimal") valState.className = "state-good";
                    else if(data.state_detected === "UV-Stressed") valState.className = "state-warn";
                    else valState.className = "state-bad";

                    renderProducts(data.recommendations);
                }
            } catch (error) {
                console.log("Polling error (Server might be down)");
            }
        }

        async function fetchDashboardData() {
            try {
                const histRes = await fetch('http://localhost:8000/api/history?days=7');
                if (histRes.ok) {
                    const histData = await histRes.json();
                    if (typeof renderTrendChart === 'function') {
                        renderTrendChart(histData.readings);
                    }
                }

                const insRes = await fetch('http://localhost:8000/api/insights?days=7');
                if (insRes.ok) {
                    const insData = await insRes.json();
                    if (typeof renderInsights === 'function') {
                        renderInsights(insData.trends);
                    }
                }

                const uvRes = await fetch('http://localhost:8000/api/uv-forecast');
                if (uvRes.ok) {
                    const uvData = await uvRes.json();
                    if (typeof renderUVForecast === 'function') {
                        renderUVForecast(uvData);
                    }
                }
            } catch (error) {
                console.log("Error fetching background dashboard data:", error);
            }
        }

        function toggleHardwareSync() {
            if(pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
                syncBtn.classList.remove('active-sync');
                syncBtn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i> <span>Hardware Sync</span>';
            } else {
                syncBtn.classList.add('active-sync');
                syncBtn.innerHTML = '<i class="fa-solid fa-satellite-dish fa-spin"></i> <span>Live Streaming...</span>';
                lastRenderedScore = null;
                resultsContainer.innerHTML = '';
                loadingSpinner.classList.remove('hidden');
                
                pollLatestData();
                pollingInterval = setInterval(pollLatestData, 1000);
                
                fetchDashboardData();
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
                        <i class="fa-solid fa-check-double"></i> Match: ${Math.round(prod.match_confidence * 100)}%
                    </div>
                    <div class="ingredients-list">
                        ${ingredientsHTML}
                    </div>
                `;
                resultsContainer.appendChild(card);
            });
        }

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

        syncBtn.addEventListener('click', toggleHardwareSync);
    }

    // ─── PROFILE LOGIC ───
    const profileForm = document.getElementById('profile-form');
    const saveStatus = document.getElementById('profile-save-status');

    if (profileForm) {
        // Load existing profile
        fetch('http://localhost:8000/api/profile')
            .then(res => res.json())
            .then(data => {
                if (data.status === 'active' && data.profile) {
                    document.getElementById('profile-type').value = data.profile.skin_type || 'Normal';
                    document.getElementById('profile-age').value = data.profile.age || '';
                    document.getElementById('profile-sensitivities').value = (data.profile.sensitivities || []).join(', ');
                    document.getElementById('profile-allergies').value = (data.profile.allergy_ingredients || []).join(', ');
                }
            })
            .catch(err => console.error("Could not load profile:", err));

        profileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const sensitivitiesInput = document.getElementById('profile-sensitivities').value;
            const allergiesInput = document.getElementById('profile-allergies').value;

            const payload = {
                skin_type: document.getElementById('profile-type').value,
                age: parseInt(document.getElementById('profile-age').value) || null,
                sensitivities: sensitivitiesInput ? sensitivitiesInput.split(',').map(s => s.trim()) : [],
                allergy_ingredients: allergiesInput ? allergiesInput.split(',').map(s => s.trim()) : []
            };

            try {
                const res = await fetch('http://localhost:8000/api/profile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (res.ok) {
                    saveStatus.classList.remove('hidden');
                    setTimeout(() => saveStatus.classList.add('hidden'), 3000);
                }
            } catch (err) {
                console.error("Failed to save profile", err);
            }
        });
    }

});
