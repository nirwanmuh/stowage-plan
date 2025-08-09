import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import itertools

st.set_page_config(page_title="Simulasi Muat Kapal", layout="wide")

# Data ukuran kendaraan (panjang, lebar) meter
KENDARAAN = {
    "IV": (5, 3),
    "V": (7, 3),
    "VI": (10, 3),
    "VII": (12, 3),
    "VIII": (16, 3),
    "IX": (21, 3),
}

# Session state untuk menyimpan kendaraan
if "kendaraan" not in st.session_state:
    st.session_state.kendaraan = []

# Input ukuran kapal
st.sidebar.header("Konfigurasi Kapal")
panjang_kapal = st.sidebar.number_input("Panjang Kapal (m)", min_value=10, value=50)
lebar_kapal = st.sidebar.number_input("Lebar Kapal (m)", min_value=5, value=15)

# Input kendaraan
st.sidebar.header("Tambah Kendaraan")
golongan = st.sidebar.selectbox("Pilih Golongan", list(KENDARAAN.keys()))
if st.sidebar.button("Tambah Kendaraan"):
    st.session_state.kendaraan.append(golongan)

# Fungsi untuk mencari kombinasi optimal (brute force sederhana)
def cari_kombinasi_optimal(kendaraan_list):
    # Semua kemungkinan urutan
    best_combo = []
    max_luas = 0

    for perm in itertools.permutations(kendaraan_list):
        posisi_x = 0
        posisi_y = 0
        baris_tertinggi = 0
        combo = []
        total_luas = 0

        for gol in perm:
            pjg, lbr = KENDARAAN[gol]

            if posisi_x + pjg <= panjang_kapal and posisi_y + lbr <= lebar_kapal:
                combo.append((gol, posisi_x, posisi_y))
                total_luas += pjg * lbr
                posisi_x += pjg
                baris_tertinggi = max(baris_tertinggi, lbr)
            else:
                posisi_x = 0
                posisi_y += baris_tertinggi
                baris_tertinggi = 0
                if posisi_y + lbr <= lebar_kapal:
                    combo.append((gol, posisi_x, posisi_y))
                    total_luas += pjg * lbr
                    posisi_x += pjg
                    baris_tertinggi = max(baris_tertinggi, lbr)

        if total_luas > max_luas:
            max_luas = total_luas
            best_combo = combo

    return best_combo, max_luas

# Hitung kombinasi optimal
combo_optimal, luas_terpakai = cari_kombinasi_optimal(st.session_state.kendaraan)
luas_kapal = panjang_kapal * lebar_kapal
sisa_luas = luas_kapal - luas_terpakai

# Tampilkan hasil
st.write(f"**Total Luas Kapal:** {luas_kapal} m²")
st.write(f"**Luas Terpakai:** {luas_terpakai} m²")
st.write(f"**Sisa Luas:** {sisa_luas} m²")

# Visualisasi titik
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_xlim(0, panjang_kapal)
ax.set_ylim(0, lebar_kapal)
ax.set_aspect('equal')
ax.set_title("Visualisasi Muat Kapal (Titik-Titik)")

# Gambar titik dan outline kendaraan
for gol, x, y in combo_optimal:
    pjg, lbr = KENDARAAN[gol]
    # titik-titik kendaraan
    xx, yy = np.meshgrid(np.linspace(x, x+pjg, int(pjg*2)), 
                         np.linspace(y, y+lbr, int(lbr*2)))
    ax.scatter(xx, yy, s=5)
    ax.text(x + pjg/2, y + lbr/2, gol, color="red", ha="center", va="center")

# Outline kapal
ax.plot([0, panjang_kapal, panjang_kapal, 0, 0],
        [0, 0, lebar_kapal, lebar_kapal, 0], 'k-')

st.pyplot(fig)
