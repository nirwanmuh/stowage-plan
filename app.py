import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import itertools
from matplotlib.patches import Rectangle

st.set_page_config(page_title="Simulasi Muat Kapal", layout="wide")

# Data ukuran kendaraan (panjang, lebar) meter dan berat (ton)
KENDARAAN = {
    "IV": {"dim": (5, 3), "berat": 1},
    "V": {"dim": (7, 3), "berat": 8},
    "VI": {"dim": (10, 3), "berat": 12},
    "VII": {"dim": (12, 3), "berat": 15},
    "VIII": {"dim": (16, 3), "berat": 18},
    "IX": {"dim": (21, 3), "berat": 30},
}

# Session state untuk menyimpan kendaraan
if "kendaraan" not in st.session_state:
    st.session_state.kendaraan = []

# Input ukuran kapal (FLOAT)
st.sidebar.header("Konfigurasi Kapal")
panjang_kapal = st.sidebar.number_input("Panjang Kapal (m)", min_value=10.0, value=50.0, step=0.1)
lebar_kapal = st.sidebar.number_input("Lebar Kapal (m)", min_value=5.0, value=15.0, step=0.1)

# Input titik seimbang vertikal
titik_seimbang_vertikal = st.sidebar.number_input(
    "Titik Seimbang Vertikal (m, dari buritan)", 
    min_value=0.0, 
    max_value=panjang_kapal, 
    value=panjang_kapal / 2, 
    step=0.1
)

# Input kendaraan
st.sidebar.header("Tambah Kendaraan")
golongan = st.sidebar.selectbox("Pilih Golongan", list(KENDARAAN.keys()))
if st.sidebar.button("Tambah Kendaraan"):
    st.session_state.kendaraan.append(golongan)

# Fungsi untuk mencari kombinasi optimal (brute force sederhana)
def cari_kombinasi_optimal(kendaraan_list):
    best_combo = []
    max_luas = 0.0

    for perm in itertools.permutations(kendaraan_list):
        posisi_x = 0.0
        posisi_y = 0.0
        baris_tertinggi = 0.0
        combo = []
        total_luas = 0.0

        for gol in perm:
            pjg, lbr = KENDARAAN[gol]["dim"]

            if posisi_x + pjg <= panjang_kapal and posisi_y + lbr <= lebar_kapal:
                combo.append((gol, posisi_x, posisi_y))
                total_luas += pjg * lbr
                posisi_x += pjg
                baris_tertinggi = max(baris_tertinggi, lbr)
            else:
                posisi_x = 0.0
                posisi_y += baris_tertinggi
                baris_tertinggi = 0.0
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

# Hitung total berat dan titik berat muatan
total_berat = sum(KENDARAAN[gol]["berat"] for gol, _, _ in combo_optimal)

if total_berat > 0:
    x_cm = sum((x + KENDARAAN[gol]["dim"][0] / 2) * KENDARAAN[gol]["berat"] for gol, x, y in combo_optimal) / total_berat
    y_cm = sum((y + KENDARAAN[gol]["dim"][1] / 2) * KENDARAAN[gol]["berat"] for gol, x, y in combo_optimal) / total_berat
else:
    x_cm, y_cm = 0, 0

# Titik seimbang horizontal otomatis = lebar_kapal / 2
titik_seimbang_horizontal = lebar_kapal / 2

# Selisih titik berat terhadap titik seimbang
selisih_vertikal = x_cm - titik_seimbang_vertikal
selisih_horizontal = y_cm - titik_seimbang_horizontal

# Tampilkan hasil
st.write(f"**Total Luas Kapal:** {luas_kapal:.2f} m²")
st.write(f"**Luas Terpakai:** {luas_terpakai:.2f} m²")
st.write(f"**Sisa Luas:** {sisa_luas:.2f} m²")
st.write(f"**Total Berat Muatan:** {total_berat:.2f} ton")
st.write(f"**Titik Berat Muatan (X, Y):** ({x_cm:.2f} m, {y_cm:.2f} m)")
st.write(f"**Titik Seimbang Vertikal:** {titik_seimbang_vertikal:.2f} m → Selisih: {selisih_vertikal:.2f} m")
st.write(f"**Titik Seimbang Horizontal:** {titik_seimbang_horizontal:.2f} m → Selisih: {selisih_horizontal:.2f} m")

# Visualisasi
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_xlim(0, panjang_kapal)
ax.set_ylim(0, lebar_kapal)
ax.set_aspect('equal')
ax.set_title("Visualisasi Muat Kapal")

# Outline kapal
kapal_outline = Rectangle((0, 0), panjang_kapal, lebar_kapal, 
                          linewidth=1.5, edgecolor='black', facecolor='none')
ax.add_patch(kapal_outline)

# Gambar kendaraan
for gol, x, y in combo_optimal:
    pjg, lbr = KENDARAAN[gol]["dim"]
    berat = KENDARAAN[gol]["berat"]
    rect = Rectangle((x, y), pjg, lbr, 
                     linewidth=1.5, edgecolor='blue', facecolor='skyblue', alpha=0.6)
    ax.add_patch(rect)
    ax.text(x + pjg/2, y + lbr/2, f"{gol}\n{berat}t", 
            color="red", ha="center", va="center", fontsize=8, fontweight="bold")
    # Titik pojok kendaraan
    pojok = [(x, y), (x+pjg, y), (x, y+lbr), (x+pjg, y+lbr)]
    for px, py in pojok:
        ax.plot(px, py, 'ko', markersize=4)

# Gambar titik berat
ax.plot(x_cm, y_cm, 'rx', markersize=10, label="Titik Berat Muatan")
# Gambar garis titik seimbang vertikal & horizontal
ax.axvline(titik_seimbang_vertikal, color='green', linestyle='--', label="Titik Seimbang Vertikal")
ax.axhline(titik_seimbang_horizontal, color='orange', linestyle='--', label="Titik Seimbang Horizontal")

ax.legend()
st.pyplot(fig)
