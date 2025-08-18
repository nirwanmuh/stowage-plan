import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import math
import random

st.set_page_config(page_title="Stowage Plan", layout="wide")

# ======= Konfigurasi kendaraan (dim dalam m, berat dalam ton) =======
KENDARAAN = {
    "IV": {"dim": (5.0, 3.0), "berat": 1.0},
    "V": {"dim": (7.0, 3.0), "berat": 8.0},
    "VI": {"dim": (10.0, 3.0), "berat": 12.0},
    "VII": {"dim": (12.0, 3.0), "berat": 15.0},
    "VIII": {"dim": (16.0, 3.0), "berat": 18.0},
    "IX": {"dim": (21.0, 3.0), "berat": 30.0},
}

WARNA_GOLONGAN = {
    "IV": "skyblue",
    "V": "lightgreen",
    "VI": "khaki",
    "VII": "salmon",
    "VIII": "plum",
    "IX": "lightcoral"
}
# ======= Session state =======
if "kendaraan" not in st.session_state:
    st.session_state.kendaraan = []  # list of golongan strings

# ======= Sidebar input =======
st.sidebar.header("Konfigurasi Kapal")
panjang_kapal = st.sidebar.number_input("Panjang Kapal (m)", min_value=10.0, value=50.0, step=0.1, format="%.1f")
lebar_kapal = st.sidebar.number_input("Lebar Kapal (m)", min_value=3.0, value=15.0, step=0.1, format="%.1f")

st.sidebar.header("Titik Seimbang")
titik_seimbang_vertikal = st.sidebar.number_input(
    "Titik Seimbang Vertikal (m, dari buritan)",
    min_value=0.0,
    max_value=float(panjang_kapal),
    value=float(panjang_kapal / 2.0),
    step=0.1,
    format="%.2f"
)
titik_seimbang_horizontal = lebar_kapal / 2.0  # otomatis

st.sidebar.header("Tambah Kendaraan")
pilih_gol = st.sidebar.selectbox("Pilih Golongan", list(KENDARAAN.keys()))

# ======= Helper functions =======
def compute_cm(placements):
    total_mass = 0.0
    mx = 0.0
    my = 0.0
    for gol, x, y in placements:
        m = KENDARAAN[gol]["berat"]
        pjg, lbr = KENDARAAN[gol]["dim"]
        cx = x + pjg / 2.0
        cy = y + lbr / 2.0
        mx += cx * m
        my += cy * m
        total_mass += m
    if total_mass > 0:
        return total_mass, mx / total_mass, my / total_mass
    else:
        return 0.0, 0.0, 0.0

def has_overlap(placements, eps=1e-9):
    n = len(placements)
    for i in range(n):
        gol1, x1, y1 = placements[i]
        w1, h1 = KENDARAAN[gol1]["dim"]
        for j in range(i+1, n):
            gol2, x2, y2 = placements[j]
            w2, h2 = KENDARAAN[gol2]["dim"]
            if not (x1 + w1 <= x2 + eps or x2 + w2 <= x1 + eps or y1 + h1 <= y2 + eps or y2 + h2 <= y1 + eps):
                return True
    return False

def validate_placements(placements, panjang, lebar, expected_count):
    if len(placements) != expected_count:
        return False, "tidak semua kendaraan dapat ditempatkan"
    for gol, x, y in placements:
        pjg, lbr = KENDARAAN[gol]["dim"]
        if x < -1e-6 or y < -1e-6 or (x + pjg) > panjang + 1e-6 or (y + lbr) > lebar + 1e-6:
            return False, "beberapa kendaraan keluar batas kapal"
    if has_overlap(placements):
        return False, "terdapat tumpang tindih kendaraan"
    return True, None

