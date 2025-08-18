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
        x1, y1, w1, h1 = new_vehicle_rect
        x2, y2, w2, h2 = placed['rect']
        # Memeriksa tumpang tindih (true jika ada tumpang tindih)
        if not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1):
            return True
    return False

def calculate_combined_cg(vehicles):
    """Menghitung titik berat gabungan dari semua kendaraan yang dimuat."""
    if not vehicles:
        return 0, 0
    total_weight = sum(VEHICLE_DATA["berat"][v['tipe']] for v in vehicles)
    if total_weight == 0:
        return 0, 0 # Menghindari pembagian dengan nol jika tidak ada berat
    weighted_sum_x = sum((v['rect'][0] + v['rect'][2] / 2) * VEHICLE_DATA["berat"][v['tipe']] for v in vehicles)
    weighted_sum_y = sum((v['rect'][1] + v['rect'][3] / 2) * VEHICLE_DATA["berat"][v['tipe']] for v in vehicles)
    return weighted_sum_x / total_weight, weighted_sum_y / total_weight

def find_optimal_placement(ship_dims, ship_balance_point, vehicles_to_load):
    """
    Algoritma Greedy untuk menemukan penempatan kendaraan yang optimal.
    Mencoba menempatkan kendaraan berdasarkan kedekatan dengan titik seimbang kapal,
    dan tidak menghilangkan kendaraan yang sudah berhasil ditempatkan.
    """
    ship_length, ship_width = ship_dims
    placed_vehicles = []
    unplaced_vehicles = []
    
    # Urutkan kendaraan dari yang terbesar agar yang besar punya prioritas tempat
    sorted_vehicles = sorted(vehicles_to_load, key=lambda v: VEHICLE_DATA["dimensi"][v][0] * VEHICLE_DATA["dimensi"][v][1], reverse=True)
    
    GRID_STEP = 0.5 # Langkah grid untuk pencarian posisi

    for i, vehicle_type in enumerate(sorted_vehicles):
        panjang_kendaraan, lebar_kendaraan = VEHICLE_DATA["dimensi"][vehicle_type]
        best_position = None
        min_distance = float('inf')

        # Iterasi melalui semua kemungkinan posisi pada grid kapal
        for x in np.arange(0, ship_length - panjang_kendaraan + GRID_STEP, GRID_STEP):
            for y in np.arange(0, ship_width - lebar_kendaraan + GRID_STEP, GRID_STEP):
                new_vehicle_rect = (x, y, panjang_kendaraan, lebar_kendaraan)
                
                # Periksa tumpang tindih dengan kendaraan yang sudah ditempatkan
                if not check_overlap(new_vehicle_rect, placed_vehicles):
                    # Buat salinan sementara untuk menghitung CG baru
                    temp_placed = copy.deepcopy(placed_vehicles)
                    temp_placed.append({'tipe': vehicle_type, 'rect': new_vehicle_rect})
                    
                    # Hitung CG gabungan dan jarak ke titik seimbang kapal
                    cg_x, cg_y = calculate_combined_cg(temp_placed)
                    distance = np.sqrt((cg_x - ship_balance_point[0])**2 + (cg_y - ship_balance_point[1])**2)
                    
                    # Jika jarak lebih kecil, update posisi terbaik
                    if distance < min_distance:
                        min_distance = distance
                        best_position = new_vehicle_rect

        # Jika posisi terbaik ditemukan, tempatkan kendaraan
        if best_position:
            placed_vehicles.append({'tipe': vehicle_type, 'rect': best_position, 'id': i})
        else:
            # Jika tidak ada tempat yang cocok, tambahkan ke daftar kendaraan yang tidak ditempatkan
            unplaced_vehicles.append(vehicle_type)
            
    return placed_vehicles, unplaced_vehicles

