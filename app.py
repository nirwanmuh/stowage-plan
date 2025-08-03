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

    def tambah_kendaraan(self, gol, berat):
        panjang_kendaraan = KENDARAAN[gol]
        label = f"G{ROMAWI[gol]}"
        center_x = self.slot_count / 2
        center_y = self.panjang / 2

        best_offset = float("inf")
        best_pos = None

        # Cari semua posisi memungkinkan
        for i in range(self.slot_count):
            center_row = self.panjang / 2
            row_candidates = sorted(
                range(self.panjang - panjang_kendaraan + 1),
                key=lambda r: abs((r + panjang_kendaraan / 2) - center_row)
            )
            for start_row in row_candidates:
                if all(self.grid[start_row + j][i] is None for j in range(panjang_kendaraan)):
                    # Simulasikan penempatan
                    total_berat = berat
                    total_x_moment = (i + 0.5) * berat
                    total_y_moment = sum((start_row + j + 0.5) * berat for j in range(panjang_kendaraan))

                    # Tambahkan beban yang sudah ada
                    for y in range(self.panjang):
                        for x in range(self.slot_count):
                            cell = self.grid[y][x]
                            if cell:
                                _, b = cell
                                total_berat += b
                                total_x_moment += (x + 0.5) * b
                                total_y_moment += (y + 0.5) * b

                    if total_berat == 0:
                        continue

                    cog_x = total_x_moment / total_berat
                    cog_y = total_y_moment / total_berat

                    offset_x = abs((cog_x - center_x) / center_x)
                    offset_y = abs((cog_y - center_y) / center_y)
                    total_offset = offset_x + offset_y

                    if total_offset < best_offset:
                        best_offset = total_offset
                        best_pos = (i, start_row)

        if best_pos:
            i, start_row = best_pos
            for j in range(panjang_kendaraan):
                self.grid[start_row + j][i] = (label, berat)
            return True, f"Slot {i+1}"
        return False, "Tidak cukup ruang"

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
        if gol in [4, 5]:
            for idx in range(1, len(self.lantai_list)):
                ok, msg = self.lantai_list[idx].tambah_kendaraan(gol, berat)
                if ok:
                    return f"(Lantai {idx+1}) {msg}"
            ok, msg = self.lantai_list[0].tambah_kendaraan(gol, berat)
            return f"(Lantai 1) {msg}"
        else:
            ok, msg = self.lantai_list[0].tambah_kendaraan(gol, berat)
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

# Streamlit session init
if "kapal" not in st.session_state:
    st.session_state.kapal = None

if "input_lantai" not in st.session_state:
    st.session_state.input_lantai = []

# Sidebar Input
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
    gol = st.sidebar.selectbox("Golongan Kendaraan", list(KENDARAAN.keys()), format_func=lambda x: f"{ROMAWI[x]} (G{x})")
    berat = st.sidebar.number_input("Berat Kendaraan (kg)", min_value=100, max_value=60000, value=3000, step=100)
    if st.sidebar.button("Tambah"):
        hasil = st.session_state.kapal.tambah_kendaraan(gol, berat)
        st.success(hasil)

    st.sidebar.markdown("### ❌ Keluarkan Kendaraan")
    gol_del = st.sidebar.selectbox("Pilih Golongan yang Akan Dikeluarkan", list(KENDARAAN.keys()), format_func=lambda x: f"{ROMAWI[x]} (G{x})")
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
            st.sidebar.write(f"Gol {ROMAWI[g]}: {sisa[g]} unit")

    st.sidebar.markdown("### 📦 Keseimbangan Kapal")
    offset_x, offset_y = st.session_state.kapal.get_center_of_gravity()
    arah_x = "kanan" if offset_x > 0 else "kiri" if offset_x < 0 else "tengah"
    arah_y = "belakang" if offset_y > 0 else "depan" if offset_y < 0 else "tengah"
    st.sidebar.write(f"- Titik Berat Horizontal: {offset_x:+.2f} ({arah_x})")
    st.sidebar.write(f"- Titik Berat Vertikal: {offset_y:+.2f} ({arah_y})")
    if abs(offset_x) < 0.3 and abs(offset_y) < 0.3:
        st.sidebar.success("⚖️ Seimbang")
    else:
        st.sidebar.warning("⚠️ Tidak Seimbang")

    st.divider()
    st.session_state.kapal.visualisasi()
