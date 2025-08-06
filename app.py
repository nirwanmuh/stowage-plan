import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Set page config
st.set_page_config(page_title="Simulasi Muatan Kapal", layout="wide")
st.title("Simulasi Muatan Kapal - 1 Lantai")

# Data kendaraan per golongan
KENDARAAN = {
    "IV": (5, 3),
    "V": (7, 3),
    "VI": (10, 3),
    "VII": (12, 3),
    "VIII": (16, 3),
    "IX": (21, 3),
}
WARNA = {
    "IV": "lightblue",
    "V": "lightgreen",
    "VI": "khaki",
    "VII": "orange",
    "VIII": "plum",
    "IX": "salmon",
}

# Sidebar input ukuran kapal
st.sidebar.header("Konfigurasi Kapal")
kapal_panjang = st.sidebar.number_input("Panjang Kapal (meter)", min_value=10, value=50)
kapal_lebar = st.sidebar.number_input("Lebar Kapal (meter)", min_value=3, value=9)

# Buat grid berdasarkan resolusi 1m
rows = int(kapal_panjang)
cols = int(kapal_lebar)
grid = np.full((rows, cols), '', dtype=object)

# Inisialisasi state
if "kendaraan" not in st.session_state:
    st.session_state.kendaraan = []

# Fungsi untuk menempatkan kendaraan otomatis

def tempatkan_kendaraan(golongan):
    panjang, lebar = KENDARAAN[golongan]
    for r in range(rows - panjang + 1):
        for c in range(cols - lebar + 1):
            area = grid[r:r+panjang, c:c+lebar]
            if np.all(area == ''):
                grid[r:r+panjang, c:c+lebar] = golongan
                return (r, c)
    return None

# Sidebar form tambah kendaraan
st.sidebar.header("Tambah Kendaraan")
with st.sidebar.form("form_kendaraan"):
    gol = st.selectbox("Golongan", list(KENDARAAN.keys()))
    submit = st.form_submit_button("Tambah")
    if submit:
        lokasi = tempatkan_kendaraan(gol)
        if lokasi:
            st.session_state.kendaraan.append((gol, lokasi))
        else:
            st.sidebar.warning("Tidak cukup ruang untuk kendaraan golongan tersebut.")

# Hitung sisa kemungkinan kendaraan per golongan
st.sidebar.header("Sisa Muat Maksimal")
def hitung_sisa(golongan):
    temp_grid = grid.copy()
    count = 0
    panjang, lebar = KENDARAAN[golongan]
    for r in range(rows - panjang + 1):
        for c in range(cols - lebar + 1):
            area = temp_grid[r:r+panjang, c:c+lebar]
            if np.all(area == ''):
                temp_grid[r:r+panjang, c:c+lebar] = golongan
                count += 1
    return count

for gol in KENDARAAN:
    sisa = hitung_sisa(gol)
    st.sidebar.write(f"Gol. {gol}: {sisa} unit")

# Visualisasi grid
def tampilkan_visual():
    fig, ax = plt.subplots(figsize=(cols/2, rows/2))
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_xticks(range(cols + 1))
    ax.set_yticks(range(rows + 1))
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.grid(True)
    
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] != '':
                gol = grid[r, c]
                ax.add_patch(Rectangle((c, rows - r - 1), 1, 1, color=WARNA[gol]))
                ax.text(c + 0.5, rows - r - 0.5, gol, ha='center', va='center', fontsize=6)

    # Tambahkan label "Depan" dan "Belakang"
    ax.text(-0.5, rows - 0.5, "Depan", rotation=90, fontsize=10, va='center')
    ax.text(-0.5, 0.5, "Belakang", rotation=90, fontsize=10, va='center')

    st.pyplot(fig)

st.subheader("Visualisasi Kapal")
tampilkan_visual()
