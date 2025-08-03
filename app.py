import streamlit as st

st.set_page_config(page_title="Dynamic Quoata")

KENDARAAN = {
    4: 5,
    5: 7,
    6: 10,
    7: 12,
    8: 16,
    9: 24
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
        label = f"G{gol}"
        for i in range(self.slot_count):
            for start_row in range(self.panjang - panjang_kendaraan, -1, -1):
                if all(self.grid[start_row + j][i] == '.' for j in range(panjang_kendaraan)):
                    for j in range(panjang_kendaraan):
                        self.grid[start_row + j][i] = label
                    return True, f"Lantai ini slot {i+1}"
        return False, f"Tidak cukup ruang"

    def keluarkan_kendaraan(self, gol):
        label = f"G{gol}"
        panjang_kendaraan = KENDARAAN[gol]
        for kolom_index in range(self.slot_count):
            for row_index in range(self.panjang - panjang_kendaraan + 1):
                if all(self.grid[row_index + j][kolom_index] == label for j in range(panjang_kendaraan)):
                    for j in range(panjang_kendaraan):
                        self.grid[row_index + j][kolom_index] = '.'
                    return True, f"Kendaraan golongan {gol} berhasil dikeluarkan dari Slot {kolom_index+1}"
        return False, f"Tidak ada kendaraan golongan {gol} ditemukan di lantai ini."

    def get_kemungkinan_sisa(self):
        sisa = {gol: 0 for gol in KENDARAAN.keys()}
    
        for i in range(self.slot_count):  # Untuk iap kolom
            row = self.panjang - 1
            while row >= 0:
                if self.grid[row][i] == '.':
                    # Hitung panjang berturut-turut kosong ke atas
                    kosong = 0
                    while row >= 0 and self.grid[row][i] == '.':
                        kosong += 1
                        row -= 1
                    # Hitung berapa kendaraan yang bisa muat dari segmen kosong ini
                    for gol, panjang in KENDARAAN.items():
                        if kosong >= panjang:
                            sisa[gol] += kosong // panjang
                else:
                    row -= 1  # Skip sel yang terisi
        return sisa

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
            return False, f"Tidak ada kendaraan golongan {gol} ditemukan di kapal."
        else:
            ok, msg = self.lantai_list[0].keluarkan_kendaraan(gol)
            if ok:
                return True, f"(Lantai 1) {msg}"
            return False, f"Tidak ada kendaraan golongan {gol} ditemukan di lantai 1."

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
                            gol = int(cell[1])
                            html_grid += f"<div style='width:30px;height:15px;background:{WARNA[gol]};text-align:center;font-size:10px;color:white'>{cell}</div>"
                html_grid += "</div>"
                st.markdown(html_grid, unsafe_allow_html=True)

# Streamlit app
st.set_page_config(layout="centered")
st.title("Dynamic Quota")

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
            f"Panjang Lantai {i+1} (meter)", min_value=1, max_value=200, value=st.session_state.input_lantai[i]["panjang"], key=f"p_{i}")
        st.session_state.input_lantai[i]["lebar"] = st.sidebar.number_input(
            f"Lebar Lantai {i+1} (meter)", min_value=3, max_value=30, value=st.session_state.input_lantai[i]["lebar"], key=f"l_{i}")

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
    gol = st.sidebar.selectbox("Golongan Kendaraan", list(KENDARAAN.keys()))
    if st.sidebar.button("Tambah"):
        hasil = st.session_state.kapal.tambah_kendaraan(gol)
        st.success(hasil)

    st.sidebar.markdown("### ❌ Keluarkan Kendaraan")
    gol_del = st.sidebar.selectbox("Pilih Golongan yang Akan Dikeluarkan", list(KENDARAAN.keys()))
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
            st.sidebar.write(f"Gol {g}: {sisa[g]} unit")

    st.divider()
    st.session_state.kapal.visualisasi()

