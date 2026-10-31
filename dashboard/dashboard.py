import os

import folium
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="Dashboard E-Commerce Olist", page_icon="🛒", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BLUE, GREY, RED, ORANGE = "#72BCD4", "#D3D3D3", "#E4572E", "#F2A541"
STATUS_ORDER = ["Tepat waktu", "Telat 1-3 hari", "Telat >3 hari"]
SEGMENT_ORDER = [
    "Champions", "Loyal Customers", "Recent Big Spenders",
    "Recent Customers", "At Risk", "Lost Customers",
]


@st.cache_data
def load_data():
    cols = [
        "order_id", "customer_unique_id", "customer_state",
        "order_purchase_timestamp", "order_month", "delivery_status",
        "is_late", "review_score", "price", "product_category_name_english",
    ]
    df = pd.read_csv(
        os.path.join(BASE_DIR, "main_data.csv"),
        usecols=cols,
        parse_dates=["order_purchase_timestamp"],
    )
    df["is_late"] = df["is_late"].astype(bool)
    geo = pd.read_csv(
        os.path.join(BASE_DIR, "state_geo.csv"),
        usecols=["customer_state", "lat", "lng"],
    )
    return df, geo


def build_rfm(df):
    recent_date = df["order_purchase_timestamp"].max()
    rfm = df.groupby("customer_unique_id", as_index=False).agg(
        last_order=("order_purchase_timestamp", "max"),
        frequency=("order_id", "nunique"),
        monetary=("price", "sum"),
    )
    rfm["recency"] = (recent_date - rfm["last_order"]).dt.days
    m_q75 = rfm["monetary"].quantile(0.75)

    kondisi = [
        (rfm["frequency"] >= 2) & (rfm["recency"] <= 180),
        (rfm["frequency"] >= 2),
        (rfm["recency"] <= 180) & (rfm["monetary"] >= m_q75),
        (rfm["recency"] <= 180),
        (rfm["recency"] <= 365),
    ]
    rfm["customer_segment"] = np.select(kondisi, SEGMENT_ORDER[:5], default="Lost Customers")
    return rfm


def risk_color(pct, nasional):
    if pct >= 15:
        return RED
    if pct >= nasional:
        return ORANGE
    return BLUE


def fmt(value):
    return f"{value:.2f}" if pd.notna(value) else "-"


def show_fig(fig):
    st.pyplot(fig)
    plt.close(fig)


df, geo_df = load_data()

st.title("🛒 Dashboard Analisis E-Commerce Olist")
st.caption(
    "Pesanan berstatus delivered, Januari 2017 - Agustus 2018. "
    "Revenue dalam BRL (Real Brasil), dihitung dari harga produk tanpa ongkos kirim."
)

st.sidebar.header("Filter Data")

min_date = df["order_purchase_timestamp"].min().date()
max_date = df["order_purchase_timestamp"].max().date()
date_range = st.sidebar.date_input(
    "Rentang tanggal pembelian",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, (tuple, list)) and len(date_range) > 0:
    start_date, end_date = date_range[0], date_range[-1]
else:
    start_date = end_date = date_range

all_states = sorted(df["customer_state"].unique())
selected_states = st.sidebar.multiselect("State pelanggan", options=all_states, default=all_states)

if not selected_states:
    st.warning("Pilih minimal satu state pada filter di sidebar.")
    st.stop()

mask = (
    (df["order_purchase_timestamp"] >= pd.Timestamp(start_date))
    & (df["order_purchase_timestamp"] < pd.Timestamp(end_date) + pd.Timedelta(days=1))
    & (df["customer_state"].isin(selected_states))
)
fdf = df[mask]

if fdf.empty:
    st.warning("Tidak ada data pada filter yang dipilih. Ubah rentang tanggal atau state.")
    st.stop()

orders_df = fdf.drop_duplicates(subset="order_id")

avg_review = orders_df["review_score"].mean()
late_pct_all = orders_df["is_late"].mean() * 100

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Revenue", f"{fdf['price'].sum():,.0f} BRL")
c2.metric("Jumlah Pesanan", f"{len(orders_df):,}")
c3.metric("Pelanggan Unik", f"{fdf['customer_unique_id'].nunique():,}")
c4.metric("Rata-rata Review", fmt(avg_review))
c5.metric("Pesanan Terlambat", f"{late_pct_all:.2f}%")

tab1, tab2, tab3 = st.tabs([
    "Pertanyaan 1: Revenue",
    "Pertanyaan 2: Pengiriman & Review",
    "Pertanyaan 3: Segmentasi RFM",
])

