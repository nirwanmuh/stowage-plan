import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

st.set_page_config(page_title="Simulasi Muat Kapal (Balance Packing)", layout="wide")

# ======= Konfigurasi kendaraan (dim dalam m, berat dalam ton) =======
KENDARAAN = {
    "IV": {"dim": (5.0, 3.0), "berat": 1.0},
    "V": {"dim": (7.0, 3.0), "berat": 8.0},
    "VI": {"dim": (10.0, 3.0), "berat": 12.0},
    "VII": {"dim": (12.0, 3.0), "berat": 15.0},
    "VIII": {"dim": (16.0, 3.0), "berat": 18.0},
    "IX": {"dim": (21.0, 3.0), "berat": 30.0},
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
    min_value=0.0, max_value=float(panjang_kapal), value=float(panjang_kapal / 2), step=0.1, format="%.2f"
)
titik_seimbang_horizontal = lebar_kapal / 2.0  # otomatis

st.sidebar.header("Tambah Kendaraan")
pilih_gol = st.sidebar.selectbox("Pilih Golongan", list(KENDARAAN.keys()))
if st.sidebar.button("Tambah Kendaraan"):
    st.session_state.kendaraan.append(pilih_gol)

if st.sidebar.button("Reset Kendaraan"):
    st.session_state.kendaraan = []

