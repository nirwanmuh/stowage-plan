import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulasi Muat Kapal", layout="wide")

# Definisi golongan kendaraan
GOLONGAN = {
    4: {"panjang": 2, "lebar": 1, "warna": "green"},
    5: {"panjang": 2, "lebar": 1, "warna": "blue"},
    6: {"panjang": 3, "lebar": 2, "warna": "orange"},
    7: {"panjang": 4, "lebar": 2, "warna": "red"},
    8: {"panjang": 5, "lebar": 2, "warna": "purple"},
    9: {"panjang": 6, "lebar": 2, "warna": "brown"},
}

ROMAWI = {4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX"}

class LantaiKapal:
    def __init__(self, panjang, lebar, nama):
        self.panjang = panjang
        self.lebar = lebar
        self.nama = nama
        self.grid = np.zeros((panjang, lebar), dtype=int)
        self.kendaraan = []  # List of tuples: (golongan, posisi_x, posisi_y, berat)

    def muat(self, golongan, berat):
        k = GOLONGAN[golongan]
        center_x = self.panjang // 2
        center_y = self.lebar // 2
        for dx in range(-center_x, center_x):
            for dy in range(-center_y, center_y):
                i = center_x + dx
                j = center_y + dy
                if i < 0 or j < 0 or i + k["panjang"] > self.panjang or j + k["lebar"] > self.lebar:
                    continue
                if np.all(self.grid[i:i + k["panjang"], j:j + k["lebar"]] == 0):
                    self.grid[i:i + k["panjang"], j:j + k["lebar"]] = golongan
                    self.kendaraan.append((golongan, i, j, berat))
                    return True
        return False

    def sisa_kapasitas(self):
        return np.sum(self.grid == 0)

    def info_kendaraan(self):
        return [(ROMAWI[g], i, j, b) for g, i, j, b in self.kendaraan]

    def total_berat(self):
        return sum(berat for _, _, _, berat in self.kendaraan)

    def momen_horizontal(self):
        return sum((j + GOLONGAN[g]["lebar"] / 2 - self.lebar / 2) * berat for g, _, j, berat in self.kendaraan)

    def momen_vertical(self):
        return sum((i + GOLONGAN[g]["panjang"] / 2 - self.panjang / 2) * berat for g, i, _, berat in self.kendaraan)

class Kapal:
    def __init__(self, lantai_defs):
        self.lantai_list = [LantaiKapal(p, l, f"Lantai {i+1}") for i, (p, l) in enumerate(lantai_defs)]

    def tambah_kendaraan(self, golongan, berat):
        prioritas = list(range(len(self.lantai_list)))
        if golongan >= 6:
            prioritas = [0]  # Golongan besar hanya di lantai bawah
        elif golongan in [4, 5] and len(self.lantai_list) > 1:
            prioritas = list(range(1, len(self.lantai_list))) + [0]  # Prioritas ke atas

        for idx in prioritas:
            if self.lantai_list[idx].muat(golongan, berat):
                return True
        return False

    def sisa_total(self):
        return sum(lantai.sisa_kapasitas() for lantai in self.lantai_list)

    def tampilkan(self):
        cols = st.columns(len(self.lantai_list))
        for i, (lantai, col) in enumerate(zip(self.lantai_list, cols)):
            fig, ax = plt.subplots(figsize=(4, 2))
            ax.imshow(lantai.grid, cmap="gray_r", origin="upper")
            for g, x, y, _ in lantai.kendaraan:
                p = GOLONGAN[g]
                rect = plt.Rectangle((y, x), p["lebar"], p["panjang"], facecolor=p["warna"], edgecolor='black')
                ax.add_patch(rect)
                ax.text(y + 0.5, x + 0.5, ROMAWI[g], color="white", ha="center", va="center", fontsize=8)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(lantai.nama)
            col.pyplot(fig)

    def tampilkan_keseimbangan(self):
        total_momen_h = sum(l.momen_horizontal() for l in self.lantai_list)
        total_momen_v = sum(l.momen_vertical() for l in self.lantai_list)
        total_berat = sum(l.total_berat() for l in self.lantai_list)
        titik_h = total_momen_h / total_berat if total_berat else 0
        titik_v = total_momen_v / total_berat if total_berat else 0
        st.metric("Titik Seimbang Horizontal (kanan = +)", f"{titik_h:.2f}")
        st.metric("Titik Seimbang Vertikal (depan = +)", f"{titik_v:.2f}")

if "lantai_defs" not in st.session_state:
    st.session_state.lantai_defs = [(10, 4)]
    st.session_state.kapal = Kapal(st.session_state.lantai_defs)

with st.sidebar:
    st.title("Konfigurasi Kapal")
    with st.expander("Ubah Dimensi Kapal"):
        jml_lantai = st.number_input("Jumlah Lantai", min_value=1, max_value=3, value=len(st.session_state.lantai_defs))
        new_defs = []
        for i in range(jml_lantai):
            p = st.number_input(f"Panjang Lantai {i+1}", min_value=4, value=st.session_state.lantai_defs[i][0] if i < len(st.session_state.lantai_defs) else 10)
            l = st.number_input(f"Lebar Lantai {i+1}", min_value=2, value=st.session_state.lantai_defs[i][1] if i < len(st.session_state.lantai_defs) else 4)
            new_defs.append((p, l))
        if st.button("Terapkan Dimensi"):
            st.session_state.lantai_defs = new_defs
            st.session_state.kapal = Kapal(new_defs)

    st.markdown("---")
    st.subheader("Tambah Kendaraan")
    golongan_input = st.selectbox("Pilih Golongan", list(ROMAWI.keys()), format_func=lambda x: f"Golongan {ROMAWI[x]}")
    berat_input = st.number_input("Masukkan Berat (kg)", min_value=100, step=100, value=1000)
    if st.button("Tambah"):
        berhasil = st.session_state.kapal.tambah_kendaraan(golongan_input, berat_input)
        if not berhasil:
            st.warning("Kendaraan tidak dapat dimuat.")

    st.markdown("---")
    st.write("**Sisa Slot Kosong:**", st.session_state.kapal.sisa_total())

st.title("Visualisasi Muatan Kapal")
st.session_state.kapal.tampilkan()
st.subheader("Keseimbangan Kapal")
st.session_state.kapal.tampilkan_keseimbangan()
