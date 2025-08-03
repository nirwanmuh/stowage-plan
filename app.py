import streamlit as st

st.set_page_config(page_title="Dynamic Quota", layout="centered")
st.title("Dynamic Quota")

KENDARAAN = {
    4: 5,
    5: 7,
    6: 10,
    7: 12,
    8: 16,
    9: 24
}

ROMAWI = {
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX"
}

WARNA = {
    4: "#f94144",
    5: "#f3722c",
    6: "#f9c74f",
    7: "#90be6d",
    8: "#43aa8b",
    9: "#577590"
}

class LantaiKapal:
    def __init__(self, panjang, lebar):
        self.panjang = panjang
        self.lebar = lebar
        self.slot_count = lebar // 3
        self.grid = [[None for _ in range(self.slot_count)] for _ in range(panjang)]

    def cari_posisi_optimal(self, gol, berat):
        panjang_kendaraan = KENDARAAN[gol]
        label = f"G{ROMAWI[gol]}"
        center = self.slot_count / 2
        kolom_prioritas = sorted(range(self.slot_count), key=lambda i: abs(i - center))

        posisi_terbaik = None
        min_offset = float("inf")

        for i in kolom_prioritas:
            for start_row in range(self.panjang - panjang_kendaraan + 1):
                if all(self.grid[start_row + j][i] is None for j in range(panjang_kendaraan)):
                    for j in range(panjang_kendaraan):
                        self.grid[start_row + j][i] = (label, berat)
                    offset_x, offset_y = self.get_offset_simulasi()
                    total_offset = abs(offset_x) + abs(offset_y)
                    if total_offset < min_offset:
                        min_offset = total_offset
                        posisi_terbaik = (i, start_row)
                    for j in range(panjang_kendaraan):
                        self.grid[start_row + j][i] = None

        return posisi_terbaik

    def get_offset_simulasi(self):
        total_berat = 0
        total_x_moment = 0
        total_y_moment = 0
        for y in range(self.panjang):
            for x in range(self.slot_count):
                cell = self.grid[y][x]
                if cell:
                    _, berat = cell
                    total_berat += berat
                    total_x_moment += (x + 0.5) * berat
                    total_y_moment += (y + 0.5) * berat

        if total_berat == 0:
            return 0.0, 0.0

        ref_x = self.slot_count / 2
        ref_y = self.panjang / 2

        cog_x = total_x_moment / total_berat
        cog_y = total_y_moment / total_berat

        offset_x = (cog_x - ref_x) / ref_x
        offset_y = (cog_y - ref_y) / ref_y

        return offset_x, offset_y

    def keluarkan_kendaraan(self, gol):
        label = f"G{ROMAWI[gol]}"
        panjang_kendaraan = KENDARAAN[gol]
        for kolom_index in range(self.slot_count):
            for row_index in range(self.panjang - panjang_kendaraan + 1):
                if all(self.grid[row_index + j][kolom_index] is not None and self.grid[row_index + j][kolom_index][0] == label for j in range(panjang_kendaraan)):
                    for j in range(panjang_kendaraan):
                        self.grid[row_index + j][kolom_index] = None
                    return True, f"Kendaraan golongan {ROMAWI[gol]} berhasil dikeluarkan dari Slot {kolom_index+1}"
        return False, f"Tidak ada kendaraan golongan {ROMAWI[gol]} ditemukan di lantai ini."

    def get_kemungkinan_sisa(self):
        sisa = {gol: 0 for gol in KENDARAAN.keys()}

        for i in range(self.slot_count):
            row = self.panjang - 1
            while row >= 0:
                if self.grid[row][i] is None:
                    kosong = 0
                    while row >= 0 and self.grid[row][i] is None:
                        kosong += 1
                        row -= 1
                    for gol, panjang in KENDARAAN.items():
                        if kosong >= panjang:
                            sisa[gol] += kosong // panjang
                else:
                    row -= 1
        return sisa

class Kapal:
    def __init__(self, lantai_defs):
        self.lantai_list = [LantaiKapal(p, l) for p, l in lantai_defs]

    def tambah_kendaraan(self, gol, berat):
        lantai_prioritas = []

        if gol in [4, 5]:
            lantai_prioritas = list(range(1, len(self.lantai_list))) + [0]
        else:
            lantai_prioritas = [0]

        for idx in lantai_prioritas:
            posisi = self.lantai_list[idx].cari_posisi_optimal(gol, berat)
            if posisi:
                i, start_row = posisi
                label = f"G{ROMAWI[gol]}"
                for j in range(KENDARAAN[gol]):
                    self.lantai_list[idx].grid[start_row + j][i] = (label, berat)
                return f"(Lantai {idx+1}) Slot {i+1}"

        return f"Tidak cukup ruang di semua lantai yang diperbolehkan."

    def keluarkan_kendaraan(self, gol):
        if gol in [4, 5]:
            ok, msg = self.lantai_list[0].keluarkan_kendaraan(gol)
            if ok:
                return True, f"(Lantai 1) {msg}"
            for idx in range(1, len(self.lantai_list)):
                ok, msg = self.lantai_list[idx].keluarkan_kendaraan(gol)
                if ok:
                    return True, f"(Lantai {idx+1}) {msg}"
            return False, f"Tidak ada kendaraan golongan {ROMAWI[gol]} ditemukan di kapal."
        else:
            ok, msg = self.lantai_list[0].keluarkan_kendaraan(gol)
            if ok:
                return True, f"(Lantai 1) {msg}"
            return False, f"Tidak ada kendaraan golongan {ROMAWI[gol]} ditemukan di lantai 1."

    def visualisasi(self):
        st.markdown("<h3 style='text-align:center;'>Visualisasi Lantai Kapal</h3>", unsafe_allow_html=True)
        layout = st.columns(len(self.lantai_list))
        for idx, lantai in enumerate(self.lantai_list):
            with layout[idx]:
                st.markdown(f"<b>Lantai {idx+1}</b>", unsafe_allow_html=True)
                html_grid = "<div style='display:grid; grid-template-columns: repeat(%d, 30px); gap:1px;'>" % (lantai.slot_count)
                for row in lantai.grid:
                    for cell in row:
                        if cell is None:
                            html_grid += "<div style='width:30px;height:15px;background:#ddd;'></div>"
                        else:
                            label, _ = cell
                            gol = next((k for k, v in ROMAWI.items() if v == label[1:]), 4)
                            html_grid += f"<div style='width:30px;height:15px;background:{WARNA[gol]};text-align:center;font-size:10px;color:white'>{label}</div>"
                html_grid += "</div>"
                st.markdown(html_grid, unsafe_allow_html=True)

    def get_center_of_gravity(self):
        total_berat = 0
        total_x_moment = 0
        total_y_moment = 0

        for lantai in self.lantai_list:
            cols = lantai.slot_count
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

        ref_x = self.lantai_list[0].slot_count / 2
        ref_y = self.lantai_list[0].panjang / 2

        cog_x = total_x_moment / total_berat
        cog_y = total_y_moment / total_berat

        offset_x = (cog_x - ref_x) / ref_x
        offset_y = (cog_y - ref_y) / ref_y

        return round(offset_x, 2), round(offset_y, 2)
