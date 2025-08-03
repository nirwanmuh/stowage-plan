import streamlit as st
import random

st.set_page_config(page_title="Simulasi Muatan Kapal", layout="wide")
st.title("Simulasi Muatan Kapal")

KENDARAAN = {
    "IV": (2, 1),
    "V": (2, 1),
    "VI": (3, 1),
    "VII": (3, 1),
    "VIII": (4, 1),
    "IX": (5, 1)
}

WARNA = {
    "IV": "#AED6F1",
    "V": "#85C1E9",
    "VI": "#F9E79F",
    "VII": "#F7DC6F",
    "VIII": "#F5B7B1",
    "IX": "#EC7063"
}

class LantaiKapal:
    def __init__(self, panjang, lebar, nama):
        self.panjang = panjang
        self.lebar = lebar
        self.nama = nama
        self.grid = [[None for _ in range(lebar)] for _ in range(panjang)]

    def muat_kendaraan(self, kendaraan, berat, posisi):
        x, y = posisi
        panjang, lebar = kendaraan
        if self.bisa_muat(kendaraan, posisi):
            for i in range(panjang):
                for j in range(lebar):
                    self.grid[y+i][x+j] = (kendaraan, berat)
            return True
        return False

    def bisa_muat(self, kendaraan, posisi):
        x, y = posisi
        panjang, lebar = kendaraan
        if y + panjang > self.panjang or x + lebar > self.lebar:
            return False
        for i in range(panjang):
            for j in range(lebar):
                if self.grid[y+i][x+j] is not None:
                    return False
        return True

    def sisa_slot(self):
        return sum(cell is None for row in self.grid for cell in row)

class Kapal:
    def __init__(self):
        self.lantai_list = []

    def tambah_lantai(self, panjang, lebar):
        nama = f"Lantai {len(self.lantai_list)+1}"
        self.lantai_list.append(LantaiKapal(panjang, lebar, nama))

    def cari_posisi_optimal(self, kendaraan, berat, golongan):
        best_offset = float('inf')
        best_pos = None
        best_lantai = None
        for idx, lantai in enumerate(self.lantai_list):
            if golongan in ["VI", "VII", "VIII", "IX"] and idx != 0:
                continue
            for y in range(lantai.panjang):
                for x in range(lantai.lebar):
                    if lantai.bisa_muat(kendaraan, (x, y)):
                        # Simulasikan penempatan
                        backup = [row[:] for row in lantai.grid]
                        lantai.muat_kendaraan(kendaraan, berat, (x, y))
                        ox, oy = self.get_center_of_gravity()
                        offset = abs(ox) + abs(oy)
                        lantai.grid = backup
                        if offset < best_offset:
                            best_offset = offset
                            best_pos = (x, y)
                            best_lantai = lantai
        return best_lantai, best_pos

    def tambah_kendaraan(self, golongan, berat):
        kendaraan = KENDARAAN[golongan]
        lantai, posisi = self.cari_posisi_optimal(kendaraan, berat, golongan)
        if lantai and posisi:
            lantai.muat_kendaraan(kendaraan, berat, posisi)
            return True
        return False

    def get_center_of_gravity(self):
        total_berat = 0
        total_x_moment = 0
        total_y_moment = 0

        for lantai in self.lantai_list:
            cols = lantai.lebar
            rows = lantai.panjang
            for y in range(rows):
                for x in range(cols):
                    cell = lantai.grid[y][x]
                    if cell:
                        _, berat = cell
                        total_berat += berat
                        total_x_moment += (x + 0.5) * berat
                        total_y_moment += (y + 0.5) * berat

        if total_berat == 0:
            return 0.0, 0.0

        ref_x = self.lantai_list[0].lebar / 2
        ref_y = self.lantai_list[0].panjang / 2

        cog_x = total_x_moment / total_berat
        cog_y = total_y_moment / total_berat

        offset_x = (cog_x - ref_x) / ref_x
        offset_y = (cog_y - ref_y) / ref_y

        return round(offset_x, 2), round(offset_y, 2)

if "kapal" not in st.session_state:
    st.session_state.kapal = Kapal()

with st.sidebar:
    st.header("Konfigurasi Kapal")
    panjang = st.number_input("Panjang Lantai", min_value=1, value=5)
    lebar = st.number_input("Lebar Lantai", min_value=1, value=10)
    if st.button("Tambah Lantai"):
        st.session_state.kapal.tambah_lantai(panjang, lebar)

    st.header("Tambah Kendaraan")
    golongan = st.selectbox("Golongan Kendaraan", list(KENDARAAN.keys()))
    berat = st.number_input("Berat Kendaraan", min_value=1, value=5)
    if st.button("Muatkan ke Kapal"):
        berhasil = st.session_state.kapal.tambah_kendaraan(golongan, berat)
        if not berhasil:
            st.error("Kendaraan tidak dapat dimuat.")

    st.markdown("### 📦 Keseimbangan Kapal")
    offset_x, offset_y = st.session_state.kapal.get_center_of_gravity()
    arah_x = "kanan" if offset_x > 0 else "kiri" if offset_x < 0 else "tengah"
    arah_y = "belakang" if offset_y > 0 else "depan" if offset_y < 0 else "tengah"
    st.write(f"- Titik Berat Horizontal: {offset_x:+.2f} ({arah_x})")
    st.write(f"- Titik Berat Vertikal: {offset_y:+.2f} ({arah_y})")
    if abs(offset_x) < 0.3 and abs(offset_y) < 0.3:
        st.success("⚖️ Seimbang")
    else:
        st.warning("⚠️ Tidak Seimbang")

st.subheader("Visualisasi Kapal")
cols = st.columns(len(st.session_state.kapal.lantai_list))
for idx, lantai in enumerate(st.session_state.kapal.lantai_list):
    with cols[idx]:
        st.markdown(f"**{lantai.nama}**")
        for row in lantai.grid:
            row_display = ""
            for cell in row:
                if cell:
                    gol = None
                    for key, val in KENDARAAN.items():
                        if val == cell[0]:
                            gol = key
                            break
                    color = WARNA[gol] if gol else "#D5DBDB"
                    row_display += f":blue_square:"
                else:
                    row_display += ":white_large_square:"
            st.markdown(row_display)
