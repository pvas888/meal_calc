# meal_planner_app.py

import pandas as pd
import streamlit as st

# 1. Configure page for full-width layout and boost max-width via CSS
st.set_page_config(page_title="Meal Planner", layout="wide")
st.markdown(
    """
    <style>
      /* Expand main content max-width */
      div[data-testid="stAppViewContainer"] > .main {
        max-width: 1800px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# 2. Load or initialize the ingredients DataFrame in session state
if "df" not in st.session_state:
    df = (
        pd.read_csv("ingredients.csv")
          .assign(
              Ingredient=lambda x: x["Ingredient"].str.strip(),
              Category=lambda x: x["Category"].str.strip(),
          )
    )
    st.session_state.df = df
else:
    df = st.session_state.df

# Identify the calorie column (containing "kcal")
kcal_col = next(col for col in df.columns if "kcal" in col.lower())

# 3. Sidebar: Reset button, Add-New-Ingredient form, Download CSV
st.sidebar.title("Meal Planner Controls")

# Reset all fields & ingredients
if st.sidebar.button("🔄 Reset All Fields"):
    for key in ["df", "selections"]:
        st.session_state.pop(key, None)
    st.experimental_rerun()

# Add new ingredient
with st.sidebar.expander("➕ Add New Ingredient", expanded=True):
    new_name = st.text_input("Ingredient Name")
    new_cat  = st.text_input("Category")
    new_kcal = st.number_input(
        "Calories per 100 g", min_value=0.0, step=1.0, value=0.0
    )
    if st.button("Add Ingredient"):
        if not new_name.strip():
            st.error("Enter a valid ingredient name.")
        elif not new_cat.strip():
            st.error("Enter a valid category.")
        elif new_kcal <= 0:
            st.error("Calories must be greater than zero.")
        else:
            # Append to in-memory DataFrame
            new_row = {
                "Ingredient": new_name.strip(),
                "Category":   new_cat.strip(),
                kcal_col:     new_kcal,
            }
            st.session_state.df = pd.concat(
                [st.session_state.df, pd.DataFrame([new_row])],
                ignore_index=True
            )
            st.success(f"Added '{new_name}' under '{new_cat}'.")
            # Rerun so new ingredient appears immediately
            st.experimental_rerun()

# Download updated CSV
csv_bytes = st.session_state.df.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(
    label="📥 Download Ingredients CSV",
    data=csv_bytes,
    file_name="ingredients_updated.csv",
    mime="text/csv",
)

# 4. Build lookups from DataFrame
df = st.session_state.df
kcal_map   = dict(zip(df["Ingredient"], df[kcal_col]))
categories = sorted(df["Category"].unique())
ings_by_cat = {
    cat: df[df["Category"] == cat]["Ingredient"].tolist()
    for cat in categories
}

# 5. Initialize or restore meal selections in session state
if "selections" not in st.session_state:
    st.session_state.selections = {
        cat: [("None", 0.0) for _ in range(5)]
        for cat in categories
    }

# 6. Main UI: Render all categories in equal-width columns
st.title("📋 Meal Planner")
total_kcal = 0.0

# Create one column per category, equally weighted
cols = st.columns([1] * len(categories))

for col, cat in zip(cols, categories):
    with col:
        st.subheader(cat)
        cat_kcal = 0.0

        for i in range(5):
            curr_ing, curr_g = st.session_state.selections[cat][i]

            # Ingredient selector
            sel_ing = st.selectbox(
                label=f"Option {i+1}",
                options=["None"] + ings_by_cat[cat],
                index=(
                    0
                    if curr_ing not in ings_by_cat[cat]
                    else ings_by_cat[cat].index(curr_ing) + 1
                ),
                key=f"{cat}_{i}_ing"
            )

            # Grams input
            sel_g = st.number_input(
                label="g",
                min_value=0.0,
                value=curr_g,
                step=5.0,
                key=f"{cat}_{i}_g"
            )

            # Store back in session state
            st.session_state.selections[cat][i] = (sel_ing, sel_g)

            # Accumulate calories for this category
            if sel_ing != "None":
                cat_kcal += sel_g * kcal_map.get(sel_ing, 0.0) / 100.0

        total_kcal += cat_kcal
        st.metric(label=f"{cat} kcal", value=f"{cat_kcal:.1f}")

# 7. Display total calories
st.markdown("---")
st.subheader(f"Total Meal Calories: {total_kcal:.1f} kcal")
