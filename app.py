import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import copy

st.set_page_config(page_title="Stowage Plan", layout="wide")

# --- KONFIGURASI DATA KENDARAAN ---
VEHICLE_DATA = {
    "dimensi": {
        "IV": (5, 3), "V": (7, 3), "VI": (10, 3),
        "VII": (12, 3), "VIII": (16, 3), "IX": (21, 3),
    },
    "berat": {
        "IV": 1, "V": 8, "VI": 12,
        "VII": 15, "VIII": 18, "IX": 30,
    },
    "warna": {
        "IV": "lightblue", "V": "lightgreen", "VI": "orange",
        "VII": "violet", "VIII": "salmon", "IX": "khaki",
    }
}

# --- FUNGSI-FUNGSI INTI ---

def check_overlap(new_vehicle_rect, placed_vehicles):
    """
    Mengecek apakah kendaraan baru tumpang tindih dengan kendaraan yang sudah ditempatkan.
    Mengembalikan True jika ada tumpang tindih, False jika tidak.
    """
    x1, y1, w1, h1 = new_vehicle_rect
    for placed in placed_vehicles:
        x2, y2, w2, h2 = placed['rect']
        if (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1):
            continue
        else:
            return True
    return False

def calculate_combined_cg(vehicles):
    """Menghitung titik berat gabungan dari semua kendaraan yang dimuat."""
    if not vehicles:
        return 0, 0
    total_weight = sum(VEHICLE_DATA["berat"][v['tipe']] for v in vehicles)
    if total_weight == 0:
        return 0, 0
    
    weighted_sum_x = 0
    weighted_sum_y = 0

    for v in vehicles:
        mid_x = v['rect'][0] + v['rect'][2] / 2
        mid_y = v['rect'][1] + v['rect'][3] / 2
        weight = VEHICLE_DATA["berat"][v['tipe']]
        weighted_sum_x += mid_x * weight
        weighted_sum_y += mid_y * weight
        
    return weighted_sum_x / total_weight, weighted_sum_y / total_weight

def find_placement_for_single_vehicle(ship_dims, ship_balance_point, vehicle_type_to_add, current_placed_vehicles):
    """
    Mencari posisi optimal untuk satu kendaraan baru ke dalam dek yang sudah berisi.
    Menggunakan logika yang sama dengan yang sebelumnya, tetapi hanya untuk satu kendaraan.
    """
    ship_length, ship_width = ship_dims
    panjang_kendaraan, lebar_kendaraan = VEHICLE_DATA["dimensi"][vehicle_type_to_add]

    # Hitung persentase pemakaian area dek kapal saat ini
    luas_kapal = ship_length * ship_width
    luas_terpakai = sum(v['rect'][2]*v['rect'][3] for v in current_placed_vehicles)
    persentase_terpakai = (luas_terpakai / luas_kapal) * 100 if luas_kapal > 0 else 0

    candidate_points = []

    if persentase_terpakai < 50:
    # Mode center fleksibel
        center_x, center_y = ship_balance_point
        panjang, lebar = VEHICLE_DATA["dimensi"][vehicle_type_to_add]
        candidate_points = [
            (center_x - panjang/2, center_y - lebar/2),  # center
            (0, 0),  # sudut kiri-belakang
            (ship_length - panjang, 0),  # sudut kanan-belakang
            (0, ship_width - lebar),  # sudut kiri-depan
            (ship_length - panjang, ship_width - lebar)  # sudut kanan-depan
        ]
    else:
    # Hasilkan semua titik kandidat dari sudut kendaraan yang sudah ada.
        candidate_points = [(0, 0)]
        for pv in current_placed_vehicles:
            vx, vy, vw, vh = pv['rect']
            candidate_points.append((vx + vw, vy))
            candidate_points.append((vx, vy + vh))
        
    # Filter titik-titik kandidat untuk memastikan berada di dalam batas kapal
    unique_candidate_points = set()
    for p in candidate_points:
        if 0 <= p[0] <= ship_length and 0 <= p[1] <= ship_width:
             unique_candidate_points.add(p)
    candidate_points = list(unique_candidate_points)
    candidate_points.sort(key=lambda p: (p[0], p[1]))
    
    panjang_kendaraan, lebar_kendaraan = VEHICLE_DATA["dimensi"][vehicle_type_to_add]
    best_position = None
    min_distance = float('inf')
    
    valid_candidate_positions = []
    
    for cx, cy in candidate_points:
        if cx + panjang_kendaraan <= ship_length and cy + lebar_kendaraan <= ship_width:
            new_vehicle_rect_proposal = (cx, cy, panjang_kendaraan, lebar_kendaraan)
            if not check_overlap(new_vehicle_rect_proposal, current_placed_vehicles):
                valid_candidate_positions.append(new_vehicle_rect_proposal)

    for proposed_rect in valid_candidate_positions:
        temp_placed = copy.deepcopy(current_placed_vehicles)
        temp_placed.append({'tipe': vehicle_type_to_add, 'rect': proposed_rect})
        
        cg_x, cg_y = calculate_combined_cg(temp_placed)
        distance = np.sqrt((cg_x - ship_balance_point[0])**2 + (cg_y - ship_balance_point[1])**2)
        
        if distance < min_distance:
            min_distance = distance
            best_position = proposed_rect
            
    return best_position