with tab1:
    st.subheader("Kategori produk dengan revenue terbesar")

    cat_df = (
        fdf.groupby("product_category_name_english")
        .agg(order_count=("order_id", "nunique"), revenue=("price", "sum"))
        .sort_values("revenue", ascending=False)
    )
    cat_df["share"] = cat_df["revenue"] / cat_df["revenue"].sum() * 100
    top10 = cat_df.head(10).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [BLUE] * min(3, len(top10)) + [GREY] * (len(top10) - 3)
    ax.barh(top10["product_category_name_english"], top10["revenue"] / 1000, color=colors)
    ax.invert_yaxis()
    x_max = top10["revenue"].max() / 1000
    for i, (rev, share) in enumerate(zip(top10["revenue"], top10["share"])):
        ax.text(rev / 1000 + x_max * 0.01, i, f"{rev / 1000:,.0f}K ({share:.2f}%)", va="center", fontsize=10)
    ax.set_xlim(0, x_max * 1.3)
    ax.set_title("Top 10 Kategori Produk berdasarkan Revenue", fontsize=15)
    ax.set_xlabel("Revenue (ribu BRL)")
    ax.set_ylabel(None)
    plt.tight_layout()
    show_fig(fig)

    st.subheader("Tren revenue bulanan")

    monthly = fdf.groupby("order_month").agg(
        order_count=("order_id", "nunique"), revenue=("price", "sum")
    )
    monthly["mom"] = monthly["revenue"].pct_change() * 100
    peak_month = monthly["revenue"].idxmax()
    peak_rev = monthly.loc[peak_month, "revenue"] / 1000
    peak_mom = monthly.loc[peak_month, "mom"]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(monthly.index, monthly["revenue"] / 1000, marker="o", linewidth=2, color=BLUE)
    ax.scatter(peak_month, peak_rev, color=RED, s=90, zorder=5)
    label = f"Puncak: {peak_rev:,.0f}K"
    if pd.notna(peak_mom):
        label += f" (MoM {peak_mom:+.2f}%)"
    right_side = list(monthly.index).index(peak_month) > len(monthly) / 2
    ax.annotate(
        label, xy=(peak_month, peak_rev),
        xytext=(-12 if right_side else 12, 0), textcoords="offset points",
        ha="right" if right_side else "left", va="center", fontsize=11,
    )
    ax.set_ylim(0, monthly["revenue"].max() / 1000 * 1.12)
    ax.set_title("Revenue Bulanan", fontsize=15)
    ax.set_ylabel("Revenue (ribu BRL)")
    ax.set_xlabel(None)
    plt.xticks(rotation=45)
    plt.tight_layout()
    show_fig(fig)

    if len(monthly) > 1:
        mom_df = monthly.dropna(subset=["mom"])
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.bar(mom_df.index, mom_df["mom"], color=[BLUE if x >= 0 else RED for x in mom_df["mom"]])
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title("Pertumbuhan Revenue Month-over-Month (%)", fontsize=15)
        ax.set_ylabel("MoM (%)")
        ax.set_xlabel(None)
        plt.xticks(rotation=45)
        plt.tight_layout()
        show_fig(fig)
        st.caption(
            "Bulan pertama dan terakhir pada rentang yang dipilih bisa hanya sebagian bulan, "
            "sehingga pertumbuhan MoM di tepi rentang kurang representatif."
        )

    st.info(
        f"Kategori dengan revenue tertinggi pada periode terpilih adalah "
        f"**{top10.iloc[0]['product_category_name_english']}** "
        f"({top10.iloc[0]['revenue']:,.0f} BRL; {top10.iloc[0]['share']:.2f}%). "
        f"Top 10 kategori menyumbang **{top10['share'].sum():.2f}%** dari total revenue. "
        f"Revenue bulanan tertinggi terjadi pada **{peak_month}** ({peak_rev * 1000:,.0f} BRL)."
    )