def visualize_placement(ship_dims, ship_balance_point, placed_vehicles):
    """Membuat visualisasi penempatan kendaraan di atas kapal."""
    ship_length, ship_width = ship_dims
    # Mengatur ukuran figure agar responsif
    fig, ax = plt.subplots(figsize=(12, max(6, ship_width * 0.4))) # Menyesuaikan tinggi berdasarkan lebar kapal
    
    # Menggambar dek kapal
    ship_deck = patches.Rectangle((0, 0), ship_length, ship_width, linewidth=2, edgecolor='black', facecolor='lightgray')
    ax.add_patch(ship_deck)

    # Menggambar setiap kendaraan yang ditempatkan
    for vehicle in placed_vehicles:
        x, y, w, h = vehicle['rect']
        color = VEHICLE_DATA["warna"][vehicle['tipe']]
        rect = patches.Rectangle((x, y), w, h, linewidth=1.5, edgecolor='black', facecolor=color, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, vehicle['tipe'], ha='center', va='center', fontsize=8, weight='bold')

    # Menandai titik seimbang kapal
    ax.plot(ship_balance_point[0], ship_balance_point[1], 'rX', markersize=12, label='Titik Seimbang Kapal', mew=2)
    
    # Menandai titik berat muatan jika ada kendaraan yang ditempatkan
    if placed_vehicles:
        cg_x, cg_y = calculate_combined_cg(placed_vehicles)
        ax.plot(cg_x, cg_y, 'bo', markersize=10, label='Titik Berat Muatan', alpha=0.8)

    # Mengatur batas plot dan aspek rasio
    ax.set_xlim(0, ship_length)
    ax.set_ylim(0, ship_width)
    ax.set_aspect('equal', adjustable='box')
    plt.xlabel("Panjang Kapal (meter)")
    plt.ylabel("Lebar Kapal (meter)")
    plt.title("Visualisasi Simulasi Muat Kapal")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout() # Memastikan semua elemen pas dalam figure
    return fig

# --- UI STREAMLIT ---

st.set_page_config(layout="wide") # Mengatur tata letak halaman menjadi lebar penuh
st.title("🚢 Aplikasi Simulasi Muat Kapal Optimal (Real-time)")

# Inisialisasi session state untuk menjaga status aplikasi
if 'vehicles_to_load' not in st.session_state:
    st.session_state.vehicles_to_load = []
if 'simulation_result' not in st.session_state:
    st.session_state.simulation_result = ([], [])

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
    
    # Selectbox untuk memilih jenis kendaraan
    st.selectbox(
        "Pilih Golongan Kendaraan", 
        options=vehicle_options, 
        key='selected_vehicle' # Menggunakan key untuk mengakses nilai dari session_state
    )
    
    # Fungsi callback untuk menambahkan kendaraan
    def add_vehicle():
        st.session_state.vehicles_to_load.append(st.session_state.selected_vehicle)

    # Fungsi callback untuk mereset daftar kendaraan
    def reset_vehicles():
        st.session_state.vehicles_to_load = []
        st.session_state.simulation_result = ([], []) # Juga reset hasil simulasi
        st.session_state.last_params = None # Memaksa simulasi ulang

    # Tombol untuk menambah dan mereset kendaraan
    st.button("➕ Tambah Kendaraan", on_click=add_vehicle)
    st.button("🗑️ Reset Daftar", on_click=reset_vehicles)

# --- LOGIKA SIMULASI REALTIME ---
# Memeriksa apakah parameter input telah berubah untuk memicu simulasi ulang
current_params = (ship_length, ship_width, balance_point_x, tuple(sorted(st.session_state.vehicles_to_load)))
if 'last_params' not in st.session_state or st.session_state.last_params != current_params:
    st.session_state.last_params = current_params
    if st.session_state.vehicles_to_load:
        with st.spinner("Mensimulasikan ulang penempatan..."):
            ship_dims = (ship_length, ship_width)
            ship_balance_point = (balance_point_x, balance_point_y)
            placed, unplaced = find_optimal_placement(ship_dims, ship_balance_point, st.session_state.vehicles_to_load)
            st.session_state.simulation_result = (placed, unplaced)
    else:
        st.session_state.simulation_result = ([], []) # Reset hasil jika daftar kosong

