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

    def get_mare_info(mare_name):
        mare = df[(df["Horse Name"].str.upper() == mare_name.upper()) & (df["Horse Gender"] == "Mare")]
        return mare.iloc[0] if not mare.empty else None

    def calculate_pedigree_match(mare_info, relative_info):
        fields = [
            "Sire (Father)", "Dam (Mother)", "Paternal Grandsire", "Paternal Granddam",
            "Maternal Grandsire", "Maternal Granddam", "Great Grandsire (Sire's Sire)",
            "Great Granddam (Sire's Dam)", "Great Grandsire (Dam's Sire)",
            "Great Granddam (Dam's Sire's Dam)", "Great Grandsire (Dam's Dam's Sire)",
            "Great Granddam (Dam's Dam's Dam)"
        ]
        shared = sum(
            mare_info.get(f) == relative_info.get(f)
            for f in fields if pd.notna(mare_info.get(f)) and pd.notna(relative_info.get(f))
        )
        return round(100 * shared / len(fields), 1)

    lineage_levels = [
        (lambda m, e: df[(df["Horse Gender"] == "Mare") & (df["Sire (Father)"] == m["Sire (Father)"]) & (df["Dam (Mother)"] == m["Dam (Mother)"]) & (df["Horse Name"] != m["Horse Name"]) & (~df["Horse Name"].isin(e))], "Full Sister"),
        (lambda m, e: df[(df["Horse Gender"] == "Mare") & (((df["Sire (Father)"] == m["Sire (Father)"]) & (df["Dam (Mother)"] != m["Dam (Mother)"])) | ((df["Dam (Mother)"] == m["Dam (Mother)"]) & (df["Sire (Father)"] != m["Sire (Father)"]))) & (~df["Horse Name"].isin(e)) & (df["Horse Name"] != m["Horse Name"])], "Half Sister"),
        (lambda m, e: df[(df["Horse Gender"] == "Mare") & (df["Maternal Granddam"] == m["Maternal Granddam"]) & (~df["Horse Name"].isin(e)) & (df["Horse Name"] != m["Horse Name"])] if pd.notna(m["Maternal Granddam"]) else pd.DataFrame(), "Maternal Granddam Shared"),
        (lambda m, e: df[(df["Horse Gender"] == "Mare") & (df["Paternal Granddam"] == m["Paternal Granddam"]) & (~df["Horse Name"].isin(e)) & (df["Horse Name"] != m["Horse Name"])] if pd.notna(m["Paternal Granddam"]) else pd.DataFrame(), "Paternal Granddam Shared"),
        (lambda m, e: df[(df["Horse Gender"] == "Mare") & (df["Great Granddam (Dam's Dam's Dam)"] == m["Great Granddam (Dam's Dam's Dam)"]) & (~df["Horse Name"].isin(e)) & (df["Horse Name"] != m["Horse Name"])] if pd.notna(m["Great Granddam (Dam's Dam's Dam)"]) else pd.DataFrame(), "Great Maternal Granddam Shared"),
        (lambda m, e: df[(df["Horse Gender"] == "Mare") & (df["Great Granddam (Sire's Dam's Dam)"] == m["Great Granddam (Sire's Dam's Dam)"]) & (~df["Horse Name"].isin(e)) & (df["Horse Name"] != m["Horse Name"])] if pd.notna(m["Great Granddam (Sire's Dam's Dam)"]) else pd.DataFrame(), "Great Paternal Granddam Shared")
    ]

    def get_offspring(mare_names):
        return df[(df["Dam (Mother)"].isin(mare_names)) & (df["Total Earnings (USD)"] > 0)]

    mare_info = get_mare_info(mare_name)
    if mare_info is None:
        st.error(f"Mare '{mare_name}' not found or is not a mare.")
        return

    collected_offspring = pd.DataFrame()
    relationships = []
    exclude = [mare_info["Horse Name"]]

    own_offspring = get_offspring([mare_info["Horse Name"]])
    if not own_offspring.empty:
        relationships += [(mare_info["Horse Name"], "Self") for _ in own_offspring["Horse Name"]]
        collected_offspring = pd.concat([collected_offspring, own_offspring])

    for get_relatives, label in lineage_levels:
        if "Sire (Father)" not in collected_offspring.columns or len(collected_offspring["Sire (Father)"].unique()) < 3:
            relatives = get_relatives(mare_info, exclude)
            if "Horse Name" in relatives.columns:
                relationships += [(m, label) for m in relatives["Horse Name"]]
                exclude += list(relatives["Horse Name"])
                offspring = get_offspring(relatives["Horse Name"])
                collected_offspring = pd.concat([collected_offspring, offspring])
        else:
            break

    if collected_offspring.empty:
        st.warning("No offspring with earnings found from mare or relatives.")
        return

    collected_offspring = (
        collected_offspring.sort_values(by="Total Earnings (USD)", ascending=False)
        .drop_duplicates("Sire (Father)")
        .head(3)
    )

    rel_df = pd.DataFrame(relationships, columns=["Mare Name", "Relationship"])
    result = pd.merge(
        collected_offspring[["Horse Name", "Total Earnings (USD)", "Sire (Father)", "Dam (Mother)"]],
        rel_df,
        left_on="Dam (Mother)", right_on="Mare Name", how="left"
    ).drop(columns=["Mare Name"])

    stallion_summary = (
        result.groupby("Sire (Father)")
        .agg(Top_Son_Earnings=("Total Earnings (USD)", "max"))
        .sort_values(by="Top_Son_Earnings", ascending=False)
        .reset_index()
    )

    stallion_details = df[df["Horse Gender"] == "Stallion"][
        ["Horse Name", "Horse Registration Number", "Birth Date", "Pedigree Link"]
    ]
    stallion_summary = pd.merge(
        stallion_summary, stallion_details,
        left_on="Sire (Father)", right_on="Horse Name", how="left"
    ).drop(columns=["Horse Name"])

    # Create tabs
    tab1, tab2, *just_tabs = st.tabs(
        ["📋 Mare Info", "⭐ Recommended Stallions"] +
        [f"📘 Justification {i+1}" for i in range(len(stallion_summary))]
    )

    with tab1:
        st.subheader("Mare Details")
        st.write(f"• Name: {mare_info['Horse Name']}")
        st.write(f"• Registration #: {mare_info['Horse Registration Number']}")
        st.write(f"• Birth Date: {mare_info['Birth Date'].date()}")
        st.write(f"• Sire: {mare_info['Sire (Father)']}")
        st.write(f"• Dam: {mare_info['Dam (Mother)']}")
        st.write(f"• Maternal Granddam: {mare_info['Maternal Granddam']}")
        st.write(f"• Paternal Granddam: {mare_info['Paternal Granddam']}")
        st.markdown(f"• [Pedigree Link]({mare_info['Pedigree Link']})")

    with tab2:
        st.subheader("Top Recommended Stallions")
        for idx, row in stallion_summary.iterrows():
            st.markdown(f"**{idx+1}. {row['Sire (Father)']}**")
            st.write(f"Earnings from Son: ${row['Top_Son_Earnings']:,.2f}")
            st.write(f"Registration #: {row['Horse Registration Number']}")
            st.write(f"Birth Date: {row['Birth Date'].date() if pd.notna(row['Birth Date']) else 'N/A'}")
            st.markdown(f"[Pedigree Link]({row['Pedigree Link']})")

    for i, row in enumerate(stallion_summary.itertuples()):
        with just_tabs[i]:
            r = result[result["Sire (Father)"] == row._1].iloc[0]
            dam = r["Dam (Mother)"]
            son = r["Horse Name"]
            earnings = r["Total Earnings (USD)"]
            rel = r["Relationship"]
            common = ""

            if rel == "Full Sister":
                common = f"They share both sire ({mare_info['Sire (Father)']}) and dam ({mare_info['Dam (Mother)']})"
            elif rel == "Half Sister":
                relative_row = df[df["Horse Name"] == dam].iloc[0]
                if relative_row["Sire (Father)"] == mare_info["Sire (Father)"]:
                    common = f"They share the same sire: {mare_info['Sire (Father)']}"
                else:
                    common = f"They share the same dam: {mare_info['Dam (Mother)']}"

            if rel == "Self":
                desc = f"{dam} is the mare herself. She previously produced {son}, who earned ${earnings:,.2f}. This confirms the pairing with {row._1} has been successful."
            else:
                relative_info = df[df["Horse Name"] == dam].iloc[0]
                pedigree_percent = calculate_pedigree_match(mare_info, relative_info)
                desc = f"{dam} is a {rel.lower()} of {mare_info['Horse Name']}. {common}. She produced {son}, who earned ${earnings:,.2f}. They share ~{pedigree_percent}% of known pedigree. This supports {row._1} as a strong recommendation."

            st.markdown(desc)

# Run
if st.button("Recommend Stallions"):
    recommend_stallions(df, selected_mare)