def arrange_balance_xy_optimal(gol_list, panjang_kapal, lebar_kapal, x_target, y_target, luas_kapal=None):
    # Hitung luas_kapal otomatis jika tidak dikirim oleh pemanggil
    if luas_kapal is None:
        luas_kapal = panjang_kapal * lebar_kapal

    placements = []
    if not gol_list:
        return placements

    # total area semua kendaraan (dipakai untuk cek sisa luas awal)
    luas_terpakai = sum(KENDARAAN[g]["dim"][0] * KENDARAAN[g]["dim"][1] for g in gol_list)
    sisa_luas = luas_kapal - luas_terpakai

    # urutkan dari yang terbesar biar penempelan lebih rapat
    sorted_gols = sorted(gol_list, key=lambda g: -(KENDARAAN[g]["dim"][0] * KENDARAAN[g]["dim"][1]))

    for gol in sorted_gols:
        pjg, lbr = KENDARAAN[gol]["dim"]
        best_choice = None
        best_score = float("inf")

        candidate_positions = []

        if not placements:
            # kendaraan pertama → letakkan mendekati target
            candidate_positions.append((max(0, x_target - pjg/2), max(0, y_target - lbr/2)))
        else:
            # aturan 1: sisa luas > 50% → tempel ke kendaraan lain
            if sisa_luas > 0.5 * luas_kapal:
                for g2, x2, y2 in placements:
                    pjg2, lbr2 = KENDARAAN[g2]["dim"]
                    # nempel kanan sejajar bawah
                    candidate_positions.append((x2 + pjg2, y2))
                    # nempel kanan sejajar atas
                    candidate_positions.append((x2 + pjg2, y2 + lbr2 - lbr))
                    
                    # nempel kiri sejajar bawah
                    candidate_positions.append((x2 - pjg, y2))
                    # nempel kiri sejajar atas
                    candidate_positions.append((x2 - pjg, y2 + lbr2 - lbr))
                    
                    # nempel depan sejajar kiri
                    candidate_positions.append((x2, y2 + lbr2))
                    # nempel depan sejajar kanan
                    candidate_positions.append((x2 + pjg2 - pjg, y2 + lbr2))
                    
                    # nempel belakang sejajar kiri
                    candidate_positions.append((x2, y2 - lbr))
                    # nempel belakang sejajar kanan
                    candidate_positions.append((x2 + pjg2 - pjg, y2 - lbr))

            else:
                # aturan 2: sisa luas < 50% → mulai dari belakang (x=0), scan y
                step_y = max(1, int(lbr))  # jaga jangan 0
                for y_try in range(0, max(1, int(lebar_kapal - lbr)) + 1, step_y):
                    candidate_positions.append((0, y_try))

        # evaluasi kandidat
        for x_try, y_try in candidate_positions:
            tmp = placements.copy()
            tmp.append((gol, x_try, y_try))
            valid, _ = validate_placements(tmp, panjang_kapal, lebar_kapal, len(tmp))
            if not valid:
                continue
            _, xcm, ycm = compute_cm(tmp)
            score = math.hypot(xcm - x_target, ycm - y_target)
            if score < best_score:
                best_score = score
                best_choice = (gol, x_try, y_try)

        if best_choice:
            placements.append(best_choice)

    return placements
arrange_balance_xy = arrange_balance_xy_optimal

def optimize_positions(placements, panjang_kapal, lebar_kapal, x_target, y_target, max_iter=500, step=0.5):
    """Optimasi posisi kendaraan dengan simulated annealing sederhana."""
    if not placements:
        return placements
    
    best = placements.copy()
    best_mass, best_xcm, best_ycm = compute_cm(best)
    best_score = (best_xcm - x_target)**2 + (best_ycm - y_target)**2
    
    current = best.copy()
    current_score = best_score
    
    T = 1.0  # temperatur awal
    cooling = 0.995  # faktor pendinginan
    
    for _ in range(max_iter):
        # pilih kendaraan acak
        idx = random.randrange(len(current))
        gol, x, y = current[idx]
        pjg, lbr = KENDARAAN[gol]["dim"]
        
        # geser posisi acak kecil
        new_x = min(max(0.0, x + random.uniform(-step, step)), panjang_kapal - pjg)
        new_y = min(max(0.0, y + random.uniform(-step, step)), lebar_kapal - lbr)
        
        candidate = current.copy()
        candidate[idx] = (gol, new_x, new_y)
        
        if has_overlap(candidate):
            continue  # skip kalau tabrakan
        
        _, xcm, ycm = compute_cm(candidate)
        score = (xcm - x_target)**2 + (ycm - y_target)**2
        
        # kriteria penerimaan (SA)
        if score < current_score or random.random() < math.exp((current_score - score) / max(T,1e-6)):
            current = candidate
            current_score = score
            
            if score < best_score:
                best = candidate
                best_score = score
        
        T *= cooling  # turunkan temperatur
    
    return best

