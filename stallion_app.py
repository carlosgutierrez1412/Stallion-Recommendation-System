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

    def calculate_pedigree_match(m1, m2):
        fields = [
            "Sire (Father)", "Dam (Mother)", "Paternal Grandsire", "Paternal Granddam",
            "Maternal Grandsire", "Maternal Granddam", "Great Grandsire (Sire's Sire)",
            "Great Granddam (Sire's Dam)", "Great Grandsire (Dam's Sire)",
            "Great Granddam (Dam's Sire's Dam)", "Great Grandsire (Dam's Dam's Sire)",
            "Great Granddam (Dam's Dam's Dam)"
        ]
        shared = sum(m1.get(f) == m2.get(f) for f in fields if pd.notna(m1.get(f)) and pd.notna(m2.get(f)))
        return round(100 * shared / len(fields), 1)

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
        st.error(f"Mare '{mare_name}' not found or is not a mare.")
        return

    tabs = [f"📋 {mare_name} Info"]
    all_relatives = get_all_relative_mares(mare_info)
    relative_earnings = []

    for rel_name, rel_type, level in all_relatives:
        rel_info = df[df["Horse Name"] == rel_name].iloc[0]
        earnings = get_offspring([rel_name])["Total Earnings (USD)"].sum()
        if earnings > 0:
            if rel_type == "Self":
                label = f"{rel_name} (Self)"
            else:
                pedigree = calculate_pedigree_match(mare_info, rel_info)
                label = f"{rel_name} ({rel_type} | {pedigree}% Pedigree)"
            relative_earnings.append((rel_name, label, level, earnings))

    top_relatives = sorted(relative_earnings, key=lambda x: (-x[3], x[2]))[:5]
    tabs += [f"🐴 {label}" for _, label, _, _ in top_relatives]

    tabs = st.tabs(tabs)

    # Mare Info Tab
    with tabs[0]:
        st.subheader("Mare Information")
        st.write(f"• Name: {mare_info['Horse Name']}")
        st.write(f"• Registration #: {mare_info['Horse Registration Number']}")
        st.write(f"• Birth Date: {mare_info['Birth Date'].date()}")
        st.write(f"• Sire: {mare_info['Sire (Father)']}")
        st.write(f"• Dam: {mare_info['Dam (Mother)']}")
        st.write(f"• Maternal Granddam: {mare_info['Maternal Granddam']}")
        st.write(f"• Paternal Granddam: {mare_info['Paternal Granddam']}")
        earnings = mare_info["Total Earnings (USD)"]
        st.write(f"• Mare Earnings: ${earnings:,.2f}" if earnings > 0 else "• Mare Earnings: No recorded earnings")
        st.markdown(f"• [Pedigree Link]({mare_info['Pedigree Link']})")

    # Relative Mare Tabs
    for idx, (rel_name, label, _, _) in enumerate(top_relatives, start=1):
        with tabs[idx]:
            st.subheader(f"Recommendations for {label}")
            offspring = get_offspring([rel_name])
            top_stallions = (
                offspring.sort_values(by="Total Earnings (USD)", ascending=False)
                .drop_duplicates("Sire (Father)")
                .head(5)
            )

            stallion_tabs = st.tabs([f"🧬 {sire}" for sire in top_stallions["Sire (Father)"]])

            for j, sire in enumerate(top_stallions["Sire (Father)"]):
                with stallion_tabs[j]:
                    pair_offspring = offspring[offspring["Sire (Father)"] == sire]
                    total_pair_earnings = pair_offspring["Total Earnings (USD)"].sum()

                    st.subheader(f"{rel_name} x {sire}")
                    st.write(f"• Total Earnings from this pair: ${total_pair_earnings:,.2f}")
                    st.markdown("---")

                    for i, row in pair_offspring.iterrows():
                        child = row["Horse Name"]
                        earning = row["Total Earnings (USD)"]
                        st.markdown(f"• **{child}** earned ${earning:,.2f}")


# Run
if st.button("Recommend Stallions"):
    recommend_stallions(df, selected_mare)
