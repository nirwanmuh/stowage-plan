import streamlit as st
import matplotlib.pyplot as plt
import random
import math

# Data golongan kendaraan (panjang, lebar, berat)
golongan_data = {
    "IV":  (5.0, 3.0, 1.0),
    "V":   (7.0, 3.0, 8.0),
    "VI":  (10.0, 3.0, 12.0),
    "VII": (12.0, 3.0, 15.0),
    "VIII":(16.0, 3.0, 18.0),
    "IX":  (21.0, 3.0, 30.0)
}

# List kendaraan terpasang: (golongan, x, y)
kendaraan_list = []

# Hitung titik berat muatan
def hitung_titik_berat(vehicles):
    if not vehicles:
        return 0.0, 0.0
    total_w = sum(golongan_data[v[0]][2] for v in vehicles)
    cx = sum((v[1] + golongan_data[v[0]][0] / 2) * golongan_data[v[0]][2] for v in vehicles) / total_w
    cy = sum((v[2] + golongan_data[v[0]][1] / 2) * golongan_data[v[0]][2] for v in vehicles) / total_w
    return cx, cy

# Cek apakah posisi muat valid
def valid_posisi(new_vehicle, vehicles, panjang_kapal, lebar_kapal):
    gol, x, y = new_vehicle
    p, l, _ = golongan_data[gol]
    if x < 0 or y < 0 or x + p > panjang_kapal or y + l > lebar_kapal:
        return False
    for v in vehicles:
        vp, vl, _ = golongan_data[v[0]]
        if not (x + p <= v[1] or v[1] + vp <= x or y + l <= v[2] or v[2] + vl <= y):
            return False
    return True

# Optimisasi lokal
def local_improve(vehicles, panjang_kapal, lebar_kapal, x_target, y_target,
                  max_iter=400, shift_step=0.2, max_shift=3.0, swap_tries=300):
    if len(vehicles) < 2:
        return vehicles  # Tidak bisa swap kalau kendaraan < 2

    best = vehicles[:]
    best_cost = jarak_cost(best, x_target, y_target)

    for _ in range(max_iter):
        # coba geser kendaraan
        idx = random.randint(0, len(best) - 1)
        for dx in [-shift_step, shift_step]:
            for dy in [-shift_step, shift_step]:
                moved = best[:]
                gol, x, y = moved[idx]
                nx, ny = x + dx, y + dy
                moved[idx] = (gol, nx, ny)
                if valid_posisi(moved[idx], moved[:idx] + moved[idx+1:], panjang_kapal, lebar_kapal):
                    cost = jarak_cost(moved, x_target, y_target)
                    if cost < best_cost:
                        best, best_cost = moved, cost

        # coba swap posisi
        if len(best) >= 2:
            for _ in range(swap_tries):
                i, j = random.sample(range(len(best)), 2)
                swapped = best[:]
                vi, vj = swapped[i], swapped[j]
                swapped[i] = (vi[0], vj[1], vj[2])
                swapped[j] = (vj[0], vi[1], vi[2])
                if valid_posisi(swapped[i], swapped[:i] + swapped[i+1:], panjang_kapal, lebar_kapal) \
                   and valid_posisi(swapped[j], swapped[:j] + swapped[j+1:], panjang_kapal, lebar_kapal):
                    cost = jarak_cost(swapped, x_target, y_target)
                    if cost < best_cost:
                        best, best_cost = swapped, cost

    return best

# Fungsi biaya jarak titik berat
def jarak_cost(vehicles, x_target, y_target):
    cx, cy = hitung_titik_berat(vehicles)
    return (cx - x_target)**2 + (cy - y_target)**2

# Cari susunan optimal
def arrange_with_optimization(vehicles, panjang_kapal, lebar_kapal, y_target, x_target):
    if not vehicles:
        return []
    init = []
    for v in vehicles:
        placed = False
        for _ in range(500):  # coba random placement awal
            x = random.uniform(0, panjang_kapal - golongan_data[v[0]][0])
            y = random.uniform(0, lebar_kapal - golongan_data[v[0]][1])
            if valid_posisi((v[0], x, y), init, panjang_kapal, lebar_kapal):
                init.append((v[0], x, y))
                placed = True
                break
        if not placed:
            return None
    return local_improve(init, panjang_kapal, lebar_kapal, x_target, y_target)

# Coba tambah kendaraan baru
def try_add_vehicle(gol):
    global kendaraan_list
    candidate_list = [(v[0], 0, 0) for v in kendaraan_list] + [(gol, 0, 0)]
    hasil = arrange_with_optimization(candidate_list, panjang_kapal, lebar_kapal,
                                      titik_seimbang_vertikal, titik_seimbang_horizontal)
    if hasil is None:
        st.error(f"Tidak bisa menambahkan golongan {gol} lagi")
    else:
        kendaraan_list = hasil

# ================= UI =================
st.sidebar.header("Kapal & Titik Seimbang")
panjang_kapal = st.sidebar.number_input("Panjang Kapal (m)", min_value=10.0, value=50.0, step=0.1)
lebar_kapal = st.sidebar.number_input("Lebar Kapal (m)", min_value=5.0, value=15.0, step=0.1)
titik_seimbang_vertikal = st.sidebar.number_input("Titik Seimbang Vertikal (m)", min_value=0.0, value=25.0, step=0.1)
titik_seimbang_horizontal = lebar_kapal / 2

pilih_gol = st.selectbox("Pilih Golongan Kendaraan", list(golongan_data.keys()))
if st.button("Tambah Kendaraan"):
    try_add_vehicle(pilih_gol)

# Visualisasi
fig, ax = plt.subplots()
ax.set_xlim(0, panjang_kapal)
ax.set_ylim(0, lebar_kapal)
ax.set_aspect('equal')
ax.plot(titik_seimbang_vertikal, titik_seimbang_horizontal, 'rx', label="Titik Seimbang Kapal")

for v in kendaraan_list:
    p, l, _ = golongan_data[v[0]]
    rect = plt.Rectangle((v[1], v[2]), p, l, fill=None, edgecolor='blue')
    ax.add_patch(rect)
    ax.text(v[1] + p/2, v[2] + l/2, v[0], ha='center', va='center', fontsize=8)

cx, cy = hitung_titik_berat(kendaraan_list)
ax.plot(cx, cy, 'go', label="Titik Berat Muatan")

ax.legend()
st.pyplot(fig)