def find_initial_optimal_placement(ship_dims, ship_balance_point, vehicles_to_load_original):
    """
    Fungsi awal untuk menempatkan semua kendaraan dari awal.
    Ini digunakan hanya saat reset atau saat aplikasi pertama kali dimuat.
    """
    ship_length, ship_width = ship_dims
    placed_vehicles = []
    unplaced_vehicles = []
    
    # Mengurutkan dari yang terbesar
    vehicles_to_load_sorted = sorted(vehicles_to_load_original, key=lambda v: VEHICLE_DATA["dimensi"][v][0] * VEHICLE_DATA["dimensi"][v][1], reverse=True)

    for vehicle_type in vehicles_to_load_sorted:
        best_pos = find_placement_for_single_vehicle(ship_dims, ship_balance_point, vehicle_type, placed_vehicles)
        if best_pos:
            placed_vehicles.append({'tipe': vehicle_type, 'rect': best_pos})
        else:
            unplaced_vehicles.append(vehicle_type)

    return placed_vehicles, unplaced_vehicles

def visualize_placement(ship_dims, ship_balance_point, placed_vehicles):
    """Membuat visualisasi penempatan kendaraan di atas kapal."""
    ship_length, ship_width = ship_dims
    
    fig, ax = plt.subplots(figsize=(12, max(6, ship_width / ship_length * 12))) 
    
    ship_deck = patches.Rectangle((0, 0), ship_length, ship_width, linewidth=2, edgecolor='black', facecolor='lightgray')
    ax.add_patch(ship_deck)

    for vehicle in placed_vehicles:
        x, y, w, h = vehicle['rect']
        color = VEHICLE_DATA["warna"][vehicle['tipe']]
        rect = patches.Rectangle((x, y), w, h, linewidth=1.5, edgecolor='black', facecolor=color, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, vehicle['tipe'], ha='center', va='center', fontsize=8, weight='bold')

    ax.plot(ship_balance_point[0], ship_balance_point[1], 'rX', markersize=12, label='Titik Seimbang Kapal', mew=2)
    
    if placed_vehicles:
        cg_x, cg_y = calculate_combined_cg(placed_vehicles)
        ax.plot(cg_x, cg_y, 'bo', markersize=10, label='Titik Berat Muatan', alpha=0.8)

    ax.set_xlim(0, ship_length)
    ax.set_ylim(0, ship_width)
    ax.set_aspect('equal', adjustable='box')
    ax.text(0, ship_width+1, "Belakang", ha='left', va='center', fontsize=10, fontweight='bold') 
    ax.text(ship_length, ship_width+1, "Depan", ha='right', va='center', fontsize=10, fontweight='bold') 
    ax.text(ship_length+1, 0, "Kanan", ha='center', va='bottom', rotation=270, fontsize=10, fontweight='bold') 
    ax.text(ship_length+1, ship_width, "Kiri", ha='center', va='top', rotation=270, fontsize=10, fontweight='bold')
    plt.xlabel("Panjang Kapal (meter)")
    plt.ylabel("Lebar Kapal (meter)")
    plt.title("Visualisasi Simulasi Muat Kapal")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    
    return fig

