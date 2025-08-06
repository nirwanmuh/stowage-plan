import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Konfigurasi
st.set_page_config(page_title="Simulasi Muat Kapal", layout="wide")
st.title("🚢 Simulasi Muat Kapal")

# Data golongan kendaraan
KENDARAAN = {
    "IV": (5, 3),
    "V": (7, 3),
    "VI": (10, 3),
    "VII": (12, 3),
    "VIII": (16, 3),
    "IX": (21, 3),
}

WARNA = {
    "IV": "skyblue",
    "V": "orange",
    "VI": "green",
    "VII": "red",
    "VIII": "purple",
    "IX": "brown"
}

# Inisialisasi session state
if "grid" not in st.session_state:
    st.session_state.grid = None
    st.session_state.kendaraan_masuk = []

# Input ukuran kapal
with st.sidebar:
    st.subheader("Ukuran Kapal")
    panjang_kapal = st.number_input("Panjang (meter)", min_value=10, value=30)
    lebar_kapal = st.number_input("Lebar (meter)", min_value=3, value=9)
    if st.button("🚫 Reset Kapal"):
        st.session_state.grid = None
        st.session_state.kendaraan_masuk = []

# Buat grid kapal berdasarkan ukuran
kapal_cols = int(panjang_kapal)
kapal_rows = int(lebar_kapal)

if st.session_state.grid is None:
    st.session_state.grid = np.full((kapal_rows, kapal_cols), "", dtype=object)

grid = st.session_state.grid

# Fungsi untuk mencari posisi penempatan
def cari_posisi_muat(panjang, lebar):
    for row in range(kapal_rows - lebar + 1):
        for col in range(kapal_cols - panjang + 1):
            blok = grid[row:row + lebar, col:col + panjang]
            if np.all(blok == ""):
                return row, col
    return None, None

# Input kendaraan
with st.sidebar:
    st.subheader("Tambah Kendaraan")
    gol = st.selectbox("Golongan Kendaraan", list(KENDARAAN.keys()))
    if st.button("➕ Masukkan Kendaraan"):
        p, l = KENDARAAN[gol]
        row, col = cari_posisi_muat(p, l)
        if row is not None:
            grid[row:row + l, col:col + p] = gol
            st.session_state.kendaraan_masuk.append((gol, row, col))
            st.success(f"Kendaraan golongan {gol} berhasil dimuat.")
        else:
            st.warning("Kapal penuh atau tidak ada ruang yang cukup.")

    if st.button("🚚 Keluarkan Terakhir"):
        if st.session_state.kendaraan_masuk:
            gol, row, col = st.session_state.kendaraan_masuk.pop()
            p, l = KENDARAAN[gol]
            grid[row:row + l, col:col + p] = ""
            st.info(f"Kendaraan golongan {gol} dikeluarkan.")
        else:
            st.warning("Tidak ada kendaraan yang bisa dikeluarkan.")

# Visualisasi Grid Kapal
def tampilkan_grid(grid):
    fig, ax = plt.subplots(figsize=(kapal_cols / 2, kapal_rows / 2))
    ax.set_xlim(0, kapal_cols)
    ax.set_ylim(0, kapal_rows)
    ax.set_xticks(np.arange(0, kapal_cols + 1, 1))
    ax.set_yticks(np.arange(0, kapal_rows + 1, 1))
    ax.grid(True)

    for row in range(kapal_rows):
        for col in range(kapal_cols):
            gol = grid[row, col]
            if gol != "":
                color = WARNA.get(gol, "gray")
                ax.add_patch(plt.Rectangle((col, kapal_rows - row - 1), 1, 1, color=color))
                ax.text(col + 0.5, kapal_rows - row - 0.5, gol, ha="center", va="center", color="white", fontsize=8)

    ax.set_aspect('equal')
    ax.set_title("Visualisasi Muatan Kapal")
    st.pyplot(fig)

tampilkan_grid(grid)