# --- AREA UTAMA DENGAN LAYOUT BARU ---
st.header("Hasil Simulasi")

placed_vehicles, unplaced_vehicles = st.session_state.simulation_result

if placed_vehicles:
    fig = visualize_placement((ship_length, ship_width), (balance_point_x, balance_point_y), placed_vehicles)
    st.pyplot(fig)
else:
    st.info("Tambahkan kendaraan dari sidebar untuk memulai simulasi.")
    # Menampilkan dek kapal kosong jika belum ada kendaraan yang ditambahkan
    fig, ax = plt.subplots(figsize=(12, max(6, ship_width * 0.4)))
    ship_deck = patches.Rectangle((0, 0), ship_length, ship_width, linewidth=2, edgecolor='black', facecolor='lightgray')
    ax.add_patch(ship_deck)
    ax.plot(balance_point_x, balance_point_y, 'rX', markersize=12, label='Titik Seimbang Kapal', mew=2)
    ax.set_xlim(0, ship_length)
    ax.set_ylim(0, ship_width)
    ax.set_aspect('equal', adjustable='box')
    plt.title("Dek Kapal Kosong")
    plt.legend()
    st.pyplot(fig)

# --- Notifikasi Kendaraan Tidak Dapat Dimuat ---
if unplaced_vehicles:
    st.error(f"⚠️ Peringatan: {unplaced_vehicles} kendaraan tidak dapat ditempatkan: {', '.join(unplaced_vehicles)}")
else:
    if st.session_state.vehicles_to_load: # Hanya tampilkan sukses jika ada kendaraan yang diusulkan
        st.success("🎉 Semua kendaraan berhasil ditempatkan!")

st.markdown("---") # Garis pemisah untuk layout

# --- Daftar Muatan ---
st.header("Daftar Muatan")
if not st.session_state.vehicles_to_load:
    st.write("Belum ada kendaraan yang ditambahkan.")
else:
    # Membuat DataFrame dengan detail kendaraan yang lebih lengkap
    data_for_df = []
    for vehicle_type in st.session_state.vehicles_to_load:
        panjang, lebar = VEHICLE_DATA["dimensi"][vehicle_type]
        berat = VEHICLE_DATA["berat"][vehicle_type]
        data_for_df.append({
            "Golongan": vehicle_type,
            "Dimensi (P x L)": f"{panjang}x{lebar} m",
            "Berat (ton)": berat
        })
    df_vehicles = pd.DataFrame(data_for_df)
    st.dataframe(df_vehicles, use_container_width=True, hide_index=True)
    
st.markdown("---") # Garis pemisah untuk layout

# --- Ringkasan Optimal ---
st.header("Ringkasan Optimal")
if placed_vehicles:
    luas_kapal = ship_length * ship_width
    luas_terpakai = sum(v['rect'][2] * v['rect'][3] for v in placed_vehicles)
    persentase_terpakai = (luas_terpakai / luas_kapal) * 100 if luas_kapal > 0 else 0
    
    cg_x, cg_y = calculate_combined_cg(placed_vehicles)
    jarak_cg = np.sqrt((cg_x - balance_point_x)**2 + (cg_y - balance_point_y)**2)

    st.metric("Jumlah Kendaraan Ditempatkan", f"{len(placed_vehicles)} dari {len(st.session_state.vehicles_to_load)}")
    st.metric("Penggunaan Area Dek", f"{persentase_terpakai:.2f} %")
    st.metric("Jarak Titik Berat Muatan ke Titik Seimbang Kapal", f"{jarak_cg:.2f} m")
else:
    st.metric("Jumlah Kendaraan Ditempatkan", "0")
    st.metric("Penggunaan Area Dek", "0.00 %")
    st.metric("Jarak Titik Berat Muatan ke Titik Seimbang Kapal", "N/A")

