import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# ✅ Umami analytics tracking
umami_script = """
<script defer src="https://cloud.umami.is/script.js" data-website-id="b5bf2f70-e4d0-4308-8804-c36a67d32dc0"></script>
"""
components.html(umami_script, height=0, width=0)

# Load dataset
df = pd.read_csv("https://drive.google.com/uc?id=14A-2Pz2ILnUB_hQF1PJ3EB073QcDhNsi&export=download")
df["Birth Date"] = pd.to_datetime(df["Birth Date"], errors="coerce")

st.title("🐎 Stallion Recommendation System")

mare_options = df[df["Horse Gender"] == "Mare"]["Horse Name"].dropna().unique()
selected_mare = st.selectbox("Select a Mare", mare_options)

def recommend_stallions(df, mare_name):
    def get_mare_info(name):
        mare = df[(df["Horse Name"].str.upper() == name.upper()) & (df["Horse Gender"] == "Mare")]
        return mare.iloc[0] if not mare.empty else None

    def build_pedigree_tree():
        return {
            "Sire (Father)": 0.50,
            "Paternal Grandsire": 0.25, "Paternal Granddam": 0.25,
            "Great Grandsire (Sire's Sire)": 0.125, "Great Granddam (Sire's Sire's Dam)": 0.125,
            "Great Grandsire (Sire's Dam's Sire)": 0.125, "Great Granddam (Sire's Dam's Dam)": 0.125,
            "Great-Great Grandsire (Sire's Sire's Sire)": 0.0625, "Great-Great Granddam (Sire's Sire's Dam)": 0.0625,
            "Great-Great Grandsire (Sire's Sire's Dam's Sire)": 0.0625, "Great-Great Granddam (Sire's Sire's Dam's Dam)": 0.0625,
            "Great-Great Grandsire (Sire's Dam's Sire)": 0.0625, "Great-Great Granddam (Sire's Dam's Dam)": 0.0625,
            "Great-Great Grandsire (Sire's Dam's Dam's Sire)": 0.0625, "Great-Great Granddam (Sire's Dam's Dam's Dam)": 0.0625,
            "Dam (Mother)": 0.50,
            "Maternal Grandsire": 0.25, "Maternal Granddam": 0.25,
            "Great Grandsire (Dam's Sire)": 0.125, "Great Granddam (Dam's Sire's Dam)": 0.125,
            "Great Grandsire (Dam's Dam's Sire)": 0.125, "Great Granddam (Dam's Dam's Dam)": 0.125,
            "Great-Great Grandsire (Dam's Sire's Sire)": 0.0625, "Great-Great Granddam (Dam's Sire's Dam)": 0.0625,
            "Great-Great Grandsire (Dam's Sire's Dam's Sire)": 0.0625, "Great-Great Granddam (Dam's Sire's Dam's Dam)": 0.0625,
            "Great-Great Grandsire (Dam's Dam's Sire)": 0.0625, "Great-Great Granddam (Dam's Dam's Dam)": 0.0625,
            "Great-Great Grandsire (Dam's Dam's Dam's Sire)": 0.0625, "Great-Great Granddam (Dam's Dam's Dam's Dam)": 0.0625,
        }

    def recursive_compare(name, path, m2_values, value, breakdown):
        if name in m2_values:
            breakdown.append(f"✅ Match found at {path}: {name} (+{value:.4f})")
            return value
        return 0.0

    def traverse_lineage(m1_row, m2_values, keys_by_branch):
        total_score = 0.0
        breakdown = []
        visited = set()
        for branch in ["Sire (Father)", "Dam (Mother)"]:
            name = m1_row.get(branch)
            if pd.notna(name) and name in m2_values:
                score = 0.50
                total_score += score
                breakdown.append(f"✅ {branch} matched: {name} (+0.50)")
                visited.add(name)
                continue
            for key in keys_by_branch[branch]:
                val = m1_row.get(key)
                if pd.notna(val) and val not in visited:
                    tree_val = pedigree_map[key]
                    score = recursive_compare(val, key, m2_values, tree_val, breakdown)
                    if score > 0:
                        total_score += score
                        visited.add(val)
                        break
        return total_score, breakdown

    def calculate_new_pedigree(m1, m2):
        global pedigree_map
        pedigree_map = build_pedigree_tree()
        m2_values = set(m2.dropna().values)
        keys_by_branch = {
            "Sire (Father)": [k for k in pedigree_map if "Sire" in k and not k.startswith("Dam")],
            "Dam (Mother)": [k for k in pedigree_map if "Dam" in k]
        }
        total_score, breakdown = traverse_lineage(m1, m2_values, keys_by_branch)
        return round(total_score * 100, 2), breakdown

    def build_relative_labels(main_mare):
        labels = {}
        for _, row in df[df["Horse Gender"] == "Mare"].iterrows():
            name = row["Horse Name"]
            if name == main_mare["Horse Name"]:
                labels[name] = "Self"
            elif row["Sire (Father)"] == main_mare["Sire (Father)"] and row["Dam (Mother)"] == main_mare["Dam (Mother)"]:
                labels[name] = "Full Sister"
            elif row["Sire (Father)"] == main_mare["Sire (Father)"]:
                labels[name] = "Half Sister (Same Sire)"
            elif row["Dam (Mother)"] == main_mare["Dam (Mother)"]:
                labels[name] = "Half Sister (Same Dam)"
            else:
                for col in main_mare.index:
                    if col.startswith("Great-Great"):
                        level = 4
                    elif col.startswith("Great "):
                        level = 3
                    elif col.startswith("Maternal") or col.startswith("Paternal"):
                        level = 2
                    else:
                        continue
                    if pd.notna(main_mare[col]) and main_mare[col] == row.get(col):
                        labels[name] = f"Lineage Relative ({col})"
                        break
        return labels

    def get_offspring(mare_names):
        return df[df["Dam (Mother)"].isin(mare_names)]

    mare_info = get_mare_info(mare_name)
    if mare_info is None:
        st.error(f"Mare '{mare_name}' not found.")
        return

    relative_labels = build_relative_labels(mare_info)
    relative_earnings = []
    for rel_name, rel_type in relative_labels.items():
        rel_info = get_mare_info(rel_name)
        if rel_info is not None:
            earnings = get_offspring([rel_name])["Total Earnings (USD)"].sum()
            relative_earnings.append((rel_name, f"{rel_name} ({rel_type})", earnings, rel_info))

    top_relatives = sorted(relative_earnings, key=lambda x: -x[2])[:5]
    tabs = ["📋 Mare Info", "📊 Pedigree % Breakdown"] + [f"🐴 {label}" for _, label, _, _ in top_relatives]
    st_tabs = st.tabs(tabs)

    with st_tabs[0]:
        st.subheader("Mare Information")
        st.write(f"• Name: {mare_info['Horse Name']}")
        st.write(f"• Registration #: {mare_info['Horse Registration Number']}")
        birth_date = mare_info["Birth Date"]
        if pd.notna(birth_date):
            st.write(f"• Birth Date: {birth_date.date()}")
        else:
            st.write("• Birth Date: Not Available")
        st.write(f"• Sire: {mare_info['Sire (Father)']}")
        st.write(f"• Dam: {mare_info['Dam (Mother)']}")
        st.write(f"• Earnings: ${mare_info['Total Earnings (USD)']:,.2f}")
        st.markdown(f"[Pedigree Link]({mare_info['Pedigree Link']})")

    with st_tabs[1]:
        st.subheader("📊 Pedigree % Breakdown")
        for rel_name, label, _, rel_info in top_relatives:
            if rel_name == mare_info["Horse Name"]:
                st.markdown(f"### {rel_name} (Self) — 100% Pedigree (by definition)")
                st.markdown("---")
                continue
            perc, breakdown = calculate_new_pedigree(mare_info, rel_info)
            st.markdown(f"### {rel_name} — {perc:.2f}% Match")
            for line in breakdown:
                st.write(line)
            st.markdown("---")

    for i, (rel_name, label, _, _) in enumerate(top_relatives, start=2):
        with st_tabs[i]:
            st.subheader(f"Recommendations for {label}")
            offspring = get_offspring([rel_name])
            if offspring.empty:
                st.info("No offspring data available.")
                continue
            top_stallions = offspring.sort_values(by="Total Earnings (USD)", ascending=False).drop_duplicates("Sire (Father)").head(5)
            stallion_tabs = st.tabs([f"🧬 {s}" for s in top_stallions["Sire (Father)"]])
            for j, sire in enumerate(top_stallions["Sire (Father)"]):
                with stallion_tabs[j]:
                    pair = offspring[offspring["Sire (Father)"] == sire]
                    total = pair["Total Earnings (USD)"].sum()
                    st.subheader(f"{rel_name} x {sire}")
                    st.write(f"• Total Earnings: ${total:,.2f}")
                    st.markdown("---")
                    for _, row in pair.iterrows():
                        st.markdown(f"• **{row['Horse Name']}** earned ${row['Total Earnings (USD)']:,.2f}")

# Run
if st.button("Recommend Stallions"):
    with st.spinner("⏳ Generating stallion recommendations..."):
        recommend_stallions(df, selected_mare)
    

