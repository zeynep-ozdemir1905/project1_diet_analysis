// 1. Point to your LOCAL Flask server
const BASE_API = "http://127.0.0.1:3000/api";
const API_URL = `${BASE_API}/diet_results`; // High-speed Redis endpoint

let barChart, scatterChart, pieChart;

const dietColors = [
    'rgba(255, 99, 132, 0.8)',  // Pink (Dash)
    'rgba(54, 162, 235, 0.8)',  // Blue (Keto)
    'rgba(255, 206, 86, 0.8)',  // Yellow (Mediterranean)
    'rgba(75, 192, 192, 0.8)',  // Teal (Paleo)
    'rgba(153, 102, 255, 0.8)', // Purple (Vegan)
];

// --- AUTH UI TOGGLE HELPER ---
function updateAuthUI(isLoggedIn) {
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) logoutBtn.style.display = isLoggedIn ? "flex" : "none";
}

// --- MAIN FETCH DATA (CHARTS) ---
async function fetchAPIData() {
    const statusDiv = document.getElementById("displayContent");
    const resultsSection = document.getElementById("resultsDisplay");
    
    try {
        const response = await fetch(API_URL);

        if (response.status === 401) {
            window.location.href = "login.html";
            return;
        }

        const apiData = await response.json();

        // Handle the "Pending" state if the Blob Trigger hasn't run yet
        if (apiData.status === "pending") {
            resultsSection.style.display = "block";
            statusDiv.innerText = apiData.message;
            return;
        }

        updateAuthUI(true);

        const data = Object.keys(apiData).map(diet => ({
            Diet_type: diet.charAt(0).toUpperCase() + diet.slice(1),
            Protein: apiData[diet]["Protein(g)"] || 0,
            Carbs: apiData[diet]["Carbs(g)"] || 0,
            Fat: apiData[diet]["Fat(g)"] || 0
        }));

        renderCharts(data);

    } catch (error) {
        console.error("Error fetching API data:", error);
        resultsSection.style.display = "block";
        statusDiv.innerHTML = "Error: Backend server offline. Run 'python app.py'";
    }
}

// --- FETCH EXTRA DATA (RECIPES & CLUSTERS) ---
async function fetchExtraData(endpoint, title) {
    const resultsSection = document.getElementById("resultsDisplay");
    const displayTitle = document.getElementById("displayTitle");
    const displayContent = document.getElementById("displayContent");

    try {
        const response = await fetch(`${BASE_API}/${endpoint}`);
        
        if (response.status === 401) {
            alert("Session expired. Please log in again.");
            return;
        }

        const data = await response.json();
        
        resultsSection.style.display = "block";
        displayTitle.innerText = title;
        
        // Show the data in a clean JSON format
        displayContent.innerText = JSON.stringify(data, null, 2);
        
        // Scroll to the results
        resultsSection.scrollIntoView({ behavior: 'smooth' });

    } catch (err) {
        alert("Could not fetch " + title + ". Is the server running?");
    }
}

// --- RENDER CHARTS ---
function renderCharts(data) {
    if(barChart) barChart.destroy();
    if(scatterChart) scatterChart.destroy();
    if(pieChart) pieChart.destroy();

    const labels = data.map(d => d.Diet_type);

    // Bar Chart
    barChart = new Chart(document.getElementById('barChart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Avg Protein (g)',
                data: data.map(d => d.Protein),
                backgroundColor: dietColors 
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });

    // Scatter Chart
    scatterChart = new Chart(document.getElementById('scatterChart'), {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Protein vs Carbs',
                data: data.map(d => ({ x: d.Protein, y: d.Carbs })),
                backgroundColor: 'rgba(123, 31, 162, 1)'
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });

    // Pie Chart
    pieChart = new Chart(document.getElementById('pieChart'), {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: 'Avg Fat (g)',
                data: data.map(d => d.Fat),
                backgroundColor: dietColors
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

// --- EVENT LISTENERS ---
document.getElementById('getInsights').addEventListener('click', fetchAPIData);

document.getElementById('dietFilter').addEventListener('change', async (e) => {
    const selected = e.target.value;
    const response = await fetch(API_URL);
    if (response.status !== 200) return;
    
    const apiData = await response.json();
    const allData = Object.keys(apiData).map(diet => ({
        Diet_type: diet,
        Protein: apiData[diet]["Protein(g)"] || 0,
        Carbs: apiData[diet]["Carbs(g)"] || 0,
        Fat: apiData[diet]["Fat(g)"] || 0
    }));

    if(selected === "All") renderCharts(allData);
    else renderCharts(allData.filter(d => d.Diet_type.toLowerCase() === selected.toLowerCase()));
});

// UPDATED: Now calling the actual backend routes
document.getElementById('getRecipes').addEventListener('click', () => {
    window.location.href = "recipes.html";
});
document.getElementById('getClusters').addEventListener('click', () => {
    fetchExtraData('diet_results', 'Average Macros (Clustered by Diet)');
});

// Initial Load
fetchAPIData();