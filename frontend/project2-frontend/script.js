// Azure API endpoint 
const API_URL = "https://diet-analysis-api-v2.azurewebsites.net/api/analyze_data";

let barChart, scatterChart, pieChart, heatmapChart;

// 1. Define unique colors for each diet type
const dietColors = [
    'rgba(255, 99, 132, 0.8)',  // Pink (Dash)
    'rgba(54, 162, 235, 0.8)',  // Blue (Keto)
    'rgba(255, 206, 86, 0.8)',  // Yellow (Mediterranean)
    'rgba(75, 192, 192, 0.8)',  // Teal (Paleo)
    'rgba(153, 102, 255, 0.8)', // Purple (Vegan)
    'rgba(255, 159, 64, 0.8)'   // Orange (Other)
];

// Fetch data from Azure Function API
async function fetchAPIData() {
    const statusDiv = document.getElementById("executionTime");
    if (statusDiv) statusDiv.innerHTML = "<span style='color: #007BFF;'>Waking up Azure API... please wait.</span>";
    
    const startTime = performance.now(); 
    try {
        const response = await fetch(API_URL);
        const apiData = await response.json();

        // 2. Transform API response with "Key Safety"
        // This ensures that even if Python sends "protein(g)" or "Protein(g)", the JS finds it.
        const data = Object.keys(apiData).map(diet => {
            const entry = apiData[diet];
            return {
                Diet_type: diet.charAt(0).toUpperCase() + diet.slice(1),
                Protein: entry["Protein(g)"] || entry["protein(g)"] || 0,
                Carbs: entry["Carbs(g)"] || entry["carbs(g)"] || 0,
                Fat: entry["Fat(g)"] || entry["fat(g)"] || 0
            };
        });

        console.log("Verified Unique Data:", data);
        renderCharts(data);

        const endTime = performance.now();
        const execTime = (endTime - startTime).toFixed(2);
        if (statusDiv) statusDiv.innerText = `Success! Execution Time: ${execTime} ms`;

    } catch (error) {
        console.error("Error fetching API data:", error);
        if (statusDiv) statusDiv.innerHTML = "<span style='color: red;'>Failed to load data. The API might be sleeping.</span>";
    }
}

// Render Charts
function renderCharts(data) {
    if(barChart) barChart.destroy();
    if(scatterChart) scatterChart.destroy();
    if(pieChart) pieChart.destroy();
    if(heatmapChart) heatmapChart.destroy();

    const labels = data.map(d => d.Diet_type);

    // 3. Bar Chart Fix: Uses the dietColors array
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
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true } }
        }
    });

    // 4. Scatter Plot
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

    // 5. Pie Chart Fix: Uses the dietColors array
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
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // 6. Heatmap Placeholder
    renderHeatmap(data);
}

function renderHeatmap(data) {
    const heatCtx = document.getElementById('heatmapChart').getContext('2d');
    // Basic Heatmap text placeholder or logic here
    console.log("Heatmap data ready for matrix rendering.");
}

// Filter functionality
document.getElementById('dietFilter').addEventListener('change', async (e) => {
    const selected = e.target.value;
    const response = await fetch(API_URL);
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

// API button listeners
document.getElementById('getInsights').addEventListener('click', fetchAPIData);
document.getElementById('getRecipes').addEventListener('click', () => alert("Recipe generation coming soon!"));
document.getElementById('getClusters').addEventListener('click', () => alert("Clustering logic triggered!"));

// Initial Trigger
fetchAPIData();
