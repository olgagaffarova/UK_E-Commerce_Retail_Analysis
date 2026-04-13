"""
UK E-Commerce Retail Analysis
Streamlit dashboard — EDA + Customer Segmentation
Dataset: UCI Online Retail (Dec 2010 – Dec 2011)
"""

import os
import warnings

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# Paths (relative to this file's location)
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
SALES_PQ  = os.path.join(BASE_DIR, "..", "03_Data", "Prepared Data", "sales_clean.parquet")
B2C_CSV   = os.path.join(BASE_DIR, "..", "03_Data", "Prepared Data", "b2c_segments.csv")
B2B_CSV   = os.path.join(BASE_DIR, "..", "03_Data", "Prepared Data", "b2b_segments.csv")

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
B2C_COLORS = {
    "Champions":       "#2ecc71",
    "Loyal Customers": "#3498db",
    "At Risk":         "#e67e22",
    "Hibernating":     "#95a5a6",
}
B2B_COLORS = {
    "Strategic Accounts": "#1a237e",
    "Core Wholesalers":   "#5c6bc0",
    "Lapsed Accounts":    "#b0bec5",
}

# ──────────────────────────────────────────────────────────────────────────────
# Data loading & cleaning (cached)
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading sales data …")
def load_sales():
    return pd.read_parquet(SALES_PQ)


@st.cache_data(show_spinner="Loading segmentation results …")
def load_segments():
    b2c = pd.read_csv(B2C_CSV)
    b2b = pd.read_csv(B2B_CSV)
    return b2c, b2b


# ──────────────────────────────────────────────────────────────────────────────
# Page helpers
# ──────────────────────────────────────────────────────────────────────────────
def kpi(col, label, value, delta=None):
    col.metric(label, value, delta)


def section(title, body):
    st.subheader(title)
    st.markdown(body)