# --- UI STREAMLIT ---

st.set_page_config(layout="wide")
st.title("Stowage Plan")

# Inisialisasi session state
if 'vehicles_input' not in st.session_state:
    st.session_state.vehicles_input = []
if 'placed_vehicles' not in st.session_state:
    st.session_state.placed_vehicles = []
if 'unplaced_vehicles' not in st.session_state:
    st.session_state.unplaced_vehicles = []
if 'last_input_count' not in st.session_state:
    st.session_state.last_input_count = 0
if 'last_ship_dims' not in st.session_state:
    st.session_state.last_ship_dims = (50.0, 15.0)

# --- SIDEBAR UNTUK INPUT ---
with st.sidebar:
    st.header("1. Parameter Kapal")
    ship_length = st.number_input("Masukkan Panjang Kapal (meter)", min_value=1.0, value=50.0, step=0.5, format="%.1f")
    ship_width = st.number_input("Masukkan Lebar Kapal (meter)", min_value=1.0, value=15.0, step=0.5, format="%.1f")
    balance_point_x = st.number_input("Titik Seimbang Panjang (meter)", min_value=0.0, max_value=ship_length, value=ship_length/2, step=0.5, format="%.1f")
    balance_point_y = ship_width / 2
    st.info(f"Titik Seimbang Kapal (P, L): ({balance_point_x:.2f} m, {balance_point_y:.2f} m)")
    
    st.header("2. Tambah Kendaraan")
    vehicle_options = list(VEHICLE_DATA["dimensi"].keys())
    
    st.selectbox(
        "Pilih Golongan Kendaraan", 
        options=vehicle_options, 
        key='selected_vehicle'
    )


    def add_vehicle():
        new_vehicle = st.session_state.selected_vehicle
        ship_dims = (ship_length, ship_width)
        ship_balance = (balance_point_x, balance_point_y)
    
        # Tambahkan kendaraan baru ke daftar input dulu
        st.session_state.vehicles_input.append(new_vehicle)
    
        # Hitung luas terpakai termasuk kendaraan baru
        luas_kapal = ship_length * ship_width
        luas_terpakai_sementara = sum(v['rect'][2]*v['rect'][3] for v in st.session_state.placed_vehicles)
        panjang_baru, lebar_baru = VEHICLE_DATA["dimensi"][new_vehicle]
        luas_terpakai_sementara += panjang_baru * lebar_baru
        persentase_terpakai_sementara = (luas_terpakai_sementara / luas_kapal) * 100 if luas_kapal > 0 else 0
    
        # Jika persentase >=50% setelah kendaraan baru, reset semua dan susun ulang semua kendaraan
        if persentase_terpakai_sementara >= 50:
            st.session_state.placed_vehicles, st.session_state.unplaced_vehicles = find_initial_optimal_placement(
                ship_dims, ship_balance, st.session_state.vehicles_input
            )
        else:
            # Mode center: tambah kendaraan baru saja
            best_pos = find_placement_for_single_vehicle(
                ship_dims, ship_balance, new_vehicle, st.session_state.placed_vehicles
            )
            if best_pos:
                st.session_state.placed_vehicles.append({'tipe': new_vehicle, 'rect': best_pos})
            else:
                st.session_state.unplaced_vehicles.append(new_vehicle)
    
    
    
    def reset_vehicles():
        st.session_state.vehicles_input = []
        st.session_state.placed_vehicles = []
        st.session_state.unplaced_vehicles = []
        st.session_state.last_input_count = 0

    st.button("➕ Tambah Kendaraan", on_click=add_vehicle)
    st.button("🗑️ Reset Daftar", on_click=reset_vehicles)

