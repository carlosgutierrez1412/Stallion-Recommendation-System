import streamlit as st
import pandas as pd

# Load dataset
df = pd.read_csv("https://drive.google.com/uc?id=1-3DesLMRhu50j2k-NhU8XaDPa-yZzjZd&export=download")
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
                continue_branch = False
            else:
                continue_branch = True

            if continue_branch:
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
            "Sire (Father)": [
                "Paternal Grandsire", "Paternal Granddam",
                "Great Grandsire (Sire's Sire)", "Great Granddam (Sire's Sire's Dam)",
                "Great Grandsire (Sire's Dam's Sire)", "Great Granddam (Sire's Dam's Dam)",
                "Great-Great Grandsire (Sire's Sire's Sire)", "Great-Great Granddam (Sire's Sire's Dam)",
                "Great-Great Grandsire (Sire's Sire's Dam's Sire)", "Great-Great Granddam (Sire's Sire's Dam's Dam)",
                "Great-Great Grandsire (Sire's Dam's Sire)", "Great-Great Granddam (Sire's Dam's Dam)",
                "Great-Great Grandsire (Sire's Dam's Dam's Sire)", "Great-Great Granddam (Sire's Dam's Dam's Dam)"
            ],
            "Dam (Mother)": [
                "Maternal Grandsire", "Maternal Granddam",
                "Great Grandsire (Dam's Sire)", "Great Granddam (Dam's Sire's Dam)",
                "Great Grandsire (Dam's Dam's Sire)", "Great Granddam (Dam's Dam's Dam)",
                "Great-Great Grandsire (Dam's Sire's Sire)", "Great-Great Granddam (Dam's Sire's Dam)",
                "Great-Great Grandsire (Dam's Sire's Dam's Sire)", "Great-Great Granddam (Dam's Sire's Dam's Dam)",
                "Great-Great Grandsire (Dam's Dam's Sire)", "Great-Great Granddam (Dam's Dam's Dam)",
                "Great-Great Grandsire (Dam's Dam's Dam's Sire)", "Great-Great Granddam (Dam's Dam's Dam's Dam)"
            ]
        }

        total_score, breakdown = traverse_lineage(m1, m2_values, keys_by_branch)
        return round(total_score * 100, 2), breakdown

    def get_offspring(mare_names):
        return df[(df["Dam (Mother)"].isin(mare_names)) & (df["Total Earnings (USD)"] > 0)]

    def get_all_relative_mares(main_mare_info):
        relatives = [(main_mare_info["Horse Name"], "Self", 0)]
        seen = set([main_mare_info["Horse Name"]])
        levels = [
            ("Full Sister", lambda m: (df["Horse Gender"] == "Mare") &
             (df["Sire (Father)"] == m["Sire (Father)"]) &
             (df["Dam (Mother)"] == m["Dam (Mother)"])),
            ("Half Sister", lambda m: (df["Horse Gender"] == "Mare") &
             (((df["Sire (Father)"] == m["Sire (Father)"]) & (df["Dam (Mother)"] != m["Dam (Mother)"])) |
              ((df["Dam (Mother)"] == m["Dam (Mother)"]) & (df["Sire (Father)"] != m["Sire (Father)"])))),
        ]
        for level_idx, (label, func) in enumerate(levels, 1):
            matches = df[func(main_mare_info) & (~df["Horse Name"].isin(seen))]
            for name in matches["Horse Name"].unique():
                relatives.append((name, label, level_idx))
                seen.add(name)
        return relatives

    mare_info = get_mare_info(mare_name)
    if mare_info is None:
        st.error(f"Mare '{mare_name}' not found.")
        return

    all_relatives = get_all_relative_mares(mare_info)
    relative_earnings = []
    for rel_name, rel_type, level in all_relatives:
        rel_info = get_mare_info(rel_name)
        earnings = get_offspring([rel_name])["Total Earnings (USD)"].sum()
        if earnings > 0:
            if rel_type == "Self":
                label = f"{rel_name} (Self)"
            else:
                pedigree = calculate_new_pedigree(mare_info, rel_info)[0]
                label = f"{rel_name} ({rel_type} | {pedigree:.1f}% Pedigree)"
            relative_earnings.append((rel_name, label, level, earnings))

    top_relatives = sorted(relative_earnings, key=lambda x: (-x[3], x[2]))[:5]
    tabs = ["📋 Mare Info", "📊 Pedigree % Breakdown"] + [f"🐴 {label}" for _, label, _, _ in top_relatives]
    st_tabs = st.tabs(tabs)

    with st_tabs[0]:
        st.subheader("Mare Information")
        st.write(f"• Name: {mare_info['Horse Name']}")
        st.write(f"• Registration #: {mare_info['Horse Registration Number']}")
        st.write(f"• Birth Date: {mare_info['Birth Date'].date()}")
        st.write(f"• Sire: {mare_info['Sire (Father)']}")
        st.write(f"• Dam: {mare_info['Dam (Mother)']}")
        st.write(f"• Earnings: ${mare_info['Total Earnings (USD)']:,.2f}")
        st.markdown(f"[Pedigree Link]({mare_info['Pedigree Link']})")

    with st_tabs[1]:
        st.subheader("📊 Pedigree % Breakdown")
        for rel_name, label, _, _ in top_relatives:
            if rel_name == mare_info["Horse Name"]:
                st.markdown(f"### {rel_name} (Self) — 100% Pedigree (by definition)")
                st.markdown("---")
                continue
            rel_info = get_mare_info(rel_name)
            perc, breakdown = calculate_new_pedigree(mare_info, rel_info)
            st.markdown(f"### {rel_name} — {perc:.2f}% Match")
            for line in breakdown:
                st.write(line)
            st.markdown("---")

    for i, (rel_name, label, _, _) in enumerate(top_relatives, start=2):
        with st_tabs[i]:
            st.subheader(f"Recommendations for {label}")
            offspring = get_offspring([rel_name])
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
    recommend_stallions(df, selected_mare)