def repack_with_shuffle(gol_list, n_try=20):
    for _ in range(n_try):
        random.shuffle(gol_list)
        placements = arrange_balance_xy(gol_list, panjang_kapal, lebar_kapal,
                                        titik_seimbang_vertikal, titik_seimbang_horizontal)
        ok, _ = validate_placements(placements, panjang_kapal, lebar_kapal, len(gol_list))
        if ok:
            return placements
    return []


# ======= Add vehicle handler =======
if st.sidebar.button("Tambah Kendaraan"):
    # Ambil semua kendaraan lama + yang baru
    candidate_list = st.session_state.kendaraan + [pilih_gol]

    # Susun ulang semuanya dari nol
    candidate_placements = arrange_balance_xy(candidate_list, panjang_kapal, lebar_kapal,
                                          titik_seimbang_vertikal, titik_seimbang_horizontal)

    ok, reason = validate_placements(candidate_placements, panjang_kapal, lebar_kapal, len(candidate_list))
    
    # kalau gagal → coba optimasi penuh
    if not ok:
        candidate_placements = arrange_balance_xy(candidate_list, panjang_kapal, lebar_kapal,
                                                  titik_seimbang_vertikal, titik_seimbang_horizontal)
        candidate_placements = optimize_positions(candidate_placements, panjang_kapal, lebar_kapal,
                                                  titik_seimbang_vertikal, titik_seimbang_horizontal,
                                                  max_iter=5000, step=0.5)

    # Validasi hasil
    ok, reason = validate_placements(candidate_placements, panjang_kapal, lebar_kapal, len(candidate_list))
    if ok:
        # Simpan daftar kendaraan (bukan posisi, supaya selalu bisa re-arrange total)
        st.session_state.kendaraan = candidate_list
        st.success(f"Berhasil menambahkan golongan {pilih_gol}")
    else:
        st.error(f"Tidak bisa menambahkan golongan {pilih_gol}")
        st.write(f"*Alasan: {reason}*")


if st.sidebar.button("Reset Kendaraan"):
    st.session_state.kendaraan = []
    st.success("Daftar kendaraan dikosongkan")

# ======= Arrange current kendaraan =======
placements = arrange_balance_xy(st.session_state.kendaraan, panjang_kapal, lebar_kapal,
                                titik_seimbang_vertikal, titik_seimbang_horizontal)

# optimasi tambahan
placements = optimize_positions(
    placements, panjang_kapal, lebar_kapal,
    titik_seimbang_vertikal, titik_seimbang_horizontal,
    max_iter=10000, step=2.0
)



# compute stats
luas_terpakai = sum(KENDARAAN[gol]["dim"][0] * KENDARAAN[gol]["dim"][1] for gol, _, _ in placements)
luas_kapal = panjang_kapal * lebar_kapal
sisa_luas = luas_kapal - luas_terpakai
total_berat, x_cm, y_cm = compute_cm(placements)
selisih_vertikal = x_cm - titik_seimbang_vertikal
selisih_horizontal = y_cm - titik_seimbang_horizontal
dist_to_target = math.hypot(selisih_vertikal, selisih_horizontal) if total_berat > 0 else 0.0

# ======= UI output =======
st.title("Stowage Plan")

# ======= Visualisasi =======
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_xlim(0, panjang_kapal)
ax.set_ylim(0, lebar_kapal)
ax.set_aspect('equal')
ax.set_title("Visualisasi Stowage Plan")

