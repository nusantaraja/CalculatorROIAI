#!/usr/bin/env python3
# Kalkulator ROI Proyek - Versi Lengkap dan Terkoreksi (2024)
# Backend: Supabase (Storage + Database)
# Dibuat oleh: Medical AI Solutions

import streamlit as st
from datetime import datetime
import locale
import matplotlib.pyplot as plt
import numpy as np
from contextlib import suppress
import io
from fpdf import FPDF
import traceback
import pytz

# Import Supabase utilities
import supabase_utils

# ====================== KONSTANTA ======================
SUPABASE_BUCKET_NAME = "laporan-pdf"  # Ganti dengan nama bucket Anda di Supabase
SUPABASE_TABLE_NAME = "laporan_roi"   # Ganti dengan nama tabel Anda di Supabase
WIB = pytz.timezone("Asia/Jakarta")

# ====================== FUNGSI-FUNGSI BANTUAN ======================

def get_wib_time():
    """Mengembalikan waktu saat ini dalam format WIB."""
    now_utc = datetime.now(pytz.utc)
    now_wib = now_utc.astimezone(WIB)
    return now_wib.strftime("%Y-%m-%d %H:%M:%S WIB")

def setup_locale():
    """Mengatur locale untuk format angka ke Rupiah."""
    for loc in ["id_ID.UTF-8", "Indonesian_Indonesia.1252", "id_ID", "ind", "Indonesian"]:
        try:
            locale.setlocale(locale.LC_ALL, loc)
            locale.currency(1000, grouping=True)
            return True
        except (locale.Error, ValueError):
            continue
    return False

def format_currency(amount):
    """Format angka ke mata uang IDR."""
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return "Rp 0"
    if setup_locale():
        try:
            return locale.currency(amount, symbol="Rp ", grouping=True, international=False)
        except (ValueError, locale.Error):
            pass
    try:
        return f"Rp {amount:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"

def calculate_roi(investment, annual_gain, years):
    """Hitung ROI dalam persen untuk X tahun."""
    if investment <= 0:
        return float("inf")
    total_gain = annual_gain * years
    try:
        return ((total_gain - investment) / abs(investment)) * 100
    except ZeroDivisionError:
        return float("inf")

# ====================== FUNGSI INTI (GRAFIK & PDF) ======================

def generate_charts(data):
    """Membuat grafik untuk visualisasi data."""
    figs = []
    plt.style.use("seaborn-v0_8-whitegrid")
    rc_params = {
        "text.color": "#333", "axes.labelcolor": "#333",
        "xtick.color": "#333", "ytick.color": "#333",
        "axes.titlecolor": "#333"
    }
    plt.rcParams.update(rc_params)

    try:
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        months = 60
        monthly_savings = data.get("total_monthly_savings", 0)
        investment = data.get("total_investment", 0)
        cumulative = [monthly_savings * m - investment for m in range(1, months + 1)]
        ax1.plot(range(1, months + 1), cumulative, color="#2E86C1", linewidth=2, marker="o", markersize=4)
        ax1.set_title("PROYEKSI ARUS KAS KUMULATIF 5 TAHUN", fontweight="bold")
        ax1.set_xlabel("Bulan")
        ax1.set_ylabel("Arus Kas Kumulatif (IDR)")
        ax1.grid(True, linestyle="--", alpha=0.6)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x)))
        ax1.axhline(0, color="red", linestyle="--", linewidth=1)
        figs.append(fig1)
    except Exception as e:
        st.error(f"Error generating cash flow chart: {e}")
        if "fig1" in locals() and fig1 is not None: plt.close(fig1)

    try:
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        categories = ["Penghematan Staff", "Penghematan Operasional", "Total Tahunan"]
        savings = [
            data.get("staff_savings_monthly", 0) * 12,
            data.get("noshow_savings_monthly", 0) * 12,
            data.get("annual_savings", 0)
        ]
        bars = ax2.bar(categories, savings, color=["#27AE60", "#F1C40F", "#E74C3C"])
        ax2.set_title("SUMBER PENGHEMATAN TAHUNAN", fontweight="bold")
        ax2.set_ylabel("Jumlah Penghematan (IDR)")
        ax2.grid(True, axis="y", linestyle="--", alpha=0.6)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x)))
        for bar in bars:
            yval = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2.0, yval, format_currency(yval), va="bottom", ha="center", fontsize=9, color="#333")
        figs.append(fig2)
    except Exception as e:
        st.error(f"Error generating savings comparison chart: {e}")
        if "fig2" in locals() and fig2 is not None: plt.close(fig2)
    
    return figs

