import streamlit as st
import pandas as pd
import gspread
import matplotlib.pyplot as plt
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="Dashboard Keuangan Pribadi", layout="wide")
# --- Google Sheets Auth ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# --- Ganti dengan ID file Google Sheets kamu ---
SPREADSHEET_ID = "1C0rWwQeuqDep_1d47IEksr-4z2EDt3nhdRda_iLtSsc"  # contoh: "1BZIiK4dA2ZkT1x..."

# --- Worksheet ---
sheet_assets = client.open_by_key(SPREADSHEET_ID).worksheet("Assets")
sheet_liabilities = client.open_by_key(SPREADSHEET_ID).worksheet("Liabilities")

# --- Load data dari Google Sheets ---
def get_data(worksheet):
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors='coerce')
        st.write("Cek tipe data kolom date:", df["date"].dtype)  # ✅ modifikasi di sini
        df["amount"] = pd.to_numeric(df["amount"], errors='coerce').fillna(0.0)
    else:
        df = pd.DataFrame(columns=["date", "category", "description", "amount"])
    return df

assets = get_data(sheet_assets)
liabilities = get_data(sheet_liabilities)

# --- Streamlit Layout ---
st.title("📊 Dashboard Keuangan Pribadi")

# --- Sidebar Form Input ---
st.sidebar.header("➕ Tambah Data Baru")

with st.sidebar.form("input_form"):
    record_type = st.selectbox("Jenis", ["Aset", "Liabilitas"])
    date = st.date_input("Tanggal", value=datetime.today())
    category = st.text_input("Kategori")
    description = st.text_input("Deskripsi")
    amount = st.number_input("Jumlah (Rp)", min_value=0.0, format="%.2f")
    submitted = st.form_submit_button("Simpan")

    if submitted:
        new_row = [date.strftime("%Y-%m-%d"), category, description, amount]
        if record_type == "Aset":
            sheet_assets.append_row(new_row)
            st.success("✅ Aset berhasil ditambahkan!")
        else:
            sheet_liabilities.append_row(new_row)
            st.success("✅ Liabilitas berhasil ditambahkan!")
        st.experimental_rerun()

# --- Perhitungan Ringkasan ---
total_assets = assets['amount'].sum()
total_liabilities = liabilities['amount'].sum()
net_worth = total_assets - total_liabilities

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Aset", f"Rp {total_assets:,.0f}")
col2.metric("💸 Total Liabilitas", f"Rp {total_liabilities:,.0f}")
col3.metric("📈 Net Worth", f"Rp {net_worth:,.0f}", delta=f"{(net_worth / total_assets * 100 if total_assets else 0):.2f}%")

# --- Pie Chart Aset vs Liabilitas ---
st.markdown("### 🔄 Rasio Aset vs Liabilitas")
if total_assets + total_liabilities == 0:
    st.warning("Tidak ada data untuk membuat pie chart. Pastikan Anda telah memasukkan data aset dan liabilitas.")
else:
    fig1, ax1 = plt.subplots()
    ax1.pie(
        [total_assets, total_liabilities],
        labels=['Assets', 'Liabilities'],
        autopct='%1.1f%%',
        startangle=90,
        colors=['#27ae60', '#e74c3c']
    )
    ax1.axis('equal')
    st.pyplot(fig1)

# --- Grafik Tren Keuangan ---
st.markdown("### 📅 Tren Keuangan dari Waktu ke Waktu")

assets_trend = assets.groupby("date")["amount"].sum().cumsum().reset_index(name="Cumulative Assets")
liabilities_trend = liabilities.groupby("date")["amount"].sum().cumsum().reset_index(name="Cumulative Liabilities")

df_merged = pd.merge(assets_trend, liabilities_trend, on="date", how="outer").fillna(method="ffill").sort_values("date")
df_merged["Net Worth"] = df_merged["Cumulative Assets"] - df_merged["Cumulative Liabilities"]

fig2, ax2 = plt.subplots(figsize=(10,5))
ax2.plot(df_merged["date"], df_merged["Cumulative Assets"], label="Assets", color='green')
ax2.plot(df_merged["date"], df_merged["Cumulative Liabilities"], label="Liabilities", color='red')
ax2.plot(df_merged["date"], df_merged["Net Worth"], label="Net Worth", color='blue')
ax2.set_title("Cumulative Financial Trend")
ax2.legend()
ax2.grid(True)
st.pyplot(fig2)

# --- Lihat Data Mentah ---
with st.expander("📂 Lihat Data Mentah"):
    st.subheader("Aset")
    st.dataframe(assets)
    st.subheader("Liabilitas")
    st.dataframe(liabilities)
