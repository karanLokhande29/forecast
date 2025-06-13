
# 📊 Multi-Unit Sales Dashboard with Forecasting (Streamlit)

This Streamlit app allows you to upload **monthly sales ZIP files** for up to 4 different factory units (Unit 1 to Unit 4). Each unit gets its own dashboard with the same features and filters.

---

## ✅ Features

- Upload ZIP file containing monthly Excel sales files (one ZIP per unit)
- View filtered monthly sales for selected unit
- Compare growth between current and previous month
- See total monthly sales and MoM growth
- View product-wise trends
- Forecast next 30 days using Linear Regression (per product and all products)
- Download CSVs for:
  - Filtered data
  - Monthly comparisons
  - Forecasts (individual and summary)

---

## 🗂️ Excel File Format

Each Excel file should be named like:
```
sales_april_2025.xlsx
sales_may_2025.xlsx
```

Each file must contain:
- `Product_Name`
- `Quantity_Sold`
- `Sales_Value`

---

## ▶️ Running the App

1. **Install requirements**
```bash
pip install -r requirements.txt
```

2. **Run the app**
```bash
streamlit run multi_unit_sales_app.py
```

---

## 🧠 Notes

- Uses `LinearRegression` from `scikit-learn` for 30-day forecasting.
- Each unit dashboard runs independently with its own uploaded ZIP file.

---

Created for Precise Chemipharma by Karan Lokhande 💼
