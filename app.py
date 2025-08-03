import streamlit as st

# Data kendaraan: panjang, berat
KENDARAAN = {
    4: (6, 2),
    5: (7, 3),
    6: (8, 4),
    7: (10, 5),
    8: (12, 6),
    9: (15, 8)
}

WARNA = {
    4: "#FF9999",
    5: "#FFCC99",
    6: "#FFFF99",
    7: "#CCFF99",
    8: "#99FFCC",
    9: "#99CCFF"
}

def romawi(val):
    return {
        4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX"
    }[val]

class LantaiKapal:
    def __init__(self, panjang, lebar):
        self.panjang = panjang
        self.lebar = lebar
        self.grid = [[None for _ in range(panjang)] for _ in range(lebar)]

    def sisa_kapasitas(self):
        return sum(1 for baris in self.grid for cell in baris if cell is None)

    def bisa_muatan(self, golongan):
        panjang, _ = KENDARAAN[golongan]
        for r in range(self.lebar):
            for c in range(self.panjang - panjang + 1):
                if all(self.grid[r][c + i] is None for i in range(panjang)):
                    return True
        return False

    def muat(self, golongan, id_kendaraan):
        panjang, _ = KENDARAAN[golongan]
        for r in range(self.lebar):
            for c in range(self.panjang - panjang + 1):
                if all(self.grid[r][c + i] is None for i in range(panjang)):
                    for i in range(panjang):
                        self.grid[r][c + i] = (golongan, id_kendaraan)
                    return True
        return False

    def total_berat_dan_titik_berat(self):
        total_berat = 0
        total_momen = 0
        for r in range(self.lebar):
            for c in range(self.panjang):
                cell = self.grid[r][c]
                if cell is not None:
                    gol, _ = cell
                    berat = KENDARAAN[gol][1]
                    total_berat += berat
                    total_momen += berat * (c + 0.5)
        if total_berat == 0:
            return 0, 0
        return total_berat, total_momen / total_berat

    def visualisasi(self):
        html_grid = ""
        for baris in self.grid:
            for cell in baris:
                if cell is None:
                    html_grid += f"<div style='width:30px;height:15px;border:1px solid #ccc;display:inline-block'></div>"
                else:
                    gol, _ = cell
                    html_grid += f"<div style='width:30px;height:15px;background:{WARNA[gol]};display:inline-block;text-align:center;font-size:10px;color:white'>{romawi(gol)}</div>"
            html_grid += "<br>"
        return html_grid

class Kapal:
    def __init__(self, list_dimensi):
        self.lantai = [LantaiKapal(p, l) for (p, l) in list_dimensi]
        self.id_kendaraan = 0

    def tambah_kendaraan(self, golongan):
        panjang, berat = KENDARAAN[golongan]
        urutan = range(len(self.lantai)) if golongan < 6 else [0]
        for idx in urutan:
            lantai = self.lantai[idx]
            if lantai.bisa_muatan(golongan):
                self.id_kendaraan += 1
                lantai.muat(golongan, self.id_kendaraan)
                return f"Kendaraan golongan {romawi(golongan)} berhasil dimuat di lantai {idx + 1}"
        return f"Tidak ada ruang untuk kendaraan golongan {romawi(golongan)}"

    def visualisasi(self):
        for i, lantai in enumerate(self.lantai):
            st.markdown(f"### Lantai {i + 1}")
            st.markdown(lantai.visualisasi(), unsafe_allow_html=True)
            berat, titik = lantai.total_berat_dan_titik_berat()
            st.write(f"Total berat: {berat} | Titik berat (X): {titik:.2f} dari {self.lantai[i].panjang}")

# Streamlit app
st.title("Simulasi Pemanfaatan Kapal untuk Kendaraan")

if "kapal" not in st.session_state:
    st.session_state.kapal = None
    st.session_state.input_lantai = []

with st.sidebar:
    st.markdown("## Konfigurasi Kapal")
    panjang = st.number_input("Panjang lantai", min_value=5, max_value=100, value=30)
    lebar = st.number_input("Lebar lantai", min_value=1, max_value=10, value=3)
    if st.button("Tambah Lantai"):
        st.session_state.input_lantai.append((panjang, lebar))

    if st.button("Mulai" ):
        st.session_state.kapal = Kapal(st.session_state.input_lantai)
        st.rerun()

if st.session_state.kapal is not None:
    st.sidebar.markdown("## Tambah Kendaraan")
    gol = st.sidebar.selectbox("Golongan Kendaraan", list(KENDARAAN.keys()), format_func=romawi)
    if st.sidebar.button("Tambah"):
        hasil = st.session_state.kapal.tambah_kendaraan(gol)
        st.success(hasil)

    st.sidebar.markdown("## Sisa Kapasitas Tiap Lantai")
    for i, lantai in enumerate(st.session_state.kapal.lantai):
        sisa = lantai.sisa_kapasitas()
        st.sidebar.write(f"Lantai {i + 1}: {sisa} slot kosong")

    st.header("Visualisasi Kapal")
    st.session_state.kapal.visualisasi()
else:
    st.info("Silakan konfigurasi kapal di sidebar dan klik 'Mulai'")
