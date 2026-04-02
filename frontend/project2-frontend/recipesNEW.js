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

function applyFilters() {
    const keyword = document.getElementById("searchInput").value.toLowerCase();
    const diet = document.getElementById("dietFilterRecipes").value;
    const sort = document.getElementById("sortSelect").value;

    let filtered = allRecipes.filter(r => {
        const matchesKeyword = r.Recipe_name.toLowerCase().includes(keyword);
        const matchesDiet = diet === "All" || r.Diet_type === diet;
        return matchesKeyword && matchesDiet;
    });

    if (sort === "protein_desc") filtered.sort((a, b) => b["Protein(g)"] - a["Protein(g)"]);
    else if (sort === "protein_asc") filtered.sort((a, b) => a["Protein(g)"] - b["Protein(g)"]);
    else if (sort === "calories_desc") filtered.sort((a, b) => b["Calories"] - a["Calories"]);
    else if (sort === "calories_asc") filtered.sort((a, b) => a["Calories"] - b["Calories"]);

    renderRecipes(filtered);
}

// Event listeners
document.getElementById("searchInput").addEventListener("input", applyFilters);
document.getElementById("dietFilterRecipes").addEventListener("change", applyFilters);
document.getElementById("sortSelect").addEventListener("change", applyFilters);

loadRecipes();