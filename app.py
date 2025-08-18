import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import copy

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
    """Mengecek apakah kendaraan baru tumpang tindih dengan kendaraan yang sudah ditempatkan."""
    for placed in placed_vehicles:
        # Unpack rectangles: (x, y, width, height)
        x1, y1, w1, h1 = new_vehicle_rect
        x2, y2, w2, h2 = placed['rect']
        
        # Kondisi tidak tumpang tindih
        if (x1 + w1 <= x2 or x2 + w2 <= x1 or
            y1 + h1 <= y2 or y2 + h2 <= y1):
            continue
        else:
            return True # Terjadi tumpang tindih
    return False

def calculate_combined_cg(vehicles):
    """Menghitung titik berat gabungan dari semua kendaraan yang dimuat."""
    if not vehicles:
        return 0, 0

    total_weight = 0
    weighted_sum_x = 0
    weighted_sum_y = 0

    for vehicle in vehicles:
        berat = VEHICLE_DATA["berat"][vehicle['tipe']]
        cx = vehicle['rect'][0] + vehicle['rect'][2] / 2
        cy = vehicle['rect'][1] + vehicle['rect'][3] / 2
        
        total_weight += berat
        weighted_sum_x += cx * berat
        weighted_sum_y += cy * berat

    if total_weight == 0:
        return 0, 0
        
    cg_x = weighted_sum_x / total_weight
    cg_y = weighted_sum_y / total_weight
    
    return cg_x, cg_y

def find_optimal_placement(ship_dims, ship_balance_point, vehicles_to_load):
    """
    Algoritma Greedy untuk menemukan penempatan kendaraan yang optimal.
    Menempatkan kendaraan terbesar terlebih dahulu pada posisi yang meminimalkan
    jarak titik berat muatan ke titik seimbang kapal.
    """
    ship_length, ship_width = ship_dims
    placed_vehicles = []
    unplaced_vehicles = []

    # Urutkan kendaraan dari yang terbesar (berdasarkan luas) ke terkecil
    sorted_vehicles = sorted(vehicles_to_load, key=lambda v: VEHICLE_DATA["dimensi"][v][0] * VEHICLE_DATA["dimensi"][v][1], reverse=True)
    
    # Resolusi grid untuk pencarian posisi (semakin kecil semakin presisi tapi lambat)
    GRID_STEP = 0.5 

    for i, vehicle_type in enumerate(sorted_vehicles):
        panjang_kendaraan, lebar_kendaraan = VEHICLE_DATA["dimensi"][vehicle_type]
        best_position = None
        min_distance = float('inf')

        # Mencari posisi terbaik di seluruh area kapal
        for x in np.arange(0, ship_length - panjang_kendaraan + GRID_STEP, GRID_STEP):
            for y in np.arange(0, ship_width - lebar_kendaraan + GRID_STEP, GRID_STEP):
                
                new_vehicle_rect = (x, y, panjang_kendaraan, lebar_kendaraan)
                
                # 1. Cek apakah tumpang tindih
                if not check_overlap(new_vehicle_rect, placed_vehicles):
                    
                    # 2. Hitung hipotesis titik berat gabungan jika kendaraan ini ditempatkan
                    temp_placed = copy.deepcopy(placed_vehicles)
                    temp_placed.append({'tipe': vehicle_type, 'rect': new_vehicle_rect})
                    
                    cg_x, cg_y = calculate_combined_cg(temp_placed)
                    
                    # 3. Hitung jarak ke titik seimbang kapal
                    distance = np.sqrt((cg_x - ship_balance_point[0])**2 + (cg_y - ship_balance_point[1])**2)
                    
                    # 4. Simpan posisi jika ini yang terbaik sejauh ini
                    if distance < min_distance:
                        min_distance = distance
                        best_position = new_vehicle_rect

        if best_position:
            placed_vehicles.append({'tipe': vehicle_type, 'rect': best_position, 'id': i})
        else:
            unplaced_vehicles.append(vehicle_type)

    return placed_vehicles, unplaced_vehicles

def visualize_placement(ship_dims, ship_balance_point, placed_vehicles):
    """Membuat visualisasi penempatan kendaraan di atas kapal."""
    ship_length, ship_width = ship_dims
    fig, ax = plt.subplots(figsize=(ship_length * 0.5, ship_width * 0.5))

    # Gambar dek kapal
    ship_deck = patches.Rectangle((0, 0), ship_length, ship_width, linewidth=2, edgecolor='black', facecolor='lightgray')
    ax.add_patch(ship_deck)

    # Gambar kendaraan yang ditempatkan
    for vehicle in placed_vehicles:
        x, y, w, h = vehicle['rect']
        color = VEHICLE_DATA["warna"][vehicle['tipe']]
        rect = patches.Rectangle((x, y), w, h, linewidth=1.5, edgecolor='black', facecolor=color, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, vehicle['tipe'], ha='center', va='center', fontsize=8, weight='bold')

    # Tandai titik seimbang kapal (target)
    ax.plot(ship_balance_point[0], ship_balance_point[1], 'rX', markersize=12, label='Titik Seimbang Kapal', mew=2)
    
    # Hitung dan tandai titik berat muatan (hasil)
    if placed_vehicles:
        cg_x, cg_y = calculate_combined_cg(placed_vehicles)
        ax.plot(cg_x, cg_y, 'bo', markersize=10, label='Titik Berat Muatan', alpha=0.8)

    ax.set_xlim(0, ship_length)
    ax.set_ylim(0, ship_width)
    ax.set_aspect('equal', adjustable='box')
    plt.xlabel("Panjang Kapal (meter)")
    plt.ylabel("Lebar Kapal (meter)")
    plt.title("Visualisasi Simulasi Muat Kapal")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    return fig


