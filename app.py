import streamlit as st
import matplotlib.pyplot as plt
import math
import random
from matplotlib.patches import Rectangle

st.set_page_config(page_title="Simulasi Muat Kapal (Optimized CM)", layout="wide")

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
    min_value=0.0,
    max_value=float(panjang_kapal),
    value=float(panjang_kapal / 2.0),
    step=0.1,
    format="%.2f"
)
titik_seimbang_horizontal = lebar_kapal / 2.0  # otomatis

st.sidebar.header("Tambah Kendaraan")
pilih_gol = st.sidebar.selectbox("Pilih Golongan", list(KENDARAAN.keys()))

if st.sidebar.button("Reset Kendaraan"):
    st.session_state.kendaraan = []
    st.success("Daftar kendaraan dikosongkan")

# ======= Utility functions =======
def compute_cm(placements):
    """Return total_mass, x_cm, y_cm. placements: list of (gol, x, y)."""
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
    return 0.0, 0.0, 0.0

def rectangles_overlap(a, b, eps=1e-9):
    """Check if rect a intersects rect b. a/b = (x,y,w,h)"""
    x1, y1, w1, h1 = a
    x2, y2, w2, h2 = b
    return not (x1 + w1 <= x2 + eps or x2 + w2 <= x1 + eps or y1 + h1 <= y2 + eps or y2 + h2 <= y1 + eps)

def has_overlap(placements, eps=1e-9):
    """Return True if any overlap exists. placements: (gol,x,y)."""
    n = len(placements)
    for i in range(n):
        gol1, x1, y1 = placements[i]
        w1, h1 = KENDARAAN[gol1]["dim"]
        for j in range(i+1, n):
            gol2, x2, y2 = placements[j]
            w2, h2 = KENDARAAN[gol2]["dim"]
            if rectangles_overlap((x1,y1,w1,h1),(x2,y2,w2,h2), eps):
                return True
    return False

def validate_placements(placements, panjang, lebar, expected_count):
    """Checks: all placed, within bounds, no overlap. Returns (ok, reason)."""
    if len(placements) != expected_count:
        return False, "tidak semua kendaraan dapat ditempatkan"
    # bounds check
    for gol, x, y in placements:
        pjg, lbr = KENDARAAN[gol]["dim"]
        if x < -1e-6 or y < -1e-6 or (x + pjg) > panjang + 1e-6 or (y + lbr) > lebar + 1e-6:
            return False, "beberapa kendaraan keluar batas kapal"
    if has_overlap(placements):
        return False, "terdapat tumpang tindih kendaraan"
    return True, None

