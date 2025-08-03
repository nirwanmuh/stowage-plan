import streamlit as st

st.set_page_config(page_title="Simulasi Muatan Kapal", layout="wide")

st.sidebar.title("Input Kapal & Kendaraan")

# Input konfigurasi lantai
if "kapal_initiated" not in st.session_state:
    st.session_state.lantai_defs = []
    st.session_state.kapal_initiated = False

lantai_count = st.sidebar.number_input("Jumlah lantai kapal", min_value=1, max_value=5, value=2, step=1)
for i in range(lantai_count):
    panjang = st.sidebar.number_input(f"Panjang lantai {i+1}", min_value=5, max_value=100, value=30, step=1, key=f"p_{i}")
    lebar = st.sidebar.number_input(f"Lebar lantai {i+1}", min_value=3, max_value=30, value=9, step=3, key=f"l_{i}")
    if i >= len(st.session_state.lantai_defs):
        st.session_state.lantai_defs.append((panjang, lebar))
    else:
        st.session_state.lantai_defs[i] = (panjang, lebar)

if st.sidebar.button("Inisialisasi Kapal"):
    st.session_state.kapal = Kapal(st.session_state.lantai_defs)
    st.session_state.kapal_initiated = True
    st.success("Kapal berhasil diinisialisasi ulang!")

if st.session_state.kapal_initiated:
    # Input kendaraan
    golongan_input = st.sidebar.selectbox("Pilih Golongan Kendaraan", options=list(ROMAWI.keys()), format_func=lambda x: f"Golongan {ROMAWI[x]}")
    if st.sidebar.button("Tambahkan Kendaraan"):
        hasil = st.session_state.kapal.tambah_kendaraan(golongan_input)
        st.sidebar.success(hasil)

    if st.sidebar.button("Keluarkan Kendaraan"):
        ok, pesan = st.session_state.kapal.keluarkan_kendaraan(golongan_input)
        if ok:
            st.sidebar.success(pesan)
        else:
            st.sidebar.warning(pesan)

    st.sidebar.divider()
    with st.sidebar.expander("Sisa Kapasitas Tiap Lantai"):
        for i, lantai in enumerate(st.session_state.kapal.lantai_list):
            sisa = lantai.get_kemungkinan_sisa()
            st.write(f"Lantai {i+1}:")
            for gol, jum in sisa.items():
                st.write(f" - Golongan {ROMAWI[gol]}: {jum} kendaraan")

    # Visualisasi
    st.session_state.kapal.visualisasi()
else:
    st.warning("Silakan inisialisasi kapal terlebih dahulu di sidebar.")
