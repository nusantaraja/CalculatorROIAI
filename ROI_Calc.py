# ROI_Calc.py

#!/usr/bin/env python3
# Kalkulator ROI 5 Tahun untuk Implementasi Proyek
# Created by: Medical Solutions
# Versi Streamlit 3.1 (2024) - Migrasi ke Supabase

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
SUPABASE_BUCKET_NAME = "laporan-pdf"  # Ganti dengan nama bucket Anda
SUPABASE_TABLE_NAME = "laporan_roi"   # Ganti dengan nama tabel Anda
WIB = pytz.timezone("Asia/Jakarta")

# ====================== FUNGSI UTAMA ======================

def get_wib_time():
    """Returns the current time formatted for WIB."""
    now_utc = datetime.now(pytz.utc)
    now_wib = now_utc.astimezone(WIB)
    return now_wib.strftime("%Y-%m-%d %H:%M:%S WIB")

def setup_locale():
    """Mengatur locale untuk format angka."""
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

# ... (Fungsi generate_charts tetap sama) ...
def generate_charts(data):
    """Generate grafik untuk visualisasi data."""
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
            data.get("noshow_savings_monthly", 0) * 12, # Tetap pakai nama variabel ini
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

# ... (Fungsi generate_pdf_report dimodifikasi untuk istilah baru) ...
def generate_pdf_report(report_data, consultant_info, figs):
    """Generate PDF report using FPDF with bundled fonts."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    font_family = "DejaVu"
    try:
        font_base_path = "fonts/ttf/"
        pdf.add_font("DejaVu", "", f"{font_base_path}DejaVuSans.ttf")
        pdf.add_font("DejaVu", "B", f"{font_base_path}DejaVuSans-Bold.ttf")
    except Exception as e:
        st.sidebar.error(f"Gagal memuat font lokal. Menggunakan Arial.")
        font_family = "Arial"
    
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

    # ... Sisa dari generate_pdf_report (Hasil Utama, Detail, Visualisasi) tetap sama
    # ... pastikan `report_data.get('...')` menggunakan key yang benar
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
    pdf.cell(0, 8, "Detail Perhitungan", new_x="LMARGIN", new_y="NEXT", border="B")
    pdf.set_font(font_family, style="", size=10)
    pdf.cell(0, 6, "Komponen Penghematan Bulanan:", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"  + Pengurangan biaya staff: {format_currency(report_data.get('staff_savings_monthly', 0))}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"  + Pengurangan kerugian operasional: {format_currency(report_data.get('noshow_savings_monthly', 0))}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"  - Biaya pemeliharaan bulanan: {format_currency(report_data.get('maintenance_cost_idr', 0))}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, style="B")
    pdf.cell(0, 6, f"  = Total Penghematan Bulanan Bersih: {format_currency(report_data.get('total_monthly_savings', 0))}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, style="")
    pdf.ln(3)
    pdf.cell(0, 6, "Breakdown Investasi Awal:", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"  - Biaya setup: {format_currency(report_data.get('setup_cost', 0))}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"  - Biaya integrasi: {format_currency(report_data.get('integration_cost', 0))}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"  - Biaya pelatihan: {format_currency(report_data.get('training_cost', 0))}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, style="B")
    pdf.cell(0, 6, f"  = Total Investasi Awal: {format_currency(report_data.get('total_investment', 0))}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_family, style="")
    pdf.ln(10)

    pdf.set_font(font_family, style="B", size=12)
    pdf.cell(0, 8, "Visualisasi Data", new_x="LMARGIN", new_y="NEXT", border="B")
    pdf.set_font(font_family, style="", size=10)
    pdf.ln(5)
    if figs:
        for i, fig in enumerate(figs):
            if fig is None: continue
            try:
                chart_path = f"/tmp/chart_{i}.png"
                fig.savefig(chart_path, bbox_inches="tight", dpi=200)
                img_width = pdf.w - 2 * pdf.l_margin
                pdf.image(chart_path, x=None, y=None, w=img_width)
                pdf.ln(5)
                plt.close(fig)
            except Exception as img_e:
                st.error(f"Error saving or embedding chart {i}: {img_e}")
                if "fig" in locals() and fig is not None: plt.close(fig)
    else:
        pdf.cell(0, 6, "Grafik tidak dapat dibuat.", new_x="LMARGIN", new_y="NEXT")

    try:
        return bytes(pdf.output())
    except Exception as pdf_err:
        st.error(f"Error finalizing PDF output: {pdf_err}")
        st.code(traceback.format_exc())
        return None

# ====================== TAMPILAN STREAMLIT ======================

def main():
    st.set_page_config(page_title="Kalkulator ROI Proyek", page_icon="💼", layout="wide")
    
    # ... (CSS Markdown tetap sama) ...
    st.markdown("""<style>...</style>""", unsafe_allow_html=True)

    st.title("💼 Kalkulator ROI 5 Tahun untuk Implementasi Proyek")
    st.markdown("**Alat interaktif untuk menghitung potensi Return on Investment (ROI) dari implementasi solusi baru.**")
    st.markdown("---")

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
        
        st.markdown("---")
        hitung_roi = st.button("🚀 HITUNG ROI & SIMPAN LAPORAN", type="primary", use_container_width=True, disabled=not consultant_info_filled)

    if hitung_roi:
        if not consultant_info_filled:
            st.error("⚠️ Harap isi semua informasi konsultan di sidebar sebelum menghitung.")
            st.stop()

        with st.spinner("⏳ Menghitung ROI dan menyiapkan laporan..."):
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
                "training_cost_usd": training_cost_usd, "maintenance_cost_idr": maintenance_cost, "setup_cost": setup_cost,
                "integration_cost": integration_cost, "training_cost": training_cost, "total_investment": total_investment,
                "staff_savings_monthly": staff_savings_monthly, "noshow_savings_monthly": noshow_savings_monthly,
                "total_monthly_savings": total_monthly_savings, "annual_savings": annual_savings,
                "payback_period": payback_period, "roi_1_year": calculate_roi(total_investment, annual_savings, 1),
                "roi_5_year": calculate_roi(total_investment, annual_savings, 5), "pdf_link": ""
            }
            consultant_info_dict = {"name": consultant_name, "email": consultant_email, "phone": consultant_phone}

            # ... (Tampilan hasil, grafik, dan expander tetap sama) ...
            st.header("📊 Hasil Analisis ROI")
            st.success("Perhitungan ROI berhasil dilakukan!")
            # ...

            st.subheader("📄 Laporan PDF & Sinkronisasi Data")
            
            date_str = datetime.now(WIB).strftime("%y%m%d")
            base_name = f"{date_str} {client_name} {client_location}"
            pdf_filename = f"{base_name}.pdf"
            supabase_file_path = f"{base_name}/{pdf_filename}" # Path di dalam bucket

            pdf_content = None
            try:
                with st.spinner("Membuat laporan PDF..."): 
                    pdf_content = generate_pdf_report(report_data, consultant_info_dict, figs)
                if pdf_content:
                    st.download_button(label="📥 Unduh Laporan PDF", data=pdf_content, file_name=pdf_filename, mime="application/pdf")
                else:
                    st.error("Gagal membuat konten PDF. Sinkronisasi tidak akan berjalan.")
            except Exception as pdf_gen_err:
                st.error(f"Terjadi kesalahan fatal saat membuat PDF: {pdf_gen_err}")
                pdf_content = None

            if pdf_content:
                supabase = supabase_utils.init_supabase_client()
                if not supabase:
                    st.warning("Kredensial Supabase tidak valid. Sinkronisasi dilewati.", icon="🔒")
                else:
                    pdf_link = None
                    with st.spinner("Mengunggah PDF ke Supabase Storage..."):
                        pdf_link = supabase_utils.upload_pdf_to_storage(supabase, pdf_content, supabase_file_path, SUPABASE_BUCKET_NAME)
                    
                    if pdf_link:
                        st.success(f"Laporan PDF berhasil diunggah. [Lihat Laporan]({pdf_link})", icon="📄")
                        report_data["pdf_link"] = pdf_link
                    else:
                        st.error("Gagal mengunggah PDF ke Supabase Storage.")

                    # Hanya lanjutkan jika link PDF ada
                    if pdf_link:
                        with st.spinner("Menyimpan data ke database Supabase..."):
                            # Siapkan data untuk DB, ganti 'inf' dengan None (akan jadi NULL)
                            db_data = report_data.copy()
                            for key, value in db_data.items():
                                if value == float('inf'):
                                    db_data[key] = None
                            # Hapus kunci yang tidak ada di tabel DB
                            db_data.pop('setup_cost', None)
                            db_data.pop('integration_cost', None)
                            db_data.pop('training_cost', None)
                            db_data.pop('total_monthly_savings', None)
                            db_data.pop('staff_savings_monthly', None)
                            db_data.pop('noshow_savings_monthly', None)

                            if supabase_utils.insert_report_data(supabase, SUPABASE_TABLE_NAME, db_data):
                                st.success("Data berhasil disimpan ke Database.", icon="📝")
                                st.balloons()
                            else:
                                st.error("Gagal menyimpan data ke Database.")
            
            st.markdown("---")
            st.caption(f"© {datetime.now().year} AI Solutions | Analisis dibuat pada {get_wib_time()}")

if __name__ == "__main__":
    if "supabase" not in st.secrets:
        st.warning("⚠️ Kredensial Supabase tidak ditemukan di Secrets. Fitur sinkronisasi tidak akan berfungsi.", icon="🔒")
    main()