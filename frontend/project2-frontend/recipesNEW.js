async function loadRecipes() {
    const container = document.getElementById("recipesContainer");

    try {
        const res = await fetch("/api/get_recipes");

        console.log("STATUS:", res.status);

        const data = await res.json();
        console.log("DATA:", data);

        container.innerHTML = "";

        if (Array.isArray(data)) {
            data.forEach(r => {
                const div = document.createElement("div");
                div.style = "background:white;padding:10px;margin:10px;border-radius:8px;";

                div.innerHTML = `
                    <h3>${r.Recipe_name}</h3>
                    <p>Protein: ${r["Protein(g)"]}</p>
                    <p>Diet: ${r.Diet_type}</p>
                `;

                container.appendChild(div);
            });
        } else {
            container.innerText = JSON.stringify(data, null, 2);
        }

    } catch (err) {
        console.error("ERROR:", err);
        container.innerText = "Error loading recipes";
    }
}

loadRecipes();