# --- SIMULASI PENEMPATAN OPTIMAL SEMUA KENDARAAN ---
ship_dims = (ship_length, ship_width)
ship_balance_point = (balance_point_x, balance_point_y)

with st.spinner("Menghitung penempatan optimal semua kendaraan..."):
    st.session_state.placed_vehicles, st.session_state.unplaced_vehicles = find_initial_optimal_placement(
        ship_dims, ship_balance_point, st.session_state.vehicles_input
    )
    
# --- AREA UTAMA ---
with st.container():
    st.header("Hasil Simulasi")
    
    if st.session_state.placed_vehicles:
        fig = visualize_placement((ship_length, ship_width), (balance_point_x, balance_point_y), st.session_state.placed_vehicles)
        st.pyplot(fig, use_container_width=True)
    else:
        st.info("Tambahkan kendaraan dari sidebar untuk memulai simulasi.")
        fig, ax = plt.subplots(figsize=(12, max(6, ship_width / ship_length * 12)))
        ship_deck = patches.Rectangle((0, 0), ship_length, ship_width, linewidth=2, edgecolor='black', facecolor='lightgray')
        ax.add_patch(ship_deck)
        ax.plot(balance_point_x, balance_point_y, 'rX', markersize=12, label='Titik Seimbang Kapal', mew=2)
        ax.set_xlim(0, ship_length)
        ax.set_ylim(0, ship_width)
        ax.set_aspect('equal', adjustable='box')
        plt.title("Dek Kapal Kosong")
        plt.legend()
        st.pyplot(fig, use_container_width=True)

# --- Notifikasi Kendaraan Tidak Dapat Dimuat ---
if st.session_state.unplaced_vehicles:
    st.error(f"⚠️ Peringatan: Kendaraan tidak dapat ditempatkan: {', '.join(st.session_state.unplaced_vehicles)}")
else:
    if st.session_state.vehicles_input:
        st.success("🎉 Semua kendaraan berhasil ditempatkan!")

st.markdown("---")

# --- Daftar Muatan ---
st.header("Daftar Kendaraan yang Berhasil Dimuat")
if not st.session_state.placed_vehicles:
    st.write("Belum ada kendaraan yang berhasil ditempatkan.")
else:
    data_for_df = []
    for vehicle in st.session_state.placed_vehicles:
        vehicle_type = vehicle['tipe']
        panjang, lebar = VEHICLE_DATA["dimensi"][vehicle_type]
        berat = VEHICLE_DATA["berat"][vehicle_type]
        data_for_df.append({
            "Golongan": vehicle_type,
            "Dimensi (P x L)": f"{panjang}x{lebar} m",
            "Berat (ton)": berat
        })
    df_vehicles = pd.DataFrame(data_for_df)
    st.dataframe(df_vehicles, use_container_width=True, hide_index=True)

st.markdown("---")

# --- Ringkasan Optimal ---
st.header("Ringkasan Optimal")
if st.session_state.placed_vehicles:
    luas_kapal = ship_length * ship_width
    luas_terpakai = sum(v['rect'][2] * v['rect'][3] for v in st.session_state.placed_vehicles)
    persentase_terpakai = (luas_terpakai / luas_kapal) * 100 if luas_kapal > 0 else 0
    
    cg_x, cg_y = calculate_combined_cg(st.session_state.placed_vehicles)
    jarak_cg = np.sqrt((cg_x - balance_point_x)**2 + (cg_y - balance_point_y)**2)

    st.metric("Jumlah Kendaraan Ditempatkan", f"{len(st.session_state.placed_vehicles)} dari {len(st.session_state.vehicles_input)}")
    st.metric("Penggunaan Area Dek", f"{persentase_terpakai:.2f} %")
    st.metric("Jarak Titik Berat Muatan ke Titik Seimbang Kapal", f"{jarak_cg:.2f} m")
else:
    st.metric("Jumlah Kendaraan Ditempatkan", "0")
    st.metric("Penggunaan Area Dek", "0.00 %")
    st.metric("Jarak Titik Berat Muatan ke Titik Seimbang Kapal", "N/A")