# --- UI STREAMLIT ---

st.set_page_config(layout="wide")
st.title("🚢 Aplikasi Simulasi Muat Kapal Optimal")

# Inisialisasi session state
if 'vehicles_to_load' not in st.session_state:
    st.session_state.vehicles_to_load = []
if 'simulation_result' not in st.session_state:
    st.session_state.simulation_result = None

# --- SIDEBAR UNTUK INPUT ---
with st.sidebar:
    st.header("1. Parameter Kapal")
    ship_length = st.number_input("Masukkan Panjang Kapal (meter)", min_value=1.0, value=50.0, step=0.5, format="%.1f")
    ship_width = st.number_input("Masukkan Lebar Kapal (meter)", min_value=1.0, value=15.0, step=0.5, format="%.1f")
    
    balance_point_x = st.number_input("Titik Seimbang Panjang (meter)", min_value=0.0, max_value=ship_length, value=ship_length/2, step=0.5, format="%.1f")
    balance_point_y = ship_width / 2
    
    st.info(f"Titik Seimbang Kapal (P, L):\n({balance_point_x:.2f} m, {balance_point_y:.2f} m)")
    
    st.header("2. Tambah Kendaraan")
    vehicle_options = list(VEHICLE_DATA["dimensi"].keys())
    selected_vehicle = st.selectbox("Pilih Golongan Kendaraan", options=vehicle_options)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Tambah Kendaraan"):
            st.session_state.vehicles_to_load.append(selected_vehicle)
            st.session_state.simulation_result = None # Reset hasil simulasi jika ada perubahan
    with col2:
        if st.button("🗑️ Reset Daftar"):
            st.session_state.vehicles_to_load = []
            st.session_state.simulation_result = None
            st.rerun()

# --- AREA UTAMA ---
col_main1, col_main2 = st.columns([1, 2])

with col_main1:
    st.header("Daftar Muatan")
    if not st.session_state.vehicles_to_load:
        st.info("Belum ada kendaraan yang ditambahkan.")
    else:
        df_vehicles = pd.DataFrame(st.session_state.vehicles_to_load, columns=["Golongan"])
        st.dataframe(df_vehicles, use_container_width=True)
        
        total_berat = sum(VEHICLE_DATA["berat"][v] for v in st.session_state.vehicles_to_load)
        total_luas = sum(VEHICLE_DATA["dimensi"][v][0] * VEHICLE_DATA["dimensi"][v][1] for v in st.session_state.vehicles_to_load)
        st.metric("Total Kendaraan", f"{len(st.session_state.vehicles_to_load)} unit")
        st.metric("Estimasi Total Berat", f"{total_berat} Ton")
        st.metric("Estimasi Total Luas", f"{total_luas} m²")

    if st.session_state.vehicles_to_load:
        if st.button("🚀 Jalankan Simulasi Penempatan", type="primary", use_container_width=True):
            with st.spinner("Mencari kombinasi optimal... Ini mungkin butuh beberapa saat."):
                ship_dims = (ship_length, ship_width)
                ship_balance_point = (balance_point_x, balance_point_y)
                placed, unplaced = find_optimal_placement(ship_dims, ship_balance_point, st.session_state.vehicles_to_load)
                st.session_state.simulation_result = (placed, unplaced)

with col_main2:
    st.header("Hasil Simulasi")
    if st.session_state.simulation_result:
        placed_vehicles, unplaced_vehicles = st.session_state.simulation_result
        
        # Tampilkan visualisasi
        fig = visualize_placement((ship_length, ship_width), (balance_point_x, balance_point_y), placed_vehicles)
        st.pyplot(fig)
        
        # Tampilkan metrik hasil
        st.subheader("Ringkasan Hasil Optimal")
        
        luas_kapal = ship_length * ship_width
        luas_terpakai = sum(v['rect'][2] * v['rect'][3] for v in placed_vehicles)
        persentase_terpakai = (luas_terpakai / luas_kapal) * 100 if luas_kapal > 0 else 0
        
        cg_x, cg_y = calculate_combined_cg(placed_vehicles)
        jarak_cg = np.sqrt((cg_x - balance_point_x)**2 + (cg_y - balance_point_y)**2)

        met_col1, met_col2, met_col3 = st.columns(3)
        met_col1.metric("Kendaraan Ditempatkan", f"{len(placed_vehicles)} / {len(st.session_state.vehicles_to_load)}")
        met_col2.metric("Penggunaan Area Dek", f"{persentase_terpakai:.2f} %")
        met_col3.metric("Jarak ke Titik Seimbang", f"{jarak_cg:.2f} m")

        if unplaced_vehicles:
            st.warning(f"Kendaraan berikut tidak dapat ditempatkan: {', '.join(unplaced_vehicles)}")
        else:
            st.success("Semua kendaraan berhasil ditempatkan!")
            
    else:
        st.info("Klik 'Jalankan Simulasi Penempatan' untuk melihat hasilnya.")
