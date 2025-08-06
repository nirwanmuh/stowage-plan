import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

st.set_page_config(page_title="Simulasi Muat Kapal", layout="wide")

# Definisi ukuran kendaraan per golongan
KENDARAAN = {
    "IV": (5, 3),
    "V": (7, 3),
    "VI": (10, 3),
    "VII": (12, 3),
    "VIII": (16, 3),
    "IX": (21, 3),
}

BERAT = {
    "IV": 1,
    "V": 8,
    "VI": 12,
    "VII": 15,
    "VIII": 18,
    "IX": 30
}
WARNA = {
    "IV": "lightblue",
    "V": "lightgreen",
    "VI": "orange",
    "VII": "violet",
    "VIII": "salmon",
    "IX": "khaki",
}

# Inisialisasi state
if "kapal" not in st.session_state:
    st.session_state.kapal = None
if "grid" not in st.session_state:
    st.session_state.grid = None
if "kendaraan" not in st.session_state:
    st.session_state.kendaraan = []

# Fungsi: mencari tempat kosong
def cari_lokasi(grid, p, l, berat, tx, ty):
    min_score = float('inf')
    best_pos = (None, None)

    for i in range(grid.shape[0] - l + 1):
        for j in range(grid.shape[1] - p + 1):
            if np.all(grid[i:i + l, j:j + p] == 0):
                cx = j + p / 2
                cy = i + l / 2
                dx = abs(cx - tx)
                dy = abs(cy - ty)
                score = berat * (dx**2 + dy**2)
                if score < min_score:
                    min_score = score
                    best_pos = (i, j)
    return best_pos

#susun ulang kendaraan
def susun_ulang_kendaraan():
    grid = np.zeros_like(st.session_state.grid, dtype=object)
    kapal = st.session_state.kapal
    tx = kapal["titik_seimbang_h"]
    ty = kapal["titik_seimbang_v"]

    kendaraan_baru = []

    # Urutkan dulu agar penyusunan lebih stabil (opsional)
    kendaraan_diurutkan = sorted(
        st.session_state.kendaraan, key=lambda x: -x["berat"]
    )

    for k in kendaraan_diurutkan:
        p, l = k["size"]
        gol = k["gol"]
        berat = k["berat"]

        i, j = cari_lokasi(grid, p, l, berat, tx, ty)
        if i is not None:
            for dx in range(l):
                for dy in range(p):
                    grid[i + dx, j + dy] = gol
            kendaraan_baru.append({
                "gol": gol,
                "pos": (i, j),
                "size": (p, l),
                "berat": berat
            })

    st.session_state.grid = grid
    st.session_state.kendaraan = kendaraan_baru

# Sidebar: konfigurasi kapal
with st.sidebar:
    st.header("Konfigurasi Kapal")
    panjang_kapal = st.number_input("Panjang Kapal (meter)", min_value=1, value=30)
    lebar_kapal = st.number_input("Lebar Kapal (meter)", min_value=1, value=12)
    titik_seimbang = st.number_input(
        "Titik Seimbang Horizontal (meter)",
        min_value=0,
        max_value=panjang_kapal,
        value=panjang_kapal // 2
    ) 
    if st.button("🔄 Buat Ulang Kapal"):
        st.session_state.kapal = {
            "panjang": panjang_kapal,
            "lebar": lebar_kapal,
            "titik_seimbang_h": titik_seimbang,
            "titik_seimbang_v": lebar_kapal / 2  # dihitung otomatis
        }
        st.session_state.grid = np.zeros((lebar_kapal, panjang_kapal), dtype=object)
        st.session_state.kendaraan = []

# Sidebar: tambah kendaraan
with st.sidebar:
    st.header("Tambah Kendaraan")
    golongan = st.selectbox("Golongan", list(KENDARAAN.keys()))
    tambah = st.button("➕ Tambahkan ke Kapal")

    if tambah:
        p, l = KENDARAAN[golongan]
        berat = BERAT[golongan]
        st.session_state.kendaraan.append({
            "gol": golongan,
            "size": (p, l),
            "berat": berat,
            "pos": (0, 0)
        })
        susun_ulang_kendaraan()

# Fungsi: tambahkan kendaraan
def tambah_kendaraan(golongan, berat_manual=None):
    kendaraan_baru = {
        "golongan": golongan,
        "ukuran": KENDARAAN[golongan],
        "berat": berat_manual if berat_manual is not None else BERAT_KENDARAAN[golongan],
    }

    # Gabungkan semua kendaraan yang sudah ada + yang baru
    semua_kendaraan = st.session_state.kendaraan_list + [kendaraan_baru]

    # Coba semua kombinasi penyusunan ulang
    hasil_terbaik = None
    sisa_ruang_terbanyak = -1
    keseimbangan_terbaik = float('inf')

    # Reset kapal
    st.session_state.kapal.reset_kapal()

    # Coba semua permutasi penyusunan ulang
    from itertools import permutations
    for urutan in permutations(semua_kendaraan):
        kapal_temp = st.session_state.kapal.copy()
        gagal = False
        for k in urutan:
            if not kapal_temp.tambah_kendaraan_otomatis(k):
                gagal = True
                break
        if not gagal:
            # Hitung sisa ruang + keseimbangan
            sisa_ruang = kapal_temp.total_sisa_grid()
            keseimbangan = kapal_temp.hitung_titik_berat()

            if hasil_terbaik is None or sisa_ruang > sisa_ruang_terbanyak or (
                sisa_ruang == sisa_ruang_terbanyak and keseimbangan < keseimbangan_terbaik
            ):
                hasil_terbaik = kapal_temp
                sisa_ruang_terbanyak = sisa_ruang
                keseimbangan_terbaik = keseimbangan

    # Simpan hasil terbaik jika ada
    if hasil_terbaik:
        st.session_state.kapal = hasil_terbaik
        st.session_state.kendaraan_list = semua_kendaraan
        st.success("Kendaraan berhasil dimuat dengan penataan ulang.")
    else:
        st.error("Kendaraan tidak bisa dimuat meskipun dengan penataan ulang.")

