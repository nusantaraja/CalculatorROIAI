# supabase_utils.py

import streamlit as st
from supabase import create_client, Client
import traceback

def init_supabase_client():
    """Initializes and returns a Supabase client using Streamlit secrets."""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Gagal menginisialisasi Supabase client: {e}", icon="🚨")
        return None

def upload_pdf_to_storage(client: Client, pdf_content: bytes, file_path: str, bucket_name: str):
    """Uploads PDF content to a Supabase Storage bucket and returns the public URL."""
    if not client:
        st.error("Supabase client tidak tersedia untuk unggah PDF.")
        return None
    try:
        # Supabase Python client v1.x expects bytes
        client.storage.from_(bucket_name).upload(file_path, pdf_content, {"contentType": "application/pdf"})
        
        # Dapatkan URL publik dari file yang baru diunggah
        public_url = client.storage.from_(bucket_name).get_public_url(file_path)
        return public_url
    except Exception as e:
        # Cek jika file sudah ada (error "Duplicate")
        if "Duplicate" in str(e):
            st.warning(f"File di '{file_path}' sudah ada. Menggunakan link yang ada.", icon="⚠️")
            public_url = client.storage.from_(bucket_name).get_public_url(file_path)
            return public_url
            
        st.error(f"Error saat mengunggah PDF ke Supabase Storage: {e}", icon="🚨")
        st.code(traceback.format_exc())
        return None

def insert_report_data(client: Client, table_name: str, data_dict: dict):
    """Inserts a dictionary of report data into a Supabase table."""
    if not client:
        st.error("Supabase client tidak tersedia untuk menyimpan data.")
        return False
    try:
        # Lakukan insert data. Supabase akan menangani konversi tipe data.
        response = client.table(table_name).insert(data_dict).execute()
        
        # Cek jika ada error dalam response
        if hasattr(response, 'error') and response.error:
            st.error(f"Gagal menyimpan data ke Supabase: {response.error.message}", icon="🚨")
            return False
        
        return True
    except Exception as e:
        st.error(f"Error saat menyimpan data ke tabel Supabase: {e}", icon="🚨")
        st.code(traceback.format_exc())
        return False