import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from st_aggrid import AgGrid, GridOptionsBuilder
from datetime import datetime
import zipfile
import warnings

warnings.filterwarnings("ignore")
st.set_page_config(page_title="📊 Multi-Unit Sales Dashboard", layout="wide")
st.title("🏭 Multi-Unit Sales Dashboard")

def process_zip(zip_file):
    with zipfile.ZipFile(zip_file) as z:
        dfs = {}
        for name in z.namelist():
            if name.endswith(".xlsx"):
                df = pd.read_excel(z.open(name))
                if {"Product_Name", "Quantity_Sold", "Sales_Value"}.issubset(df.columns):
                    try:
                        # Extract month-year directly from file name like "April 2024.xlsx"
                        file_title = name.replace(".xlsx", "").strip()
                        date = pd.to_datetime(file_title, format="%B %Y")
                        df["Date"] = date
                        dfs[date] = df
                    except:
                        st.warning(f"⚠️ Could not parse date from file: {name}")
        return dfs

def tag_product_activity(df):
    counts = df.groupby("Product_Name")["Date"].nunique().reset_index()
    counts.columns = ["Product_Name", "Active_Months"]
    counts["Activity_Type"] = counts["Active_Months"].apply(
        lambda x: "Consistent" if x >= 5 else ("Intermittent" if x > 1 else "One-Time"))
    return counts

def custom_month_summary(df, start_month, end_month):
    df["Month_dt"] = pd.to_datetime(df["Month"], format="%B %Y")
    start_dt = pd.to_datetime(start_month, format="%B %Y")
    end_dt = pd.to_datetime(end_month, format="%B %Y")
    filtered_df = df[(df["Month_dt"] >= start_dt) & (df["Month_dt"] <= end_dt)]

    summary = filtered_df.groupby("Product_Name").agg({
        "Quantity_Sold": "sum",
        "Sales_Value": "sum",
        "Month": "nunique"
    }).rename(columns={"Month": "Months_Active"}).reset_index()

    summary["Average_Quantity"] = (summary["Quantity_Sold"] / summary["Months_Active"]).round(2)
    summary["Average_Sales"] = (summary["Sales_Value"] / summary["Months_Active"]).round(2)
    return summary

tab_labels = ["Unit 1", "Unit 2", "Unit 3", "Unit 4"]
tabs = st.tabs(tab_labels)

for idx, unit in enumerate(tab_labels):
    with tabs[idx]:
        uploaded_zip = st.file_uploader(f"Upload ZIP for {unit}", type="zip", key=f"{unit}_upload")
        if uploaded_zip:
            dfs = process_zip(uploaded_zip)
            if len(dfs) < 2:
                st.error("❗ Upload at least two valid monthly Excel sheets.")
            else:
                all_dates = sorted(dfs.keys())
                combined_df = pd.concat([df.assign(Month=dt.strftime("%B %Y")) for dt, df in dfs.items()])
                month_options = [dt.strftime("%B %Y") for dt in all_dates]
                selected_month = st.selectbox(f"Select Month - {unit}", month_options, index=len(month_options)-1, key=f"{unit}_month")
                filtered_data = combined_df[combined_df["Month"] == selected_month]

                product_filter = st.text_input(f"Search Product Name - {unit}", key=f"{unit}_filter")
                if product_filter:
                    filtered_data = filtered_data[filtered_data["Product_Name"].str.contains(product_filter, case=False)]

                st.subheader(f"📄 Sales Data - {selected_month}")
                gb_all = GridOptionsBuilder.from_dataframe(filtered_data)
                gb_all.configure_pagination()
                gb_all.configure_default_column(filterable=True, sortable=True, resizable=True)
                AgGrid(filtered_data, gridOptions=gb_all.build(), theme='material')
                st.download_button("📤 Download Data", data=filtered_data.to_csv(index=False),
                                   file_name=f"{unit}_{selected_month.replace(' ', '_')}.csv")

                st.markdown(f"### 💰 Total Sales: ₹{filtered_data['Sales_Value'].sum():,.2f}")

                st.markdown("### 📌 Custom Range Summary")
                start_m = st.selectbox(f"From Month - {unit}", month_options, key=f"{unit}_start")
                end_m = st.selectbox(f"To Month - {unit}", month_options, index=len(month_options)-1, key=f"{unit}_end")
                if month_options.index(start_m) <= month_options.index(end_m):
                    summary = custom_month_summary(combined_df, start_m, end_m)
                    AgGrid(summary)
                else:
                    st.warning("⚠️ Start month must be before end month.")

                # Monthly Summary with Rolling Averages
                monthly_summary = combined_df.groupby("Date").agg({
                    "Quantity_Sold": "sum", "Sales_Value": "sum"
                }).sort_index().reset_index()
                monthly_summary["Month"] = monthly_summary["Date"].dt.strftime("%B %Y")
                monthly_summary["Rolling_Avg_Quantity"] = monthly_summary["Quantity_Sold"].rolling(window=3, min_periods=1).mean()
                monthly_summary["Rolling_Avg_Sales"] = monthly_summary["Sales_Value"].rolling(window=3, min_periods=1).mean()
                st.subheader("📅 Monthly Sales Summary (with Rolling Averages)")
                AgGrid(monthly_summary[["Month", "Quantity_Sold", "Sales_Value", "Rolling_Avg_Quantity", "Rolling_Avg_Sales"]].round(2))

                # Product Activity Type (One-Time, Intermittent, Consistent)
                st.subheader("📌 Product Activity Classification")
                activity_df = tag_product_activity(combined_df)
                AgGrid(activity_df)

                # Product-wise Trends
                st.markdown("---")
                st.subheader("📊 Product-wise Trendline")
                selected_prod = st.selectbox("Choose Product", sorted(combined_df["Product_Name"].unique()), key=f"{unit}_trend")
                trend_data = combined_df[combined_df["Product_Name"] == selected_prod].groupby("Date")[["Quantity_Sold", "Sales_Value"]].sum().reset_index()
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(trend_data["Date"], trend_data["Quantity_Sold"], marker="o", label="Quantity Sold")
                ax.plot(trend_data["Date"], trend_data["Sales_Value"], marker="x", label="Sales Value")
                ax.set_title(f"Trendline: {selected_prod}")
                ax.legend()
                st.pyplot(fig)
