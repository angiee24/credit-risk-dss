import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Credit Decision Support System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #fcfdfe; }
    
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        margin-bottom: 15px;
    }
    
    .status-alert {
        background: #fff5f5;
        border-left: 5px solid #e53e3e;
        padding: 15px;
        border-radius: 4px;
        color: #9b2c2c;
        font-size: 14px;
        margin-bottom: 20px;
    }

    .insight-section {
        background: #f8fafc;
        border-radius: 8px;
        padding: 18px;
        border: 1px solid #edf2f7;
        color: #334155;
        font-size: 14px;
        line-height: 1.6;
    }

    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #1a202c; }
    </style>
""", unsafe_allow_html=True)

def map_risk_status(status):
    status = str(status)
    mapping = {
        'C': 'Lancar (Current)',
        '0': 'Dini (0-29 Hari)',
        '1': 'Ringan (30-59 Hari)',
        '2': 'Sedang (60-89 Hari)',
        '3': 'Berat (90-119 Hari)',
        '4': 'Macet (120-149 Hari)',
        '5': 'Gagal Bayar (>150 Hari)',
        'X': 'Tanpa Riwayat'
    }
    return mapping.get(status, 'Lainnya')

risk_color_map = {
    'Lancar (Current)': '#2ecc71',
    'Tanpa Riwayat': '#9ca3af',
    'Dini (0-29 Hari)': '#34d399',
    'Ringan (30-59 Hari)': '#a7f3d0',
    'Sedang (60-89 Hari)': '#f1c40f',
    'Berat (90-119 Hari)': '#f39c12',
    'Macet (120-149 Hari)': '#e74c3c',
    'Gagal Bayar (>150 Hari)': '#c0392b',
    'Lainnya': '#cbd5e1'
}

def define_risk_segment(status):
    status = str(status)
    if status in ['C', '0', '1', 'X']: return 'Low Risk'
    if status in ['2', '3']: return 'Medium Risk'
    return 'High Risk'

@st.cache_data
def load_data(path):
    if not os.path.exists(path): return None
    df = pd.read_csv(path)
    df = df.dropna(subset=['STATUS'])
    df['Risk_Label'] = df['STATUS'].apply(map_risk_status)
    df['Risk_Segment'] = df['STATUS'].apply(define_risk_segment)
    return df

df = load_data("hasil_dss_credit_decision.csv")

if df is None:
    st.error("Gagal memuat dataset: 'hasil_dss_credit_decision.csv' tidak ditemukan.")
    st.stop()

st.sidebar.markdown("### Navigasi Portofolio")
income_types = df['NAME_INCOME_TYPE'].unique().tolist()
selected_income = st.sidebar.multiselect("Klasifikasi Pekerjaan:", options=income_types, default=income_types)

risk_segments = df['Risk_Segment'].unique().tolist()
selected_risk = st.sidebar.multiselect("Profil Risiko:", options=risk_segments, default=risk_segments)

df_filtered = df[(df['NAME_INCOME_TYPE'].isin(selected_income)) & (df['Risk_Segment'].isin(selected_risk))]

if df_filtered.empty:
    st.warning("⚠️ Data tidak ditemukan dengan kriteria filter saat ini.")
    st.stop()

st.title("Credit Risk Intelligence Dashboard")
st.markdown("<p style='color:#718096;'>Visualisasi analitik untuk pemantauan kualitas kredit dan optimasi keputusan persetujuan.</p>", unsafe_allow_html=True)

total_n = len(df_filtered)
avg_score = df_filtered['risk_score'].mean() if total_n > 0 else 0
approval_rate = (len(df_filtered[df_filtered['credit_decision'] == 'APPROVE']) / total_n) * 100 if total_n > 0 else 0
high_risk_n = len(df_filtered[df_filtered['Risk_Segment'] == 'High Risk'])

if total_n > 0 and (high_risk_n / total_n) > 0.15:
    st.markdown("<div class='status-alert'><b>Peringatan Risiko:</b> Konsentrasi nasabah berisiko tinggi melampaui ambang batas 15%. Pengetatan kebijakan diperlukan.</div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Populasi", f"{total_n:,}")
col2.metric("Rerata Skor Kredit", f"{avg_score:.1f}")
col3.metric("Laju Persetujuan", f"{approval_rate:.1f}%")
col4.metric("Indeks Risiko Tinggi", f"{(high_risk_n/total_n*100):.1f}%" if total_n > 0 else "0%")

st.markdown("---")

row1_left, row1_right = st.columns(2)

with row1_left:
    fig_score = px.histogram(
        df_filtered, x='risk_score', color='credit_decision',
        title="Distribusi Skor Kredit Berdasarkan Keputusan",
        color_discrete_map={'APPROVE': '#2f855a', 'REJECT': '#c53030'},
        barmode='overlay', opacity=0.7
    )
    fig_score.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis_title="Skor Kredit", yaxis_title="Jumlah Nasabah")
    st.plotly_chart(fig_score, use_container_width=True)

with row1_right:
    risk_comp = df_filtered['Risk_Label'].value_counts().reset_index()
    risk_comp.columns = ['Status Kolektibilitas', 'Total']
    fig_pie = px.pie(
        risk_comp, names='Status Kolektibilitas', values='Total', 
        title="Komposisi Kolektibilitas Portofolio",
        hole=0.5, 
        color='Status Kolektibilitas',
        color_discrete_map=risk_color_map
    )
    fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("### Simulasi Kebijakan & Strategi")
col_sim, col_ins = st.columns([1, 1])

with col_sim:
    st.markdown("<p style='font-size:14px; color:#4a5568;'>Simulasi dampak perubahan ambang batas skor (Credit Score Cut-off) terhadap tingkat persetujuan.</p>", unsafe_allow_html=True)
    cut_off = st.slider("Ambang Batas Skor (Cut-off):", 0, 100, 50)
    potential_approve = len(df_filtered[df_filtered['risk_score'] >= cut_off])
    new_rate = (potential_approve / total_n) * 100 if total_n > 0 else 0
    st.info(f"**Proyeksi:** Dengan Cut-off skor **{cut_off}**, estimasi Laju Persetujuan akan bergerak menjadi **{new_rate:.1f}%**.")

with col_ins:
    st.markdown("#### Rekomendasi Strategis")
    median_reject = df[df['credit_decision']=='REJECT']['risk_score'].median()
    median_reject_val = median_reject if pd.notna(median_reject) else 0
    st.markdown(f"""
    <div class='insight-section'>
        <b>Analisis Kualitas:</b> Mayoritas penolakan (REJECT) tersentralisasi pada skor di bawah {median_reject_val:.0f}. 
        Model bekerja konsisten dengan parameter risiko.<br><br>
        <b>Langkah Mitigasi:</b> Untuk segmen <i>{selected_income[0] if len(selected_income) > 0 else 'Umum'}</i>, disarankan peninjauan manual jika skor berada di area marginal (45-55).
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.subheader("Daftar Keputusan & Aksi")

