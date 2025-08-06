import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="Simulasi Kapal", layout="wide")
st.title("🚢 Simulasi Muatan Kapal (1 Lantai)")

# Konstanta ukuran kendaraan per golongan (panjang, lebar)
KENDARAAN = {
    4: (2, 1),
    5: (2, 1),
    6: (3, 1),
    7: (3, 1),
    8: (4, 1),
    9: (5, 2),
}

ROMAWI = {4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX"}
WARNA = {4: "skyblue", 5: "limegreen", 6: "orange", 7: "gold", 8: "violet", 9: "tomato"}

# Inisialisasi session state
if 'grid' not in st.session_state:
    st.session_state.grid = None
if 'kendaraan_list' not in st.session_state:
    st.session_state.kendaraan_list = []
if 'kapal_dimensi' not in st.session_state:
    st.session_state.kapal_dimensi = (0, 0)

# Konfigurasi ukuran kapal
with st.sidebar:
    st.header("⚙️ Konfigurasi Kapal")
    panjang = st.number_input("Panjang kapal (grid)", min_value=5, value=10)
    lebar = st.number_input("Lebar kapal (grid)", min_value=2, value=5)

    if st.button("Set Ulang Kapal"):
        st.session_state.kapal_dimensi = (panjang, lebar)
        st.session_state.grid = np.zeros((panjang, lebar), dtype=int)
        st.session_state.kendaraan_list = []

# Fungsi mencari posisi kosong
def cari_posisi(grid, ukuran):
    p, l = ukuran
    for i in range(grid.shape[0] - p + 1):
        for j in range(grid.shape[1] - l + 1):
            if np.all(grid[i:i+p, j:j+l] == 0):
                return i, j
    return None

# Tambahkan kendaraan
st.subheader("➕ Tambah Kendaraan")
col1, col2 = st.columns(2)
with col1:
    golongan = st.selectbox("Pilih golongan kendaraan", options=list(KENDARAAN.keys()), format_func=lambda x: f"Golongan {ROMAWI[x]}")
with col2:
    nama = st.text_input("Nama / ID kendaraan (opsional)", value=f"ID-{len(st.session_state.kendaraan_list)+1}")

if st.button("Tambahkan ke kapal"):
    if st.session_state.grid is None:
        st.warning("Silakan set dulu ukuran kapal di sidebar.")
    else:
        ukuran = KENDARAAN[golongan]
        posisi = cari_posisi(st.session_state.grid, ukuran)
        if posisi:
            i, j = posisi
            p, l = ukuran
            st.session_state.grid[i:i+p, j:j+l] = golongan
            st.session_state.kendaraan_list.append({
                "nama": nama,
                "golongan": golongan,
                "ukuran": ukuran,
                "posisi": posisi
            })
            st.success(f"Kendaraan {nama} berhasil ditambahkan.")
        else:
            st.error("Tidak ada ruang kosong untuk kendaraan ini!")

# Tampilkan visualisasi
def tampilkan_grid(grid):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, grid.shape[1])
    ax.set_ylim(0, grid.shape[0])
    ax.set_xticks(np.arange(0, grid.shape[1]+1, 1))
    ax.set_yticks(np.arange(0, grid.shape[0]+1, 1))
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.grid(True)

    for kendaraan in st.session_state.kendaraan_list:
        i, j = kendaraan["posisi"]
        p, l = kendaraan["ukuran"]
        gol = kendaraan["golongan"]
        warna = WARNA[gol]
        rect = patches.Rectangle((j, grid.shape[0] - i - p), l, p, linewidth=1, edgecolor='black', facecolor=warna)
        ax.add_patch(rect)
        ax.text(j + l/2, grid.shape[0] - i - p/2, ROMAWI[gol], color='black', ha='center', va='center', fontsize=12, weight='bold')

    st.pyplot(fig)

if st.session_state.grid is not None:
    st.subheader("📦 Visualisasi Kapal")
    tampilkan_grid(st.session_state.grid)

# Hapus kendaraan
st.subheader("🗑️ Hapus Kendaraan")
if st.session_state.kendaraan_list:
    opsi_hapus = [f"{v['nama']} (Gol. {ROMAWI[v['golongan']]})" for v in st.session_state.kendaraan_list]
    idx_hapus = st.selectbox("Pilih kendaraan yang ingin dihapus", options=range(len(opsi_hapus)), format_func=lambda x: opsi_hapus[x])
    if st.button("Hapus kendaraan"):
        kendaraan = st.session_state.kendaraan_list.pop(idx_hapus)
        i, j = kendaraan["posisi"]
        p, l = kendaraan["ukuran"]
        st.session_state.grid[i:i+p, j:j+l] = 0
        st.success(f"Kendaraan {kendaraan['nama']} telah dihapus.")
else:
    st.info("Belum ada kendaraan dimuat.")
