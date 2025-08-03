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
        self.grid = [['.' for _ in range(self.slot_count)] for _ in range(panjang)]

    def tambah_kendaraan(self, gol):
        panjang_kendaraan = KENDARAAN[gol]
        label = f"G{ROMAWI[gol]}"
        center = self.slot_count / 2
        kolom_prioritas = sorted(range(self.slot_count), key=lambda i: abs(i - center))

        for i in kolom_prioritas:
            for start_row in range(self.panjang - panjang_kendaraan, -1, -1):
                if all(self.grid[start_row + j][i] == '.' for j in range(panjang_kendaraan)):
                    for j in range(panjang_kendaraan):
                        self.grid[start_row + j][i] = label
                    return True, f"Lantai ini slot {i+1}"
        return False, f"Tidak cukup ruang"

    def keluarkan_kendaraan(self, gol):
        label = f"G{ROMAWI[gol]}"
        panjang_kendaraan = KENDARAAN[gol]
        for kolom_index in range(self.slot_count):
            for row_index in range(self.panjang - panjang_kendaraan + 1):
                if all(self.grid[row_index + j][kolom_index] == label for j in range(panjang_kendaraan)):
                    for j in range(panjang_kendaraan):
                        self.grid[row_index + j][kolom_index] = '.'
                    return True, f"Kendaraan golongan {ROMAWI[gol]} berhasil dikeluarkan dari Slot {kolom_index+1}"
        return False, f"Tidak ada kendaraan golongan {ROMAWI[gol]} ditemukan di lantai ini."

    def get_kemungkinan_sisa(self):
        sisa = {gol: 0 for gol in KENDARAAN.keys()}

        for i in range(self.slot_count):
            row = self.panjang - 1
            while row >= 0:
                if self.grid[row][i] == '.':
                    kosong = 0
                    while row >= 0 and self.grid[row][i] == '.':
                        kosong += 1
                        row -= 1
                    for gol, panjang in KENDARAAN.items():
                        if kosong >= panjang:
                            sisa[gol] += kosong // panjang
                else:
                    row -= 1
        return sisa

    def titik_berat(self):
        total_berat = 0
        total_x = 0
        total_y = 0
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell != '.':
                    gol = next((g for g, r in ROMAWI.items() if f"G{r}" == cell), 4)
                    berat = gol * 1000
                    total_berat += berat
                    total_x += x * berat
                    total_y += y * berat
        if total_berat == 0:
            return None
        return total_x / total_berat, total_y / total_berat, total_berat

class Kapal:
    def __init__(self, lantai_defs):
        self.lantai_list = [LantaiKapal(p, l) for p, l in lantai_defs]

    def tambah_kendaraan(self, gol):
        if gol in [4, 5]:
            for idx in range(1, len(self.lantai_list)):
                ok, msg = self.lantai_list[idx].tambah_kendaraan(gol)
                if ok:
                    return f"(Lantai {idx+1}) {msg}"
            ok, msg = self.lantai_list[0].tambah_kendaraan(gol)
            return f"(Lantai 1) {msg}"
        else:
            ok, msg = self.lantai_list[0].tambah_kendaraan(gol)
            return f"(Lantai 1) {msg}"

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
                        if cell == '.':
                            html_grid += "<div style='width:30px;height:15px;background:#ddd;'></div>"
                        else:
                            gol = next((k for k, v in ROMAWI.items() if v == cell[1:]), 4)
                            html_grid += f"<div style='width:30px;height:15px;background:{WARNA[gol]};text-align:center;font-size:10px;color:white'>{cell}</div>"
                html_grid += "</div>"
                st.markdown(html_grid, unsafe_allow_html=True)

        # Hitung titik berat total kapal
        total_berat = 0
        total_x = 0
        total_y = 0
        max_slot = max([l.slot_count for l in self.lantai_list])
        max_panjang = max([l.panjang for l in self.lantai_list])

        for lantai in self.lantai_list:
            result = lantai.titik_berat()
            if result:
                x, y, berat = result
                total_berat += berat
                total_x += x * berat
                total_y += y * berat

        if total_berat > 0:
            x_cog = total_x / total_berat
            y_cog = total_y / total_berat
            tengah_x = max_slot / 2
            tengah_y = max_panjang / 2
            st.info(f"Titik berat kapal: x = {x_cog:.2f}, y = {y_cog:.2f}")
            st.success(f"Titik tengah ideal: x = {tengah_x:.2f}, y = {tengah_y:.2f}")
            if abs(x_cog - tengah_x) < 1 and abs(y_cog - tengah_y) < 1:
                st.success("Kapal dalam kondisi seimbang.")
            else:
                st.warning("Kapal tidak seimbang. Perlu penyesuaian muatan.")
