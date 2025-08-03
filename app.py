import streamlit as st

st.set_page_config(page_title="Simulasi Muatan Kapal", layout="wide")
st.title("Simulasi Muatan Kendaraan dalam Kapal")

KENDARAAN = {
    4: 5,
    5: 7,
    6: 10,
    7: 12,
    8: 15,
    9: 18
}
ROMAWI = {
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX"
}
WARNA = ["#FFCCCC", "#CCFFCC", "#CCCCFF", "#FFFFCC", "#CCFFFF", "#FFCCFF"]

class LantaiKapal:
    def __init__(self, panjang, slot_count):
        self.panjang = panjang
        self.slot_count = slot_count
        self.grid = [[None for _ in range(slot_count)] for _ in range(panjang)]

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

    def visualisasi(self, lantai_ke):
        st.markdown(f"### Lantai {lantai_ke+1}")
        for row in self.grid:
            cols = st.columns(len(row))
            for i, cell in enumerate(row):
                with cols[i]:
                    if cell:
                        label, _ = cell
                        warna = WARNA[hash(label) % len(WARNA)]
                        st.markdown(f"<div style='background-color:{warna};padding:10px;text-align:center;border-radius:5px'>{label}</div>", unsafe_allow_html=True)
                    else:
                        st.empty()

class Kapal:
    def __init__(self, ukuran_lantai):
        self.lantai_list = [LantaiKapal(panjang, slot) for panjang, slot in ukuran_lantai]

    def tambah_kendaraan(self, gol, berat):
        lantai_prioritas = list(range(1, len(self.lantai_list))) + [0] if gol in [4, 5] else [0]
        for idx in lantai_prioritas:
            posisi = self.lantai_list[idx].cari_posisi_optimal(gol, berat)
            if posisi:
                i, start_row = posisi
                label = f"G{ROMAWI[gol]}"
                for j in range(KENDARAAN[gol]):
                    self.lantai_list[idx].grid[start_row + j][i] = (label, berat)
                return f"Lantai {idx+1} Slot {i+1}"
        return "Tidak cukup ruang"

    def get_center_of_gravity(self):
        total_berat = 0
        total_x_moment = 0
        total_y_moment = 0
        total_slot = 0
        total_panjang = 0
        for lantai in self.lantai_list:
            total_slot = max(total_slot, lantai.slot_count)
            total_panjang = max(total_panjang, lantai.panjang)
            for y in range(lantai.panjang):
                for x in range(lantai.slot_count):
                    cell = lantai.grid[y][x]
                    if cell:
                        _, berat = cell
                        total_berat += berat
                        total_x_moment += (x + 0.5) * berat
                        total_y_moment += (y + 0.5) * berat
        if total_berat == 0:
            return 0.0, 0.0
        ref_x = total_slot / 2
        ref_y = total_panjang / 2
        cog_x = total_x_moment / total_berat
        cog_y = total_y_moment / total_berat
        offset_x = (cog_x - ref_x) / ref_x
        offset_y = (cog_y - ref_y) / ref_y
        return offset_x, offset_y

    def visualisasi(self):
        for idx, lantai in enumerate(self.lantai_list):
            lantai.visualisasi(idx)

# UI Streamlit
if 'kapal' not in st.session_state:
    st.session_state.kapal = Kapal([(10, 6), (10, 6)])  # Contoh dua lantai dengan panjang 10 dan lebar 6

with st.sidebar:
    st.header("Input Kendaraan")
    gol = st.selectbox("Golongan", list(ROMAWI.keys()), format_func=lambda x: f"{ROMAWI[x]} (Gol {x})")
    berat = st.number_input("Berat (ton)", min_value=1.0, step=0.1)
    if st.button("Tambah Kendaraan"):
        hasil = st.session_state.kapal.tambah_kendaraan(gol, berat)
        st.success(hasil)

    st.header("Keseimbangan")
    offset_x, offset_y = st.session_state.kapal.get_center_of_gravity()
    st.metric("Offset Horizontal", f"{offset_x:+.2%}")
    st.metric("Offset Vertikal", f"{offset_y:+.2%}")

st.session_state.kapal.visualisasi()
