import streamlit as st
import pandas as pd

# Load dataset from Google Drive
file_id = "126l5KmypB1_0K2mhJEYS57lZnHM5Oa-7"
csv_url = f"https://drive.google.com/uc?id={file_id}"
df = pd.read_csv(csv_url)

st.title("🐎 Stallion Recommendation System")

# Mare dropdown
mare_options = df[df["Horse Gender"] == "Mare"]["Horse Name"].dropna().unique()
selected_mare = st.selectbox("Select a Mare", mare_options)

def recommend_stallions(df, mare_name):
    df["Birth Date"] = pd.to_datetime(df["Birth Date"], errors="coerce")

    def get_mare_info(name):
        mare = df[(df["Horse Name"].str.upper() == name.upper()) & (df["Horse Gender"] == "Mare")]
        return mare.iloc[0] if not mare.empty else None

    def pedigree_breakdown(m1, m2):
        breakdown = []
        pedigree = 0.0

        # Level 1: Parents
        if m1["Sire (Father)"] == m2["Sire (Father)"]:
            pedigree += 50
            breakdown.append(f"✅ Sire matched: {m1['Sire (Father)']} (+50%)")
        if m1["Dam (Mother)"] == m2["Dam (Mother)"]:
            pedigree += 50
            breakdown.append(f"✅ Dam matched: {m1['Dam (Mother)']} (+50%)")

        # Level 2: Grandparents (12.5%)
        grandparents = [
            ("Paternal Grandsire", 12.5), ("Paternal Granddam", 12.5),
            ("Maternal Grandsire", 12.5), ("Maternal Granddam", 12.5)
        ]
        for gp, score in grandparents:
            if pd.notna(m1[gp]) and m1[gp] == m2[gp]:
                pedigree += score
                breakdown.append(f"✅ {gp} matched: {m1[gp]} (+{score}%)")

        # Level 3: Great-Grandparents (3.125%)
        greats = [
            ("Great Grandsire (Sire's Sire)", 3.125),
            ("Great Granddam (Sire's Dam)", 3.125),
            ("Great Grandsire (Dam's Sire)", 3.125),
            ("Great Granddam (Dam's Sire's Dam)", 3.125),
            ("Great Grandsire (Dam's Dam's Sire)", 3.125),
            ("Great Granddam (Dam's Dam's Dam)", 3.125)
        ]
        for gp, score in greats:
            if pd.notna(m1[gp]) and m1[gp] == m2[gp]:
                pedigree += score
                breakdown.append(f"✅ {gp} matched: {m1[gp]} (+{score}%)")

        return round(pedigree, 2), breakdown

    def get_offspring(mare_names):
        return df[(df["Dam (Mother)"].isin(mare_names)) & (df["Total Earnings (USD)"] > 0)]

    def get_all_relative_mares(main_mare_info):
        relatives = [(main_mare_info["Horse Name"], "Self", 0)]
        seen = set([main_mare_info["Horse Name"]])

        levels = [
            ("Full Sister", lambda m: (df["Horse Gender"] == "Mare") & (df["Sire (Father)"] == m["Sire (Father)"]) & (df["Dam (Mother)"] == m["Dam (Mother)"])),
            ("Half Sister", lambda m: (df["Horse Gender"] == "Mare") & (((df["Sire (Father)"] == m["Sire (Father)"]) & (df["Dam (Mother)"] != m["Dam (Mother)"])) | ((df["Dam (Mother)"] == m["Dam (Mother)"]) & (df["Sire (Father)"] != m["Sire (Father)"])))),
            ("Maternal Granddam Shared", lambda m: pd.notna(m["Maternal Granddam"]) and (df["Maternal Granddam"] == m["Maternal Granddam"])),
            ("Paternal Granddam Shared", lambda m: pd.notna(m["Paternal Granddam"]) and (df["Paternal Granddam"] == m["Paternal Granddam"])),
            ("Great Maternal Granddam Shared", lambda m: pd.notna(m["Great Granddam (Dam's Dam's Dam)"]) and (df["Great Granddam (Dam's Dam's Dam)"] == m["Great Granddam (Dam's Dam's Dam)"])),
            ("Great Paternal Granddam Shared", lambda m: pd.notna(m["Great Granddam (Sire's Dam's Dam)"]) and (df["Great Granddam (Sire's Dam's Dam)"] == m["Great Granddam (Sire's Dam's Dam)"]))
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
                pedigree = pedigree_breakdown(mare_info, rel_info)[0]
                label = f"{rel_name} ({rel_type} | {pedigree}% Pedigree)"
            relative_earnings.append((rel_name, label, level, earnings))

    top_relatives = sorted(relative_earnings, key=lambda x: (-x[3], x[2]))[:5]
    tabs = ["📋 Mare Info", "📊 Pedigree % Breakdown"] + [f"🐴 {label}" for _, label, _, _ in top_relatives]
    st_tabs = st.tabs(tabs)

    # Mare Info
    with st_tabs[0]:
        st.subheader("Mare Information")
        st.write(f"• Name: {mare_info['Horse Name']}")
        st.write(f"• Registration #: {mare_info['Horse Registration Number']}")
        st.write(f"• Birth Date: {mare_info['Birth Date'].date()}")
        st.write(f"• Sire: {mare_info['Sire (Father)']}")
        st.write(f"• Dam: {mare_info['Dam (Mother)']}")
        st.write(f"• Earnings: ${mare_info['Total Earnings (USD)']:,.2f}")
        st.markdown(f"[Pedigree Link]({mare_info['Pedigree Link']})")

    # Pedigree Breakdown Tab
    with st_tabs[1]:
        st.subheader("📊 Pedigree % Breakdown")
        for rel_name, label, _, _ in top_relatives:
            if rel_name == mare_info["Horse Name"]:
                st.markdown(f"### {rel_name} (Self) — 100% Pedigree (by definition)")
                st.markdown("---")
                continue

            rel_info = get_mare_info(rel_name)
            perc, breakdown = pedigree_breakdown(mare_info, rel_info)
            st.markdown(f"### {rel_name} — {perc}% Match")
            for line in breakdown:
                st.write(line)
            st.markdown("---")


    # Recommendation Tabs
    for i, (rel_name, label, _, _) in enumerate(top_relatives, start=2):
        with st_tabs[i]:
            st.subheader(f"Recommendations for {label}")
            offspring = get_offspring([rel_name])
            top_stallions = (
                offspring.sort_values(by="Total Earnings (USD)", ascending=False)
                .drop_duplicates("Sire (Father)").head(5)
            )
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