# GANTI FUNGSI LAMA INI DENGAN YANG BARU DI ROI_Calc.py

def generate_pdf_report(report_data, consultant_info, figs):
    """Membuat laporan PDF dari data yang dihitung, dengan fallback font."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Coba gunakan font DejaVu, jika gagal, beralih ke Arial
    font_family = "DejaVu"
    try:
        font_base_path = "fonts/ttf/"
        pdf.add_font("DejaVu", "", f"{font_base_path}DejaVuSans.ttf")
        pdf.add_font("DejaVu", "B", f"{font_base_path}DejaVuSans-Bold.ttf")
        # Tambahkan varian lain jika Anda sudah mengunggahnya
        with suppress(FileNotFoundError, RuntimeError):
             pdf.add_font("DejaVu", "I", f"{font_base_path}DejaVuSans-Oblique.ttf")
             pdf.add_font("DejaVu", "BI", f"{font_base_path}DejaVuSans-BoldOblique.ttf")

    except (FileNotFoundError, RuntimeError):
        font_family = "Arial"  # Font fallback yang aman
        st.warning(
            f"⚠️ Font 'DejaVu' tidak ditemukan. Laporan PDF akan dibuat menggunakan font '{font_family}'. "
            "Pastikan folder `fonts/ttf/` dan isinya sudah diunggah dengan benar.", 
            icon="ℹ️"
        )

    # Mulai membuat konten PDF menggunakan font_family yang sudah ditentukan
    pdf.set_font(font_family, style="B", size=16)
    pdf.cell(0, 10, f"Laporan Analisis ROI - {report_data.get('client_name', 'N/A')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font(font_family, style="", size=10)
    pdf.cell(0, 5, f"Tanggal Dibuat: {get_wib_time()}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)

    pdf.set_font(font_family, style="B", size=12)
    pdf.cell(0, 8, "Informasi Konsultan", new_x="LMARGIN", new_y="NEXT", border="B")
    pdf.set_font(font_family, style="", size=10)
    pdf.cell(0, 6, f"Nama: {consultant_info.get('name', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Email: {consultant_info.get('email', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"No. HP/WA: {consultant_info.get('phone', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font(font_family, style="B", size=12)
    pdf.cell(0, 8, "Informasi Klien / Proyek", new_x="LMARGIN", new_y="NEXT", border="B")
    pdf.set_font(font_family, style="", size=10)
    pdf.cell(0, 6, f"Nama: {report_data.get('client_name', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Lokasi: {report_data.get('client_location', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font(font_family, style="B", size=12)
    pdf.cell(0, 8, "Hasil Utama Analisis ROI", new_x="LMARGIN", new_y="NEXT", border="B")
    pdf.set_font(font_family, style="", size=10)
    col_width = pdf.w / 2 - pdf.l_margin - 1
    line_height = 7
    pdf.cell(col_width, line_height, "Investasi Awal:", border=1)
    pdf.cell(col_width, line_height, format_currency(report_data.get("total_investment", 0)), new_x="LMARGIN", new_y="NEXT", border=1, align="R")
    pdf.cell(col_width, line_height, "Penghematan Tahunan:", border=1)
    pdf.cell(col_width, line_height, format_currency(report_data.get("annual_savings", 0)), new_x="LMARGIN", new_y="NEXT", border=1, align="R")
    roi_1y = report_data.get("roi_1_year", float("inf"))
    pdf.cell(col_width, line_height, "ROI 1 Tahun:", border=1)
    pdf.cell(col_width, line_height, f"{roi_1y:.1f}%" if roi_1y != float("inf") else "N/A", new_x="LMARGIN", new_y="NEXT", border=1, align="R")
    roi_5y = report_data.get("roi_5_year", float("inf"))
    pdf.cell(col_width, line_height, "ROI 5 Tahun:", border=1)
    pdf.cell(col_width, line_height, f"{roi_5y:.1f}%" if roi_5y != float("inf") else "N/A", new_x="LMARGIN", new_y="NEXT", border=1, align="R")
    pb = report_data.get("payback_period", float("inf"))
    pdf.cell(col_width, line_height, "Periode Pengembalian (Bulan):", border=1)
    pdf.cell(col_width, line_height, f"{pb:.1f}" if pb != float("inf") else "N/A", new_x="LMARGIN", new_y="NEXT", border=1, align="R")
    pdf.ln(5)
    
    pdf.set_font(font_family, style="B", size=12)
    pdf.cell(0, 8, "Visualisasi Data", new_x="LMARGIN", new_y="NEXT", border="B")
    pdf.ln(5)
    if figs:
        for i, fig in enumerate(figs):
            if fig is None: continue
            try:
                chart_buffer = io.BytesIO()
                fig.savefig(chart_buffer, format="PNG", bbox_inches="tight", dpi=200)
                chart_buffer.seek(0)
                img_width = pdf.w - 2 * pdf.l_margin
                pdf.image(chart_buffer, x=None, y=None, w=img_width, type="PNG")
                pdf.ln(5)
                plt.close(fig)
            except Exception as img_e:
                st.error(f"Error saat menyematkan grafik {i}: {img_e}")
                if "fig" in locals() and fig is not None: plt.close(fig)
    else:
        pdf.cell(0, 6, "Grafik tidak dapat dibuat.", new_x="LMARGIN", new_y="NEXT")

    try:
        return bytes(pdf.output())
    except Exception as pdf_err:
        st.error(f"Error saat finalisasi output PDF: {pdf_err}")
        st.code(traceback.format_exc())
        return None

# ====================== APLIKASI UTAMA STREAMLIT ======================
def main():
    st.set_page_config(page_title="Kalkulator ROI Proyek", page_icon="💼", layout="wide")
    
    # Inisialisasi session state untuk status sinkronisasi
    if 'sync_status' not in st.session_state:
        st.session_state.sync_status = "idle" # Status bisa 'idle', 'success', atau 'fail'

def main():
    st.set_page_config(page_title="Kalkulator ROI Proyek", page_icon="💼", layout="wide")
    
    st.markdown("""
    <style>
    .stButton>button {
        background-color: #2E86C1; color: white; font-weight: bold;
        border-radius: 5px; padding: 0.5rem 1rem;
    }
    .stButton>button:hover { background-color: #21618C; }
    .stMetric {
        background-color: var(--secondary-background-color); border-left: 5px solid #2E86C1;
        padding: 15px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stTextInput label, .stNumberInput label, .stSlider label {
        font-weight: bold; color: var(--text-color);
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("💼 Kalkulator ROI 5 Tahun untuk Implementasi Proyek")
    st.markdown("**Alat interaktif untuk menghitung potensi Return on Investment (ROI) dari implementasi solusi baru.**")
    st.markdown("---")

    # --- SIDEBAR: SEMUA INPUT PENGGUNA DI SINI ---
    with st.sidebar:
        st.header("👤 Informasi Konsultan")
        consultant_name = st.text_input("Nama Konsultan", key="consultant_name", placeholder="Masukkan Nama Anda")
        consultant_email = st.text_input("Email Konsultan", key="consultant_email", placeholder="nama@email.com")
        consultant_phone = st.text_input("No. HP/WA Konsultan", key="consultant_phone", placeholder="08xxxxxxxxxx")
        consultant_info_filled = bool(consultant_name and consultant_email and consultant_phone)
        if not consultant_info_filled:
            st.warning("Harap isi semua informasi konsultan.")
        
        st.markdown("---")
        st.header("⚙️ Parameter Input ROI")
        st.subheader("Informasi Klien / Proyek")
        client_name = st.text_input("Nama Klien / Proyek", "Proyek Alfa", key="client_name")
        client_location = st.text_input("Lokasi (Kota/Provinsi)", "Jakarta", key="client_location")
        
        st.subheader("Parameter Operasional")
        col1_op, col2_op = st.columns(2)
        with col1_op:
            total_staff = st.number_input("Total Staff Terlibat", min_value=1, value=200, step=10, key="total_staff")
            monthly_appointments = st.number_input("Rata-rata Transaksi/Bulan", min_value=1, value=5000, step=100, key="monthly_appointments")
        with col2_op:
            admin_staff = st.number_input("Jumlah Staff Admin Terkait", min_value=1, value=20, step=1, key="admin_staff")
            noshow_rate = st.slider("Tingkat Inefisiensi Saat Ini (%)", 0.0, 50.0, 15.0, step=0.5, key="noshow_rate", format="%.1f%%") / 100
        
        st.subheader("Parameter Biaya")
        col1_cost, col2_cost = st.columns(2)
        with col1_cost:
            avg_salary = st.number_input("Rata-rata Gaji Staff Admin (IDR/Bulan)", min_value=0, value=8000000, step=100000, key="avg_salary", format="%d")
        with col2_cost:
            revenue_per_appointment = st.number_input("Rata-rata Pendapatan/Transaksi (IDR)", min_value=0, value=250000, step=10000, key="revenue_per_appointment", format="%d")
        
        st.subheader("Estimasi Efisiensi dengan Solusi Baru")
        col1_eff, col2_eff = st.columns(2)
        with col1_eff:
            staff_reduction = st.slider("Pengurangan Beban Kerja Staff Admin (%)", 0.0, 80.0, 30.0, step=1.0, key="staff_reduction", format="%.1f%%") / 100
        with col2_eff:
            noshow_reduction = st.slider("Pengurangan Tingkat Inefisiensi (%)", 0.0, 80.0, 40.0, step=1.0, key="noshow_reduction", format="%.1f%%") / 100
        
        st.subheader("Estimasi Biaya Implementasi")
        exchange_rate = st.number_input("Asumsi Kurs USD-IDR", min_value=1000, value=16000, step=100, key="exchange_rate", format="%d")
        col1_impl, col2_impl = st.columns(2)
        with col1_impl:
            setup_cost_usd = st.number_input("Biaya Setup Awal (USD)", min_value=0, value=20000, step=1000, key="setup_cost_usd", format="%d")
            training_cost_usd = st.number_input("Biaya Pelatihan Tim (USD)", min_value=0, value=10000, step=500, key="training_cost_usd", format="%d")
        with col2_impl:
            integration_cost_usd = st.number_input("Biaya Integrasi Sistem (USD)", min_value=0, value=15000, step=1000, key="integration_cost_usd", format="%d")
            maintenance_cost = st.number_input("Biaya Pemeliharaan (IDR/Bulan)", min_value=0, value=5000000, step=500000, key="maintenance_cost", format="%d")
        # --- INDIKATOR RAHASIA ---
        if st.session_state.sync_status == "success":
            st.markdown("---")
            st.markdown("<p style='text-align: center; color: #3dd56d;'>✅ Sinkronisasi Berhasil</p>", unsafe_allow_html=True)
        elif st.session_state.sync_status == "fail":
            st.markdown("---")
            st.markdown("<p style='text-align: center; color: #ff4b4b;'>❌ Sinkronisasi Gagal</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        # TOMBOL INI Memicu SEMUA LOGIKA DI BAWAH
        hitung_roi = st.button("🚀 HITUNG ROI & SIMPAN LAPORAN", type="primary", use_container_width=True, disabled=not consultant_info_filled)

    # --- LOGIKA UTAMA: HANYA BERJALAN JIKA TOMBOL DITEKAN ---
    if hitung_roi:
        # Reset status setiap kali tombol ditekan
        st.session_state.sync_status = "idle"

        if not consultant_info_filled:
            st.error("⚠️ Harap isi semua informasi konsultan di sidebar sebelum menghitung.")
            st.stop()

        # ... (semua kode perhitungan, tampilan metric, grafik, dan expander tetap sama) ...
        # ...

        # 5. BUAT PDF DAN SINKRONISASI KE SUPABASE
        st.subheader("📄 Laporan PDF & Sinkronisasi Data")
        date_str = datetime.now(WIB).strftime("%y%m%d")
        base_name = f"{date_str} {client_name} {client_location}"
        pdf_filename = f"{base_name}.pdf"
        supabase_file_path = f"{base_name}/{pdf_filename}" 

        pdf_content = None
        with st.spinner("Membuat laporan PDF..."): 
            try:
                pdf_content = generate_pdf_report(report_data, consultant_info_dict, figs)
                if pdf_content:
                    st.download_button(label="📥 Unduh Laporan PDF", data=pdf_content, file_name=pdf_filename, mime="application/pdf")
                else:
                    st.error("Gagal membuat konten PDF. Sinkronisasi tidak akan berjalan.")
                    st.session_state.sync_status = "fail" # Tandai gagal
            except Exception as pdf_gen_err:
                st.error(f"Terjadi kesalahan fatal saat membuat PDF: {pdf_gen_err}")
                st.code(traceback.format_exc())
                st.session_state.sync_status = "fail" # Tandai gagal

        if pdf_content and st.session_state.sync_status != "fail":
            supabase = supabase_utils.init_supabase_client()
            if not supabase:
                st.warning("Kredensial Supabase tidak valid. Sinkronisasi dilewati.", icon="🔒")
                st.session_state.sync_status = "fail" # Tandai gagal
            else:
                pdf_link = None
                with st.spinner("Mengunggah PDF & menyimpan data..."):
                    pdf_link = supabase_utils.upload_pdf_to_storage(supabase, pdf_content, supabase_file_path, SUPABASE_BUCKET_NAME)
                
                if pdf_link:
                    report_data["pdf_link"] = pdf_link
                    db_data = {k: v for k, v in report_data.items() if k not in ["staff_savings_monthly", "noshow_savings_monthly", "total_monthly_savings"]}
                    for key, value in db_data.items():
                        if value == float('inf'):
                            db_data[key] = None
                    
                    if supabase_utils.insert_report_data(supabase, SUPABASE_TABLE_NAME, db_data):
                        # INI DIA KUNCINYA! Tandai bahwa semua berhasil.
                        st.session_state.sync_status = "success"
                        st.balloons()
                    else:
                        st.error("Gagal menyimpan data ke Database.")
                        st.session_state.sync_status = "fail" # Tandai gagal
                else:
                    st.error("Gagal mengunggah PDF ke Supabase Storage.")
                    st.session_state.sync_status = "fail" # Tandai gagal
        
        # --- Footer ---
        st.markdown("---")
        st.caption(f"© {datetime.now().year} Medical AI Solutions | Analisis dibuat pada {get_wib_time()}")

# ====================== ENTRY POINT APLIKASI ======================
if __name__ == "__main__":
    if "supabase" not in st.secrets:
        st.warning("⚠️ Kredensial Supabase tidak ditemukan di Secrets. Fitur sinkronisasi tidak akan berfungsi.", icon="🔒")
    main()