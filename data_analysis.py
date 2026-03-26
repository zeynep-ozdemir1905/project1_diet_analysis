import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# -----------------------------
# 1. Load Dataset
# -----------------------------
# Updated to match your actual filename
df = pd.read_csv("All_Diets.csv")

# -----------------------------
# 2. Clean Data (Handle Missing Values)
# -----------------------------
numeric_cols = ['Protein(g)', 'Carbs(g)', 'Fat(g)']
# Using transform to fill NaNs with the mean of their specific Diet_type for better accuracy
df[numeric_cols] = df.groupby('Diet_type')[numeric_cols].transform(lambda x: x.fillna(x.mean()))

# -----------------------------
# 3. Average Macronutrients per Diet Type
# -----------------------------
avg_macros = df.groupby('Diet_type')[numeric_cols].mean()
print("\nAverage Macronutrients by Diet Type:")
print(avg_macros)

# -----------------------------
# 4. Top 5 Protein-Rich Recipes per Diet
# -----------------------------
top_protein_recipes = (
    df.sort_values('Protein(g)', ascending=False)
      .groupby('Diet_type')
      .head(5)
)

top_protein_recipes.to_csv("top_protein_recipes.csv", index=False)
print("\nTop 5 protein-rich recipes saved successfully!")

# -----------------------------
# 5. Diet with Highest Protein Content
# -----------------------------
highest_protein_diet = avg_macros['Protein(g)'].idxmax()
print(f"\nDiet type with highest average protein: {highest_protein_diet}")

# -----------------------------
# 6. Most Common Cuisine per Diet Type
# -----------------------------
# Updated 'Cuisine' to 'Cuisine_type'
common_cuisines = (
    df.groupby('Diet_type')['Cuisine_type']
      .agg(lambda x: x.value_counts().idxmax())
)

print("\nMost common cuisines by diet type:")
print(common_cuisines)

# -----------------------------
# 7. Create New Metrics
# -----------------------------
df['Protein_to_Carbs_ratio'] = df['Protein(g)'] / df['Carbs(g)']
df['Carbs_to_Fat_ratio'] = df['Carbs(g)'] / df['Fat(g)']

# -----------------------------
# 8. Visualization: Bar Chart
# -----------------------------
# Improved plotting logic to ensure the figure size applies correctly
ax = avg_macros.plot(kind='bar', figsize=(10, 6))
plt.title("Average Macronutrient Content by Diet Type")
plt.ylabel("Grams")
plt.xlabel("Diet Type")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("avg_macronutrients_bar_chart.png")
plt.close()

# -----------------------------
# 9. Visualization: Heatmap
# -----------------------------
plt.figure(figsize=(8, 6))
sns.heatmap(avg_macros, annot=True, cmap="YlGnBu", fmt=".2f")
plt.title("Heatmap of Macronutrients by Diet Type")
plt.tight_layout()
plt.savefig("macronutrient_heatmap.png")
plt.close()

# -----------------------------
# 10. Visualization: Scatter Plot
# -----------------------------
# Updated 'Cuisine' to 'Cuisine_type'
plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=top_protein_recipes,
    x='Protein(g)',
    y='Carbs(g)',
    hue='Cuisine_type',
    style='Diet_type',
    s=100
)
plt.title("Top 5 Protein-Rich Recipes by Cuisine")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig("top_protein_scatter_plot.png")
plt.close()

print("\nAll visualizations saved successfully!")
