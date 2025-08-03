import streamlit as st
import numpy as np

st.set_page_config(layout="wide")

# ------------------------
# Parameter sistem
# ------------------------
slot_per_baris = 10
panjang_lantai = 6  # jumlah baris (depan-belakang)

GOLONGAN_INFO = {
    "IV": 2,
    "V": 3,
    "VI": 4,
    "VII": 5,
    "VIII": 6,
    "IX": 7
}

golongan_prioritas = ["IV", "V", "VI", "VII", "VIII", "IX"]

# ------------------------
# Kelas Lantai
# ------------------------
class LantaiKapal:
    def __init__(self, nama, panjang, lebar):
        self.nama = nama
        self.panjang = panjang
        self.lebar = lebar
        self.grid = [[None for _ in range(lebar)] for _ in range(panjang)]

    def bisa_memuat(self, panjang_kendaraan):
        for y in range(self.panjang):
            for x in range(self.lebar - panjang_kendaraan + 1):
                if all(self.grid[y][x + i] is None for i in range(panjang_kendaraan)):
                    return True
        return False

    def muat_kendaraan_optimal(self, golongan, panjang_kendaraan, semua_posisi):
        posisi_terbaik = None
        min_jarak = float('inf')

        for y in range(self.panjang):
            for x in range(self.lebar - panjang_kendaraan + 1):
                if all(self.grid[y][x + i] is None for i in range(panjang_kendaraan)):
                    posisi = semua_posisi + [(x + panjang_kendaraan/2, y + 0.5, panjang_kendaraan)]
                    cx, cy = get_center_of_mass(posisi)
                    dx = abs(cx - self.lebar/2)
                    dy = abs(cy - self.panjang/2)
                    jarak = dx + dy
                    if jarak < min_jarak:
                        min_jarak = jarak
                        posisi_terbaik = (x, y)

        if posisi_terbaik:
            x, y = posisi_terbaik
            for i in range(panjang_kendaraan):
                self.grid[y][x + i] = golongan
            return True

        return False

    def hapus_semua(self):
        self.grid = [[None for _ in range(self.lebar)] for _ in range(self.panjang)]

    def posisi_kendaraan(self):
        posisi = []
        for y in range(self.panjang):
            for x in range(self.lebar):
                if self.grid[y][x] and (x == 0 or self.grid[y][x-1] != self.grid[y][x]):
                    panjang = 1
                    while x + panjang < self.lebar and self.grid[y][x + panjang] == self.grid[y][x]:
                        panjang += 1
                    posisi.append((x + panjang/2, y + 0.5, panjang))
        return posisi

# ------------------------
# Fungsi bantu
# ------------------------
def get_center_of_mass(posisi):
    total_massa = sum(p for _, _, p in posisi)
    cx = sum(x * p for x, _, p in posisi) / total_massa
    cy = sum(y * p for _, y, p in posisi) / total_massa
    return cx, cy

def tampilkan_lantai(lantai: LantaiKapal):
    st.markdown(f"**{lantai.nama}**")
    for row in lantai.grid:
        st.markdown("".join(
            f"<span style='display:inline-block; width:25px; height:25px; text-align:center; border:1px solid #ccc; background:#eaeaea'>{cell if cell else '&nbsp;'}</span>"
            for cell in row
        ), unsafe_allow_html=True)

# ------------------------
# Fungsi utama
# ------------------------
def atur_ulang_semua_kendaraan(daftar_golongan, semua_lantai):
    # Kosongkan semua lantai
    for l in semua_lantai:
        l.hapus_semua()

    kendaraan_teralokasi = {g: 0 for g in daftar_golongan}

    for gol in daftar_golongan:
        panjang = GOLONGAN_INFO[gol]
        while True:
            semua_posisi = []
            for lt in semua_lantai:
                semua_posisi += lt.posisi_kendaraan()

            terpasang = False
            for lt in semua_lantai:
                if gol in ["IV", "V"] and lt != semua_lantai[0]:
                    if lt.muat_kendaraan_optimal(gol, panjang, semua_posisi):
                        kendaraan_teralokasi[gol] += 1
                        terpasang = True
                        break
                elif gol not in ["IV", "V"] and lt == semua_lantai[0]:
                    if lt.muat_kendaraan_optimal(gol, panjang, semua_posisi):
                        kendaraan_teralokasi[gol] += 1
                        terpasang = True
                        break
            if not terpasang:
                break

    return kendaraan_teralokasi

# ------------------------
# Streamlit UI
# ------------------------
st.title("🚢 Penataan Kendaraan di Dalam Kapal")

jml_lantai = st.sidebar.number_input("Jumlah lantai", 1, 5, 2)
lantai_list = []
for i in range(jml_lantai):
    panjang = st.sidebar.number_input(f"Panjang lantai {i+1}", 1, 20, panjang_lantai, key=f"panjang_{i}")
    lebar = st.sidebar.number_input(f"Lebar lantai {i+1}", 1, 20, slot_per_baris, key=f"lebar_{i}")
    lantai_list.append(LantaiKapal(f"Lantai {i+1}", panjang, lebar))

st.sidebar.markdown("---")

# Input kendaraan
jumlah_kendaraan = {}
for gol in golongan_prioritas:
    jumlah_kendaraan[gol] = st.sidebar.number_input(f"Jumlah kendaraan golongan {gol}", 0, 100, 0)

if st.sidebar.button("Atur Kendaraan"):
    hasil = atur_ulang_semua_kendaraan(
        [gol for gol in golongan_prioritas for _ in range(jumlah_kendaraan[gol])],
        lantai_list
    )

    st.success("Penataan kendaraan selesai ✅")

    for lt in lantai_list:
        tampilkan_lantai(lt)

    semua_posisi = []
    for lt in lantai_list:
        semua_posisi += lt.posisi_kendaraan()

    cx, cy = get_center_of_mass(semua_posisi)
    st.markdown(f"**Titik pusat berat:** X = `{cx:.2f}`, Y = `{cy:.2f}`")

    # Hitung sisa kendaraan yang bisa ditampung
    kapasitas_terpakai = {g: hasil.get(g, 0) for g in golongan_prioritas}
    kapasitas_diminta = jumlah_kendaraan
    st.markdown("### Sisa kendaraan yang tidak dapat dimuat:")
    for g in golongan_prioritas:
        sisa = kapasitas_diminta[g] - kapasitas_terpakai.get(g, 0)
        st.markdown(f"- Golongan {g}: {max(sisa, 0)} unit")