# ======= Fungsi penataan untuk menjaga titik berat mendekati target =======
def arrange_to_balance(gol_list, panjang_kapal, lebar_kapal, x_target):
    """
    Heuristik penataan:
    - sort by weight desc
    - buat beberapa baris berdasarkan lebar kendaraan minimal
    - assign each vehicle to the row with smallest total mass (to balance vertically)
    - within row, place vehicles alternating left/right around x_target (centered packing)
    - shift whole layout if goes out of bounds, fallback to greedy packing if necessary
    """
    if not gol_list:
        return []

    # parameters
    min_row_height = min(KENDARAAN[g]["dim"][1] for g in KENDARAAN)  # typically 3.0
    n_rows = max(1, int(lebar_kapal // min_row_height))
    # if rounding leaves small leftover, still ok; we'll compute y positions centered
    row_height = min_row_height

    # create rows with data: placed (list), total_mass
    rows = [{"placed": [], "mass": 0.0, "left_cursor": x_target, "right_cursor": x_target, "toggle": 0} for _ in range(n_rows)]

    # sort vehicles by weight descending
    sorted_gols = sorted(gol_list, key=lambda g: -KENDARAAN[g]["berat"])

    # assign each vehicle to the row with smallest mass (to spread vertically)
    for gol in sorted_gols:
        # pick row index with minimal total mass
        row_idx = min(range(n_rows), key=lambda i: rows[i]["mass"])
        rows[row_idx]["placed"].append(gol)
        rows[row_idx]["mass"] += KENDARAAN[gol]["berat"]

    # compute row y positions so rows are centered vertically
    total_rows_height = n_rows * row_height
    start_y = max(0.0, (lebar_kapal - total_rows_height) / 2.0)  # bottom y of first row
    row_ys = [start_y + i * row_height for i in range(n_rows)]

    placements = []  # list of (gol, x, y)

    # within each row, place vehicles around x_target alternating sides
    for i, row in enumerate(rows):
        y = row_ys[i]
        # start cursors at x_target
        left_cursor = x_target
        right_cursor = x_target
        toggle = 0
        for gol in row["placed"]:
            pjg, lbr = KENDARAAN[gol]["dim"]
            # alternate: first place at center-right, then center-left, etc. 
            # But to avoid overlap, place left by subtracting pjg
            if toggle % 2 == 0:
                # place to the right
                x = right_cursor
                right_cursor = right_cursor + pjg
            else:
                # place to the left
                x = left_cursor - pjg
                left_cursor = x
            toggle += 1
            placements.append((gol, float(x), float(y)))
        # store cursors (not used further)

    # after placements compute bounding box and shift to fit inside ship
    xs = [x for (_, x, _) in placements] + [x + KENDARAAN[gol]["dim"][0] for (gol, x, _) in placements]
    if xs:
        min_x = min(xs)
        max_x = max(xs)
    else:
        min_x, max_x = 0.0, 0.0

    shift = 0.0
    if min_x < 0.0:
        shift = -min_x
    elif max_x > panjang_kapal:
        shift = -(max_x - panjang_kapal)

    if shift != 0.0:
        placements = [(gol, x + shift, y) for (gol, x, y) in placements]

    # if after shift anything still outside bounds, fallback greedy packing (left-to-right)
    xs2 = [x for (_, x, _) in placements] + [x + KENDARAAN[gol]["dim"][0] for (gol, x, _) in placements]
    if xs2 and (min(xs2) < -1e-6 or max(xs2) > panjang_kapal + 1e-6):
        # fallback: fill row by row left->right starting x=0
        placements = []
        for i, row in enumerate(rows):
            y = row_ys[i]
            x_cursor = 0.0
            for gol in row["placed"]:
                pjg, lbr = KENDARAAN[gol]["dim"]
                if x_cursor + pjg <= panjang_kapal + 1e-6:
                    placements.append((gol, float(x_cursor), float(y)))
                    x_cursor += pjg
                else:
                    # can't place more in this row
                    break

    # final clamp to valid range (just in case)
    final = []
    for gol, x, y in placements:
        pjg, lbr = KENDARAAN[gol]["dim"]
        x = max(0.0, min(x, panjang_kapal - pjg))
        y = max(0.0, min(y, lebar_kapal - lbr))
        final.append((gol, float(x), float(y)))

    return final

# ======= Arrange vehicles and compute metrics =======
placements = arrange_to_balance(st.session_state.kendaraan, panjang_kapal, lebar_kapal, titik_seimbang_vertikal)

# compute stats
luas_terpakai = sum(KENDARAAN[gol]["dim"][0] * KENDARAAN[gol]["dim"][1] for gol, _, _ in placements)
luas_kapal = panjang_kapal * lebar_kapal
sisa_luas = luas_kapal - luas_terpakai
total_berat = sum(KENDARAAN[gol]["berat"] for gol, _, _ in placements)

if total_berat > 0:
    x_cm = sum((x + KENDARAAN[gol]["dim"][0] / 2.0) * KENDARAAN[gol]["berat"] for gol, x, y in placements) / total_berat
    y_cm = sum((y + KENDARAAN[gol]["dim"][1] / 2.0) * KENDARAAN[gol]["berat"] for gol, x, y in placements) / total_berat
else:
    x_cm, y_cm = 0.0, 0.0

selisih_vertikal = x_cm - titik_seimbang_vertikal
selisih_horizontal = y_cm - titik_seimbang_horizontal

# ======= UI output =======
st.title("Simulasi Muat Kapal — Penataan untuk Menjaga Titik Berat")

col1, col2 = st.columns([1, 1])
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

# ======= Visualisasi =======
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_xlim(0, panjang_kapal)
ax.set_ylim(0, lebar_kapal)
ax.set_aspect('equal')
ax.set_title("Visualisasi Muat Kapal (Penataan untuk Keseimbangan)")

# kapal outline
kapal_outline = Rectangle((0, 0), panjang_kapal, lebar_kapal, linewidth=1.5, edgecolor='black', facecolor='none')
ax.add_patch(kapal_outline)

# gambar kendaraan
for gol, x, y in placements:
    pjg, lbr = KENDARAAN[gol]["dim"]
    berat = KENDARAAN[gol]["berat"]
    rect = Rectangle((x, y), pjg, lbr, linewidth=1.2, edgecolor='blue', facecolor='skyblue', alpha=0.6)
    ax.add_patch(rect)
    ax.text(x + pjg/2.0, y + lbr/2.0, f"{gol}\n{berat}t", ha='center', va='center', fontsize=8, color='red')
    # titik pojok
    corners = [(x, y), (x + pjg, y), (x, y + lbr), (x + pjg, y + lbr)]
    for cx, cy in corners:
        ax.plot(cx, cy, 'ko', markersize=3)

# titik berat muatan dan garis seimbang
ax.plot(x_cm, y_cm, 'rx', markersize=10, label="Titik Berat Muatan")
ax.axvline(titik_seimbang_vertikal, color='green', linestyle='--', label="Titik Seimbang Vertikal")
ax.axhline(titik_seimbang_horizontal, color='orange', linestyle='--', label="Titik Seimbang Horizontal")
ax.legend()

st.pyplot(fig)
