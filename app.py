import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config("Simulasi Muatan Kapal", layout="wide")
st.title("🚢 Simulasi Muatan Kapal Berdasarkan Golongan Kendaraan")

# Data golongan kendaraan
KENDARAAN = {
    "IV": (5, 3),
    "V": (7, 3),
    "VI": (10, 3),
    "VII": (12, 3),
    "VIII": (16, 3),
    "IX": (21, 3)
}

WARNA = {
    "IV": "#ff9999",
    "V": "#66b3ff",
    "VI": "#99ff99",
    "VII": "#ffcc99",
    "VIII": "#c2c2f0",
    "IX": "#ffb3e6"
}

# Inisialisasi state
if "kapal" not in st.session_state:
    st.session_state.kapal = None
if "grid" not in st.session_state:
    st.session_state.grid = None
if "kendaraan_masuk" not in st.session_state:
    st.session_state.kendaraan_masuk = []

# Fungsi membuat grid kosong
def buat_grid(panjang, lebar):
    baris = int(panjang)
    kolom = int(lebar)
    return np.full((baris, kolom), '', dtype=object)

# Fungsi menambahkan kendaraan secara manual
def tambah_kendaraan(gol):
    panjang_kendaraan, lebar_kendaraan = KENDARAAN[gol]
    grid = st.session_state.grid
    rows, cols = grid.shape

    # Pindai grid secara baris, cari lokasi kosong untuk kendaraan
    for i in range(rows - panjang_kendaraan + 1):
        for j in range(cols - lebar_kendaraan + 1):
            area = grid[i:i+panjang_kendaraan, j:j+lebar_kendaraan]
            if np.all(area == ''):
                grid[i:i+panjang_kendaraan, j:j+lebar_kendaraan] = gol
                st.session_state.kendaraan_masuk.append(gol)
                return True
    return False  # Tidak cukup tempat

# Fungsi visualisasi grid
def tampilkan_grid(grid):
    fig, ax = plt.subplots(figsize=(10, 6))
    rows, cols = grid.shape
    for i in range(rows):
        for j in range(cols):
            val = grid[i, j]
            color = WARNA.get(val, "#FFFFFF")
            ax.add_patch(plt.Rectangle((j, rows - i - 1), 1, 1, facecolor=color, edgecolor='black'))
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_xticks(np.arange(0, cols + 1, 1))
    ax.set_yticks(np.arange(0, rows + 1, 1))
    ax.set_aspect('equal')
    ax.set_title("Visualisasi Muatan Kapal")
    ax.axis('off')
    st.pyplot(fig)

# Input dimensi kapal
with st.sidebar:
    st.subheader("⚙️ Konfigurasi Kapal")
    panjang_kapal = st.number_input("Panjang kapal (meter)", min_value=10, value=40, step=1)
    lebar_kapal = st.number_input("Lebar kapal (meter)", min_value=3, value=12, step=1)

    if st.button("🚢 Buat Kapal"):
        st.session_state.grid = buat_grid(panjang_kapal, lebar_kapal)
        st.session_state.kendaraan_masuk = []

    if st.session_state.grid is not None:
        st.subheader("➕ Tambah Kendaraan")
        golongan = st.selectbox("Pilih golongan", list(KENDARAAN.keys()))
        if st.button("Tambahkan"):
            berhasil = tambah_kendaraan(golongan)
            if not berhasil:
                st.warning("❌ Tidak cukup ruang untuk kendaraan ini!")

# Visualisasi
if st.session_state.grid is not None:
    tampilkan_grid(st.session_state.grid)

    st.markdown("### 📦 Kendaraan yang Telah Masuk:")
    st.write(st.session_state.kendaraan_masuk)

    sisa = np.count_nonzero(st.session_state.grid == '')
    total = st.session_state.grid.size
    st.success(f"Sisa ruang: {sisa} dari {total} unit ({(sisa/total)*100:.2f}%)")
