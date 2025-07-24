import pandas as pd
import streamlit as st

# 1. Load or initialize the ingredients DataFrame in session state
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

# Identify the calorie column
kcal_col = next(col for col in df.columns if "kcal" in col.lower())

# 2. Sidebar: Reset button, Add-Ingredient form, Download CSV
st.sidebar.title("Meal Planner Controls")

if st.sidebar.button("🔄 Reset All Fields"):
    for key in ["df", "selections"]:
        st.session_state.pop(key, None)
    st.experimental_rerun()

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
            st.error("Calories must be > 0.")
        else:
            new_row = {
                "Ingredient": new_name.strip(),
                "Category":   new_cat.strip(),
                kcal_col:     new_kcal,
            }
            st.session_state.df = pd.concat(
                [st.session_state.df, pd.DataFrame([new_row])],
                ignore_index=True,
            )
            st.success(f"{new_name} added under {new_cat}.")
            st.experimental_rerun()

csv_data = st.session_state.df.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(
    "📥 Download Ingredients CSV",
    data=csv_data,
    file_name="ingredients_updated.csv",
    mime="text/csv",
)

# 3. Prepare lookups from (possibly updated) DataFrame
df = st.session_state.df
kcal_map   = dict(zip(df["Ingredient"], df[kcal_col]))
categories = sorted(df["Category"].unique())
ings_by_cat = {
    cat: df[df["Category"] == cat]["Ingredient"].tolist()
    for cat in categories
}

# 4. Initialize meal selections in session state
if "selections" not in st.session_state:
    st.session_state.selections = {
        cat: [("None", 0.0) for _ in range(5)] for cat in categories
    }

# 5. Main UI: Two-column layout for categories
st.title("📋 Meal Planner")
total_kcal = 0.0

# Pair categories two-by-two
pairs = [categories[i : i + 2] for i in range(0, len(categories), 2)]
for pair in pairs:
    cols = st.columns(7)
    for col, cat in zip(cols, pair):
        with col:
            st.subheader(cat)
            cat_kcal = 0.0
            for i in range(5):
                curr_ing, curr_g = st.session_state.selections[cat][i]

                sel_ing = st.selectbox(
                    f"Option {i+1}",
                    ["None"] + ings_by_cat[cat],
                    index=(
                        0
                        if curr_ing not in ings_by_cat[cat]
                        else ings_by_cat[cat].index(curr_ing) + 1
                    ),
                    key=f"{cat}_{i}_ing",
                )

                sel_g = st.number_input(
                    "g",
                    min_value=0.0,
                    value=curr_g,
                    step=5.0,
                    key=f"{cat}_{i}_g",
                )

                st.session_state.selections[cat][i] = (sel_ing, sel_g)
                if sel_ing != "None":
                    cat_kcal += sel_g * kcal_map.get(sel_ing, 0.0) / 100.0

            total_kcal += cat_kcal
            st.metric(f"{cat} kcal", f"{cat_kcal:.1f}")

st.markdown("---")
st.subheader(f"Total Meal Calories: {total_kcal:.1f} kcal")