# ======= Initial greedy placement (centered rows) =======
def initial_arrange(gol_list, panjang_kapal, lebar_kapal, x_target):
    """Greedy initial layout: heavy->light, assign to rows trying to center around x_target."""
    placements = []
    if not gol_list:
        return placements

    min_row_height = min(KENDARAAN[g]["dim"][1] for g in KENDARAAN)
    n_rows = max(1, int(lebar_kapal // min_row_height))
    row_height = min_row_height
    total_rows_height = n_rows * row_height
    start_y = max(0.0, (lebar_kapal - total_rows_height) / 2.0)
    row_ys = [start_y + i * row_height for i in range(n_rows)]

    # sort by weight desc
    sorted_gols = sorted(gol_list, key=lambda g: -KENDARAAN[g]["berat"])

    # row cursors for left/right placement around x_target
    rows = [{"left": x_target, "right": x_target, "placed": []} for _ in range(n_rows)]

    # assign to row with smallest total mass so far
    row_masses = [0.0]*n_rows
    for gol in sorted_gols:
        ri = min(range(n_rows), key=lambda i: row_masses[i])
        rows[ri]["placed"].append(gol)
        row_masses[ri] += KENDARAAN[gol]["berat"]

    # place in each row alternating right/left from center
    for i, row in enumerate(rows):
        y = row_ys[i]
        left = row["left"]
        right = row["right"]
        toggle = 0
        for gol in row["placed"]:
            pjg, lbr = KENDARAAN[gol]["dim"]
            if toggle % 2 == 0:
                x = right
                right += pjg
            else:
                x = left - pjg
                left = x
            placements.append((gol, float(x), float(y)))
            toggle += 1

    # shift to fit inside bounds if needed
    if placements:
        min_x = min(x for (_, x, _) in placements)
        max_x = max(x + KENDARAAN[gol]["dim"][0] for (gol, x, _) in placements)
        shift = 0.0
        if min_x < 0.0:
            shift = -min_x
        elif max_x > panjang_kapal:
            shift = -(max_x - panjang_kapal)
        if shift != 0.0:
            placements = [(gol, float(x+shift), float(y)) for gol,x,y in placements]

    # clamp to valid
    final = []
    for gol,x,y in placements:
        pjg,lbr = KENDARAAN[gol]["dim"]
        x = max(0.0, min(x, panjang_kapal - pjg))
        y = max(0.0, min(y, lebar_kapal - lbr))
        final.append((gol,float(x),float(y)))
    return final

# ======= Local improvement =======
def local_improve(placements, panjang_kapal, lebar_kapal, x_target, y_target,
                  max_iter=500, shift_step=0.2, max_shift=3.0, swap_tries=200):
    """
    Try small x-shifts per vehicle to reduce CM distance to target, and random swaps.
    - shift_step: granularity of shifts (m)
    - max_shift: max distance to try shifting a single vehicle (m)
    - swap_tries: number of random swap attempts
    """
    if not placements:
        return placements

    best = placements.copy()
    _, bx, by = compute_cm(best)
    best_score = math.hypot(bx - x_target, by - y_target)

    # attempt simple shifts (hill-climb)
    improved = True
    it = 0
    while improved and it < max_iter:
        improved = False
        it += 1
        # iterate vehicles in random order for diversification
        order = list(range(len(best)))
        random.shuffle(order)
        for idx in order:
            gol, x_old, y = best[idx]
            pjg, lbr = KENDARAAN[gol]["dim"]
            # try shifts from -max_shift..+max_shift with step
            shifts = [round(s, 3) for s in 
                      [i*shift_step for i in range(int(-max_shift/shift_step), int(max_shift/shift_step)+1)]]
            random.shuffle(shifts)
            for ds in shifts:
                x_new = x_old + ds
                # quick bounds check
                if x_new < -1e-6 or (x_new + pjg) > panjang_kapal + 1e-6:
                    continue
                # build candidate placements
                cand = best.copy()
                cand[idx] = (gol, float(x_new), float(y))
                # check overlap quickly
                if has_overlap(cand):
                    continue
                # compute score
                _, cx, cy = compute_cm(cand)
                score = math.hypot(cx - x_target, cy - y_target)
                # prefer smaller score and prefer minimal movement (tie-break)
                if score + 1e-6 < best_score:
                    best = cand
                    best_score = score
                    improved = True
                    break
            if improved:
                break

    # attempt random swaps to escape local minima
    for _ in range(swap_tries):
        i, j = random.sample(range(len(best)), 2)
        cand = best.copy()
        # swap positions
        a = cand[i]
        b = cand[j]
        cand[i] = (a[0], b[1], b[2])  # place gol a at position of b
        cand[j] = (b[0], a[1], a[2])  # place gol b at position of a
        # ensure within bounds
        ok = True
        for golc, xc, yc in cand:
            pjg, lbr = KENDARAAN[golc]["dim"]
            if xc < -1e-6 or yc < -1e-6 or (xc + pjg) > panjang_kapal + 1e-6 or (yc + lbr) > lebar_kapal + 1e-6:
                ok = False
                break
        if not ok:
            continue
        if has_overlap(cand):
            continue
        _, cx, cy = compute_cm(cand)
        score = math.hypot(cx - x_target, cy - y_target)
        if score + 1e-9 < best_score:
            best = cand
            best_score = score
            # optionally continue further swaps from new best
    return best

# ======= Main arrangement routine that tries initial + improve =======
def arrange_with_optimization(gol_list, panjang_kapal, lebar_kapal, x_target, y_target):
    # initial greedy
    init = initial_arrange(gol_list, panjang_kapal, lebar_kapal, x_target)
    # if initial cannot place all (length mismatch), try fallback left-to-right fill rows
    if len(init) != len(gol_list):
        # fallback simpler fill left->right row by row
        min_row_height = min(KENDARAAN[g]["dim"][1] for g in KENDARAAN)
        n_rows = max(1, int(lebar_kapal // min_row_height))
        row_height = min_row_height
        total_rows_height = n_rows * row_height
        start_y = max(0.0, (lebar_kapal - total_rows_height) / 2.0)
        row_ys = [start_y + i * row_height for i in range(n_rows)]
        placements = []
        sorted_gols = sorted(gol_list, key=lambda g: -KENDARAAN[g]["berat"])
        ri = 0
        for gol in sorted_gols:
            pjg, lbr = KENDARAAN[gol]["dim"]
            x_cursor = 0.0
            placed = False
            # try to place in current row, if not fit, next row
            for r in range(n_rows):
                y = row_ys[(ri + r) % n_rows]
                # find x_cursor by checking existing in that row
                used = [ (x,w) for gg,x,y0 in placements if y0==y for (_,w,_) in [(gg, KENDARAAN[gg]["dim"][0],0)] ]
                # simple packing: pack to the rightmost of placed in that row
                if not used:
                    x_try = 0.0
                else:
                    rightmost = max(x + w for (x,w) in used)
                    x_try = rightmost
                if x_try + pjg <= panjang_kapal + 1e-6:
                    placements.append((gol, float(x_try), float(y)))
                    placed = True
                    break
            if not placed:
                # cannot place this gol, give up early
                return []
        init = placements

    # validate init
    ok, reason = validate_placements(init, panjang_kapal, lebar_kapal, len(gol_list))
    if not ok:
        return []  # fail to place

    # local improvement
    improved = local_improve(init, panjang_kapal, lebar_kapal, x_target, y_target,
                             max_iter=400, shift_step=0.2, max_shift=3.0, swap_tries=300)
    # final validation
    ok2, reason2 = validate_placements(improved, panjang_kapal, lebar_kapal, len(gol_list))
    if not ok2:
        # if improvement broke something (shouldn't), fallback to init
        return init
    return improved

# ======= Handler to attempt add vehicle (test first) =======
def try_add_vehicle(gol_candidate):
    candidate_list = st.session_state.kendaraan + [gol_candidate]
    placements_candidate = arrange_with_optimization(candidate_list, panjang_kapal, lebar_kapal,
                                                     titik_seimbang_vertikal, titik_seimbang_horizontal)
    ok, reason = validate_placements(placements_candidate, panjang_kapal, lebar_kapal, len(candidate_list))
    if ok:
        # commit
        st.session_state.kendaraan.append(gol_candidate)
        st.success(f"Berhasil menambahkan golongan {gol_candidate}")
    else:
        st.error(f"tidak bisa menambahkan golongan {gol_candidate} lagi")
        st.write(f"*Alasan: {reason}*")

# ======= UI: add button =======
if st.sidebar.button("Tambah Kendaraan"):
    try_add_vehicle(pilih_gol)

# ======= Arrange current vehicles for display =======
placements = arrange_with_optimization(st.session_state.kendaraan, panjang_kapal, lebar_kapal,
                                       titik_seimbang_vertikal, titik_seimbang_horizontal)

# compute stats
luas_terpakai = sum(KENDARAAN[gol]["dim"][0]*KENDARAAN[gol]["dim"][1] for gol,_,_ in placements)
luas_kapal = panjang_kapal * lebar_kapal
sisa_luas = luas_kapal - luas_terpakai
total_mass, x_cm, y_cm = compute_cm(placements)
selisih_vertikal = x_cm - titik_seimbang_vertikal
selisih_horizontal = y_cm - titik_seimbang_horizontal
dist_to_target = math.hypot(selisih_vertikal, selisih_horizontal) if total_mass>0 else 0.0

# ======= Output =======
st.title("Simulasi Muat Kapal — Optimasi Titik Berat (X & Y)")

c1, c2 = st.columns([1,1])
with c1:
    st.subheader("Ringkasan")
    st.write(f"Panjang kapal: **{panjang_kapal:.2f} m**")
    st.write(f"Lebar kapal: **{lebar_kapal:.2f} m**")
    st.write(f"Titik seimbang vertikal (target): **{titik_seimbang_vertikal:.2f} m**")
    st.write(f"Titik seimbang horizontal (target): **{titik_seimbang_horizontal:.2f} m**")
    st.write(f"Jumlah kendaraan: **{len(st.session_state.kendaraan)}**")
    st.write(f"Luas kapal: **{luas_kapal:.2f} m²**")
    st.write(f"Luas terpakai: **{luas_terpakai:.2f} m²**")
    st.write(f"Sisa luas: **{sisa_luas:.2f} m²**")
    st.write(f"Total berat muatan: **{total_mass:.2f} t**")
    st.write(f"Titik berat muatan (x,y): **({x_cm:.2f} m, {y_cm:.2f} m)**")
    st.write(f"Selisih vertikal: **{selisih_vertikal:.2f} m**")
    st.write(f"Selisih horizontal: **{selisih_horizontal:.2f} m**")
    st.write(f"Jarak CM → target: **{dist_to_target:.3f} m**")

with c2:
    st.subheader("Daftar Kendaraan & Posisi")
    if placements:
        table = []
        for i,(gol,x,y) in enumerate(placements, start=1):
            pjg,lbr = KENDARAAN[gol]["dim"]
            berat = KENDARAAN[gol]["berat"]
            table.append({"#": i, "Gol": gol, "x (m)": round(x,2), "y (m)": round(y,2),
                          "p (m)": pjg, "l (m)": lbr, "berat (t)": berat})
        st.table(table)
    else:
        st.write("Belum ada kendaraan atau tidak dapat ditata.")

# ======= Visualization =======
fig, ax = plt.subplots(figsize=(10,5))
ax.set_xlim(0, panjang_kapal)
ax.set_ylim(0, lebar_kapal)
ax.set_aspect('equal')
ax.set_title("Visualisasi Muat Kapal — Optimasi CM")

# kapal outline
ax.add_patch(Rectangle((0,0), panjang_kapal, lebar_kapal, linewidth=1.3, edgecolor='black', facecolor='none'))

for gol,x,y in placements:
    pjg,lbr = KENDARAAN[gol]["dim"]
    berat = KENDARAAN[gol]["berat"]
    ax.add_patch(Rectangle((x,y), pjg, lbr, linewidth=1.2, edgecolor='blue', facecolor='skyblue', alpha=0.7))
    ax.text(x + pjg/2.0, y + lbr/2.0, f"{gol}\n{berat}t", ha='center', va='center', fontsize=8, color='red')
    # corner dots
    corners = [(x,y),(x+pjg,y),(x,y+lbr),(x+pjg,y+lbr)]
    for cx,cy in corners:
        ax.plot(cx, cy, 'ko', markersize=3)

# CM and balance lines
if total_mass>0:
    ax.plot(x_cm, y_cm, 'rx', markersize=10, label="Titik Berat Muatan")
ax.axvline(titik_seimbang_vertikal, color='green', linestyle='--', label="Titik Seimbang Vertikal")
ax.axhline(titik_seimbang_horizontal, color='orange', linestyle='--', label="Titik Seimbang Horizontal")
ax.legend()
st.pyplot(fig)
