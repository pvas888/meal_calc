


# meal_planner_app.py

import os
import pandas as pd
import streamlit as st

# 1. Load your CSV (assumes ingredients.csv lives in the repo root)
CSV_PATH = "ingredients.csv"
df = pd.read_csv(CSV_PATH).assign(
    Ingredient=lambda x: x["Ingredient"].str.strip(),
    Category=lambda x: x["Category"].str.strip()
)

# Detect which column has the calories
kcal_col = next(c for c in df.columns if "kcal" in c.lower())

# Build lookup maps
kcal_map = dict(zip(df["Ingredient"], df[kcal_col]))
categories = sorted(df["Category"].unique())
ings_by_cat = {
    cat: df[df["Category"] == cat]["Ingredient"].tolist()
    for cat in categories
}

# 2. Sidebar: Reset button
st.sidebar.title("Meal Planner Controls")
if st.sidebar.button("🔄 Reset All Fields"):
    st.session_state.clear()

# 3. Initialize session state for selections
if "selections" not in st.session_state:
    st.session_state.selections = {
        cat: [("None", 0.0) for _ in range(5)]
        for cat in categories
    }

# 4. Main UI
st.title("📋 Meal Planner")
total_kcal = 0.0

for cat in categories:
    st.subheader(cat)
    cols = st.columns([2, 1])
    cat_kcal = 0.0

    # Render 5 ingredient selectors per category
    for i in range(5):
        current_ing, current_g = st.session_state.selections[cat][i]

        # Ingredient dropdown
        sel_ing = cols[0].selectbox(
            label=f"Option {i+1}",
            options=["None"] + ings_by_cat[cat],
            index=0 if current_ing not in ings_by_cat[cat]
                  else ings_by_cat[cat].index(current_ing) + 1,
            key=f"{cat}_{i}_ing"
        )

        # Grams input
        sel_g = cols[1].number_input(
            label="g",
            min_value=0.0,
            value=current_g,
            step=5.0,
            key=f"{cat}_{i}_g"
        )

        # Store back in session state
        st.session_state.selections[cat][i] = (sel_ing, sel_g)

        # Calculate calories for this line
        if sel_ing != "None":
            cat_kcal += sel_g * kcal_map.get(sel_ing, 0.0) / 100.0

    total_kcal += cat_kcal
    st.metric(label=f"{cat} kcal", value=f"{cat_kcal:.1f}")

st.markdown("---")
st.subheader(f"Total Meal Calories: {total_kcal:.1f} kcal")

# In[ ]:



