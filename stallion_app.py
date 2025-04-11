import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import time

# ✅ Umami analytics tracking
umami_script = """
<script defer src="https://cloud.umami.is/script.js" data-website-id="b5bf2f70-e4d0-4308-8804-c36a67d32dc0"></script>
"""
components.html(umami_script, height=0, width=0)

# ✅ Load dataset
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
            "Sire (Father)": 0.50, "Dam (Mother)": 0.50,
            "Paternal Grandsire": 0.25, "Paternal Granddam": 0.25,
            "Maternal Grandsire": 0.25, "Maternal Granddam": 0.25,
            "Great Grandsire (Sire's Sire)": 0.125, "Great Granddam (Sire's Sire's Dam)": 0.125,
            "Great Grandsire (Sire's Dam's Sire)": 0.125, "Great Granddam (Sire's Dam's Dam)": 0.125,
            "Great Grandsire (Dam's Sire)": 0.125, "Great Granddam (Dam's Sire's Dam)": 0.125,
            "Great Grandsire (Dam's Dam's Sire)": 0.125, "Great Granddam (Dam's Dam's Dam)": 0.125,
            "Great-Great Grandsire (Sire's Sire's Sire)": 0.0625, "Great-Great Granddam (Sire's Sire's Dam)": 0.0625,
            "Great-Great Grandsire (Sire's Sire's Dam's Sire)": 0.0625, "Great-Great Granddam (Sire's Sire's Dam's Dam)": 0.0625,
            "Great-Great Grandsire (Sire's Dam's Sire)": 0.0625, "Great-Great Granddam (Sire's Dam's Dam)": 0.0625,
            "Great-Great Grandsire (Sire's Dam's Dam's Sire)": 0.0625, "Great-Great Granddam (Sire's Dam's Dam's Dam)": 0.0625,
            "Great-Great Grandsire (Dam's Sire's Sire)": 0.0625, "Great-Great Granddam (Dam's Sire's Dam)": 0.0625,
            "Great-Great Grandsire (Dam's Sire's Dam's Sire)": 0.0625, "Great-Great Granddam (Dam's Sire's Dam's Dam)": 0.0625,
            "Great-Great Grandsire (Dam's Dam's Sire)": 0.0625, "Great-Great Granddam (Dam's Dam's Dam)": 0.0625,
            "Great-Great Grandsire (Dam's Dam's Dam's Sire)": 0.0625, "Great-Great Granddam (Dam's Dam's Dam's Dam)": 0.0625,
        }

    def get_ancestor_score_map(horse_row):
        pedigree_map = build_pedigree_tree()
        score_map = {}
        label_map = {}
        for ancestor_col, score in pedigree_map.items():
            ancestor_name = horse_row.get(ancestor_col)
            if pd.notna(ancestor_name):
                if ancestor_name not in score_map:
                    score_map[ancestor_name] = []
                    label_map[ancestor_name] = []
                score_map[ancestor_name].append(score)
                label_map[ancestor_name].append(ancestor_col)
        return score_map, label_map

    def calculate_pedigree_percentage(m1_row, m2_row):
        map1, labels1 = get_ancestor_score_map(m1_row)
        map2, labels2 = get_ancestor_score_map(m2_row)

        common_ancestors = set(map1.keys()) & set(map2.keys())
        breakdown = []
        total_score = 0

        for ancestor in common_ancestors:
            avg_score = (sum(map1[ancestor]) / len(map1[ancestor]) + sum(map2[ancestor]) / len(map2[ancestor])) / 2
            total_score += avg_score
            combined_label = set(labels1[ancestor]) | set(labels2[ancestor])
            breakdown.append(f"✅ {ancestor} (matched at: {', '.join(combined_label)}) — averaged contribution = {avg_score:.4f}")

        pedigree_percent = round((total_score * 100), 2)
        return pedigree_percent, breakdown

    def classify_relationship(mare_row, relative_row):
        if mare_row["Horse Name"] == relative_row["Horse Name"]:
            return "Self"
        if mare_row["Sire (Father)"] == relative_row["Sire (Father)"] and mare_row["Dam (Mother)"] == relative_row["Dam (Mother)"]:
            return "Full Sister"
        if mare_row["Sire (Father)"] == relative_row["Sire (Father)"]:
            return "Half Sister (Paternal)"
        if mare_row["Dam (Mother)"] == relative_row["Dam (Mother)"]:
            return "Half Sister (Maternal)"

        pedigree_map = build_pedigree_tree()
        maternal_labels = [k for k in pedigree_map if "Dam" in k]
        paternal_labels = [k for k in pedigree_map if "Sire" in k and not k.startswith("Dam")]

        for level in range(2, 5):
            shared_maternal = any(mare_row[col] == relative_row[col] for col in maternal_labels if f"{level}th" not in col and pd.notna(mare_row[col]) and mare_row[col] == relative_row[col])
            shared_paternal = any(mare_row[col] == relative_row[col] for col in paternal_labels if f"{level}th" not in col and pd.notna(mare_row[col]) and mare_row[col] == relative_row[col])
            if shared_paternal:
                return f"{level}rd Degree Paternal Relative" if level == 3 else f"{level}th Degree Paternal Relative"
            if shared_maternal:
                return f"{level}rd Degree Maternal Relative" if level == 3 else f"{level}th Degree Maternal Relative"

        return "Distant Lineage Relative"

    def get_offspring(mare_names):
        return df[df["Dam (Mother)"].isin(mare_names)]

    mare_info = get_mare_info(mare_name)
    if mare_info is None:
        st.error("Mare not found.")
        return

    relatives = []
    mare_earnings = get_offspring([mare_info["Horse Name"]])["Total Earnings (USD)"].sum()
    if mare_earnings > 0:
        relatives.append((mare_info["Horse Name"], f"{mare_info['Horse Name']} (Self)", None, mare_earnings, mare_info, [], "Self"))

    mares = df[df["Horse Gender"] == "Mare"].copy()
    for _, row in mares.iterrows():
        if row["Horse Name"] == mare_info["Horse Name"]:
            continue
        earnings = get_offspring([row["Horse Name"]])["Total Earnings (USD)"].sum()
        if earnings > 0:
            perc, breakdown = calculate_pedigree_percentage(mare_info, row)
            label = classify_relationship(mare_info, row)
            relatives.append((row["Horse Name"], row["Horse Name"], perc, earnings, row, breakdown, label))

    relatives_sorted = sorted(relatives, key=lambda x: (-x[2] if x[2] is not None else float('-inf')))
    top_relatives = relatives_sorted[:5]

    tabs = ["📋 Mare Info", "📊 Pedigree % Breakdown"] + [
        f"🐴 {name} ({rel_type}) — {perc:.2f}%" if perc is not None else f"🐴 {name} (Self)"
        for name, _, perc, _, _, _, rel_type in top_relatives
    ]
    st_tabs = st.tabs(tabs)

    with st_tabs[0]:
        st.subheader("Mare Information")
        st.write(f"• Name: {mare_info['Horse Name']}")
        st.write(f"• Registration #: {mare_info['Horse Registration Number']}")
        st.write(f"• Birth Date: {mare_info['Birth Date'].date() if pd.notna(mare_info['Birth Date']) else 'N/A'}")
        st.write(f"• Sire: {mare_info['Sire (Father)']}")
        st.write(f"• Dam: {mare_info['Dam (Mother)']}")
        st.write(f"• Earnings: ${mare_info['Total Earnings (USD)']:,.2f}")
        st.markdown(f"[Pedigree Link]({mare_info['Pedigree Link']})")

    with st_tabs[1]:
        st.subheader("📊 Pedigree % Breakdown")
        for name, _, perc, _, _, breakdown, rel_type in top_relatives:
            if perc is None:
                st.markdown(f"### {name} (Self) — 100% Pedigree (by definition)")
            else:
                st.markdown(f"### {name} ({rel_type}) — {perc:.2f}% Match")
                for line in breakdown:
                    st.write(line)
            st.markdown("---")

    for i, (name, _, perc, _, _, _, rel_type) in enumerate(top_relatives, start=2):
        with st_tabs[i]:
            if perc is None:
                st.subheader(f"Recommendations for {name} — 100% Pedigree (Self)")
            else:
                st.subheader(f"Recommendations for {name} ({rel_type}) — {perc:.2f}%")
            offspring = get_offspring([name])
            if offspring.empty:
                st.info("No offspring data available.")
                continue
            top_stallions = offspring.sort_values("Total Earnings (USD)", ascending=False).drop_duplicates("Sire (Father)").head(5)
            stallion_tabs = st.tabs([f"🧬 {s}" for s in top_stallions["Sire (Father)"]])
            for j, sire in enumerate(top_stallions["Sire (Father)"]):
                with stallion_tabs[j]:
                    pair = offspring[offspring["Sire (Father)"] == sire]
                    total = pair["Total Earnings (USD)"].sum()
                    st.subheader(f"{name} x {sire}")
                    st.write(f"• Total Earnings: ${total:,.2f}")
                    for _, row in pair.iterrows():
                        st.markdown(f"• **{row['Horse Name']}** earned ${row['Total Earnings (USD)']:,.2f}")
                    st.markdown("---")

if st.button("Recommend Stallions"):
    start_time = time.time()
    with st.spinner("⏳ Generating stallion recommendations..."):
        recommend_stallions(df, selected_mare)
    st.success(f"✅ Recommendations ready in {time.time() - start_time:.2f} seconds!")