with tab2:
    st.subheader("Review score berdasarkan ketepatan pengiriman")

    on_time = orders_df.loc[~orders_df["is_late"], "review_score"].mean()
    late = orders_df.loc[orders_df["is_late"], "review_score"].mean()
    gap = on_time - late

    m1, m2, m3 = st.columns(3)
    m1.metric("Review pesanan tepat waktu", fmt(on_time))
    m2.metric("Review pesanan terlambat", fmt(late))
    m3.metric("Selisih skor", f"{fmt(gap)} poin" if pd.notna(gap) else "-")

    status_df = (
        orders_df.groupby("delivery_status")
        .agg(order_count=("order_id", "nunique"), avg_review_score=("review_score", "mean"))
        .reindex(STATUS_ORDER)
    )
    status_df["order_count"] = status_df["order_count"].fillna(0).astype(int)

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(status_df.index, status_df["avg_review_score"], color=[BLUE, GREY, GREY])
    for bar, n in zip(bars, status_df["order_count"]):
        h = bar.get_height()
        if pd.notna(h):
            ax.text(
                bar.get_x() + bar.get_width() / 2, h + 0.08,
                f"{h:.2f}\n({n:,} pesanan)", ha="center", fontsize=11,
            )
    ax.set_ylim(0, 5.3)
    ax.set_title("Rata-rata Review Score berdasarkan Status Pengiriman", fontsize=15)
    ax.set_ylabel("Rata-rata review score (1-5)")
    ax.set_xlabel(None)
    plt.tight_layout()
    show_fig(fig)

    st.subheader("State dengan persentase keterlambatan tertinggi")

    state_df = (
        orders_df.groupby("customer_state")
        .agg(
            order_count=("order_id", "nunique"),
            late_count=("is_late", "sum"),
            late_pct=("is_late", lambda x: x.mean() * 100),
        )
        .reset_index()
    )
    nasional = orders_df["is_late"].mean() * 100

    min_orders = st.slider(
        "Minimal jumlah pesanan per state (agar persentase representatif)", 1, 500, 100
    )
    top5 = (
        state_df[state_df["order_count"] >= min_orders]
        .sort_values("late_pct", ascending=False)
        .head(5)
    )

    if top5.empty:
        st.info("Tidak ada state yang memenuhi minimal jumlah pesanan. Turunkan nilai slider.")
    else:
        fig, ax = plt.subplots(figsize=(10, 5))
        colors = [BLUE] + [GREY] * (len(top5) - 1)
        ax.barh(top5["customer_state"], top5["late_pct"], color=colors)
        ax.invert_yaxis()
        for i, (pct, n) in enumerate(zip(top5["late_pct"], top5["order_count"])):
            ax.text(pct + 0.3, i, f"{pct:.2f}% ({n:,} pesanan)", va="center", fontsize=10)
        ax.axvline(nasional, color=RED, linestyle="--", linewidth=1.5,
                   label=f"Rata-rata nasional {nasional:.2f}%")
        ax.legend(loc="lower right")
        ax.set_title("Top 5 State dengan Persentase Keterlambatan Tertinggi", fontsize=15)
        ax.set_xlabel("Pesanan terlambat (%)")
        ax.set_ylabel(None)
        ax.set_xlim(0, top5["late_pct"].max() * 1.4)
        plt.tight_layout()
        show_fig(fig)

        st.info(
            f"State dengan keterlambatan tertinggi adalah **{top5.iloc[0]['customer_state']}** "
            f"({top5.iloc[0]['late_pct']:.2f}%), dibanding rata-rata nasional {nasional:.2f}%."
        )

    st.subheader("Peta keterlambatan per state")
    map_df = state_df.merge(geo_df, on="customer_state", how="left").dropna(subset=["lat", "lng"])

    tab_map, tab_static = st.tabs(["Peta interaktif", "Peta statis"])

    with tab_map:
        peta = folium.Map(
            location=[-14.2, -51.9],
            zoom_start=4,
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            attr="Tiles &copy; Esri",
        )
        for _, r in map_df.iterrows():
            warna = risk_color(r["late_pct"], nasional)
            folium.CircleMarker(
                location=[r["lat"], r["lng"]],
                radius=4 + r["order_count"] ** 0.5 / 12,
                color=warna, fill=True, fill_color=warna, fill_opacity=0.7,
                tooltip=f"{r['customer_state']}: {r['late_pct']:.2f}% terlambat ({r['order_count']:,} pesanan)",
            ).add_to(peta)
        st_folium(peta, height=480, use_container_width=True, returned_objects=[])
        st.markdown(
            "🔴 Tinggi (>=15%) &nbsp;&nbsp; 🟠 Sedang (di atas rata-rata nasional) "
            "&nbsp;&nbsp; 🔵 Rendah (di bawah rata-rata nasional). Ukuran lingkaran = jumlah pesanan."
        )

    with tab_static:
        fig, ax = plt.subplots(figsize=(8, 8))
        warna_titik = [risk_color(p, nasional) for p in map_df["late_pct"]]
        ax.scatter(map_df["lng"], map_df["lat"], s=map_df["order_count"] / 12 + 40,
                   c=warna_titik, alpha=0.75, edgecolors="white", linewidths=1)
        for _, r in map_df.iterrows():
            ax.annotate(r["customer_state"], (r["lng"], r["lat"]), fontsize=9, ha="center", va="center")
        ax.set_title("Persentase Keterlambatan per State (ukuran = jumlah pesanan)", fontsize=13)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_aspect("equal")
        plt.tight_layout()
        show_fig(fig)

