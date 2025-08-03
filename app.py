import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

ROMAWI = {4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX"}
KENDARAAN = {
    4: {"panjang": 2, "lebar": 3, "berat": 2},
    5: {"panjang": 2, "lebar": 3, "berat": 3},
    6: {"panjang": 3, "lebar": 3, "berat": 5},
    7: {"panjang": 3, "lebar": 3, "berat": 6},
    8: {"panjang": 4, "lebar": 3, "berat": 8},
    9: {"panjang": 5, "lebar": 3, "berat": 10},
}

class Lantai:
    def __init__(self, panjang, lebar):
        self.panjang = panjang
        self.lebar = lebar
        self.grid = np.zeros((panjang, lebar))
        self.kendaraan = []  # List of dict: golongan, posisi

    def reset(self):
        self.grid[:, :] = 0
        self.kendaraan = []

    def muat(self, golongan):
        k = KENDARAAN[golongan]
        for i in range(self.panjang - k["panjang"] + 1):
            for j in range(self.lebar - k["lebar"] + 1):
                if np.all(self.grid[i:i + k["panjang"], j:j + k["lebar"]] == 0):
                    self.grid[i:i + k["panjang"], j:j + k["lebar"]] = golongan
                    self.kendaraan.append({"golongan": golongan, "x": i, "y": j})
                    return True
        return False

    def total_berat(self):
        return sum(KENDARAAN[k["golongan"]]["berat"] for k in self.kendaraan)

    def pusat_berat(self):
        total = self.total_berat()
        if total == 0:
            return (self.panjang / 2, self.lebar / 2)
        x = sum((k["x"] + KENDARAAN[k["golongan"]]["panjang"] / 2) * KENDARAAN[k["golongan"]]["berat"] for k in self.kendaraan) / total
        y = sum((k["y"] + KENDARAAN[k["golongan"]]["lebar"] / 2) * KENDARAAN[k["golongan"]]["berat"] for k in self.kendaraan) / total
        return (x, y)

    def visualisasi(self, index):
        fig, ax = plt.subplots()
        ax.imshow(self.grid, cmap="tab20")
        for k in self.kendaraan:
            ax.text(k["y"] + 0.5, k["x"] + 0.5, ROMAWI[k["golongan"]], ha='center', va='center', color='black')
        ax.set_title(f"Lantai {index + 1}")
        st.pyplot(fig)

class Kapal:
    def __init__(self, lantai_defs):
        self.lantai_list = [Lantai(p, l) for p, l in lantai_defs]
        self.kendaraan_terdaftar = []

    def reset(self):
        for lantai in self.lantai_list:
            lantai.reset()
        self.kendaraan_terdaftar = []

    def tambah_kendaraan(self, golongan):
        self.kendaraan_terdaftar.append(golongan)
        self.reoptimalkan()
        return f"Kendaraan golongan {ROMAWI[golongan]} ditambahkan dan diatur ulang."

    def keluarkan_kendaraan(self, golongan):
        if golongan in self.kendaraan_terdaftar:
            self.kendaraan_terdaftar.remove(golongan)
            self.reoptimalkan()
            return True, f"Kendaraan golongan {ROMAWI[golongan]} dikeluarkan."
        return False, "Kendaraan tidak ditemukan."

    def reoptimalkan(self):
        for lantai in self.lantai_list:
            lantai.reset()

        kendaraan_sisa = []
        kendaraan_urut = sorted(self.kendaraan_terdaftar, key=lambda x: -x)

        for gol in kendaraan_urut:
            ditempatkan = False
            for idx, lantai in enumerate(self.lantai_list):
                if gol >= 6 and idx > 0:
                    continue
                if gol in [4, 5] and idx == 0 and any(l.muat(gol) for l in self.lantai_list[1:]):
                    continue
                if lantai.muat(gol):
                    ditempatkan = True
                    break
            if not ditempatkan:
                kendaraan_sisa.append(gol)

        self.kendaraan_terdaftar = [k for k in self.kendaraan_terdaftar if k not in kendaraan_sisa]

    def visualisasi(self):
        st.subheader("Visualisasi Kapal")
        col = st.columns(len(self.lantai_list))
        for i, lantai in enumerate(self.lantai_list):
            with col[i]:
                lantai.visualisasi(i)

        berat_total = sum(l.total_berat() for l in self.lantai_list)
        if berat_total > 0:
            x_all = sum(l.pusat_berat()[0] * l.total_berat() for l in self.lantai_list) / berat_total
            y_all = sum(l.pusat_berat()[1] * l.total_berat() for l in self.lantai_list) / berat_total
            st.markdown(f"**Titik Berat Horizontal:** {y_all:.2f} (dari lebar tengah {self.lantai_list[0].lebar/2})")
            st.markdown(f"**Titik Berat Vertikal:** {x_all:.2f} (dari panjang tengah {self.lantai_list[0].panjang/2})")
        else:
            st.info("Belum ada kendaraan dimuat.")

# Sidebar
st.sidebar.header("Definisi Lantai Kapal")
if "lantai_defs" not in st.session_state:
    st.session_state.lantai_defs = []

p = st.sidebar.number_input("Panjang Lantai", 5, 100, 20)
l = st.sidebar.number_input("Lebar Lantai", 3, 30, 9, step=3)
if st.sidebar.button("Tambah Lantai"):
    st.session_state.lantai_defs.append((p, l))
    st.session_state.kapal = Kapal(st.session_state.lantai_defs)

if st.sidebar.button("Reset Kapal"):
    st.session_state.lantai_defs = []
    st.session_state.kapal = None
    st.experimental_rerun()

# Inisialisasi kapal
if st.session_state.lantai_defs and "kapal" not in st.session_state:
    st.session_state.kapal = Kapal(st.session_state.lantai_defs)

if "kapal" in st.session_state:
    st.subheader("Tambah Kendaraan")
    pilih = st.selectbox("Pilih Golongan", options=[4, 5, 6, 7, 8, 9], format_func=lambda x: f"Golongan {ROMAWI[x]}")
    if st.button("Masukkan Kendaraan"):
        st.success(st.session_state.kapal.tambah_kendaraan(pilih))

    st.subheader("Keluarkan Kendaraan")
    if st.button("Keluarkan Kendaraan"):
        ok, pesan = st.session_state.kapal.keluarkan_kendaraan(pilih)
        if ok:
            st.success(pesan)
        else:
            st.warning(pesan)

    st.session_state.kapal.visualisasi()
else:
    st.warning("Silakan tambahkan lantai terlebih dahulu.")
