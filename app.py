import streamlit as st

st.set_page_config(page_title="Dynamic Quota", layout="wide")
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

    def kosongkan(self):
        self.grid = [['.' for _ in range(self.slot_count)] for _ in range(self.panjang)]

class Kapal:
    def __init__(self, lantai_defs):
        self.lantai_defs = lantai_defs
        self.lantai_list = [LantaiKapal(p, l) for p, l in lantai_defs]
        self.kendaraan_list = []

    def reset(self):
        self.lantai_list = [LantaiKapal(p, l) for p, l in self.lantai_defs]

    def tambah_kendaraan(self, gol):
        self.kendaraan_list.append(gol)
        self.reset()
        for gol in self.kendaraan_list:
            self._atur_kendaraan(gol)

    def _atur_kendaraan(self, gol):
        if gol in [4, 5]:
            for idx in range(1, len(self.lantai_list)):
                ok, _ = self.lantai_list[idx].tambah_kendaraan(gol)
                if ok:
                    return
            self.lantai_list[0].tambah_kendaraan(gol)
        else:
            self.lantai_list[0].tambah_kendaraan(gol)

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

        total_berat = 0
        total_x = 0
        total_y = 0
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
            st.info(f"Titik berat kapal (horizontal, vertical): (x = {x_cog:.2f}, y = {y_cog:.2f})")

        total_sisa = {gol: 0 for gol in KENDARAAN.keys()}
        for lantai in self.lantai_list:
            sisa = lantai.get_kemungkinan_sisa()
            for gol, jumlah in sisa.items():
                total_sisa[gol] += jumlah

        with st.expander("Sisa Kapasitas per Golongan"):
            for gol in sorted(total_sisa.keys()):
                st.markdown(f"Golongan {ROMAWI[gol]}: {total_sisa[gol]} kendaraan")

# Sidebar
with st.sidebar:
    st.header("Input Kapal")
    jumlah_lantai = st.number_input("Jumlah Lantai", min_value=1, max_value=5, value=2)
    lantai_defs = []
    for i in range(jumlah_lantai):
        panjang = st.number_input(f"Panjang Lantai {i+1}", min_value=10, value=30, key=f"p{i}")
        lebar = st.number_input(f"Lebar Lantai {i+1}", min_value=3, value=12, step=3, key=f"l{i}")
        lantai_defs.append((panjang, lebar))

    if 'kapal' not in st.session_state or st.button("Buat Ulang Kapal"):
        st.session_state.kapal = Kapal(lantai_defs)

    st.divider()
    st.header("Tambah Kendaraan")
    gol = st.selectbox("Pilih Golongan", options=sorted(KENDARAAN.keys()), format_func=lambda g: f"Golongan {ROMAWI[g]}")
    if st.button("Tambah"):
        st.session_state.kapal.tambah_kendaraan(gol)

# Visualisasi utama
st.session_state.kapal.visualisasi()
