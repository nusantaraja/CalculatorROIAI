#!/usr/bin/env python3
# Kalkulator ROI Proyek - Versi Final dan Lengkap (2024)
# Backend: Supabase | Fitur: Indikator Sinkronisasi Rahasia
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
SUPABASE_BUCKET_NAME = "laporan-pdf"
SUPABASE_TABLE_NAME = "laporan_roi"
WIB = pytz.timezone("Asia/Jakarta")

# ====================== FUNGSI-FUNGSI BANTUAN ======================
def get_wib_time():
    now_utc = datetime.now(pytz.utc)
    return now_utc.astimezone(WIB).strftime("%Y-%m-%d %H:%M:%S WIB")

def setup_locale():
    for loc in ["id_ID.UTF-8", "Indonesian_Indonesia.1252", "id_ID", "ind", "Indonesian"]:
        with suppress(locale.Error, ValueError):
            locale.setlocale(locale.LC_ALL, loc)
            return True
    return False

def format_currency(amount):
    try: amount = float(amount)
    except (ValueError, TypeError): return "Rp 0"
    if setup_locale(): return locale.currency(amount, symbol="Rp ", grouping=True, international=False)
    return f"Rp {amount:,.0f}".replace(",", ".")

def calculate_roi(investment, annual_gain, years):
    if investment <= 0: return float("inf")
    total_gain = annual_gain * years
    try: return ((total_gain - investment) / abs(investment)) * 100
    except ZeroDivisionError: return float("inf")

# ====================== FUNGSI INTI (GRAFIK & PDF) ======================
def generate_charts(data):
    figs = []
    # ... (Isi fungsi ini sama seperti sebelumnya, tidak perlu diubah) ...
    return figs

def generate_pdf_report(report_data, consultant_info, figs):
    pdf = FPDF()
    # ... (Isi fungsi ini sama seperti sebelumnya, tidak perlu diubah) ...
    return bytes(pdf.output())