# ──────────────────────────────────────────────────────────────────────────────
# Page 1 — Overview
# ──────────────────────────────────────────────────────────────────────────────
def page_overview(sales):
    st.title("UK Online Retail — Dashboard Overview")
    st.markdown(
        """
        This dashboard analyses the **UCI Online Retail dataset**, covering transactions from a
        UK-based wholesale gift retailer between **December 2010 and December 2011**.
        The dataset contains over **540,000 invoice line items** across **38 countries**.

        Use the sidebar to navigate between pages:

        | Page | Contents |
        |------|----------|
        | Overview | Dataset snapshot & KPIs |
        | Data Quality | Missing values, duplicates, cleaning steps |
        | Revenue & Trends | Monthly revenue, B2B vs B2C split |
        | Geography & Products | Top countries and best-selling products |
        | Customer Segmentation | RFM-based K-Means clustering (B2C + B2B) |
        """
    )

    st.divider()
    st.subheader("Key Business Metrics")

    total_rev    = sales["Revenue"].sum()
    n_customers  = sales["CustomerID"].dropna().nunique()
    n_invoices   = sales["InvoiceNo"].nunique()
    n_countries  = sales["Country"].nunique()
    avg_order    = sales.groupby("InvoiceNo")["Revenue"].sum().mean()
    b2b_rev_share = (
        sales[sales["CustomerType"] == "B2B"]["Revenue"].sum() / total_rev * 100
    )

    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)
    kpi(c1, "Total Revenue",       f"£{total_rev:,.0f}")
    kpi(c2, "Unique Customers",    f"{n_customers:,}")
    kpi(c3, "Total Orders",        f"{n_invoices:,}")
    kpi(c4, "Countries Served",    f"{n_countries}")
    kpi(c5, "Avg Order Value",     f"£{avg_order:,.2f}")
    kpi(c6, "B2B Revenue Share",   f"{b2b_rev_share:.1f}%")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        section("Dataset at a Glance", "")
        st.dataframe(
            pd.DataFrame(
                {
                    "Metric": [
                        "Raw rows", "Rows after cleaning", "Date range",
                        "Unique products", "Missing CustomerID",
                    ],
                    "Value": [
                        "541,909",
                        f"{len(sales):,}",
                        "Dec 2010 – Dec 2011",
                        f"{sales['StockCode'].nunique():,}",
                        "24.9 %",
                    ],
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

    with col_r:
        section("Customer Mix", "")
        seg_counts = sales[sales["CustomerType"].notna()].groupby("CustomerType").agg(
            Customers=("CustomerID", "nunique"),
            Revenue=("Revenue", "sum"),
        ).reset_index()
        seg_counts["Revenue Share %"] = (
            seg_counts["Revenue"] / seg_counts["Revenue"].sum() * 100
        ).round(1)
        seg_counts["Revenue"] = seg_counts["Revenue"].apply(lambda x: f"£{x:,.0f}")
        st.dataframe(seg_counts, hide_index=True, use_container_width=True)

    st.divider()
    st.markdown(
        """
        > **Key takeaway:** B2B customers are only **15 %** of the customer base but generate
        > **42 %** of all revenue — making wholesale retention a top strategic priority.
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# Page 2 — Data Quality
# ──────────────────────────────────────────────────────────────────────────────
def page_data_quality(sales):
    st.title("Data Quality & Cleaning")
    st.markdown(
        """
        Before any analysis, the raw dataset required several cleaning steps.
        Understanding *why* data is dirty — and how it was fixed — is essential for
        trusting the downstream results.
        """
    )

    st.divider()

    # ── Missing values ────────────────────────────────────────────────────────
    section(
        "1. Missing Values",
        """
        Two columns contain nulls: **Description** (0.3 %) and **CustomerID** (24.9 %).
        Description nulls are minor and don't affect revenue calculations.
        CustomerID nulls represent **anonymous transactions** — orders placed without
        an account — and are excluded from customer-level analyses.
        """,
    )

    missing = pd.DataFrame(
        {
            "Column":  ["InvoiceNo", "StockCode", "Description",
                        "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"],
            "Null %":  [0.0, 0.0, 0.27, 0.0, 0.0, 0.0, 24.93, 0.0],
        }
    )
    fig_miss = px.bar(
        missing,
        x="Column", y="Null %",
        title="Missing Value Rate per Column (%)",
        color="Null %",
        color_continuous_scale="Reds",
        text="Null %",
    )
    fig_miss.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig_miss.update_layout(
        coloraxis_showscale=False,
        plot_bgcolor="white",
        height=380,
        yaxis_title="Missing %",
    )
    st.plotly_chart(fig_miss, use_container_width=True)

    st.divider()

    # ── Duplicates ────────────────────────────────────────────────────────────
    section(
        "2. Duplicate Rows",
        """
        The raw dataset contains two types of duplicate problems:

        | Type | Count | Root Cause | Fix |
        |------|-------|------------|-----|
        | **Exact full-row duplicates** | 5,268 | Data pipeline re-ingestion | `drop_duplicates()` |
        | **Same InvoiceNo + StockCode, different Quantity** | 5,416 rows | Split line items entered separately | Aggregate with `sum(Quantity)` |

        After both steps, **531,808 rows** remain (down from 541,909).
        """,
    )

    dup_data = pd.DataFrame(
        {
            "Stage":   ["Raw", "After drop exact dups", "After aggregate split items"],
            "Rows":    [541909, 536641, 531808],
        }
    )
    fig_dup = px.bar(
        dup_data,
        x="Stage", y="Rows",
        title="Row Count at Each Cleaning Stage",
        color="Rows",
        color_continuous_scale="Blues",
        text="Rows",
    )
    fig_dup.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_dup.update_layout(
        coloraxis_showscale=False,
        plot_bgcolor="white",
        height=380,
    )
    st.plotly_chart(fig_dup, use_container_width=True)

    st.divider()

    # ── Cancellations & noise ─────────────────────────────────────────────────
    section(
        "3. Cancellations & Non-Product Rows",
        """
        The cleaned dataset still contains noise that must be excluded from revenue analysis:

        - **Negative Quantity rows** — returns and cancellations (InvoiceNo starts with 'C')
        - **Zero or negative UnitPrice** — adjustments, samples, write-offs
        - **Fee / administrative StockCodes** — `AMAZONFEE`, `POST`, `BANK CHARGES`, etc.

        After applying these filters, the final **sales dataset** contains **517,778 rows**.
        """,
    )

    removal_df = pd.DataFrame(
        {
            "Filter":        ["Cancellations (Qty ≤ 0)", "Zero/negative UnitPrice", "Fee StockCodes", "Net sales rows"],
            "Rows Affected": [9200, 2100, 2730, 517778],
        }
    )

    fig_rem = px.bar(
        removal_df.iloc[:-1],
        x="Filter", y="Rows Affected",
        title="Rows Removed by Filter Type (approx.)",
        color="Rows Affected",
        color_continuous_scale="Oranges",
        text="Rows Affected",
    )
    fig_rem.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_rem.update_layout(
        coloraxis_showscale=False,
        plot_bgcolor="white",
        height=380,
    )
    st.plotly_chart(fig_rem, use_container_width=True)

    st.markdown(
        """
        > **Summary:** The cleaning pipeline removed ~4.5 % of raw rows through
        > deduplication and exclusion of noise, leaving a high-quality sales dataset
        > of 517,778 line items totalling **£10.25M in revenue**.
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# Page 3 — Revenue & Trends
# ──────────────────────────────────────────────────────────────────────────────
def page_revenue(sales):
    st.title("Revenue & Time Trends")
    st.markdown(
        """
        Revenue analysis answers the most fundamental question: **when and who drives the money?**
        Monthly trends reveal seasonality, while the B2B/B2C breakdown shows structural dynamics
        that inform pricing and retention strategy.
        """
    )

    st.divider()

    # ── Monthly revenue ───────────────────────────────────────────────────────
    section(
        "Monthly Revenue Trend",
        """
        Gift retail is highly seasonal. Revenue builds through Q3 and peaks sharply in
        **November 2011** as customers place Christmas orders. The dip in January 2011
        reflects post-holiday slowdown — a normal retail pattern.
        """,
    )

    monthly = (
        sales.groupby("YearMonth")["Revenue"]
        .sum()
        .reset_index()
    )
    monthly["YearMonth"] = monthly["YearMonth"].astype(str)
    peak_month = monthly.loc[monthly["Revenue"].idxmax(), "YearMonth"]

    fig_monthly = px.bar(
        monthly,
        x="YearMonth",
        y="Revenue",
        title="Monthly Revenue (Dec 2010 – Dec 2011)",
        labels={"YearMonth": "Month", "Revenue": "Revenue (£)"},
        color="Revenue",
        color_continuous_scale="Blues",
        text="Revenue",
    )
    fig_monthly.update_traces(texttemplate="£%{text:,.0f}", textposition="outside")
    fig_monthly.update_layout(
        xaxis_tickangle=-45,
        coloraxis_showscale=False,
        plot_bgcolor="white",
        height=460,
        margin=dict(t=60, b=80),
    )
    st.plotly_chart(fig_monthly, use_container_width=True)
    st.caption(f"Peak month: **{peak_month}** — highest single-month revenue in the dataset.")

    st.divider()

    # ── B2B vs B2C ────────────────────────────────────────────────────────────
    section(
        "B2B vs B2C Revenue Breakdown",
        """
        The dataset serves two structurally different customer types, classified by average
        line-item quantity:

        - **B2B (Wholesale):** mean qty > 20 units per line → bulk purchasing behaviour
        - **B2C (Retail):** mean qty ≤ 20 units per line → individual consumer behaviour

        Despite being only **15 %** of customers, B2B accounts generate **42 %** of revenue —
        driven by much larger average order sizes.
        """,
    )

    seg = (
        sales[sales["CustomerType"].notna()]
        .groupby("CustomerType")
        .agg(
            TotalRevenue=("Revenue", "sum"),
            AvgLineValue=("Revenue", "mean"),
            Customers=("CustomerID", "nunique"),
        )
        .reset_index()
    )
    seg["rev_share"] = seg["TotalRevenue"] / seg["TotalRevenue"].sum() * 100
    seg["cust_share"] = seg["Customers"] / seg["Customers"].sum() * 100

    col1, col2 = st.columns(2)

    with col1:
        fig_rev = px.bar(
            seg,
            x="CustomerType",
            y="TotalRevenue",
            title="Total Revenue by Segment",
            color="CustomerType",
            color_discrete_map={"B2B": "#1f77b4", "B2C": "#aec7e8"},
            text="TotalRevenue",
            labels={"TotalRevenue": "Revenue (£)", "CustomerType": ""},
        )
        fig_rev.update_traces(texttemplate="£%{text:,.0f}", textposition="outside")
        fig_rev.update_layout(showlegend=False, plot_bgcolor="white", height=380)
        st.plotly_chart(fig_rev, use_container_width=True)

    with col2:
        fig_avg = px.bar(
            seg,
            x="CustomerType",
            y="AvgLineValue",
            title="Avg Line Item Value by Segment",
            color="CustomerType",
            color_discrete_map={"B2B": "#1f77b4", "B2C": "#aec7e8"},
            text="AvgLineValue",
            labels={"AvgLineValue": "Avg Revenue per Line (£)", "CustomerType": ""},
        )
        fig_avg.update_traces(texttemplate="£%{text:.2f}", textposition="outside")
        fig_avg.update_layout(showlegend=False, plot_bgcolor="white", height=380)
        st.plotly_chart(fig_avg, use_container_width=True)

    st.divider()

    # ── Monthly B2B vs B2C split ──────────────────────────────────────────────
    section(
        "Monthly Revenue by Segment",
        """
        B2B revenue is more stable month-to-month (repeat wholesale orders), while B2C
        peaks more sharply around the holiday season — consistent with seasonal gift purchasing.
        """,
    )

    monthly_seg = (
        sales[sales["CustomerType"].notna()]
        .groupby(["YearMonth", "CustomerType"])["Revenue"]
        .sum()
        .reset_index()
    )
    monthly_seg["YearMonth"] = monthly_seg["YearMonth"].astype(str)

    fig_seg_time = px.bar(
        monthly_seg,
        x="YearMonth",
        y="Revenue",
        color="CustomerType",
        title="Monthly Revenue Split: B2B vs B2C",
        labels={"YearMonth": "Month", "Revenue": "Revenue (£)", "CustomerType": "Segment"},
        color_discrete_map={"B2B": "#1f77b4", "B2C": "#aec7e8"},
        barmode="stack",
    )
    fig_seg_time.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor="white",
        height=420,
        margin=dict(t=60, b=80),
    )
    st.plotly_chart(fig_seg_time, use_container_width=True)

    st.markdown(
        """
        > **Key Takeaways:**
        > - November 2011 is the peak revenue month, driven primarily by B2C holiday orders.
        > - B2B revenue is relatively flat, reflecting stable wholesale reorder cycles.
        > - The B2B avg line value (£99.50) is **7× higher** than B2C (£14.44),
        >   confirming the structural difference in purchasing behaviour.
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# Page 4 — Geography & Products
# ──────────────────────────────────────────────────────────────────────────────
def page_geo_products(sales):
    st.title("Geography & Products")
    st.markdown(
        """
        Where does revenue come from geographically, and which products drive the most value?
        Understanding this guides inventory allocation, logistics planning, and marketing spend.
        """
    )

    st.divider()

    # ── Top countries ─────────────────────────────────────────────────────────
    section(
        "Top 10 Countries by Revenue",
        """
        The **United Kingdom** dominates, accounting for ~84 % of revenue — consistent with
        a UK-based retailer. The remaining 16 % is spread across Europe and beyond, with
        **Netherlands**, **EIRE (Ireland)**, **Germany**, and **France** as the leading
        international markets.
        """,
    )

    top_geo = (
        sales.groupby("Country")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
        .sort_values("Revenue")
    )

    fig_geo = px.bar(
        top_geo,
        x="Revenue",
        y="Country",
        orientation="h",
        title="Top 10 Countries by Revenue",
        color="Revenue",
        color_continuous_scale="Blues",
        text="Revenue",
        labels={"Revenue": "Revenue (£)", "Country": ""},
    )
    fig_geo.update_traces(texttemplate="£%{text:,.0f}", textposition="outside")
    fig_geo.update_layout(
        coloraxis_showscale=False,
        plot_bgcolor="white",
        height=440,
        margin=dict(l=0, r=100, t=50),
    )
    st.plotly_chart(fig_geo, use_container_width=True)

    uk_rev   = sales[sales["Country"] == "United Kingdom"]["Revenue"].sum()
    intl_rev = sales[sales["Country"] != "United Kingdom"]["Revenue"].sum()
    total    = sales["Revenue"].sum()

    col1, col2 = st.columns(2)
    col1.metric("UK Revenue",            f"£{uk_rev:,.0f}",   f"{uk_rev/total:.1%} of total")
    col2.metric("International Revenue", f"£{intl_rev:,.0f}", f"{intl_rev/total:.1%} of total")

    st.divider()

    # ── Top products ──────────────────────────────────────────────────────────
    section(
        "Top 10 Products by Revenue",
        """
        The top products by revenue are dominated by **decorative home items** and
        **party/gift accessories** — matching the retailer's wholesale-gift positioning.
        The *REGENCY CAKESTAND 3 TIER* leads by value at over £174k.

        Notably, products that top the **units sold** chart aren't always the highest
        revenue earners — low unit-price items like *PAPER CRAFT, LITTLE BIRDIE* sell
        in enormous volumes but yield less revenue per unit.
        """,
    )

    top_rev = (
        sales.groupby("Description")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
        .sort_values("Revenue")
    )
    top_qty = (
        sales.groupby("Description")["Quantity"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
        .sort_values("Quantity")
    )

    tab1, tab2 = st.tabs(["By Revenue", "By Units Sold"])

    with tab1:
        fig_prod_rev = px.bar(
            top_rev,
            x="Revenue",
            y="Description",
            orientation="h",
            title="Top 10 Products — Revenue",
            color="Revenue",
            color_continuous_scale="Blues",
            text="Revenue",
            labels={"Revenue": "Revenue (£)", "Description": ""},
        )
        fig_prod_rev.update_traces(texttemplate="£%{text:,.0f}", textposition="outside")
        fig_prod_rev.update_layout(
            coloraxis_showscale=False,
            plot_bgcolor="white",
            height=440,
            margin=dict(l=0, r=100, t=50),
        )
        st.plotly_chart(fig_prod_rev, use_container_width=True)

    with tab2:
        fig_prod_qty = px.bar(
            top_qty,
            x="Quantity",
            y="Description",
            orientation="h",
            title="Top 10 Products — Units Sold",
            color="Quantity",
            color_continuous_scale="Greens",
            text="Quantity",
            labels={"Quantity": "Units Sold", "Description": ""},
        )
        fig_prod_qty.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_prod_qty.update_layout(
            coloraxis_showscale=False,
            plot_bgcolor="white",
            height=440,
            margin=dict(l=0, r=60, t=50),
        )
        st.plotly_chart(fig_prod_qty, use_container_width=True)

    st.markdown(
        """
        > **Insight:** The divergence between revenue rank and volume rank highlights the
        > importance of **margin analysis** — high-volume low-price items may not justify
        > shelf space if they don't contribute proportionally to profit.
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# Page 5 — Customer Segmentation
# ──────────────────────────────────────────────────────────────────────────────
def page_segmentation(b2c, b2b):
    st.title("Customer Segmentation — RFM + K-Means")
    st.markdown(
        """
        Customers were segmented using **RFM (Recency, Frequency, Monetary)** features,
        processed independently for B2C and B2B cohorts.

        | Step | Detail |
        |------|--------|
        | Feature engineering | Recency (days since last order), Frequency (unique invoices), Monetary (total £), AOV, Tenure |
        | RFM scoring | Quintile scores 1–5 within each segment independently |
        | Preprocessing | Log₁p transform + StandardScaler to compress skew |
        | Algorithm | K-Means (B2C: k=4, B2B: k=3) |
        | Cluster labelling | Ranked by mean composite RFM_total score |

        B2C and B2B were clustered **separately** because their purchasing dynamics differ
        too much to cluster together meaningfully.
        """
    )

    st.divider()

    # ════════════════════════════════════════════════════════════════════════
    # B2C Segmentation
    # ════════════════════════════════════════════════════════════════════════
    st.header("B2C Customer Segments (k = 4)")
    st.markdown(
        """
        **3,686 retail customers** were clustered into 4 segments based on RFM behaviour.
        Segments are named by business interpretation (highest RFM composite = Champions).

        | Segment | Typical Behaviour |
        |---------|------------------|
        | **Champions** | Bought recently, buy often, spend the most |
        | **Loyal Customers** | Buy regularly, solid spend — Champions in waiting |
        | **At Risk** | Previously valuable, now going quiet |
        | **Hibernating** | Haven't purchased in a long time, low historical value |
        """
    )

    # B2C Radar
    section("RFM Radar — B2C Segments", "")
    radar_b2c = b2c.groupby("Segment")[["R_score", "F_score", "M_score"]].mean()
    radar_norm = (radar_b2c - 1.0) / 4.0 * 100.0
    categories = ["Recency", "Frequency", "Monetary"]
    theta = categories + [categories[0]]

    fig_radar_b2c = go.Figure()
    for seg in ["Champions", "Loyal Customers", "At Risk", "Hibernating"]:
        if seg not in radar_norm.index:
            continue
        vals = list(radar_norm.loc[seg]) + [radar_norm.loc[seg].iloc[0]]
        fig_radar_b2c.add_trace(
            go.Scatterpolar(
                r=vals, theta=theta, fill="toself", name=seg,
                line=dict(color=B2C_COLORS.get(seg, "#95a5a6"), width=2),
            )
        )
    fig_radar_b2c.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="B2C Segment RFM Profiles (normalised 0–100)",
        height=450,
    )
    st.plotly_chart(fig_radar_b2c, use_container_width=True)
    st.caption(
        "Champions score high on all three dimensions. At Risk and Hibernating show "
        "lower recency scores (meaning they haven't bought recently)."
    )

    # B2C Scatter
    section(
        "Recency vs Monetary — B2C",
        "Each dot is a customer. Size = order frequency. Champions cluster in the "
        "bottom-right (low recency = recent buyers, high monetary = high spenders).",
    )
    b2c_scatter = b2c.copy()
    b2c_scatter["monetary_log"] = np.log1p(b2c_scatter["monetary"])

    fig_scatter_b2c = px.scatter(
        b2c_scatter,
        x="recency",
        y="monetary_log",
        color="Segment",
        size="frequency",
        size_max=20,
        color_discrete_map=B2C_COLORS,
        opacity=0.65,
        title="B2C Segments: Recency vs Revenue (bubble = frequency)",
        labels={
            "recency":      "Recency (days since last purchase)",
            "monetary_log": "log(Total Revenue £)",
            "frequency":    "Order Frequency",
        },
    )
    fig_scatter_b2c.update_layout(height=480, plot_bgcolor="white")
    st.plotly_chart(fig_scatter_b2c, use_container_width=True)

    # B2C bar summary
    section("Segment Size & Revenue — B2C", "")
    b2c_prof = (
        b2c.groupby("Segment")
        .agg(
            n_customers=("CustomerID", "count"),
            total_revenue=("monetary", "sum"),
            avg_monetary=("monetary", "mean"),
        )
        .reset_index()
    )
    b2c_prof["rev_share"] = b2c_prof["total_revenue"] / b2c_prof["total_revenue"].sum() * 100

    fig_b2c_bars = make_subplots(
        rows=1, cols=3,
        subplot_titles=("Customers per Segment", "Revenue Share (%)", "Avg Monetary Value (£)"),
    )
    seg_order_b2c = ["Champions", "Loyal Customers", "At Risk", "Hibernating"]
    b2c_plot = b2c_prof.set_index("Segment").reindex(seg_order_b2c).reset_index().dropna()
    bar_colors_b2c = [B2C_COLORS.get(s, "#95a5a6") for s in b2c_plot["Segment"]]

    fig_b2c_bars.add_trace(
        go.Bar(x=b2c_plot["Segment"], y=b2c_plot["n_customers"],
               marker_color=bar_colors_b2c, showlegend=False,
               text=b2c_plot["n_customers"], textposition="outside"),
        row=1, col=1,
    )
    fig_b2c_bars.add_trace(
        go.Bar(x=b2c_plot["Segment"], y=b2c_plot["rev_share"].round(1),
               marker_color=bar_colors_b2c, showlegend=False,
               text=b2c_plot["rev_share"].round(1), textposition="outside",
               texttemplate="%{text:.1f}%"),
        row=1, col=2,
    )
    fig_b2c_bars.add_trace(
        go.Bar(x=b2c_plot["Segment"], y=b2c_plot["avg_monetary"].round(0),
               marker_color=bar_colors_b2c, showlegend=False,
               text=b2c_plot["avg_monetary"].round(0), textposition="outside",
               texttemplate="£%{text:,.0f}"),
        row=1, col=3,
    )
    fig_b2c_bars.update_layout(
        height=420, plot_bgcolor="white",
        title_text="B2C Segment Summary",
    )
    st.plotly_chart(fig_b2c_bars, use_container_width=True)

    st.markdown(
        """
        > **B2C Insight:** Champions are a small but disproportionately valuable group —
        > they should receive VIP treatment, early access, and referral incentives.
        > At Risk customers represent recoverable revenue; a time-limited reactivation
        > campaign targeting the high-value subset is the highest-ROI intervention.
        """
    )

    st.divider()

    # ════════════════════════════════════════════════════════════════════════
    # B2B Segmentation
    # ════════════════════════════════════════════════════════════════════════
    st.header("B2B Customer Segments (k = 3)")
    st.markdown(
        """
        **653 wholesale customers** were clustered into 3 segments.
        B2B dynamics differ significantly: shorter reorder cycles (60-day churn window
        vs 90-day for B2C), much larger average order values, and higher revenue concentration.

        | Segment | Typical Behaviour |
        |---------|------------------|
        | **Strategic Accounts** | Anchor accounts — high frequency, high monetary. Losing one is painful. |
        | **Core Wholesalers** | Regular, consistent buyers — upgrade path to Strategic exists. |
        | **Lapsed Accounts** | Formerly purchasing, now silent — risk of permanent churn. |
        """
    )

    # B2B Radar
    section("RFM Radar — B2B Segments", "")
    radar_b2b = b2b.groupby("Segment")[["R_score", "F_score", "M_score"]].mean()
    radar_b2b_norm = (radar_b2b - 1.0) / 4.0 * 100.0

    fig_radar_b2b = go.Figure()
    for seg in ["Strategic Accounts", "Core Wholesalers", "Lapsed Accounts"]:
        if seg not in radar_b2b_norm.index:
            continue
        vals = list(radar_b2b_norm.loc[seg]) + [radar_b2b_norm.loc[seg].iloc[0]]
        fig_radar_b2b.add_trace(
            go.Scatterpolar(
                r=vals, theta=theta, fill="toself", name=seg,
                line=dict(color=B2B_COLORS.get(seg, "#607d8b"), width=2),
            )
        )
    fig_radar_b2b.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="B2B Segment RFM Profiles (normalised 0–100)",
        height=450,
    )
    st.plotly_chart(fig_radar_b2b, use_container_width=True)

    # B2B Scatter
    section(
        "Recency vs Monetary — B2B",
        "Strategic Accounts sit bottom-right (recent + high revenue). "
        "Lapsed Accounts drift top-left (long since last order, lower monetary).",
    )
    b2b_scatter = b2b.copy()
    b2b_scatter["monetary_log"] = np.log1p(b2b_scatter["monetary"])

    fig_scatter_b2b = px.scatter(
        b2b_scatter,
        x="recency",
        y="monetary_log",
        color="Segment",
        size="frequency",
        size_max=25,
        color_discrete_map=B2B_COLORS,
        opacity=0.75,
        title="B2B Segments: Recency vs Revenue (bubble = frequency)",
        labels={
            "recency":      "Recency (days since last order)",
            "monetary_log": "log(Total Revenue £)",
            "frequency":    "Order Frequency",
        },
    )
    fig_scatter_b2b.update_layout(height=480, plot_bgcolor="white")
    st.plotly_chart(fig_scatter_b2b, use_container_width=True)

    # B2B bar summary
    section("Segment Size & Revenue — B2B", "")
    b2b_prof = (
        b2b.groupby("Segment")
        .agg(
            n_customers=("CustomerID", "count"),
            total_revenue=("monetary", "sum"),
            avg_monetary=("monetary", "mean"),
        )
        .reset_index()
    )
    b2b_prof["rev_share"] = b2b_prof["total_revenue"] / b2b_prof["total_revenue"].sum() * 100

    fig_b2b_bars = make_subplots(
        rows=1, cols=3,
        subplot_titles=("Accounts per Segment", "Revenue Share (%)", "Avg Monetary (£)"),
    )
    seg_order_b2b = ["Strategic Accounts", "Core Wholesalers", "Lapsed Accounts"]
    b2b_plot = b2b_prof.set_index("Segment").reindex(seg_order_b2b).reset_index().dropna()
    bar_colors_b2b = [B2B_COLORS.get(s, "#607d8b") for s in b2b_plot["Segment"]]

    fig_b2b_bars.add_trace(
        go.Bar(x=b2b_plot["Segment"], y=b2b_plot["n_customers"],
               marker_color=bar_colors_b2b, showlegend=False,
               text=b2b_plot["n_customers"], textposition="outside"),
        row=1, col=1,
    )
    fig_b2b_bars.add_trace(
        go.Bar(x=b2b_plot["Segment"], y=b2b_plot["rev_share"].round(1),
               marker_color=bar_colors_b2b, showlegend=False,
               text=b2b_plot["rev_share"].round(1), textposition="outside",
               texttemplate="%{text:.1f}%"),
        row=1, col=2,
    )
    fig_b2b_bars.add_trace(
        go.Bar(x=b2b_plot["Segment"], y=b2b_plot["avg_monetary"].round(0),
               marker_color=bar_colors_b2b, showlegend=False,
               text=b2b_plot["avg_monetary"].round(0), textposition="outside",
               texttemplate="£%{text:,.0f}"),
        row=1, col=3,
    )
    fig_b2b_bars.update_layout(
        height=420, plot_bgcolor="white",
        title_text="B2B Segment Summary",
    )
    st.plotly_chart(fig_b2b_bars, use_container_width=True)

    st.markdown(
        """
        > **B2B Insight:** Lapsed Accounts represent the highest-risk / highest-opportunity
        > category — they generated significant historical revenue but have gone dark.
        > A personalised outreach campaign (dedicated account manager contact, volume
        > discount offer) should be the immediate priority.
        """
    )

    st.divider()

    # ── Revenue Pareto ────────────────────────────────────────────────────────
    st.header("Revenue Concentration — Pareto Analysis")
    st.markdown(
        """
        Does the classic **80/20 rule** hold? The Pareto curve below shows the cumulative
        revenue contribution as customers are ranked from highest to lowest spenders.
        """
    )

    all_customers = (
        pd.concat([b2c[["CustomerID", "monetary"]], b2b[["CustomerID", "monetary"]]])
        .sort_values("monetary", ascending=False)
        .reset_index(drop=True)
    )
    all_customers["cum_rev"]      = all_customers["monetary"].cumsum()
    all_customers["cum_rev_pct"]  = all_customers["cum_rev"] / all_customers["monetary"].sum() * 100
    all_customers["cum_cust_pct"] = (np.arange(1, len(all_customers) + 1) / len(all_customers)) * 100

    idx_80 = int((all_customers["cum_rev_pct"] >= 80).idxmax())
    cust_at_80 = all_customers.loc[idx_80, "cum_cust_pct"]

    fig_pareto = go.Figure()
    fig_pareto.add_trace(
        go.Scatter(
            x=all_customers["cum_cust_pct"],
            y=all_customers["cum_rev_pct"],
            mode="lines",
            name="Cumulative Revenue",
            line=dict(color="#1f77b4", width=2),
            fill="tozeroy",
            fillcolor="rgba(31,119,180,0.15)",
        )
    )
    fig_pareto.add_hline(y=80, line_dash="dash", line_color="red",
                         annotation_text="80% revenue threshold", annotation_position="top right")
    fig_pareto.add_vline(x=cust_at_80, line_dash="dot", line_color="orange",
                         annotation_text=f"{cust_at_80:.1f}% of customers",
                         annotation_position="bottom right")
    fig_pareto.update_layout(
        title="Revenue Pareto: Cumulative Revenue vs Customer %",
        xaxis_title="Cumulative % of Customers (ranked by revenue)",
        yaxis_title="Cumulative % of Revenue",
        plot_bgcolor="white",
        height=440,
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

    st.info(
        f"**{cust_at_80:.1f}% of customers generate 80% of revenue** — confirming a "
        f"strong Pareto concentration. Retention of the top revenue tier is far more "
        f"valuable than equivalent acquisition spend."
    )

    st.divider()

    # ── Conclusion ────────────────────────────────────────────────────────────
    st.header("Conclusion & Strategic Recommendations")

    st.markdown(
        """
        ### What the Analysis Found

        This end-to-end analysis of the UK Online Retail dataset reveals a business with
        strong fundamentals and clear optimisation levers:

        ---

        #### Revenue & Seasonality
        - Total revenue: **£10.25M** over 13 months
        - Q4 seasonality is pronounced — **November 2011** is the peak month, driven by
          holiday gift purchasing
        - A modest post-holiday dip in Jan–Feb 2011 is followed by steady growth through Q3

        ---

        #### Customer Structure
        - **85 %** of customers are B2C (retail) but generate only **58 %** of revenue
        - **15 %** are B2B (wholesale) but generate **42 %** of revenue at 7× the average order value
        - Revenue is highly concentrated: a small minority of customers drives the majority of income

        ---

        #### B2C Action Plan

        | Segment | Priority | Recommended Action |
        |---------|----------|--------------------|
        | Champions | Protect | VIP programme, early product access, referral incentive. No heavy discounting. |
        | Loyal Customers | Grow | Personalised recommendations, loyalty tier upgrade, frequency nudge. |
        | At Risk | Recover | Time-limited reactivation email (10–15 % off, 7-day expiry). Focus on high-value sub-group. |
        | Hibernating | Re-engage or write off | Low-cost email re-engagement; accept higher churn rate here. |

        ---

        #### B2B Action Plan

        | Segment | Priority | Recommended Action |
        |---------|----------|--------------------|
        | Strategic Accounts | Protect at all costs | Dedicated account manager. Quarterly reviews. Locked volume discounts. |
        | Core Wholesalers | Grow | Frequency nudge. Product range expansion pitch. Growth incentive at +20 % volume. |
        | Lapsed Accounts | Win back | Personalised outreach from sales team. Understand why they stopped. Make a concrete offer. |

        ---

        #### Key Metrics to Track Going Forward

        - **Champion retention rate** (target > 85 %)
        - **At Risk reactivation conversion** (target > 15 % within 30 days of campaign)
        - **Lapsed B2B reactivation** (target > 20 % of lapsed accounts placing one order within 90 days)
        - **B2B revenue share** — should be maintained or grown as a strategic priority
        - **Seasonal revenue smoothing** — explore Q1/Q2 promotional campaigns to reduce dependence on Q4

        ---

        > The segmentation framework built here provides a **living customer intelligence layer**.
        > It should be re-run quarterly as new transaction data arrives — customer segments
        > shift over time, and the action plan must keep pace.
        """
    )


# ──────────────────────────────────────────────────────────────────────────────
# Main app
# ──────────────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="UK E-Commerce Analytics",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar navigation
    st.sidebar.title("UK E-Commerce Retail")
    st.sidebar.markdown("**Dec 2010 – Dec 2011**")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigate",
        [
            "Overview",
            "Data Quality",
            "Revenue & Trends",
            "Geography & Products",
            "Customer Segmentation",
        ],
    )

    st.sidebar.divider()
    st.sidebar.markdown(
        "**Dataset:** UCI Online Retail  \n"
        "**Rows (raw):** 541,909  \n"
        "**Countries:** 38  \n"
        "**Period:** 13 months"
    )

    # Load data
    sales = load_sales()
    b2c, b2b = load_segments()

    # Route pages
    if page == "Overview":
        page_overview(sales)
    elif page == "Data Quality":
        page_data_quality(sales)
    elif page == "Revenue & Trends":
        page_revenue(sales)
    elif page == "Geography & Products":
        page_geo_products(sales)
    elif page == "Customer Segmentation":
        page_segmentation(b2c, b2b)


if __name__ == "__main__":
    main()
