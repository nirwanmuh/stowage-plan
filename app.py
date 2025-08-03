import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# ----------------------------
# Konfigurasi Golongan Kendaraan
# ----------------------------
GOLONGAN = {
    "IV": {"panjang": 2, "lebar": 1, "berat": 3},
    "V": {"panjang": 2, "lebar": 2, "berat": 4},
    "VI": {"panjang": 3, "lebar": 2, "berat": 5},
    "VII": {"panjang": 4, "lebar": 2, "berat": 6},
    "VIII": {"panjang": 5, "lebar": 2, "berat": 8},
    "IX": {"panjang": 6, "lebar": 3, "berat": 10},
}

# ----------------------------
# Kelas Lantai dan Kapal
# ----------------------------
class Lantai:
    def __init__(self, panjang, lebar, nama):
        self.panjang = panjang
        self.lebar = lebar
        self.grid = np.zeros((panjang, lebar), dtype=int)
        self.nama = nama
        self.kendaraan = []

    def muat(self, golongan):
        k = GOLONGAN[golongan]
        center_i = self.panjang // 2
        center_j = self.lebar // 2

        posisi_diperiksa = []
        for di in range(self.panjang):
            for dj in range(self.lebar):
                i = center_i + (-1)**(di % 2) * (di // 2)
                j = center_j + (-1)**(dj % 2) * (dj // 2)
                if 0 <= i <= self.panjang - k["panjang"] and 0 <= j <= self.lebar - k["lebar"]:
                    posisi_diperiksa.append((i, j))

        for i, j in posisi_diperiksa:
            if np.all(self.grid[i:i + k["panjang"], j:j + k["lebar"]] == 0):
                self.grid[i:i + k["panjang"], j:j + k["lebar"]] = len(self.kendaraan) + 1
                self.kendaraan.append((golongan, i, j))
                return True
        return False

    def total_berat(self):
        return sum(GOLONGAN[k][“berat”] for k, _, _ in self.kendaraan)

    def hapus_semua(self):
        self.grid[:, :] = 0
        self.kendaraan = []

class Kapal:
    def __init__(self, lantai_defs):
        self.lantai_list = [Lantai(**d, nama=f"Lantai {i+1}") for i, d in enumerate(lantai_defs)]
        self.riwayat_kendaraan = []

    def tambah_kendaraan(self, golongan):
        # Reset semua
        self.riwayat_kendaraan.append(golongan)
        self.reoptimalkan()

    def reoptimalkan(self):
        for lantai in self.lantai_list:
            lantai.hapus_semua()

        for golongan in self.riwayat_kendaraan:
            if golongan in ("VI", "VII", "VIII", "IX"):
                idx = 0  # Lantai bawah
                self.lantai_list[idx].muat(golongan)
            else:
                # Golongan IV dan V
                ditempatkan = False
                for idx in range(1, len(self.lantai_list)):
                    if self.lantai_list[idx].muat(golongan):
                        ditempatkan = True
                        break
                if not ditempatkan:
                    self.lantai_list[0].muat(golongan)

    def keluarkan_terakhir(self):
        if self.riwayat_kendaraan:
            self.riwayat_kendaraan.pop()
            self.reoptimalkan()

    def info_kapasitas(self):
        total = sum(l.panjang * l.lebar for l in self.lantai_list)
        terpakai = sum(len(l.kendaraan) for l in self.lantai_list)
        return f"{terpakai} slot terpakai dari {total} slot"

# ----------------------------
# Streamlit Sidebar
# ----------------------------
if "lantai_defs" not in st.session_state:
    st.session_state.lantai_defs = []

st.sidebar.header("Konfigurasi Kapal")
with st.sidebar.expander("🛠️ Tambah Lantai"):
    panjang = st.number_input("Panjang (grid)", 5, 50, 10)
    lebar = st.number_input("Lebar (grid)", 2, 10, 4)
    if st.button("Tambah Lantai"):
        st.session_state.lantai_defs.append({"panjang": panjang, "lebar": lebar})

if st.sidebar.button("Reset Kapal"):
    st.session_state.lantai_defs = []
    st.session_state.kapal = None

# ----------------------------
# Inisialisasi Kapal
# ----------------------------
if st.session_state.lantai_defs:
    if "kapal" not in st.session_state or st.session_state.kapal is None:
        st.session_state.kapal = Kapal(st.session_state.lantai_defs)

    kapal: Kapal = st.session_state.kapal

    st.sidebar.markdown("---")
    st.sidebar.subheader("Tambah Kendaraan")
    golongan_input = st.sidebar.selectbox("Pilih Golongan", list(GOLONGAN.keys()))
    if st.sidebar.button("Tambah Kendaraan"):
        kapal.tambah_kendaraan(golongan_input)

    if st.sidebar.button("Keluarkan Terakhir"):
        kapal.keluarkan_terakhir()

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**{kapal.info_kapasitas()}**")

# ----------------------------
# Visualisasi Kapal
# ----------------------------
if st.session_state.lantai_defs:
    st.title("🚢 Visualisasi Muatan Kapal")
    col_viz = st.columns(len(kapal.lantai_list))

    for col, lantai in zip(col_viz, kapal.lantai_list):
        fig, ax = plt.subplots()
        ax.imshow(lantai.grid, cmap='tab20', origin='upper')
        ax.set_title(f"{lantai.nama}")
        ax.set_xticks([])
        ax.set_yticks([])
        col.pyplot(fig)
