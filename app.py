import streamlit as st
import math

# Konstanta ukuran kendaraan (panjang, lebar)
KENDARAAN = {
    "IV": (5, 3),
    "V": (7, 3),
    "VI": (10, 3),
    "VII": (12, 3),
    "VIII": (16, 3),
    "IX": (21, 3)
}

# Emoji kendaraan untuk visualisasi
EMOJI = {
    "IV": "🚗",
    "V": "🚙",
    "VI": "🚐",
    "VII": "🚚",
    "VIII": "🛻",
    "IX": "🚛"
}

st.set_page_config(page_title="Simulasi Muatan Kapal", layout="wide")
st.title("🚢 Simulasi Kapasitas Muat Kapal")

# Inisialisasi session state
if "kendaraan_manual" not in st.session_state:
    st.session_state.kendaraan_manual = []

kapal_panjang = st.number_input("Masukkan panjang kapal (meter)", min_value=1, value=50)
kapal_lebar = st.number_input("Masukkan lebar kapal (meter)", min_value=1, value=9)

blok_lebar = 3
slot_lebar = kapal_lebar // blok_lebar
slot_panjang = kapal_panjang

st.divider()
st.subheader("➕ Tambah Kendaraan Manual")
col1, col2 = st.columns(2)
with col1:
    jenis = st.selectbox("Pilih golongan kendaraan", list(KENDARAAN.keys()))
with col2:
    if st.button("Tambah Kendaraan"):
        st.session_state.kendaraan_manual.append(jenis)

if st.button("🔄 Reset Semua Kendaraan"):
    st.session_state.kendaraan_manual = []

st.write(f"Total kendaraan manual: {len(st.session_state.kendaraan_manual)}")
st.write("Daftar kendaraan manual:", st.session_state.kendaraan_manual)

# Fungsi kombinasi optimal (seperti sebelumnya)
def kombinasi_optimal(panjang_kapal):
    dp = [0] * (panjang_kapal + 1)
    backtrack = [None] * (panjang_kapal + 1)

    for i in range(1, panjang_kapal + 1):
        for gol, (pj, _) in KENDARAAN.items():
            if i >= pj:
                if dp[i] < dp[i - pj] + 1:
                    dp[i] = dp[i - pj] + 1
                    backtrack[i] = gol

    hasil = []
    i = panjang_kapal
    while i > 0 and backtrack[i]:
        gol = backtrack[i]
        pj, _ = KENDARAAN[gol]
        hasil.append(gol)
        i -= pj
    return hasil[::-1]

# Visual grid dan isi kendaraan
kapal_grid = [[] for _ in range(int(slot_lebar))]

# 1. Isi dengan kendaraan manual
manual_queue = st.session_state.kendaraan_manual.copy()
for jalur in kapal_grid:
    panjang_tersisa = slot_panjang
    while manual_queue:
        gol = manual_queue[0]
        pj, _ = KENDARAAN[gol]
        if panjang_tersisa >= pj:
            jalur.append(gol)
            panjang_tersisa -= pj
            manual_queue.pop(0)
        else:
            break

# 2. Tambahkan sisanya dari kombinasi optimal
for jalur in kapal_grid:
    panjang_tersisa = slot_panjang - sum(KENDARAAN[gol][0] for gol in jalur)
    tambahan = kombinasi_optimal(panjang_tersisa)
    jalur.extend(tambahan)

# Hitung statistik
from collections import Counter
total_counter = Counter()
for jalur in kapal_grid:
    total_counter.update(jalur)

total_area_kapal = kapal_panjang * kapal_lebar
total_area_terpakai = sum(
    count * KENDARAAN[gol][0] * KENDARAAN[gol][1] for gol, count in total_counter.items()
)
sisa_area = total_area_kapal - total_area_terpakai

st.divider()
st.subheader("📊 Hasil Simulasi Muatan")

for gol in sorted(total_counter):
    st.write(f"- Golongan {gol}: {total_counter[gol]} unit")

st.write(f"### Total area terpakai: {total_area_terpakai} m²")
st.write(f"### Sisa area: {sisa_area} m² dari {total_area_kapal} m²")

# Visualisasi Grid
st.divider()
st.subheader("🧱 Visualisasi Muatan Kapal per Jalur (dari depan ke belakang)")

cols = st.columns(int(slot_lebar))
for idx, col in enumerate(cols):
    with col:
        st.markdown(f"**Jalur {idx+1}**")
        for gol in kapal_grid[idx]:
            st.markdown(f"{EMOJI.get(gol, '📦')} Gol {gol}")