# Fungsi: tampilkan grid
def tampilkan_grid(grid):
    rows, cols = grid.shape
    fig, ax = plt.subplots(figsize=(cols / 2, rows / 2 + 1))
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_xticks(np.arange(0, cols + 1, 1))
    ax.set_yticks(np.arange(0, rows + 1, 1))
    ax.grid(True)

    # Gambar kendaraan sebagai satu kotak besar per kendaraan
    for kendaraan in st.session_state.kendaraan:
        gol = kendaraan['gol']
        i, j = kendaraan['pos']
        p, l = kendaraan['size']
        # Rectangle dari pojok kiri bawah, jadi ubah baris ke koordinat matplotlib
        y = rows - i - l
        rect = Rectangle(
            (j, y), p, l,
            facecolor=WARNA.get(gol, "gray"),
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(rect)
        ax.text(j + p/2, y + l/2, gol, ha="center", va="center", fontsize=10, weight="bold")

    # Garis vertikal titik seimbang horizontal
    if st.session_state.kapal and "titik_seimbang_h" in st.session_state.kapal:
        x_seimbang = st.session_state.kapal["titik_seimbang_h"]
        ax.axvline(x=x_seimbang, color="red", linestyle="--", linewidth=1.5)
        ax.text(x_seimbang, rows + 0.3, "Titik Seimbang (Depan-Belakang)", color="red", fontsize=8, ha="center")

    # Garis horizontal titik seimbang vertikal
    if "titik_seimbang_v" in st.session_state.kapal:
        y_seimbang = st.session_state.kapal["titik_seimbang_v"]
        ax.axhline(y=rows - y_seimbang, color="red", linestyle="--", linewidth=1.5)
        ax.text(cols + 0.2, rows - y_seimbang, "Titik Seimbang (Kiri-Kanan)", color="red", fontsize=8, va="center", rotation=90)

    # Label depan dan belakang
    ax.text(0, -0.8, "⬅️ Depan", ha="left", va="center", fontsize=10, weight="bold")
    ax.text(cols, -0.8, "Belakang ➡️", ha="right", va="center", fontsize=10, weight="bold")

    ax.set_aspect('equal')
    st.pyplot(fig)

# Fungsi: hitung sisa ruang dan kemungkinan kendaraan
def hitung_sisa_dan_kemungkinan(grid):
    sisa_kosong = np.sum(grid == 0)
    luas_tersisa = sisa_kosong * 1  # 1m x 1m
    kemungkinan = {}
    for gol, (p, l) in KENDARAAN.items():
        luas_kendaraan = p * l
        muat = luas_tersisa // luas_kendaraan
        kemungkinan[gol] = int(muat)
    return luas_tersisa, kemungkinan

# Hitung momen total saat ini
def hitung_total_momen():
    kapal = st.session_state.kapal
    titik_seimbang_x = kapal["titik_seimbang_h"]
    titik_seimbang_y = kapal["titik_seimbang_v"]
    total_momen_x = 0
    total_momen_y = 0

    for k in st.session_state.kendaraan:
        i, j = k["pos"]
        p, l = k["size"]
        berat = k["berat"]
        cx = j + p / 2
        cy = i + l / 2
        total_momen_x += berat * (cx - titik_seimbang_x)
        total_momen_y += berat * (cy - titik_seimbang_y)

    return total_momen_x, total_momen_y

# Tampilan utama
st.title("🚢 Simulasi Kapasitas Muat Kapal")
if st.session_state.kapal:
    st.subheader("Visualisasi Muatan Kapal")
    tampilkan_grid(st.session_state.grid)

    st.subheader("Sisa Kapasitas & Kemungkinan Muat")
    sisa, kemungkinan = hitung_sisa_dan_kemungkinan(st.session_state.grid)
    st.write(f"**Sisa luas ruang kosong:** {sisa} m²")
    st.table([{"Golongan": gol, "Masih Bisa Muat": jumlah} for gol, jumlah in kemungkinan.items()])

    st.subheader("Daftar Kendaraan Saat Ini")
    if st.session_state.kendaraan:
        for idx, k in enumerate(st.session_state.kendaraan, 1):
            st.write(f"{idx}. Golongan {k['gol']} di posisi {k['pos']} ukuran {k['size']}")
    else:
        st.info("Belum ada kendaraan di kapal.")

    total_mx, total_my = hitung_total_momen()
    st.subheader("🔧 Total Momen Saat Ini")
    st.write(f"Momen Horizontal (Depan–Belakang): **{total_mx:.2f}**")
    st.write(f"Momen Vertikal (Kiri–Kanan): **{total_my:.2f}**")
    
    if abs(total_mx) < 1 and abs(total_my) < 1:
        st.success("✅ Kapal dalam keadaan seimbang.")
    else:
        st.warning("⚠️ Kapal belum seimbang.")
else:
    st.info("Silakan buat kapal terlebih dahulu melalui sidebar.")
