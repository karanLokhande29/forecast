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
st.title("🏠 Multi-Unit Sales Dashboard")

def process_zip(zip_file):
    with zipfile.ZipFile(zip_file) as z:
        dfs = {}
        for name in z.namelist():
            if name.endswith(".xlsx"):
                df = pd.read_excel(z.open(name))
                if {"Item Name", "Quantity", "Value"}.issubset(df.columns):
                    try:
                        # Handle filename like "April 2024.xlsx"
                        month_year = name.replace(".xlsx", "")
                        date = pd.to_datetime(month_year, format="%B %Y")
                        df["Date"] = date
                        df = df.rename(columns={
                            "Item Name": "Product_Name",
                            "Quantity": "Quantity_Sold",
                            "Value": "Sales_Value"
                        })
                        dfs[date] = df
                    except:
                        st.warning(f"⚠️ Could not parse date from file: {name}")
        return dfs

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
                st.download_button("📄 Download Data", data=filtered_data.to_csv(index=False), file_name=f"{unit}_{selected_month.replace(' ', '_')}.csv")

                st.markdown(f"### 💰 Total Sales: ₹{filtered_data['Sales_Value'].sum():,.2f}")

                # Monthly Summary Table
                monthly_summary = combined_df.groupby("Date").agg({
                    "Quantity_Sold": "sum", "Sales_Value": "sum"
                }).sort_index().reset_index()
                monthly_summary["Month"] = monthly_summary["Date"].dt.strftime("%B %Y")
                monthly_summary["MoM_Growth_Quantity_%"] = monthly_summary["Quantity_Sold"].pct_change() * 100
                monthly_summary["MoM_Growth_Sales_Value_%"] = monthly_summary["Sales_Value"].pct_change() * 100
                monthly_summary = monthly_summary[["Month", "Quantity_Sold", "Sales_Value", "MoM_Growth_Quantity_%", "MoM_Growth_Sales_Value_%"]]
                st.subheader("📅 Monthly Sales Summary")
                AgGrid(monthly_summary.round(2))

                # 🔻 All Graphs Placed at End
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

                st.subheader("🔮 Forecast for All Products (Next Month)")
                history = combined_df.groupby(["Date", "Product_Name"]).agg({"Quantity_Sold": "sum", "Sales_Value": "sum"}).reset_index()
                history["Date_Ordinal"] = history["Date"].map(datetime.toordinal)
                forecasts = []
                for prod in sorted(history["Product_Name"].unique()):
                    prod_df = history[history["Product_Name"] == prod]
                    if len(prod_df) >= 2:
                        model_qty = LinearRegression().fit(prod_df[["Date_Ordinal"]], prod_df["Quantity_Sold"])
                        model_val = LinearRegression().fit(prod_df[["Date_Ordinal"]], prod_df["Sales_Value"])
                        target_date = prod_df["Date"].max() + pd.DateOffset(months=1)
                        ord_val = target_date.toordinal()
                        qty = model_qty.predict([[ord_val]])[0]
                        val = model_val.predict([[ord_val]])[0]
                        forecasts.append({
                            "Product_Name": prod,
                            "Forecasted_Quantity": round(qty),
                            "Forecasted_Sales_Value": round(val, 2)
                        })

                forecast_df = pd.DataFrame(forecasts)
                AgGrid(forecast_df)
                st.markdown(f"### 💡 Total Forecasted Sales: ₹{forecast_df['Forecasted_Sales_Value'].sum():,.2f}")
