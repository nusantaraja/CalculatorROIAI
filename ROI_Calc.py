#!/usr/bin/env python3
# Kalkulator ROI Proyek - Versi FINAL dengan `st.session_state` (2024)
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
import pytz

import supabase_utils

# ====================== KONSTANTA ======================
SUPABASE_BUCKET_NAME = "laporan-pdf"
SUPABASE_TABLE_NAME = "laporan_roi"
WIB = pytz.timezone("Asia/Jakarta")

# ====================== FUNGSI-FUNGSI BANTUAN (Tidak Perlu Diubah) ======================
def get_wib_time():
    return datetime.now(pytz.utc).astimezone(WIB).strftime("%Y-%m-%d %H:%M:%S WIB")

def setup_locale():
    for loc in ["id_ID.UTF-8", "Indonesian_Indonesia.1252"]:
        with suppress(locale.Error, ValueError):
            locale.setlocale(locale.LC_ALL, loc); return True
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

def generate_charts(data):
    # ... Fungsi ini sudah benar, tidak perlu diubah ...
    return []

def generate_pdf_report(report_data, consultant_info, figs):
    # ... Fungsi ini sudah benar, tidak perlu diubah ...
    return bytes()

# ====================== APLIKASI UTAMA STREAMLIT ======================
def main():
    st.set_page_config(page_title="Kalkulator ROI Proyek", page_icon="💼", layout="wide")

    # KUNCI UTAMA #1: Inisialisasi semua variabel yang perlu diingat di session_state.
    if "calculation_done" not in st.session_state:
        st.session_state.calculation_done = False
        st.session_state.report_data = {}
        st.session_state.consultant_info = {}
        st.session_state.figs = []
        st.session_state.pdf_content = None
        st.session_state.sync_status = "idle"

    st.markdown("""<style>...</style>""", unsafe_allow_html=True) # CSS disembunyikan
    st.title("💼 Kalkulator ROI 5 Tahun untuk Implementasi Proyek")
    st.markdown("**Alat interaktif untuk menghitung potensi Return on Investment (ROI) dari implementasi solusi baru.**")
    st.markdown("---")

    with st.sidebar:
        st.header("👤 Informasi Konsultan")
        consultant_name = st.text_input("Nama Konsultan", key="consultant_name")
        consultant_email = st.text_input("Email Konsultan", key="consultant_email")
        consultant_phone = st.text_input("No. HP/WA Konsultan", key="consultant_phone")
        consultant_info_filled = bool(consultant_name and consultant_email and consultant_phone)
        if not consultant_info_filled: st.warning("Harap isi semua informasi konsultan.")
        
        st.markdown("---")
        # ... Semua input lainnya di sidebar (st.number_input, st.slider) sudah benar ...
        # ...
        
        hitung_roi = st.button("🚀 HITUNG ROI & SIMPAN LAPORAN", type="primary", use_container_width=True, disabled=not consultant_info_filled)

        if st.session_state.sync_status == "success":
            st.markdown("---"); st.markdown("<p style='text-align: center; color: #3dd56d;'>✅ Sinkronisasi Berhasil</p>", unsafe_allow_html=True)
        elif st.session_state.sync_status == "fail":
            st.markdown("---"); st.markdown("<p style='text-align: center; color: #ff4b4b;'>❌ Sinkronisasi Gagal</p>", unsafe_allow_html=True)

    # KUNCI UTAMA #2: Blok ini HANYA untuk menghitung dan MENYIMPAN ke session_state.
    if hitung_roi:
        st.session_state.sync_status = "idle"
        if not consultant_info_filled:
            st.error("⚠️ Harap isi semua informasi konsultan di sidebar."); st.stop()

        with st.spinner("⏳ Menghitung & memproses data..."):
            setup_cost = setup_cost_usd * exchange_rate # Asumsi variabel input ada
            total_investment = setup_cost # Sederhanakan untuk contoh
            annual_savings = 50000000 # Contoh
            payback_period = 2.2 # Contoh

            report_data = { "total_investment": total_investment, "annual_savings": annual_savings, "payback_period": payback_period, "roi_5_year": 2615.5 }
            # ... Isi `report_data` dengan semua hasil kalkulasi Anda yang lengkap ...

            consultant_info = {"name": consultant_name, "email": consultant_email, "phone": consultant_phone}
            figs = generate_charts(report_data)
            pdf_content = generate_pdf_report(report_data, consultant_info, figs)

            # Simpan semua hasil ke "memori" aplikasi
            st.session_state.report_data = report_data
            st.session_state.consultant_info = consultant_info
            st.session_state.figs = figs
            st.session_state.pdf_content = pdf_content
            st.session_state.calculation_done = True
            
            # Lakukan sinkronisasi sekarang juga
            if pdf_content:
                supabase = supabase_utils.init_supabase_client()
                if supabase:
                    date_str = datetime.now(WIB).strftime("%y%m%d")
                    base_name = f"{date_str} {client_name} {client_location}"
                    supabase_file_path = f"{base_name}/{base_name}.pdf"
                    pdf_link = supabase_utils.upload_pdf_to_storage(supabase, pdf_content, supabase_file_path, SUPABASE_BUCKET_NAME)
                    if pdf_link:
                        # ... Logika simpan ke DB ...
                        st.session_state.sync_status = "success"
                        st.balloons()
                    else:
                        st.session_state.sync_status = "fail"
                else:
                    st.session_state.sync_status = "fail"
            else:
                st.session_state.sync_status = "fail"


    # KUNCI UTAMA #3: Blok ini HANYA untuk MENAMPILKAN hasil dari session_state.
    # Ini akan tetap tampil bahkan setelah skrip dijalankan ulang.
    if st.session_state.calculation_done:
        st.header("📊 Hasil Analisis ROI")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Investasi Awal", format_currency(st.session_state.report_data.get("total_investment", 0)))
        col2.metric("Penghematan Tahunan", format_currency(st.session_state.report_data.get("annual_savings", 0)))
        roi_5y = st.session_state.report_data.get("roi_5_year", float("inf"))
        col3.metric("ROI 5 Tahun", f"{roi_5y:.1f}%" if roi_5y != float("inf") else "N/A")
        pb = st.session_state.report_data.get("payback_period", float("inf"))
        col4.metric("Payback Period (Bulan)", f"{pb:.1f}" if pb != float("inf") else "N/A")

        st.subheader("📈 Visualisasi Data")
        if st.session_state.figs:
            for fig in st.session_state.figs:
                if fig: st.pyplot(fig)
        
        with st.expander("🔍 Lihat Detail Perhitungan"):
            # ... Tampilkan detail dari st.session_state.report_data ...
            st.write(f"**Total Investasi:** {format_currency(st.session_state.report_data.get('total_investment', 0))}")

        st.subheader("📄 Laporan PDF & Sinkronisasi Data")
        if st.session_state.pdf_content:
            st.download_button(
                label="📥 Unduh Laporan PDF",
                data=st.session_state.pdf_content,
                file_name=f"{st.session_state.report_data.get('client_name', 'Laporan')} ROI.pdf",
                mime="application/pdf"
            )
        
        st.markdown("---")
        st.caption(f"© {datetime.now().year} Medical AI Solutions | Analisis dibuat pada {get_wib_time()}")

if __name__ == "__main__":
    if "supabase" not in st.secrets:
        st.warning("⚠️ Kredensial Supabase tidak ditemukan.", icon="🔒")
    main()