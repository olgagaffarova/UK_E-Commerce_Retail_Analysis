# UK E-Commerce Retail Analysis

End-to-end data analysis project on the **UCI Online Retail dataset** — a UK-based wholesale gift retailer covering **541,909 transactions** across **38 countries** from December 2010 to December 2011.

🔗 **Live Dashboard:** [uk-e-commerce-retail-analysis.streamlit.app](https://uk-e-commerce-retail-analysis.streamlit.app)

---

## Project Overview

This project covers the full analytics pipeline: raw data ingestion, cleaning, exploratory analysis, customer segmentation, and an interactive dashboard.

| Area | Details |
|------|---------|
| Dataset | UCI Online Retail (Dec 2010 – Dec 2011) |
| Raw rows | 541,909 invoice line items |
| Countries | 38 |
| Total Revenue | £10.25M |
| Customers | 4,339 identified |

---

## Dashboard Pages

The Streamlit dashboard has 5 pages:

1. **Overview** — KPIs: total revenue, customers, orders, avg order value, B2B/B2C split
2. **Data Quality** — missing values, duplicate handling, cleaning pipeline
3. **Revenue & Trends** — monthly revenue trend, B2B vs B2C breakdown, seasonality
4. **Geography & Products** — top 10 countries and best-selling products by revenue and volume
5. **Customer Segmentation** — RFM-based K-Means clustering for B2C (k=4) and B2B (k=3)

---

## Key Findings

- **B2B customers** are only 15% of the customer base but generate **42% of revenue**
- Revenue peaks sharply in **November 2011** driven by Christmas gift orders
- **United Kingdom** accounts for ~84% of revenue; Netherlands, Ireland, Germany and France lead international markets
- RFM segmentation identified actionable clusters: Champions, Loyal Customers, At Risk, Hibernating (B2C) and Strategic Accounts, Core Wholesalers, Lapsed Accounts (B2B)
- Top 20% of customers generate ~80% of revenue — strong Pareto concentration

---

## Repository Structure

```
UK_E-Commerce_Retail_Analysis/
│
├── 02 Streamlit/
│   └── app.py                  # Streamlit dashboard (5 pages)
│
├── 03 Scripts/
│   ├── OnlineRetail_EDA.ipynb          # Exploratory data analysis
│   └── Customer Segmentation.ipynb     # RFM scoring + K-Means clustering
│
├── 03_Data/
│   ├── Original Data/
│   │   └── OnlineRetail.csv            # Raw UCI dataset
│   └── Prepared Data/
│       ├── sales_clean.parquet         # Cleaned sales data (used by dashboard)
│       ├── b2c_segments.csv            # B2C RFM cluster results
│       └── b2b_segments.csv            # B2B RFM cluster results
│
├── requirements.txt
└── README.md
```

---

## Methods

**Data Cleaning**
- Removed 5,268 exact duplicate rows
- Aggregated 5,416 split line items (same invoice + product, different quantity entries)
- Excluded cancellations (negative quantity), zero-price rows, and non-product stock codes

**Customer Segmentation**
- B2B / B2C classification based on mean order quantity per line (threshold: 20 units)
- RFM features: Recency, Frequency, Monetary value, AOV, Tenure
- Log₁p transform + StandardScaler to handle skew before clustering
- K-Means with k=4 (B2C) and k=3 (B2B), clusters ranked by composite RFM score

---

## Tech Stack

- **Python** — pandas, numpy, scikit-learn
- **Visualisation** — Plotly, Matplotlib, Seaborn
- **Dashboard** — Streamlit
- **Data** — [UCI Machine Learning Repository — Online Retail](https://archive.ics.uci.edu/ml/datasets/Online+Retail)

---

## How to Run Locally

```bash
pip install -r requirements.txt
streamlit run "02 Streamlit/app.py"
```
