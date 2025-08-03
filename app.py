import streamlit as st
import numpy as np

st.set_page_config(page_title="Simulasi Pemuatan Kapal", layout="wide")

# Sidebar input konfigurasi kapal
st.sidebar.header("Konfigurasi Kapal")
if "konfigurasi_done" not in st.session_state:
    st.session_state.kendaraan_list = []
    st.session_state.konfigurasi_done = False
    st.session_state.grid_kapal = []

lantai_count = st.sidebar.number_input("Jumlah Lantai", min_value=1, max_value=3, value=1)
lantai_defs = []
for i in range(lantai_count):
    st.sidebar.markdown(f"**Lantai {i+1}**")
    panjang = st.sidebar.number_input(f"Panjang Lantai {i+1} (grid)", min_value=5, value=10, key=f"p{i}_panjang")
    lebar = st.sidebar.number_input(f"Lebar Lantai {i+1} (grid)", min_value=2, value=5, key=f"p{i}_lebar")
    lantai_defs.append((panjang, lebar))

if st.sidebar.button("Set Konfigurasi") or not st.session_state.konfigurasi_done:
    st.session_state.grid_kapal = [np.zeros((p, l), dtype=int) for p, l in lantai_defs]
    st.session_state.kendaraan_list = []
    st.session_state.konfigurasi_done = True

# Sidebar input kendaraan
st.sidebar.header("Input Kendaraan")
golongan_map = {
    "IV": (2, 1, 4000),
    "V": (2, 2, 5000),
    "VI": (3, 2, 7000),
    "VII": (3, 3, 9000),
    "VIII": (4, 3, 12000),
    "IX": (4, 4, 15000)
}
golongan_input = st.sidebar.selectbox("Golongan Kendaraan", list(golongan_map.keys()))

if st.sidebar.button("Tambah Kendaraan"):
    panjang, lebar, berat = golongan_map[golongan_input]
    kapal_lantai = st.session_state.grid_kapal

    # Cari posisi mulai dari tengah lantai
    for lantai_idx, grid in enumerate(kapal_lantai):
        g_p, g_l = grid.shape
        mid_x, mid_y = g_p // 2, g_l // 2

        found = False
        for i in range(mid_x - g_p//2, mid_x + g_p//2):
            for j in range(mid_y - g_l//2, mid_y + g_l//2):
                if i < 0 or j < 0 or i+panjang > g_p or j+lebar > g_l:
                    continue
                if np.all(grid[i:i+panjang, j:j+lebar] == 0):
                    grid[i:i+panjang, j:j+lebar] = len(st.session_state.kendaraan_list) + 1
                    st.session_state.kendaraan_list.append({
                        "lantai": lantai_idx,
                        "x": i,
                        "y": j,
                        "panjang": panjang,
                        "lebar": lebar,
                        "berat": berat
                    })
                    found = True
                    break
            if found:
                break

# Visualisasi lantai
st.title("Visualisasi Pemuatan Kapal")
for idx, grid in enumerate(st.session_state.grid_kapal):
    st.markdown(f"### Lantai {idx+1}")
    grid_display = ""
    for row in grid:
        grid_display += "".join([f"[{int(val):02}]" if val > 0 else "[  ]" for val in row]) + "\n"
    st.text(grid_display)

# Hitung keseimbangan
st.sidebar.header("Informasi Keseimbangan")
total_berat = 0
sum_x = 0
sum_y = 0
for k in st.session_state.kendaraan_list:
    grid_p, grid_l = lantai_defs[k["lantai"]]
    x_tengah = k["x"] + k["panjang"] / 2
    y_tengah = k["y"] + k["lebar"] / 2
    total_berat += k["berat"]
    sum_x += k["berat"] * x_tengah
    sum_y += k["berat"] * y_tengah

if total_berat > 0:
    center_x = sum_x / total_berat
    center_y = sum_y / total_berat
else:
    center_x, center_y = 0, 0

ideal_x = np.mean([p / 2 for p, _ in lantai_defs])
ideal_y = np.mean([l / 2 for _, l in lantai_defs])

st.sidebar.markdown(f"**Titik Berat Aktual**: ({center_x:.2f}, {center_y:.2f})")
st.sidebar.markdown(f"**Titik Ideal**: ({ideal_x:.2f}, {ideal_y:.2f})")
st.sidebar.markdown(f"**Deviasi Horizontal**: {center_x - ideal_x:.2f}")
st.sidebar.markdown(f"**Deviasi Vertikal**: {center_y - ideal_y:.2f}")

# Informasi kendaraan
st.sidebar.header("Daftar Kendaraan")
for idx, k in enumerate(st.session_state.kendaraan_list):
    st.sidebar.markdown(f"{idx+1}. Gol {k['panjang']}x{k['lebar']} Berat: {k['berat']} kg (Lantai {k['lantai']+1})")
