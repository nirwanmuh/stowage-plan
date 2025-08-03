import streamlit as st
import math

st.set_page_config(page_title="Dynamic Quota", layout="centered")

# Golongan → panjang kendaraan (meter)
KENDARAAN = {
    4: 5,
    5: 7,
    6: 10,
    7: 12,
    8: 16,
    9: 24
}

# Golongan → berat kendaraan (ton)
BERAT = {
    4: 2.5,
    5: 3,
    6: 5,
    7: 7,
    8: 10,
    9: 15
}

# Golongan → warna grid
WARNA = {
    4: "#f94144",
    5: "#f3722c",
    6: "#f9c74f",
    7: "#90be6d",
    8: "#43aa8b",
    9: "#577590"
}

# Golongan → angka Romawi
ROMAWI = {
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX"
}

def label_romawi(val):
    return f"Golongan {ROMAWI[val]}"

class LantaiKapal:
    def __init__(self, panjang, lebar):
        self.panjang = panjang
        self.lebar = lebar
        self.slot_count = lebar // 3
        self.grid = [['.' for _ in range(self.slot_count)] for _ in range(panjang)]

    def tambah_kendaraan(self, gol):
        panjang_kendaraan = KENDARAAN[gol]
        berat = BERAT[gol]
        label = f"G{gol}"

        mid = (self.slot_count - 1) / 2
        best_diff = math.inf
        best_pos = None

        for i in range(self.slot_count):
            for start_row in range(self.panjang - panjang_kendaraan, -1, -1):
                if all(self.grid[start_row + j][i] == '.' for j in range(panjang_kendaraan)):
                    jarak_dari_tengah = i - mid
                    momen = abs(berat * jarak_dari_tengah)
                    if momen < best_diff:
                        best_diff = momen
                        best_pos = (start_row, i)

        if best_pos:
            r, c = best_pos
            for j in range(panjang_kendaraan):
                self.grid[r + j][c] = label
            return True, f"Slot {c+1} (terdekat titik seimbang)"
        else:
            return False, f"Tidak cukup ruang"

    def keluarkan_kendaraan(self, gol):
        label = f"G{gol}"
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

    def hitung_keseimbangan(self):
        total_momen = 0
        total_berat = 0
        mid = (self.slot_count - 1) / 2

        for c in range(self.slot_count):
            for r in range(self.panjang):
                cell = self.grid[r][c]
                if cell != '.':
                    gol = int(cell[1:])
                    berat = BERAT[gol]
                    jarak = c - mid
                    total_momen += berat * jarak
                    total_berat += berat

        if total_berat == 0:
            return 0
        return total_momen / total_berat

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
                html_grid = "<div style='overflow-y:auto; max-height:400px; display:grid; grid-template-columns: repeat(%d, 30px); gap:1px;'>" % (lantai.slot_count)
                for row in lantai.grid:
                    for cell in row:
                        if cell == '.':
                            html_grid += "<div style='width:30px;height:15px;background:#ddd;'></div>"
                        else:
                            gol = int(cell[1:])
                            romawi = ROMAWI[gol]
                            html_grid += f"<div style='width:30px;height:15px;background:{WARNA[gol]};text-align:center;font-size:10px;color:white'>{romawi}</div>"
                html_grid += "</div>"
                st.markdown(html_grid, unsafe_allow_html=True)

        st.markdown("### ⚖️ Titik Keseimbangan Horizontal")
        for i, lantai in enumerate(self.lantai_list):
            tb = lantai.hitung_keseimbangan()
            if abs(tb) < 0.5:
                st.success(f"Lantai {i+1}: {tb:.2f} (Stabil)")
            elif abs(tb) < 1:
                st.warning(f"Lantai {i+1}: {tb:.2f} (Sedikit miring)")
            else:
                arah = "kanan" if tb > 0 else "kiri"
                st.error(f"Lantai {i+1}: {tb:.2f} (Terlalu berat ke {arah})")

# Streamlit app
st.title("Dynamic Quota dengan Titik Seimbang")

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
            f"Panjang Lantai {i+1} (meter)", min_value=1, max_value=200,
            value=st.session_state.input_lantai[i]["panjang"], key=f"p_{i}")
        st.session_state.input_lantai[i]["lebar"] = st.sidebar.number_input(
            f"Lebar Lantai {i+1} (meter)", min_value=3, max_value=30,
            value=st.session_state.input_lantai[i]["lebar"], key=f"l_{i}")

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
    gol = st.sidebar.selectbox("Golongan Kendaraan", list(KENDARAAN.keys()), format_func=label_romawi)
    if st.sidebar.button("Tambah"):
        hasil = st.session_state.kapal.tambah_kendaraan(gol)
        st.success(hasil)

    st.sidebar.markdown("### ❌ Keluarkan Kendaraan")
    gol_del = st.sidebar.selectbox("Pilih Golongan yang Akan Dikeluarkan", list(KENDARAAN.keys()), format_func=label_romawi)
    if st.sidebar.button("Keluarkan"):
        ok, msg = st.session_state.kapal.keluarkan_kendaraan(gol_del)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    st.sidebar.markdown("### ℹ️ Info Sisa Muat")
    for i, lantai in enumerate(st.session_state.kapal.lantai_list):
        st.sidebar.markdown(f"**Lantai {i+1}**")
        sisa = lantai.get_kemungkinan_sisa()
        for g in sorted(sisa.keys()):
            if g >= 6 and i > 0:
                continue
            st.sidebar.write(f"Golongan {ROMAWI[g]}: {sisa[g]} unit")

    st.divider()
    st.session_state.kapal.visualisasi()
