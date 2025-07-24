#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

# Cell 1: Imports, CSV load & mappings, ScrollableFrame

CSV_PATH = r"C:\Users\pvas888\Desktop\ingredients.csv"
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"Cannot find CSV at {CSV_PATH}")

df = pd.read_csv(CSV_PATH)
df['Ingredient'] = df['Ingredient'].str.strip()
df['Category']   = df['Category'].str.strip()

# Identify the kcal column (must contain 'kcal')
kcal_col = next((c for c in df.columns if 'kcal' in c.lower()), None)
if not kcal_col:
    raise KeyError("CSV needs a column header containing 'kcal'")

kcal_map = dict(zip(df['Ingredient'], df[kcal_col]))
CATEGORIES = sorted(df['Category'].unique())
INGS_BY_CAT = {
    cat: sorted(df[df['Category'] == cat]['Ingredient'].tolist())
    for cat in CATEGORIES
}

class ScrollableFrame(ttk.Frame):
    """A frame with a vertical scrollbar and mouse-wheel support."""
    def __init__(self, container):
        super().__init__(container)
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        vsb    = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        )
        self.inner = ttk.Frame(canvas)
        canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )


class MealPlanner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meal Planner")
        self.geometry("1000x900")

        sf = ScrollableFrame(self)
        sf.pack(fill="both", expand=True, padx=10, pady=10)
        p = sf.inner

        # Store frames and labels
        self.ing_frames = {}     # {category: [(Combobox, Entry), ...]}
        self.kcal_labels = {}    # {category: StringVar}
        self.total_kcal_var = tk.StringVar(value="Total: 0.0 kcal")

        # Ingredient selection panels
        ING_COLS = 7
        container = ttk.Frame(p)
        container.grid(row=0, column=0, columnspan=ING_COLS, pady=10)

        for idx, cat in enumerate(CATEGORIES):
            r = idx // ING_COLS
            c = idx % ING_COLS
            frame = ttk.LabelFrame(container, text=cat, padding=5)
            frame.grid(row=r, column=c, padx=10, pady=5, sticky="nw")

            opts = ["None"] + INGS_BY_CAT[cat]
            slots = []
            for i in range(5):
                base_row = i * 2

                ttk.Label(frame, text=f"Option {i+1}:").grid(
                    row=base_row, column=0, sticky="w")
                cb = ttk.Combobox(
                    frame, values=opts, state="readonly", width=18)
                cb.current(0)
                cb.grid(row=base_row, column=1, padx=5)

                ttk.Label(frame, text="Grams:").grid(
                    row=base_row+1, column=0, sticky="w")
                e_avail = ttk.Entry(frame, width=6)
                e_avail.insert(0, "0")
                e_avail.grid(row=base_row+1, column=1, sticky="w")

                # Recalculate on any change
                e_avail.bind("<KeyRelease>", lambda e: self.calculate())
                cb.bind("<<ComboboxSelected>>", lambda e: self.calculate())

                slots.append((cb, e_avail))

            self.ing_frames[cat] = slots

            # Label to show this category's total kcal
            kcal_var = tk.StringVar(value="0.0 kcal")
            self.kcal_labels[cat] = kcal_var
            ttk.Label(frame, textvariable=kcal_var,
                      foreground="blue").grid(row=10, column=0,
                                              columnspan=2, pady=5)

        # Total meal kcal display
        ttk.Label(p, textvariable=self.total_kcal_var,
                  font=("Arial", 14), foreground="darkgreen")\
            .grid(row=1, column=0, columnspan=ING_COLS, pady=(10,20))

        # Add New Ingredient Section
        ttk.Label(p, text="➕ Add New Ingredient",
                  font=("Arial", 12, "bold"))\
            .grid(row=2, column=0, columnspan=ING_COLS, pady=(0,5))

        form = ttk.Frame(p)
        form.grid(row=3, column=0, columnspan=ING_COLS, pady=5, sticky="w")

        ttk.Label(form, text="Name:").grid(row=0, column=0, sticky="w")
        self.new_name = ttk.Entry(form, width=20)
        self.new_name.grid(row=0, column=1, padx=5)

        ttk.Label(form, text="Calories/100g:").grid(row=0, column=2, sticky="w")
        self.new_kcal = ttk.Entry(form, width=10)
        self.new_kcal.grid(row=0, column=3, padx=5)

        ttk.Label(form, text="Category:").grid(row=0, column=4, sticky="w")
        self.new_cat = ttk.Combobox(form, values=CATEGORIES,
                                    state="readonly", width=15)
        self.new_cat.grid(row=0, column=5, padx=5)

        ttk.Button(form, text="Add Ingredient",
                   command=self.add_ingredient)\
            .grid(row=0, column=6, padx=10)

        # Perform initial calculation
        self.calculate()

    def calculate(self):
        """Recalculate calories per category and total."""
        total_kcal = 0.0
        for cat, slots in self.ing_frames.items():
            cat_kcal = 0.0
            for cb, e_avail in slots:
                ing = cb.get()
                if ing == "None":
                    continue
                try:
                    grams = float(e_avail.get() or 0)
                except ValueError:
                    grams = 0.0
                cat_kcal += grams * kcal_map.get(ing, 0.0) / 100.0

            self.kcal_labels[cat].set(f"{cat_kcal:.1f} kcal")
            total_kcal += cat_kcal

        self.total_kcal_var.set(f"Total: {total_kcal:.1f} kcal")

    def add_ingredient(self):
        """Add a new ingredient to the CSV, reload data, and refresh dropdowns."""
        name = self.new_name.get().strip()
        kcal_txt = self.new_kcal.get().strip()
        cat  = self.new_cat.get().strip()

        if not name or not kcal_txt or not cat:
            return messagebox.showerror("Error", "All fields are required.")

        try:
            kcal_val = float(kcal_txt)
        except ValueError:
            return messagebox.showerror("Error", "Calories must be a number.")

        # Append to CSV
        new_row = pd.DataFrame(
            [[name, cat, kcal_val]],
            columns=['Ingredient', 'Category', kcal_col]
        )
        new_row.to_csv(CSV_PATH, mode='a', header=False, index=False)

        # Update in-memory data
        df.loc[len(df)] = [name, cat, kcal_val]
        kcal_map[name] = kcal_val

        if cat not in INGS_BY_CAT:
            INGS_BY_CAT[cat] = []
            CATEGORIES.append(cat)

        INGS_BY_CAT[cat].append(name)
        INGS_BY_CAT[cat] = sorted(INGS_BY_CAT[cat])

        # Refresh the dropdown values for this category
        for cb, _ in self.ing_frames.get(cat, []):
            cb['values'] = ["None"] + INGS_BY_CAT[cat]

        messagebox.showinfo(
            "Success", f"Added '{name}' to category '{cat}'."
        )

        # Clear form fields
        self.new_name.delete(0, tk.END)
        self.new_kcal.delete(0, tk.END)
        self.new_cat.set("")


if __name__ == "__main__":
    app = MealPlanner()
    app.mainloop()

# In[ ]:



