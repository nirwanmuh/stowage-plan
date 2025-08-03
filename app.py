import streamlit as st
import numpy as np
import random

st.set_page_config(page_title="Simulasi Muatan Kapal", layout="wide")

# Data kendaraan
KENDARAAN = {
    4: {"panjang": 6, "lebar": 3, "berat": 4000},
    5: {"panjang": 7, "lebar": 3, "berat": 5000},
    6: {"panjang": 9, "lebar": 3, "berat": 7000},
    7: {"panjang": 12, "lebar": 3, "berat": 10000},
    8: {"panjang": 15, "lebar": 3, "berat": 13000},
    9: {"panjang": 18, "lebar": 3, "berat": 15000},
}

ROMAWI = {4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX"}
WARNA = {4: "lightblue", 5: "lightskyblue", 6: "orange", 7: "tomato", 8: "salmon", 9: "red"}

class LantaiKapal:
    def __init__(self, panjang, lebar):
        self.panjang = panjang
        self.lebar = lebar
        self.grid = np.zeros((panjang, lebar), dtype=int)
        self.kendaraan = []

    def muat(self, golongan, prioritaskan=True):
        k = KENDARAAN[golongan]
        for i in range(self.panjang - k["panjang"] + 1):
            for j in range(self.lebar - k["lebar"] + 1):
                if np.all(self.grid[i:i + k["panjang"], j:j + k["lebar"]] == 0):
                    self.grid[i:i + k["panjang"], j:j + k["lebar"]] = golongan
                    self.kendaraan.append((golongan, i, j))
                    return True
        return False

    def keluarkan(self, golongan):
        for idx, (g, i, j) in enumerate(self.kendaraan):
            if g == golongan:
                k = KENDARAAN[g]
                self.grid[i:i + k["panjang"], j:j + k["lebar"]] = 0
                self.kendaraan.pop(idx)
                return True
        return False

    def get_kemungkinan_sisa(self):
        count = {}
        kosong = np.argwhere(self.grid == 0)
        for gol in KENDARAAN:
            k = KENDARAAN[gol]
            cocok = 0
            for i in range(self.panjang - k["panjang"] + 1):
                for j in range(self.lebar - k["lebar"] + 1):
                    if np.all(self.grid[i:i + k["panjang"], j:j + k["lebar"]] == 0):
                        cocok += 1
            count[gol] = cocok
        return count

    def total_berat_dan_titik(self):
        total_berat = 0
        titik_x = 0
        titik_y = 0
        for g, i, j in self.kendaraan:
            k = KENDARAAN[g]
            berat = k["berat"]
            total_berat += berat
            titik_x += berat * (i + k["panjang"] / 2)
            titik_y += berat * (j + k["lebar"] / 2)
        if total_berat == 0:
            return 0, 0, 0
        return total_berat, titik_x / total_berat, titik_y / total_berat

class Kapal:
    def __init__(self, lantai_defs):
        self.lantai_list = [LantaiKapal(p, l) for p, l in lantai_defs]

    def tambah_kendaraan(self, golongan):
        kendaraan = KENDARAAN[golongan]
        prioritas = list(range(1, len(self.lantai_list))) + [0] if golongan in [4, 5] else [0]
        for idx in prioritas:
            if self.lantai_list[idx].muat(golongan):
                self.reoptimalkan()
                return f"Kendaraan golongan {ROMAWI[golongan]} dimuat di lantai {idx+1}"
        return f"Kendaraan golongan {ROMAWI[golongan]} tidak muat"

    def keluarkan_kendaraan(self, golongan):
        for lantai in self.lantai_list:
            if lantai.keluarkan(golongan):
                self.reoptimalkan()
                return True, f"Kendaraan golongan {ROMAWI[golongan]} dikeluarkan"
        return False, f"Tidak ada kendaraan golongan {ROMAWI[golongan]}"

    def reoptimalkan(self):
        semua_kendaraan = []
        for lantai in self.lantai_list:
            semua_kendaraan += lantai.kendaraan[:]
            lantai.grid[:, :] = 0
            lantai.kendaraan.clear()
        for g, _, _ in semua_kendaraan:
            self.tambah_kendaraan(g)

    def visualisasi(self):
        col_kapal = st.columns(len(self.lantai_list))
        for idx, lantai in enumerate(self.lantai_list):
            with col_kapal[idx]:
                st.markdown(f"**Lantai {idx+1}**")
                grid = lantai.grid
                for i in range(grid.shape[0]):
                    row = ""
                    for j in range(grid.shape[1]):
                        g = grid[i, j]
                        color = WARNA.get(g, "white")
                        label = ROMAWI.get(g, "")
                        row += f"<div style='width:30px;height:30px;background:{color};display:inline-block;border:1px solid gray;text-align:center;font-size:12px'>{label}</div>"
                    st.markdown(row, unsafe_allow_html=True)
                berat, x, y = lantai.total_berat_dan_titik()
                tengah_x = lantai.panjang / 2
                tengah_y = lantai.lebar / 2
                st.caption(f"Berat total: {berat} kg")
                st.caption(f"Titik berat (x={x:.1f}, y={y:.1f})")
                st.caption(f"Selisih dari tengah → dx={abs(x - tengah_x):.1f}, dy={abs(y - tengah_y):.1f}")

# Sidebar input
st.sidebar.title("Input Kapal & Kendaraan")

if "kapal_initiated" not in st.session_state:
    st.session_state.lantai_defs = []
    st.session_state.kapal_initiated = False

lantai_count = st.sidebar.number_input("Jumlah lantai kapal", min_value=1, max_value=5, value=2, step=1)
for i in range(lantai_count):
    panjang = st.sidebar.number_input(f"Panjang lantai {i+1}", min_value=5, max_value=100, value=30, step=1, key=f"p_{i}")
    lebar = st.sidebar.number_input(f"Lebar lantai {i+1}", min_value=3, max_value=30, value=9, step=3, key=f"l_{i}")
    if i >= len(st.session_state.lantai_defs):
        st.session_state.lantai_defs.append((panjang, lebar))
    else:
        st.session_state.lantai_defs[i] = (panjang, lebar)

if st.sidebar.button("Inisialisasi Kapal"):
    st.session_state.kapal = Kapal(st.session_state.lantai_defs)
    st.session_state.kapal_initiated = True
    st.success("Kapal berhasil diinisialisasi ulang!")

if st.session_state.kapal_initiated:
    golongan_input = st.sidebar.selectbox("Pilih Golongan Kendaraan", options=list(ROMAWI.keys()), format_func=lambda x: f"Golongan {ROMAWI[x]}")
    if st.sidebar.button("Tambahkan Kendaraan"):
        hasil = st.session_state.kapal.tambah_kendaraan(golongan_input)
        st.sidebar.success(hasil)

    if st.sidebar.button("Keluarkan Kendaraan"):
        ok, pesan = st.session_state.kapal.keluarkan_kendaraan(golongan_input)
        if ok:
            st.sidebar.success(pesan)
        else:
            st.sidebar.warning(pesan)

    st.sidebar.divider()
    with st.sidebar.expander("Sisa Kapasitas Tiap Lantai"):
        for i, lantai in enumerate(st.session_state.kapal.lantai_list):
            sisa = lantai.get_kemungkinan_sisa()
            st.write(f"Lantai {i+1}:")
            for gol, jum in sisa.items():
                st.write(f" - Golongan {ROMAWI[gol]}: {jum} kendaraan")

    st.session_state.kapal.visualisasi()
else:
    st.warning("Silakan inisialisasi kapal terlebih dahulu di sidebar.")
