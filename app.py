import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

st.set_page_config(page_title="Simulasi Muat Kapal (Balance XY)", layout="wide")

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
    st.session_state.kendaraan = []

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

# ======= Helper functions =======
def compute_cm(placements):
    """Compute total weight and center of mass (x_cm, y_cm). placements list of (gol, x, y)."""
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

def arrange_balance_xy(gol_list, panjang_kapal, lebar_kapal, x_target, y_target):
    """
    Greedy heuristic:
    - sort vehicles by weight desc
    - create rows based on minimal vehicle width (lbr)
    - for each vehicle (heavy->light) try placing at every row and side (left/right)
      using the current cursors for that row, pick the placement that minimizes distance
      from (x_target, y_target) for the resulting center of mass.
    - if after all placements some vehicles overflow bounds, shift or fallback to row greedy.
    """
    placements = []
    if not gol_list:
        return placements

    # rows
    min_row_height = min(KENDARAAN[g]["dim"][1] for g in KENDARAAN)  # typical 3.0
    n_rows = max(1, int(lebar_kapal // min_row_height))
    row_height = min_row_height
    total_rows_height = n_rows * row_height
    start_y = max(0.0, (lebar_kapal - total_rows_height) / 2.0)
    row_ys = [start_y + i * row_height for i in range(n_rows)]

    # state per row: left_cursor (x coordinate where next left placement will start), right_cursor
    row_state = [{"left_cursor": x_target, "right_cursor": x_target, "placed": []} for _ in range(n_rows)]

    # sort vehicles by weight descending
    sorted_gols = sorted(gol_list, key=lambda g: -KENDARAAN[g]["berat"])

    # place one by one
    for gol in sorted_gols:
        best_choice = None
        best_score = float("inf")
        best_tmp = None

        # try every row and both sides
        for ri in range(n_rows):
            pjg, lbr = KENDARAAN[gol]["dim"]
            # compute candidate x for right placement
            right_x = row_state[ri]["right_cursor"]
            left_x = row_state[ri]["left_cursor"] - pjg

            # two candidate placements: right and left
            candidates = [("right", right_x), ("left", left_x)]
            for side, cand_x in candidates:
                cand_y = row_ys[ri]
                # create temp placements including this candidate + existing placements
                tmp = placements.copy()
                tmp.append((gol, float(cand_x), float(cand_y)))
                # also include already placed items from row_state (they are in placements)
                # compute CM
                _, xcm_tmp, ycm_tmp = compute_cm(tmp)
                # score = euclidean distance to target
                score = ((xcm_tmp - x_target)**2 + (ycm_tmp - y_target)**2)**0.5
                # but penalize if candidate would start beyond left bound much (< -eps) or right bound (> panjang)
                if cand_x < -1e-6 or (cand_x + pjg) > panjang_kapal + 1e-6:
                    score += 1e6  # huge penalty for out-of-bounds
                # choose minimal score
                if score < best_score:
                    best_score = score
                    best_choice = (ri, side, cand_x, row_ys[ri])
                    best_tmp = tmp

        # if a feasible best_choice found, commit it
        if best_choice is not None:
            ri, side, x_chosen, y_chosen = best_choice
            placements.append((gol, float(x_chosen), float(y_chosen)))
            row_state[ri]["placed"].append(gol)
            if side == "right":
                row_state[ri]["right_cursor"] = x_chosen + KENDARAAN[gol]["dim"][0]
            else:
                # left placed at x_chosen, so new left_cursor is x_chosen
                row_state[ri]["left_cursor"] = x_chosen
        else:
            # fallback: append at x=0 of first row that has space
            placed_flag = False
            for ri in range(n_rows):
                x_try = 0.0
                pjg, lbr = KENDARAAN[gol]["dim"]
                if x_try + pjg <= panjang_kapal + 1e-6:
                    placements.append((gol, float(x_try), float(row_ys[ri])))
                    row_state[ri]["placed"].append(gol)
                    row_state[ri]["right_cursor"] = x_try + pjg
                    placed_flag = True
                    break
            if not placed_flag:
                # can't place, skip this vehicle
                continue

    # after all placements, try to shift whole layout to fit within ship
    if placements:
        min_x = min(x for (_, x, _) in placements)
        max_x = max(x + KENDARAAN[gol]["dim"][0] for (gol, x, _) in placements)
        shift = 0.0
        if min_x < 0.0:
            shift = -min_x
        elif max_x > panjang_kapal:
            shift = -(max_x - panjang_kapal)
        if shift != 0.0:
            placements = [(gol, float(x + shift), float(y)) for gol, x, y in placements]

    # clamp and final cleanup (ensure no negative coords and within bounds)
    final = []
    for gol, x, y in placements:
        pjg, lbr = KENDARAAN[gol]["dim"]
        x = max(0.0, min(x, panjang_kapal - pjg))
        y = max(0.0, min(y, lebar_kapal - lbr))
        final.append((gol, float(x), float(y)))

    return final

# ======= Arrange vehicles and compute metrics =======
placements = arrange_balance_xy(st.session_state.kendaraan, panjang_kapal, lebar_kapal,
                                titik_seimbang_vertikal, titik_seimbang_horizontal)

# compute stats
luas_terpakai = sum(KENDARAAN[gol]["dim"][0] * KENDARAAN[gol]["dim"][1] for gol, _, _ in placements)
luas_kapal = panjang_kapal * lebar_kapal
sisa_luas = luas_kapal - luas_terpakai
total_berat, x_cm, y_cm = compute_cm(placements)
selisih_vertikal = x_cm - titik_seimbang_vertikal
selisih_horizontal = y_cm - titik_seimbang_horizontal
dist_to_target = ((selisih_vertikal**2 + selisih_horizontal**2)**0.5) if total_berat > 0 else 0.0

# ======= UI output =======
st.title("Simulasi Muat Kapal — Penataan untuk Keseimbangan XY")

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

# ======= Visualisasi =======
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_xlim(0, panjang_kapal)
ax.set_ylim(0, lebar_kapal)
ax.set_aspect('equal')
ax.set_title("Visualisasi Muat Kapal (Penataan XY)")

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
if total_berat > 0:
    ax.plot(x_cm, y_cm, 'rx', markersize=10, label="Titik Berat Muatan")
ax.axvline(titik_seimbang_vertikal, color='green', linestyle='--', label="Titik Seimbang Vertikal")
ax.axhline(titik_seimbang_horizontal, color='orange', linestyle='--', label="Titik Seimbang Horizontal")
ax.legend()
st.pyplot(fig)
