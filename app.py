import streamlit as st
import math

st.set_page_config(page_title="Stabilitas Kapal 2D", layout="centered")
st.title("Stabilitas Kapal - Titik Berat Horizontal & Vertikal")

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
        self.kendaraan_terpasang = []

    def reset_grid(self):
        self.grid = [['.' for _ in range(self.slot_count)] for _ in range(self.panjang)]
        for k in self.kendaraan_terpasang:
            for j in range(k['panjang']):
                self.grid[k['row'] + j][k['col']] = f"G{ROMAWI[k['gol']]}"

    def get_center_of_mass(self):
        total_weight = 0
        sum_x = 0
        sum_y = 0
        for k in self.kendaraan_terpasang:
            berat = KENDARAAN[k['gol']]
            x = k['col'] + 0.5
            y = k['row'] + k['panjang'] / 2
            sum_x += berat * x
            sum_y += berat * y
            total_weight += berat
        if total_weight == 0:
            return None
        return (sum_x / total_weight, sum_y / total_weight)

    def cari_semua_posisi(self, gol):
        panjang_kendaraan = KENDARAAN[gol]
        posisi_valid = []
        for i in range(self.slot_count):
            for start_row in range(self.panjang - panjang_kendaraan + 1):
                if all(self.grid[start_row + j][i] == '.' for j in range(panjang_kendaraan)):
                    posisi_valid.append((i, start_row))
        return posisi_valid

    def update_kendaraan(self, daftar_kendaraan):
        self.kendaraan_terpasang = []
        self.grid = [['.' for _ in range(self.slot_count)] for _ in range(self.panjang)]
        for gol in daftar_kendaraan:
            self.tambah_kendaraan(gol)

    def tambah_kendaraan(self, gol):
        panjang_kendaraan = KENDARAAN[gol]
        label = f"G{ROMAWI[gol]}"
        semua_posisi = self.cari_semua_posisi(gol)
        terbaik = None
        jarak_terdekat = float('inf')

        for col, row in semua_posisi:
            self.kendaraan_terpasang.append({"gol": gol, "col": col, "row": row, "panjang": panjang_kendaraan})
            self.reset_grid()
            com = self.get_center_of_mass()
            self.kendaraan_terpasang.pop()
            if com:
                x0 = self.slot_count / 2
                y0 = self.panjang / 2
                jarak = math.sqrt((com[0] - x0) ** 2 + (com[1] - y0) ** 2)
                if jarak < jarak_terdekat:
                    jarak_terdekat = jarak
                    terbaik = (col, row)

        if terbaik:
            col, row = terbaik
            for j in range(panjang_kendaraan):
                self.grid[row + j][col] = label
            self.kendaraan_terpasang.append({"gol": gol, "col": col, "row": row, "panjang": panjang_kendaraan})
            return True, f"Slot {col+1} baris {row+1}"
        return False, "Tidak cukup ruang"

    def sisa_kemungkinan(self):
        kosong = [['.' for _ in range(self.slot_count)] for _ in range(self.panjang)]
        for row in range(self.panjang):
            for col in range(self.slot_count):
                if self.grid[row][col] != '.':
                    kosong[row][col] = '#'
        hasil = {gol: 0 for gol in KENDARAAN}
        for gol, pj in KENDARAAN.items():
            for col in range(self.slot_count):
                row = 0
                while row <= self.panjang - pj:
                    if all(kosong[row + j][col] == '.' for j in range(pj)):
                        hasil[gol] += 1
                        row += pj
                    else:
                        row += 1
        return hasil

    def visualisasi(self):
        st.markdown("<b>Visualisasi</b>", unsafe_allow_html=True)
        html_grid = "<div style='display:grid; grid-template-columns: repeat(%d, 30px); gap:1px;'>" % (self.slot_count)
        for row in self.grid:
            for cell in row:
                if cell == '.':
                    html_grid += "<div style='width:30px;height:15px;background:#ddd;'></div>"
                else:
                    gol = next((k for k, v in ROMAWI.items() if v == cell[1:]), 4)
                    html_grid += f"<div style='width:30px;height:15px;background:{WARNA[gol]};text-align:center;font-size:10px;color:white'>{cell}</div>"
        html_grid += "</div>"
        st.markdown(html_grid, unsafe_allow_html=True)
        com = self.get_center_of_mass()
        if com:
            st.markdown(f"<small>Pusat Berat (x, y): <b>{com[0]:.2f}, {com[1]:.2f}</b></small>", unsafe_allow_html=True)

class Kapal:
    def __init__(self, lantai_defs):
        self.lantai_list = [LantaiKapal(p, l) for p, l in lantai_defs]
        self.daftar_kendaraan = []

    def tambah_kendaraan(self, gol):
        self.daftar_kendaraan.append(gol)
        for lantai in self.lantai_list:
            lantai.update_kendaraan([g for g in self.daftar_kendaraan if g >= 6] + [g for g in self.daftar_kendaraan if g < 6])
        return "Kendaraan dimuat ulang dan dioptimalkan"

    def visualisasi(self):
        layout = st.columns(len(self.lantai_list))
        for idx, lantai in enumerate(self.lantai_list):
            with layout[idx]:
                st.markdown(f"<b>Lantai {idx+1}</b>", unsafe_allow_html=True)
                lantai.visualisasi()
                st.markdown("<i>Sisa muat:</i>")
                sisa = lantai.sisa_kemungkinan()
                for g in sorted(sisa):
                    if g >= 6 and idx > 0:
                        continue
                    st.markdown(f"Gol {ROMAWI[g]}: {sisa[g]} unit")

# Streamlit Session
if "kapal" not in st.session_state:
    st.session_state.kapal = None
if "input_lantai" not in st.session_state:
    st.session_state.input_lantai = []

st.sidebar.header("Pengaturan Kapal")

if st.session_state.kapal is None:
    jumlah = st.sidebar.number_input("Jumlah lantai kapal", min_value=1, max_value=5, value=2)
    if len(st.session_state.input_lantai) != jumlah:
        st.session_state.input_lantai = [{"panjang": 30, "lebar": 9} for _ in range(jumlah)]

    for i in range(jumlah):
        st.sidebar.markdown(f"**Lantai {i+1}**")
        st.session_state.input_lantai[i]["panjang"] = st.sidebar.number_input(
            f"Panjang Lantai {i+1}", min_value=1, max_value=200, value=st.session_state.input_lantai[i]["panjang"], key=f"p_{i}")
        st.session_state.input_lantai[i]["lebar"] = st.sidebar.number_input(
            f"Lebar Lantai {i+1}", min_value=3, max_value=30, value=st.session_state.input_lantai[i]["lebar"], key=f"l_{i}")

    if st.sidebar.button("Mulai"):
        data = [(d["panjang"], d["lebar"]) for d in st.session_state.input_lantai]
        st.session_state.kapal = Kapal(data)
        st.rerun()
else:
    st.sidebar.success("Kapal aktif ✅")
    if st.sidebar.button("Reset"):
        st.session_state.kapal = None
        st.rerun()

    st.sidebar.markdown("### 🚗 Tambah Kendaraan")
    gol = st.sidebar.selectbox("Golongan Kendaraan", list(KENDARAAN.keys()), format_func=lambda x: f"{ROMAWI[x]} (G{x})")
    if st.sidebar.button("Tambah"):
        hasil = st.session_state.kapal.tambah_kendaraan(gol)
        st.success(hasil)

    st.divider()
    st.session_state.kapal.visualisasi()
