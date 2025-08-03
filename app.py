import streamlit as st
import numpy as np

# Warna untuk setiap golongan
WARNA = {
    4: "#1f77b4",
    5: "#ff7f0e",
    6: "#2ca02c",
    7: "#d62728",
    8: "#9467bd",
    9: "#8c564b"
}

ROMAWI = {
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX"
}

# Data kendaraan per golongan: panjang, lebar, berat
KENDARAAN = {
    4: (6, 2, 2),
    5: (7, 2, 3),
    6: (10, 3, 5),
    7: (12, 3, 7),
    8: (14, 3, 10),
    9: (16, 3, 13)
}

def label_romawi(val):
    return f"Golongan {ROMAWI[val]}"

class LantaiKapal:
    def __init__(self, panjang, lebar):
        self.panjang = panjang
        self.lebar = lebar
        self.grid = [[None for _ in range(panjang)] for _ in range(lebar)]

    def bisa_ditempatkan(self, pjg, lbr, baris, kolom):
        if baris + lbr > self.lebar or kolom + pjg > self.panjang:
            return False
        for i in range(baris, baris + lbr):
            for j in range(kolom, kolom + pjg):
                if self.grid[i][j] is not None:
                    return False
        return True

    def tempatkan(self, golongan, baris, kolom):
        pjg, lbr, _ = KENDARAAN[golongan]
        for i in range(baris, baris + lbr):
            for j in range(kolom, kolom + pjg):
                self.grid[i][j] = f"G{golongan}"

    def hapus(self, baris, kolom):
        nilai = self.grid[baris][kolom]
        if nilai is None:
            return False, "Slot kosong"
        for i in range(self.lebar):
            for j in range(self.panjang):
                if self.grid[i][j] == nilai:
                    self.grid[i][j] = None
        return True, f"Kendaraan golongan {ROMAWI[int(nilai[1:])]} berhasil dikeluarkan"

    def visualisasi(self):
        html_grid = ""
        for baris in self.grid:
            for cell in baris:
                if cell is None:
                    html_grid += f"<div style='width:30px;height:15px;border:1px solid #ccc;display:inline-block'></div>"
                else:
                    gol = int(cell[1:])
                    html_grid += f"<div style='width:30px;height:15px;background:{WARNA[gol]};display:inline-block;text-align:center;font-size:10px;color:white'>{ROMAWI[gol]}</div>"
            html_grid += "<br>"
        return html_grid

    def muatan_total_dan_titik_berat(self):
        total_berat = 0
        total_momen = 0
        for i in range(self.lebar):
            for j in range(self.panjang):
                cell = self.grid[i][j]
                if cell is not None:
                    gol = int(cell[1:])
                    berat = KENDARAAN[gol][2]
                    total_berat += berat
                    total_momen += berat * (j + 0.5)
        if total_berat == 0:
            return 0, 0
        return total_berat, total_momen / total_berat

class Kapal:
    def __init__(self, data_lantai):
        self.lantai = [LantaiKapal(p, l) for p, l in data_lantai]

    def tambah_kendaraan(self, golongan):
        pjg, lbr, _ = KENDARAAN[golongan]
        lantai_prioritas = list(range(1, len(self.lantai))) + [0] if golongan in [4, 5] else [0]
        for idx in lantai_prioritas:
            lantai = self.lantai[idx]
            for i in range(lantai.lebar):
                for j in range(lantai.panjang):
                    if lantai.bisa_ditempatkan(pjg, lbr, i, j):
                        lantai.tempatkan(golongan, i, j)
                        return f"Kendaraan golongan {ROMAWI[golongan]} berhasil ditempatkan di Lantai {idx+1}"
        return f"Tidak ada ruang tersedia untuk golongan {ROMAWI[golongan]}"

    def keluarkan_kendaraan(self, idx_lantai, baris, kolom):
        return self.lantai[idx_lantai].hapus(baris, kolom)

    def visualisasi(self):
        vis = ""
        for i, lantai in enumerate(self.lantai):
            vis += f"<div style='display:inline-block;margin-right:20px'>"
            vis += f"<h4 style='text-align:center'>Lantai {i+1}</h4>"
            vis += lantai.visualisasi()
            total_berat, titik_berat = lantai.muatan_total_dan_titik_berat()
            vis += f"<p>Total Berat: {total_berat}</p><p>Titik Berat Horisontal: {titik_berat:.2f} / {lantai.panjang}</p>"
            vis += "</div>"
        return vis

def get_kemungkinan_sisa():
    sisa = {k: 0 for k in KENDARAAN}
    for g in KENDARAAN:
        for _ in range(100):
            hasil = st.session_state.kapal.tambah_kendaraan(g)
            if "berhasil" in hasil:
                sisa[g] += 1
            else:
                break
    return sisa

st.set_page_config(layout="wide")
st.title("Simulasi Muat Kapal dengan Titik Berat Seimbang")

if "kapal" not in st.session_state:
    st.session_state.kapal = None

if "input_lantai" not in st.session_state:
    st.session_state.input_lantai = []

st.sidebar.markdown("### Konfigurasi Kapal")
jumlah = st.sidebar.number_input("Jumlah Lantai", 1, 5, 2)
st.session_state.input_lantai = []
for i in range(jumlah):
    p = st.sidebar.number_input(f"Panjang Lantai {i+1}", 10, 100, 30, key=f"pjg{i}")
    l = st.sidebar.number_input(f"Lebar Lantai {i+1}", 2, 10, 4, key=f"lbr{i}")
    st.session_state.input_lantai.append((p, l))

if st.sidebar.button("Mulai"):
    st.session_state.kapal = Kapal(st.session_state.input_lantai)
    st.rerun()

if st.session_state.kapal:
    st.sidebar.markdown("### 🚗 Tambah Kendaraan")
    gol = st.sidebar.selectbox("Golongan Kendaraan", list(KENDARAAN.keys()), format_func=label_romawi)
    if st.sidebar.button("Tambah"):
        hasil = st.session_state.kapal.tambah_kendaraan(gol)
        st.success(hasil)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ❌ Keluarkan Kendaraan")
    idx = st.sidebar.number_input("Lantai", 1, jumlah, 1) - 1
    bar = st.sidebar.number_input("Baris", 0, 100, 0)
    kol = st.sidebar.number_input("Kolom", 0, 100, 0)
    if st.sidebar.button("Keluarkan"):
        ok, pesan = st.session_state.kapal.keluarkan_kendaraan(idx, bar, kol)
        if ok:
            st.success(pesan)
        else:
            st.error(pesan)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Kapasitas Tersisa per Golongan")
    sisa = get_kemungkinan_sisa()
    for g in sisa:
        st.sidebar.write(f"Golongan {ROMAWI[g]}: {sisa[g]} unit")

    st.markdown(st.session_state.kapal.visualisasi(), unsafe_allow_html=True)
else:
    st.info("Klik 'Mulai' untuk memulai simulasi.")
