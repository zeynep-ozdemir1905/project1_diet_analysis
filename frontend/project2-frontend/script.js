// 1. Point to your LOCAL Flask server for Phase 3 Security
const API_URL = "http://127.0.0.1:3000/api/analyze_data";

let barChart, scatterChart, pieChart, heatmapChart;

const dietColors = [
    'rgba(255, 99, 132, 0.8)',  // Pink (Dash)
    'rgba(54, 162, 235, 0.8)',  // Blue (Keto)
    'rgba(255, 206, 86, 0.8)',  // Yellow (Mediterranean)
    'rgba(75, 192, 192, 0.8)',  // Teal (Paleo)
    'rgba(153, 102, 255, 0.8)', // Purple (Vegan)
    'rgba(255, 159, 64, 0.8)'   // Orange (Other)
];

// --- AUTH UI TOGGLE HELPER ---
// This handles the UX by showing/hiding buttons based on login status
function updateAuthUI(isLoggedIn) {
    const loginBtn = document.getElementById("loginBtn");
    const logoutBtn = document.getElementById("logoutBtn");

    if (isLoggedIn) {
        if (loginBtn) loginBtn.style.display = "none";
        if (logoutBtn) logoutBtn.style.display = "flex"; 
    } else {
        if (loginBtn) loginBtn.style.display = "flex"; 
        if (logoutBtn) logoutBtn.style.display = "none";
    }
}

// Fetch data through Local Backend (Flask)
async function fetchAPIData() {
    const statusDiv = document.getElementById("executionTime");
    const chartsContainer = document.getElementById("chartsContainer"); 
    
    if (statusDiv) statusDiv.innerHTML = "<span style='color: #007BFF;'>Verifying Security Handshake...</span>";
    
    const startTime = performance.now(); 
    try {
        const response = await fetch(API_URL);

        // 2. Security Check: If unauthorized (401), lock the UI and show Login button
        if (response.status === 401) {
            updateAuthUI(false);
            if (chartsContainer) {
                chartsContainer.style.opacity = "0.2";
                chartsContainer.style.pointerEvents = "none";
            }
            if (statusDiv) statusDiv.innerHTML = "<span style='color:red;'>⚠️ Access Denied: Please Login with GitHub to view insights.</span>";
            return;
        }

        // 3. Authorized: Show Logout button and process data
        const apiData = await response.json();
        updateAuthUI(true);

        const data = Object.keys(apiData).map(diet => {
            const entry = apiData[diet];
            return {
                Diet_type: diet.charAt(0).toUpperCase() + diet.slice(1),
                Protein: entry["Protein(g)"] || entry["protein(g)"] || 0,
                Carbs: entry["Carbs(g)"] || entry["carbs(g)"] || 0,
                Fat: entry["Fat(g)"] || entry["fat(g)"] || 0
            };
        });

        // Restore UI Visibility
        if (chartsContainer) {
            chartsContainer.style.opacity = "1";
            chartsContainer.style.pointerEvents = "auto";
        }

        renderCharts(data);

        const endTime = performance.now();
        const execTime = (endTime - startTime).toFixed(2);
        if (statusDiv) statusDiv.innerText = `Success! Execution Time: ${execTime} ms`;

    } catch (error) {
        console.error("Error fetching API data:", error);
        updateAuthUI(false);
        if (statusDiv) statusDiv.innerHTML = "<span style='color: red;'>Error: Authentication server offline. Run 'python app.py'</span>";
    }
}

// --- RENDER CHARTS LOGIC ---
function renderCharts(data) {
    if(barChart) barChart.destroy();
    if(scatterChart) scatterChart.destroy();
    if(pieChart) pieChart.destroy();
    if(heatmapChart) heatmapChart.destroy();

    const labels = data.map(d => d.Diet_type);

    // Bar Chart
    const barCtx = document.getElementById('barChart').getContext('2d');
    barChart = new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Protein (g)',
                data: data.map(d => d.Protein),
                backgroundColor: dietColors 
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
    });

    // Scatter Chart
    const scatterCtx = document.getElementById('scatterChart').getContext('2d');
    scatterChart = new Chart(scatterCtx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Protein vs Carbs',
                data: data.map(d => ({ x: d.Protein, y: d.Carbs })),
                backgroundColor: 'rgba(123, 31, 162, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'Protein (g)' } },
                y: { title: { display: true, text: 'Carbs (g)' } }
            }
        }
    });

    // Pie Chart
    const pieCtx = document.getElementById('pieChart').getContext('2d');
    pieChart = new Chart(pieCtx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: 'Fat Distribution',
                data: data.map(d => d.Fat),
                backgroundColor: dietColors
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });

    renderHeatmap(data);
}

function renderHeatmap(data) {
    console.log("Heatmap ready.");
}

// --- FILTER & LISTENERS ---
document.getElementById('dietFilter').addEventListener('change', async (e) => {
    const selected = e.target.value;
    const response = await fetch(API_URL);
    if (response.status === 401) return; 
    
    const apiData = await response.json();
    const allData = Object.keys(apiData).map(diet => ({
        Diet_type: diet,
        Protein: apiData[diet]["Protein(g)"] || apiData[diet]["protein(g)"] || 0,
        Carbs: apiData[diet]["Carbs(g)"] || apiData[diet]["carbs(g)"] || 0,
        Fat: apiData[diet]["Fat(g)"] || apiData[diet]["fat(g)"] || 0
    }));

    if(selected === "All") renderCharts(allData);
    else renderCharts(allData.filter(d => d.Diet_type.toLowerCase() === selected.toLowerCase()));
});

document.getElementById('getInsights').addEventListener('click', fetchAPIData);

// Placeholders for your other buttons
if (document.getElementById('getRecipes')) {
    document.getElementById('getRecipes').addEventListener('click', () => alert("Recipe generation coming soon!"));
}
if (document.getElementById('getClusters')) {
    document.getElementById('getClusters').addEventListener('click', () => alert("Clustering logic triggered!"));
}

// Initial Trigger on page load
fetchAPIData();