act1, act2, act3 = st.columns([1, 1, 2])
with act1:
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Ekspor Data Keputusan", data=csv, file_name="credit_decision_report.csv", mime="text/csv", use_container_width=True)
with act2:
    if st.button("🚨 Kirim Notifikasi Penolakan", use_container_width=True):
        st.toast("Menyiapkan antrian notifikasi untuk nasabah REJECT...", icon="✉️")
with act3:
    st.markdown("<p style='text-align:right; font-size:12px; color:#a0aec0; margin-top:10px;'>Data diperbarui secara otomatis dari sistem inti.</p>", unsafe_allow_html=True)

crm_table = df_filtered[['ID', 'AMT_INCOME_TOTAL', 'NAME_INCOME_TYPE', 'Risk_Label', 'risk_score', 'credit_decision']].copy()
crm_table.columns = ['ID Nasabah', 'Pendapatan', 'Tipe Pekerjaan', 'Status Risiko', 'Skor Kredit', 'Keputusan']

def color_decision(val):
    if val == 'REJECT': return 'color: white; background-color: #c53030'
    elif val == 'APPROVE': return 'color: white; background-color: #2f855a'
    return ''

st.dataframe(
    crm_table.head(100).style.map(color_decision, subset=['Keputusan']).format({"Pendapatan": "Rp {:,.0f}"}),
    use_container_width=True,
    height=350
)