with tab3:
    st.subheader("Segmentasi pelanggan berdasarkan RFM")

    rfm_df = build_rfm(fdf)

    segment_df = (
        rfm_df.groupby("customer_segment")
        .agg(
            customer_count=("customer_unique_id", "nunique"),
            total_revenue=("monetary", "sum"),
            avg_monetary=("monetary", "mean"),
            avg_recency=("recency", "mean"),
        )
        .reindex(SEGMENT_ORDER)
    )
    segment_df[["customer_count", "total_revenue"]] = segment_df[["customer_count", "total_revenue"]].fillna(0)
    segment_df["customer_pct"] = segment_df["customer_count"] / segment_df["customer_count"].sum() * 100
    segment_df["revenue_pct"] = segment_df["total_revenue"] / segment_df["total_revenue"].sum() * 100

    repeat_pct = (rfm_df["frequency"] > 1).mean() * 100
    r1, r2, r3 = st.columns(3)
    r1.metric("Pelanggan unik", f"{len(rfm_df):,}")
    r2.metric("Pelanggan beli lebih dari 1x", f"{repeat_pct:.2f}%")
    r3.metric("Median recency", f"{rfm_df['recency'].median():.0f} hari")

    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(16, 6))

    cnt = segment_df["customer_count"]
    colors_cnt = [BLUE if v == cnt.max() else GREY for v in cnt]
    ax[0].barh(segment_df.index, cnt, color=colors_cnt)
    ax[0].invert_yaxis()
    for i, (n, p) in enumerate(zip(cnt, segment_df["customer_pct"])):
        ax[0].text(n + cnt.max() * 0.01, i, f"{n:,.0f} ({p:.1f}%)", va="center", fontsize=10)
    ax[0].set_xlim(0, cnt.max() * 1.3)
    ax[0].set_title("Jumlah Pelanggan per Segmen", fontsize=14)

    rev = segment_df["total_revenue"]
    colors_rev = [BLUE if v == rev.max() else GREY for v in rev]
    ax[1].barh(segment_df.index, rev / 1000, color=colors_rev)
    ax[1].invert_yaxis()
    for i, (r, p) in enumerate(zip(rev, segment_df["revenue_pct"])):
        ax[1].text(r / 1000 + rev.max() / 1000 * 0.01, i, f"{r / 1000:,.0f}K ({p:.1f}%)", va="center", fontsize=10)
    ax[1].set_xlim(0, rev.max() / 1000 * 1.3)
    ax[1].set_title("Total Revenue per Segmen (ribu BRL)", fontsize=14)
    ax[1].set_yticklabels([])

    plt.suptitle("Segmentasi Pelanggan berdasarkan RFM", fontsize=16)
    plt.tight_layout()
    show_fig(fig)

    top_seg = segment_df["total_revenue"].idxmax()
    st.info(
        f"Segmen dengan revenue terbesar adalah **{top_seg}** "
        f"({segment_df.loc[top_seg, 'revenue_pct']:.2f}% dari total revenue, "
        f"{segment_df.loc[top_seg, 'customer_pct']:.2f}% dari pelanggan)."
    )

    st.dataframe(
        segment_df.round(2).rename(columns={
            "customer_count": "Jumlah pelanggan", "total_revenue": "Total revenue (BRL)",
            "avg_monetary": "Rata-rata monetary", "avg_recency": "Rata-rata recency (hari)",
            "customer_pct": "% pelanggan", "revenue_pct": "% revenue",
        }),
        use_container_width=True,
    )
    st.caption(
        "RFM dihitung ulang dari data yang terfilter. Tanggal acuan recency adalah "
        "transaksi terakhir pada periode terpilih."
    )

    with st.expander("Aturan segmentasi (manual grouping)"):
        st.markdown(
            """
| Segmen | Aturan |
|---|---|
| Champions | Frequency >= 2 dan Recency <= 180 hari |
| Loyal Customers | Frequency >= 2 dan Recency > 180 hari |
| Recent Big Spenders | Frequency = 1, Recency <= 180 hari, Monetary >= kuartil 3 |
| Recent Customers | Frequency = 1 dan Recency <= 180 hari |
| At Risk | Frequency = 1 dan Recency 181-365 hari |
| Lost Customers | Frequency = 1 dan Recency > 365 hari |
"""
        )

with st.expander("Catatan data"):
    st.markdown(
        """
- Sumber: Brazilian E-Commerce Public Dataset by Olist.
- Hanya pesanan berstatus *delivered* pada Januari 2017 - Agustus 2018.
- Revenue = jumlah `price` (tanpa ongkos kirim), dalam BRL.
- Keterlambatan diukur terhadap tanggal estimasi tiba (`order_estimated_delivery_date`).
- Hubungan keterlambatan dan review bersifat asosiasi, bukan sebab-akibat.
"""
    )