# Outline kapal
kapal_outline = Rectangle((0, 0), panjang_kapal, lebar_kapal,
                          linewidth=1.5, edgecolor='black', facecolor='none')
ax.add_patch(kapal_outline)

# Label orientasi kapal
ax.text(0, lebar_kapal+1, "Belakang", ha='left', va='center', fontsize=10, fontweight='bold')
ax.text(panjang_kapal, lebar_kapal+1, "Depan", ha='right', va='center', fontsize=10, fontweight='bold')
ax.text(panjang_kapal+1, 0, "Kanan", ha='center', va='bottom', rotation=270, fontsize=10, fontweight='bold')
ax.text(panjang_kapal+1, lebar_kapal, "Kiri", ha='center', va='top', rotation=270, fontsize=10, fontweight='bold')

# Gambar kendaraan
for gol, x, y in placements:
    pjg, lbr = KENDARAAN[gol]["dim"]
    berat = KENDARAAN[gol]["berat"]
    warna = WARNA_GOLONGAN.get(gol, "gray")
    rect = Rectangle((x, y), pjg, lbr, linewidth=1.2,
                     edgecolor='black', facecolor=warna, alpha=0.6, label=f"Golongan {gol}")
    ax.add_patch(rect)
    ax.text(x + pjg / 2.0, y + lbr / 2.0, f"{gol}\n{berat}t",
            ha='center', va='center', fontsize=8, color='black')

# Titik berat
if total_berat > 0:
    ax.plot(x_cm, y_cm, 'rx', markersize=10, label="Titik Berat Muatan")

# Garis seimbang
ax.axvline(titik_seimbang_vertikal, color='green', linestyle='--', label="Titik Seimbang Vertikal")
ax.axhline(titik_seimbang_horizontal, color='orange', linestyle='--', label="Titik Seimbang Horizontal")

# Legend di bawah grafik
handles, labels = ax.get_legend_handles_labels()
by_label = dict(zip(labels, handles))  # Hilangkan duplikat
ax.legend(by_label.values(), by_label.keys(),
          loc='upper center', bbox_to_anchor=(0.5, -0.1),
          ncol=4)

st.pyplot(fig)

# ======= Ringkasan & Daftar =======
col1, col2 = st.columns([1.0, 1.0])
with col1:
    st.subheader("Ringkasan Muatan")
    st.write(f"- Panjang kapal: **{panjang_kapal:.2f} m**")
    st.write(f"- Lebar kapal: **{lebar_kapal:.2f} m**")
    st.write(f"- Titik seimbang vertikal (target): **{titik_seimbang_vertikal:.2f} m**")
    st.write(f"- Titik seimbang horizontal (target): **{titik_seimbang_horizontal:.2f} m**")
    st.write(f"- Jumlah kendaraan: **{len(st.session_state.kendaraan)}**")
    st.write(f"- Luas kapal: **{luas_kapal:.2f} m²**")
    st.write(f"- Luas terpakai: **{luas_terpakai:.2f} m²**")
    st.write(f"- Sisa luas: **{sisa_luas:.2f} m²**")
    st.write(f"- Total berat muatan: **{total_berat:.2f} ton**")
    st.write(f"- Titik berat muatan (x,y): **({x_cm:.2f} m, {y_cm:.2f} m)**")
    st.write(f"- Selisih vertikal: **{selisih_vertikal:.2f} m**")
    st.write(f"- Selisih horizontal: **{selisih_horizontal:.2f} m**")
    st.write(f"- Jarak pusat massa → target: **{dist_to_target:.3f} m**")

with col2:
    st.subheader("Daftar Kendaraan & Posisi")
    if placements:
        table = []
        for idx, (gol, x, y) in enumerate(placements, start=1):
            pjg, lbr = KENDARAAN[gol]["dim"]
            berat = KENDARAAN[gol]["berat"]
            table.append({"#": idx, "Gol": gol, "x (m)": round(x, 2), "y (m)": round(y, 2),
                          "p (m)": pjg, "l (m)": lbr, "berat (t)": berat})
        st.table(table)
    else:
        st.write("Belum ada kendaraan.")
