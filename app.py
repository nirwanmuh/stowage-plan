import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Ukuran kendaraan: panjang (meter), lebar (meter)
KENDARAAN = {
    "IV": (5, 3),
    "V": (7, 3),
    "VI": (10, 3),
    "VII": (12, 3),
    "VIII": (16, 3),
    "IX": (21, 3),
}

# Warna kendaraan untuk visualisasi
WARNA = {
    "IV": "lightblue",
    "V": "lightgreen",
    "VI": "orange",
    "VII": "yellow",
    "VIII": "violet",
    "IX": "red"
}

st.set_page_config(layout="wide")
st.title("🚢 Visualisasi Muatan Kapal")

kapal_panjang = st.number_input("Masukkan panjang kapal (meter)", min_value=10, value=50)
kapal_lebar = st.number_input("Masukkan lebar kapal (meter)", min_value=3, value=9)

grid = np.full((kapal_panjang, kapal_lebar), "", dtype=object)

# Fungsi untuk menempatkan kendaraan
def tempatkan_kendaraan(grid, golongan, posisi_awal):
    panjang, lebar = KENDARAAN[golongan]
    x, y = posisi_awal
    if x + panjang > grid.shape[0] or y + lebar > grid.shape[1]:
        return False
    for i in range(panjang):
        for j in range(lebar):
            if grid[x + i, y + j] != "":
                return False
    for i in range(panjang):
        for j in range(lebar):
            grid[x + i, y + j] = golongan
    return True

# Kombinasi optimal kendaraan per jalur
def kombinasi_optimal(panjang):
    dp = [0] * (panjang + 1)
    backtrack = [None] * (panjang + 1)
    for i in range(1, panjang + 1):
        for gol, (pj, _) in KENDARAAN.items():
            if i >= pj and dp[i] < dp[i - pj] + 1:
                dp[i] = dp[i - pj] + 1
                backtrack[i] = gol
    hasil = []
    i = panjang
    while i > 0 and backtrack[i]:
        gol = backtrack[i]
        hasil.append(gol)
        i -= KENDARAAN[gol][0]
    return hasil[::-1]

# Tempatkan kendaraan ke grid per jalur 3 meter
slot_count = kapal_lebar // 3
kendaraan_posisi = []
for s in range(slot_count):
    kolom_awal = s * 3
    kendaraan_di_jalur = kombinasi_optimal(kapal_panjang)
    posisi_x = 0
    for gol in kendaraan_di_jalur:
        if tempatkan_kendaraan(grid, gol, (posisi_x, kolom_awal)):
            kendaraan_posisi.append((gol, posisi_x, kolom_awal))
            posisi_x += KENDARAAN[gol][0]

# Gambar grid visual
fig, ax = plt.subplots(figsize=(kapal_lebar / 1.5, kapal_panjang / 3))
ax.set_xlim(0, kapal_lebar)
ax.set_ylim(0, kapal_panjang)
ax.set_xticks(np.arange(0, kapal_lebar + 1, 1))
ax.set_yticks(np.arange(0, kapal_panjang + 1, 1))
ax.grid(True)
ax.invert_yaxis()
ax.set_title("🧱 Visualisasi Layout Kapal (Tampak Atas)")

# Tambahkan kendaraan ke gambar
for gol, x, y in kendaraan_posisi:
    panjang, lebar = KENDARAAN[gol]
    rect = patches.Rectangle((y, x), lebar, panjang, linewidth=1, edgecolor='black', facecolor=WARNA[gol])
    ax.add_patch(rect)
    ax.text(y + lebar / 2, x + panjang / 2, gol, va='center', ha='center', fontsize=6)

# Tampilkan
st.pyplot(fig)