# ====================== APLIKASI UTAMA STREAMLIT ======================
def main():
    st.set_page_config(page_title="Kalkulator ROI Proyek", page_icon="💼", layout="wide")
    
    # KUNCI #1: Inisialisasi session state di paling atas!
    if 'sync_status' not in st.session_state:
        st.session_state.sync_status = "idle"

    st.markdown("""<style>...</style>""", unsafe_allow_html=True) # CSS disembunyikan untuk keringkasan
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
        if not consultant_info_filled: st.warning("Harap isi semua informasi konsultan.")
        
        st.markdown("---")
        st.header("⚙️ Parameter Input ROI")
        st.subheader("Informasi Klien / Proyek")
        client_name = st.text_input("Nama Klien / Proyek", "Proyek Alfa", key="client_name")
        client_location = st.text_input("Lokasi (Kota/Provinsi)", "Jakarta", key="client_location")
        st.subheader("Parameter Operasional"); col1_op, col2_op = st.columns(2)
        with col1_op:
            total_staff = st.number_input("Total Staff Terlibat", 1, value=200, step=10, key="total_staff")
            monthly_appointments = st.number_input("Rata-rata Transaksi/Bulan", 1, value=5000, step=100, key="monthly_appointments")
        with col2_op:
            admin_staff = st.number_input("Jumlah Staff Admin Terkait", 1, value=20, step=1, key="admin_staff")
            noshow_rate = st.slider("Tingkat Inefisiensi (%)", 0.0, 50.0, 15.0, 0.5, key="noshow_rate", format="%.1f%%") / 100
        st.subheader("Parameter Biaya"); col1_cost, col2_cost = st.columns(2)
        with col1_cost: avg_salary = st.number_input("Gaji Staff Admin (IDR/Bulan)", 0, value=5000000, step=100000, key="avg_salary", format="%d")
        with col2_cost: revenue_per_appointment = st.number_input("Pendapatan/Transaksi (IDR)", 0, value=250000, step=10000, key="revenue_per_appointment", format="%d")
        st.subheader("Estimasi Efisiensi dengan Solusi Baru"); col1_eff, col2_eff = st.columns(2)
        with col1_eff: staff_reduction = st.slider("Pengurangan Beban Kerja Staff (%)", 0.0, 80.0, 30.0, 1.0, key="staff_reduction", format="%.1f%%") / 100
        with col2_eff: noshow_reduction = st.slider("Pengurangan Inefisiensi (%)", 0.0, 80.0, 40.0, 1.0, key="noshow_reduction", format="%.1f%%") / 100
        st.subheader("Estimasi Biaya Implementasi")
        exchange_rate = st.number_input("Asumsi Kurs USD-IDR", 1000, value=16000, step=100, key="exchange_rate", format="%d")
        col1_impl, col2_impl = st.columns(2)
        with col1_impl:
            setup_cost_usd = st.number_input("Biaya Setup Awal (USD)", 0, value=10000, step=1000, key="setup_cost_usd", format="%d")
            training_cost_usd = st.number_input("Biaya Pelatihan Tim (USD)", 0, value=1500, step=500, key="training_cost_usd", format="%d")
        with col2_impl:
            integration_cost_usd = st.number_input("Biaya Integrasi Sistem (USD)", 0, value=3000, step=1000, key="integration_cost_usd", format="%d")
            maintenance_cost = st.number_input("Biaya Pemeliharaan (IDR/Bulan)", 0, value=0, step=500000, key="maintenance_cost", format="%d")
        st.markdown("---")
        hitung_roi = st.button("🚀 HITUNG ROI & SIMPAN LAPORAN", type="primary", use_container_width=True, disabled=not consultant_info_filled)

        # KUNCI #2: Indikator rahasia ditempatkan di akhir sidebar
        if st.session_state.sync_status == "success":
            st.markdown("---")
            st.markdown("<p style='text-align: center; color: #3dd56d;'>✅ Sinkronisasi Berhasil</p>", unsafe_allow_html=True)
        elif st.session_state.sync_status == "fail":
            st.markdown("---")
            st.markdown("<p style='text-align: center; color: #ff4b4b;'>❌ Sinkronisasi Gagal</p>", unsafe_allow_html=True)

    # --- LOGIKA UTAMA: HANYA BERJALAN JIKA TOMBOL DITEKAN ---
    if hitung_roi:
        st.session_state.sync_status = "idle" # Reset status setiap kali tombol ditekan
        if not consultant_info_filled:
            st.error("⚠️ Harap isi semua informasi konsultan di sidebar."); st.stop()

        # KUNCI #3: SEMUA PERHITUNGAN DILAKUKAN DI SINI!
        with st.spinner("⏳ Menghitung ROI..."):
            setup_cost = setup_cost_usd * exchange_rate
            integration_cost = integration_cost_usd * exchange_rate
            training_cost = training_cost_usd * exchange_rate
            total_investment = setup_cost + integration_cost + training_cost
            staff_savings_monthly = (admin_staff * avg_salary) * staff_reduction
            noshow_saved_appointments = monthly_appointments * noshow_rate * noshow_reduction
            noshow_savings_monthly = noshow_saved_appointments * revenue_per_appointment
            total_monthly_savings = staff_savings_monthly + noshow_savings_monthly - maintenance_cost
            annual_savings = total_monthly_savings * 12
            payback_period = total_investment / total_monthly_savings if total_monthly_savings > 0 else float("inf")
            
            report_data = {
                "timestamp": get_wib_time(), "consultant_name": consultant_name, "consultant_email": consultant_email,
                "consultant_phone": consultant_phone, "client_name": client_name, "client_location": client_location,
                "total_staff": total_staff, "admin_staff": admin_staff, "monthly_appointments": monthly_appointments,
                "noshow_rate_before": noshow_rate * 100, "avg_salary": avg_salary, "revenue_per_appointment": revenue_per_appointment,
                "staff_reduction_pct": staff_reduction * 100, "noshow_reduction_pct": noshow_reduction * 100,
                "exchange_rate": exchange_rate, "setup_cost_usd": setup_cost_usd, "integration_cost_usd": integration_cost_usd,
                "training_cost_usd": training_cost_usd, "maintenance_cost_idr": maintenance_cost,
                "total_investment": total_investment, "annual_savings": annual_savings,
                "payback_period": payback_period, "roi_1_year": calculate_roi(total_investment, annual_savings, 1),
                "roi_5_year": calculate_roi(total_investment, annual_savings, 5), "pdf_link": "",
                "staff_savings_monthly": staff_savings_monthly, "noshow_savings_monthly": noshow_savings_monthly,
                "total_monthly_savings": total_monthly_savings
            }
            consultant_info_dict = {"name": consultant_name, "email": consultant_email, "phone": consultant_phone}

        # HASIL PERHITUNGAN DITAMPILKAN
        st.header("📊 Hasil Analisis ROI")
        col1_res, col2_res, col3_res, col4_res = st.columns(4)
        col1_res.metric("Investasi Awal", format_currency(report_data["total_investment"]))
        col2_res.metric("Penghematan Tahunan", format_currency(report_data["annual_savings"]))
        roi_5y = report_data["roi_5_year"]
        col3_res.metric("ROI 5 Tahun", f"{roi_5y:.1f}%" if roi_5y != float("inf") else "N/A")
        pb = report_data["payback_period"]
        col4_res.metric("Payback Period (Bulan)", f"{pb:.1f}" if pb != float("inf") else "N/A")
        
        st.subheader("📈 Visualisasi Data")
        figs = generate_charts(report_data)
        if figs:
            for fig in figs:
                if fig: st.pyplot(fig)

        # ... (Expander untuk detail perhitungan) ...

        # BUAT PDF DAN SINKRONISASI
        st.subheader("📄 Laporan PDF & Sinkronisasi Data")
        pdf_content = None
        with st.spinner("Membuat laporan PDF..."):
            try:
                pdf_content = generate_pdf_report(report_data, consultant_info_dict, figs)
                if pdf_content: st.download_button("📥 Unduh Laporan PDF", pdf_content, f"{client_name} ROI Report.pdf", "application/pdf")
                else: st.error("Gagal membuat konten PDF."); st.session_state.sync_status = "fail"
            except Exception as e:
                st.error(f"Terjadi kesalahan saat membuat PDF: {e}"); st.session_state.sync_status = "fail"
        
        if pdf_content and st.session_state.sync_status != "fail":
            supabase = supabase_utils.init_supabase_client()
            if not supabase: st.warning("Kredensial Supabase tidak valid."); st.session_state.sync_status = "fail"
            else:
                with st.spinner("Mengunggah PDF & menyimpan data..."):
                    date_str = datetime.now(WIB).strftime("%y%m%d")
                    base_name = f"{date_str} {client_name} {client_location}"
                    supabase_file_path = f"{base_name}/{base_name}.pdf"
                    pdf_link = supabase_utils.upload_pdf_to_storage(supabase, pdf_content, supabase_file_path, SUPABASE_BUCKET_NAME)
                    if pdf_link:
                        report_data["pdf_link"] = pdf_link
                        db_data = {k: v for k, v in report_data.items() if k not in ["staff_savings_monthly", "noshow_savings_monthly", "total_monthly_savings"]}
                        for k, v in db_data.items():
                            if v == float('inf'): db_data[k] = None
                        if supabase_utils.insert_report_data(supabase, SUPABASE_TABLE_NAME, db_data):
                            st.session_state.sync_status = "success"; st.balloons()
                        else: st.error("Gagal menyimpan data ke Database."); st.session_state.sync_status = "fail"
                    else: st.error("Gagal mengunggah PDF ke Supabase Storage."); st.session_state.sync_status = "fail"

        st.markdown("---")
        st.caption(f"© {datetime.now().year} Medical AI Solutions | Analisis dibuat pada {get_wib_time()}")

# ====================== ENTRY POINT APLIKASI ======================
if __name__ == "__main__":
    if "supabase" not in st.secrets:
        st.warning("⚠️ Kredensial Supabase tidak ditemukan di Secrets.", icon="🔒")
    main()