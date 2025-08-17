import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import math

st.set_page_config(page_title="Stowage Plan", layout="wide")

# ======= Konfigurasi kendaraan (dim dalam m, berat default dalam ton) =======
KENDARAAN = {
    "IV": {"dim": (5.0, 3.0), "berat": 1.0},
    "V": {"dim": (7.0, 3.0), "berat": 2.0},
    "VI": {"dim": (12.0, 3.5), "berat": 5.0},
    "VII": {"dim": (18.0, 3.5), "berat": 8.0},
    "VIII": {"dim": (20.0, 3.5), "berat": 12.0},
    "IX": {"dim": (25.0, 4.0), "berat": 20.0},
}
ROMAWI = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
WARNA = {
    "IV": "tab:blue", "V": "tab:orange", "VI": "tab:green",
    "VII": "tab:red", "VIII": "tab:purple", "IX": "tab:brown"
}

# ======= Kelas LantaiKapal dan Kapal =======
class LantaiKapal:
    def __init__(self, panjang, lebar, nama):
        self.panjang = panjang
        self.lebar = lebar
        self.nama = nama
        self.kendaraan = []

    def reset(self):
        self.kendaraan = []

    def tambah(self, kendaraan):
        self.kendaraan.append(kendaraan)


class Kapal:
    def __init__(self, lantai_list):
        self.lantai = lantai_list

    def reset(self):
        for l in self.lantai:
            l.reset()

    def semua_kendaraan(self):
        data = []
        for l in self.lantai:
            for k in l.kendaraan:
                data.append((l, k))
        return data

    def titik_berat(self):
        total_berat = 0
        sum_x = sum_y = 0
        for l in self.lantai:
            for k in l.kendaraan:
                x, y, w, h, berat, _ = k
                cx = x + w / 2
                cy = y + h / 2
                sum_x += cx * berat
                sum_y += cy * berat
                total_berat += berat
        if total_berat == 0:
            return (0, 0)
        return (sum_x / total_berat, sum_y / total_berat)

    def seimbang_horizontal(self):
        """Cek apakah titik berat horizontal sudah dekat ke tengah"""
        cx, cy = self.titik_berat()
        tengah = self.lantai[0].lebar / 2
        return abs(cx - tengah) < 0.5  # toleransi 0.5m


# ======= Algoritma penempatan =======
def optimasi_penempatan(kapal, daftar_kendaraan):
    kapal.reset()
    mid_x = kapal.lantai[0].lebar / 2

    for kendaraan in daftar_kendaraan:
        gol, berat = kendaraan
        dim_x, dim_y = KENDARAAN[gol]["dim"]

        ditempatkan = False

        # coba semua lantai
        for lantai in kapal.lantai:
            # arahkan penempatan dimulai dari tengah
            posisi_x = mid_x - dim_y/2
            step = dim_y
            posisi_list = []

            # jika horizontal sudah seimbang, utamakan belakang
            if kapal.seimbang_horizontal():
                posisi_list = [(x, lantai.panjang - dim_x) for x in [posisi_x]]
            else:
                # normal: isi dari tengah ke depan & belakang
                posisi_list = [
                    (posisi_x, 0),
                    (posisi_x, lantai.panjang - dim_x)
                ]

            for (x, y) in posisi_list:
                if x >= 0 and x + dim_y <= lantai.lebar and y >= 0 and y + dim_x <= lantai.panjang:
                    lantai.tambah((x, y, dim_y, dim_x, berat, gol))
                    ditempatkan = True
                    break
            if ditempatkan:
                break


# ======= Streamlit UI =======
st.sidebar.title("Konfigurasi Kapal")

# input lantai
jumlah_lantai = st.sidebar.number_input("Jumlah Lantai", 1, 3, 1)
lantai_list = []
for i in range(jumlah_lantai):
    panjang = st.sidebar.number_input(f"Panjang Lantai {ROMAWI[i]} (m)", 20, 200, 60)
    lebar = st.sidebar.number_input(f"Lebar Lantai {ROMAWI[i]} (m)", 10, 30, 20)
    lantai_list.append(LantaiKapal(panjang, lebar, ROMAWI[i]))

kapal = Kapal(lantai_list)

# state kendaraan
if "daftar_kendaraan" not in st.session_state:
    st.session_state.daftar_kendaraan = []

# tambah kendaraan
st.sidebar.subheader("Tambah Kendaraan")
golongan = st.sidebar.selectbox("Golongan", list(KENDARAAN.keys()))
berat_manual = st.sidebar.number_input("Berat (ton)", 1.0, 50.0, KENDARAAN[golongan]["berat"])
if st.sidebar.button("Tambah"):
    st.session_state.daftar_kendaraan.append((golongan, berat_manual))

# keluar kendaraan
st.sidebar.subheader("Keluarkan Kendaraan")
if st.session_state.daftar_kendaraan:
    idx = st.sidebar.number_input("Index kendaraan keluar", 1, len(st.session_state.daftar_kendaraan))
    if st.sidebar.button("Keluarkan"):
        st.session_state.daftar_kendaraan.pop(idx - 1)

# optimasi ulang
optimasi_penempatan(kapal, st.session_state.daftar_kendaraan)

# ======= Visualisasi =======
fig, axes = plt.subplots(1, len(kapal.lantai), figsize=(12, 6))
if len(kapal.lantai) == 1:
    axes = [axes]

for ax, lantai in zip(axes, kapal.lantai):
    ax.set_title(f"Lantai {lantai.nama}")
    ax.set_xlim(0, lantai.lebar)
    ax.set_ylim(0, lantai.panjang)
    ax.set_aspect('equal')
    ax.invert_yaxis()

    # tanda depan-belakang
    ax.text(lantai.lebar/2, 1, "Depan", ha="center", va="bottom", fontsize=8)
    ax.text(lantai.lebar/2, lantai.panjang-1, "Belakang", ha="center", va="top", fontsize=8)

    for x, y, w, h, berat, gol in lantai.kendaraan:
        rect = Rectangle((x, y), w, h, facecolor=WARNA[gol], edgecolor="black")
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, f"{gol}\n{berat}t", ha="center", va="center", fontsize=6, color="white")

# titik berat
cx, cy = kapal.titik_berat()
for ax in axes:
    ax.plot(cx, cy, "rx", markersize=10)

st.pyplot(fig)

# info keseimbangan
cx, cy = kapal.titik_berat()
tengah_x = kapal.lantai[0].lebar / 2
tengah_y = kapal.lantai[0].panjang / 2
st.sidebar.subheader("Info Keseimbangan")
st.sidebar.write(f"Titik berat (x,y): ({cx:.2f}, {cy:.2f})")
st.sidebar.write(f"Tengah kapal: ({tengah_x:.2f}, {tengah_y:.2f})")
if kapal.seimbang_horizontal():
    st.sidebar.success("Seimbang horizontal ✅")
else:
    st.sidebar.warning("Belum seimbang horizontal ⚠️")
