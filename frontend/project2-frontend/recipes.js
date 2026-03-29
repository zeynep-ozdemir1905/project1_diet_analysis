async function loadRecipes() {
    const container = document.getElementById("recipesContainer");

    try {
        const res = await fetch("http://127.0.0.1:3000/api/top_protein_recipes");
        const data = await res.json();

        console.log("DATA:", data); // DEBUG

        container.innerHTML = "";

        // Case 1: array (correct)
        if (Array.isArray(data)) {
            data.forEach(r => {
                container.innerHTML += `
                    <div style="background:white;padding:10px;margin:10px;border-radius:8px;">
                        <h3>${r.Recipe_name}</h3>
                        <p>Protein: ${r["Protein(g)"]}</p>
                        <p>Diet: ${r.Diet_type}</p>
                    </div>
                `;
            });
        } 
        // Case 2: object (wrong structure fallback)
        else {
            container.innerText = JSON.stringify(data, null, 2);
        }

    } catch (err) {
        console.error(err);
        container.innerText = "Error loading recipes";
    }
}

loadRecipes();