let allRecipes = [];

async function loadRecipes() {
    const container = document.getElementById("recipesContainer");

    try {
        const res = await fetch("/api/get_recipes");
        const data = await res.json();
        allRecipes = Array.isArray(data) ? data : [];
        renderRecipes(allRecipes);
    } catch (err) {
        console.error("ERROR:", err);
        container.innerText = "Error loading recipes";
    }
}

function renderRecipes(data) {
    const container = document.getElementById("recipesContainer");
    container.innerHTML = "";

    if (!data.length) {
        container.innerText = "No recipes found.";
        return;
    }

    data.forEach(r => {
        const div = document.createElement("div");
        div.style = "background:white;padding:15px;margin:10px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);";
        div.innerHTML = `
            <h3>${r.Recipe_name}</h3>
            <p><strong>Diet:</strong> ${r.Diet_type}</p>
            <p><strong>Protein:</strong> ${r["Protein(g)"]}g</p>
            <p><strong>Carbs:</strong> ${r["Carbs(g)"]}g</p>
            <p><strong>Fat:</strong> ${r["Fat(g)"]}g</p>
            <p><strong>Calories:</strong> ${r["Calories"] || "N/A"}</p>
        `;
        container.appendChild(div);
    });
}


const PAGE_SIZE = 10;
let currentPage = 1;

function renderRecipes(data) {
    const container = document.getElementById("recipesContainer");
    container.innerHTML = "";

    const totalPages = Math.ceil(data.length / PAGE_SIZE);
    const paginated = data.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

    paginated.forEach(r => {
        const div = document.createElement("div");
        div.style = "background:white;padding:15px;margin:10px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1);";
        div.innerHTML = `
            <h3>${r.Recipe_name}</h3>
            <p><strong>Diet:</strong> ${r.Diet_type}</p>
            <p><strong>Protein:</strong> ${r["Protein(g)"]}g</p>
            <p><strong>Carbs:</strong> ${r["Carbs(g)"]}g</p>
            <p><strong>Fat:</strong> ${r["Fat(g)"]}g</p>
        `;
        container.appendChild(div);
    });

    // Pagination controls
    const controls = document.createElement("div");
    controls.style = "text-align:center;margin:20px;";
    controls.innerHTML = `
        <button onclick="changePage(-1)" ${currentPage === 1 ? 'disabled' : ''} 
            style="padding:8px 16px;margin:5px;border-radius:6px;cursor:pointer;">Previous</button>
        <span>Page ${currentPage} of ${totalPages}</span>
        <button onclick="changePage(1)" ${currentPage === totalPages ? 'disabled' : ''}
            style="padding:8px 16px;margin:5px;border-radius:6px;cursor:pointer;">Next</button>
    `;
    container.appendChild(controls);
}

function changePage(direction) {
    currentPage += direction;
    applyFilters();
}

// Reset to page 1 when filters change
function applyFilters() {
    currentPage = 1; // remove this line from applyFilters and keep it only in changePage

}

function applyFilters() {
    const keyword = document.getElementById("searchInput").value.toLowerCase();
    const diet = document.getElementById("dietFilterRecipes").value;

    let filtered = allRecipes.filter(r => {
        const matchesKeyword = r.Recipe_name.toLowerCase().includes(keyword);
        const matchesDiet = diet === "All" || r.Diet_type === diet;
        return matchesKeyword && matchesDiet;
    });

    renderRecipes(filtered);
}

// Event listeners
document.getElementById("searchInput").addEventListener("input", applyFilters);
document.getElementById("dietFilterRecipes").addEventListener("change", applyFilters);

loadRecipes();