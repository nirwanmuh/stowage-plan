import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

st.set_page_config(page_title="Simulasi Muat Kapal", layout="wide")

# Definisi ukuran kendaraan per golongan
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
    "VI": "orange",
    "VII": "violet",
    "VIII": "salmon",
    "IX": "khaki",
}

# Inisialisasi state
if "kapal" not in st.session_state:
    st.session_state.kapal = None
if "grid" not in st.session_state:
    st.session_state.grid = None
if "kendaraan" not in st.session_state:
    st.session_state.kendaraan = []

# Sidebar: konfigurasi kapal
with st.sidebar:
    st.header("Konfigurasi Kapal")
    panjang_kapal = st.number_input("Panjang Kapal (meter)", min_value=1, value=30)
    lebar_kapal = st.number_input("Lebar Kapal (meter)", min_value=1, value=12)
    titik_seimbang = st.number_input(
        "Titik Seimbang Horizontal (meter)",
        min_value=0,
        max_value=panjang_kapal,
        value=panjang_kapal // 2
    ) 
    if st.button("🔄 Buat Ulang Kapal"):
        st.session_state.kapal = {
            "panjang": panjang_kapal,
            "lebar": lebar_kapal,
            "titik_seimbang_h": titik_seimbang,
            "titik_seimbang_v": lebar_kapal / 2  # dihitung otomatis
        }
        st.session_state.grid = np.zeros((lebar_kapal, panjang_kapal), dtype=object)
        st.session_state.kendaraan = []

# Sidebar: tambah kendaraan
with st.sidebar:
    st.header("Tambah Kendaraan")
    golongan = st.selectbox("Golongan", list(KENDARAAN.keys()))
    tambah = st.button("➕ Tambahkan ke Kapal")

# Fungsi: mencari tempat kosong
def cari_lokasi(grid, p, l):
    rows, cols = grid.shape
    for i in range(rows - l + 1):
        for j in range(cols - p + 1):
            potongan = grid[i:i+l, j:j+p]
            if np.all(potongan == 0):
                return i, j
    return None, None

# Fungsi: tambahkan kendaraan
def tambahkan_kendaraan(gol):
    p, l = KENDARAAN[gol]
    i, j = cari_lokasi(st.session_state.grid, p, l)
    if i is not None:
        for dx in range(l):
            for dy in range(p):
                st.session_state.grid[i+dx, j+dy] = gol
        st.session_state.kendaraan.append({"gol": gol, "pos": (i, j), "size": (p, l)})
        return True
    return False

# Jalankan tambah kendaraan
if tambah:
    if not st.session_state.kapal:
        st.warning("Buat kapal terlebih dahulu!")
    else:
        berhasil = tambahkan_kendaraan(golongan)
        if not berhasil:
            st.error("❌ Tidak ada ruang yang cukup untuk kendaraan ini.")

# Fungsi: tampilkan grid
def tampilkan_grid(grid):
    rows, cols = grid.shape
    fig, ax = plt.subplots(figsize=(cols / 2, rows / 2))
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_xticks(np.arange(0, cols + 1, 1))
    ax.set_yticks(np.arange(0, rows + 1, 1))
    ax.grid(True)
    # Garis vertikal titik seimbang horizontal
    if st.session_state.kapal and "titik_seimbang_h" in st.session_state.kapal:
        x_seimbang = st.session_state.kapal["titik_seimbang_h"]
        ax.axvline(x=x_seimbang, color="red", linestyle="--", linewidth=1.5)
        ax.text(x_seimbang, rows + 0.3, "Titik Seimbang (Depan-Belakang)", color="red", fontsize=8, ha="center")

    # Garis horizontal titik seimbang vertikal
    if "titik_seimbang_v" in st.session_state.kapal:
        y_seimbang = st.session_state.kapal["titik_seimbang_v"]
        ax.axhline(y=rows - y_seimbang, color="red", linestyle="--", linewidth=1.5)
        ax.text(cols + 0.2, rows - y_seimbang, "Titik Seimbang (Kiri-Kanan)", color="red", fontsize=8, va="center", rotation=90)



    for i in range(rows):
        for j in range(cols):
            val = grid[i, j]
            if val != 0:
                rect = Rectangle((j, rows - i - 1), 1, 1, color=WARNA.get(val, "gray"))
                ax.add_patch(rect)
                ax.text(j + 0.5, rows - i - 0.5, val, ha="center", va="center", fontsize=8)

    # Tambahkan teks "Depan" dan "Belakang"
    ax.text(0, -0.8, "⬅️ Depan", ha="left", va="center", fontsize=10, weight="bold")
    ax.text(cols, -0.8, "Belakang ➡️", ha="right", va="center", fontsize=10, weight="bold")

    ax.set_aspect('equal')
    st.pyplot(fig)

# Fungsi: hitung sisa ruang dan kemungkinan kendaraan
def hitung_sisa_dan_kemungkinan(grid):
    sisa_kosong = np.sum(grid == 0)
    luas_tersisa = sisa_kosong * 1  # 1m x 1m
    kemungkinan = {}
    for gol, (p, l) in KENDARAAN.items():
        luas_kendaraan = p * l
        muat = luas_tersisa // luas_kendaraan
        kemungkinan[gol] = int(muat)
    return luas_tersisa, kemungkinan

# Tampilan utama
st.title("🚢 Simulasi Kapasitas Muat Kapal")
if st.session_state.kapal:
    st.subheader("Visualisasi Muatan Kapal")
    tampilkan_grid(st.session_state.grid)

    st.subheader("Sisa Kapasitas & Kemungkinan Muat")
    sisa, kemungkinan = hitung_sisa_dan_kemungkinan(st.session_state.grid)
    st.write(f"**Sisa luas ruang kosong:** {sisa} m²")
    st.table([{"Golongan": gol, "Masih Bisa Muat": jumlah} for gol, jumlah in kemungkinan.items()])

    st.subheader("Daftar Kendaraan Saat Ini")
    if st.session_state.kendaraan:
        for idx, k in enumerate(st.session_state.kendaraan, 1):
            st.write(f"{idx}. Golongan {k['gol']} di posisi {k['pos']} ukuran {k['size']}")
    else:
        st.info("Belum ada kendaraan di kapal.")
else:
    st.info("Silakan buat kapal terlebih dahulu melalui sidebar.")
