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
    """
    Mengecek apakah kendaraan baru tumpang tindih dengan kendaraan yang sudah ditempatkan.
    Mengembalikan True jika ada tumpang tindih, False jika tidak.
    """
    x1, y1, w1, h1 = new_vehicle_rect
    for placed in placed_vehicles:
        x2, y2, w2, h2 = placed['rect']
        # Kondisi tidak tumpang tindih: jika satu persegi panjang berada di kiri, kanan, atas, atau bawah yang lain
        if (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1):
            continue # Tidak tumpang tindih, lanjutkan ke kendaraan berikutnya
        else:
            return True # Ada tumpang tindih
    return False # Tidak ada tumpang tindih dengan kendaraan mana pun

def calculate_combined_cg(vehicles):
    """Menghitung titik berat gabungan dari semua kendaraan yang dimuat."""
    if not vehicles:
        return 0, 0
    total_weight = sum(VEHICLE_DATA["berat"][v['tipe']] for v in vehicles)
    if total_weight == 0:
        return 0, 0 # Menghindari pembagian dengan nol jika tidak ada berat
    
    weighted_sum_x = 0
    weighted_sum_y = 0

    for v in vehicles:
        # Titik tengah X dan Y kendaraan
        mid_x = v['rect'][0] + v['rect'][2] / 2
        mid_y = v['rect'][1] + v['rect'][3] / 2
        weight = VEHICLE_DATA["berat"][v['tipe']]
        weighted_sum_x += mid_x * weight
        weighted_sum_y += mid_y * weight
        
    return weighted_sum_x / total_weight, weighted_sum_y / total_weight

def find_optimal_placement(ship_dims, ship_balance_point, vehicles_to_load_original):
    """
    Algoritma Greedy untuk menemukan penempatan kendaraan yang optimal.
    Menggunakan pendekatan 'candidate points' untuk mengoptimalkan ruang pencarian.
    Akan menempatkan kendaraan dalam urutan yang diberikan, tanpa menggantikan yang sudah ada.
    Kendaraan pertama akan diutamakan untuk ditempatkan di tengah kapal.
    """
    ship_length, ship_width = ship_dims
    placed_vehicles = []
    unplaced_vehicles = []

    # Membuat salinan daftar kendaraan yang akan dimuat untuk diurutkan
    vehicles_to_load_sorted = sorted(vehicles_to_load_original, key=lambda v: VEHICLE_DATA["dimensi"][v][0] * VEHICLE_DATA["dimensi"][v][1], reverse=True)

    # Inisialisasi daftar titik-titik kandidat untuk penempatan kendaraan baru.
    candidate_points = [(0, 0)] # Dimulai dengan titik (0,0).

    for i, vehicle_type in enumerate(vehicles_to_load_sorted):
        panjang_kendaraan, lebar_kendaraan = VEHICLE_DATA["dimensi"][vehicle_type]
        best_position = None
        min_distance = float('inf')
        
        # --- LOGIKA KHUSUS UNTUK KENDARAAN PERTAMA ---
        if not placed_vehicles: # Jika ini adalah kendaraan pertama yang akan ditempatkan
            # Hitung posisi agar kendaraan berada tepat di tengah kapal
            center_x_ship = ship_balance_point[0]
            center_y_ship = ship_balance_point[1]
            
            # Posisi sudut kiri bawah kendaraan agar titik tengahnya berada di titik seimbang kapal
            proposed_x = center_x_ship - panjang_kendaraan / 2
            proposed_y = center_y_ship - lebar_kendaraan / 2
            
            # Periksa apakah posisi ini valid (di dalam batas kapal)
            if (0 <= proposed_x and proposed_x + panjang_kendaraan <= ship_length and
                0 <= proposed_y and proposed_y + lebar_kendaraan <= ship_width):
                
                # Jika valid, jadikan ini posisi terbaik untuk kendaraan pertama
                best_position = (proposed_x, proposed_y, panjang_kendaraan, lebar_kendaraan)
                min_distance = 0 # Jarak ideal, langsung pilih ini
            
            # Jika tidak bisa ditempatkan tepat di tengah, fallback ke pencarian greedy normal
            # (Tidak perlu else, karena best_position akan tetap None, dan loop di bawah akan berjalan)
        # --- AKHIR LOGIKA KHUSUS KENDARAAN PERTAMA ---
        
        # Jika best_position belum ditemukan (bukan kendaraan pertama atau tidak bisa di tengah),
        # lakukan pencarian greedy dari titik kandidat yang ada.
        if best_position is None:
            # Buat daftar kandidat posisi yang valid (tidak tumpang tindih dan dalam batas kapal)
            valid_candidate_positions = []
            for cx, cy in sorted(candidate_points, key=lambda p: (p[0], p[1])):
                if cx + panjang_kendaraan <= ship_length and cy + lebar_kendaraan <= ship_width:
                    new_vehicle_rect_proposal = (cx, cy, panjang_kendaraan, lebar_kendaraan)
                    if not check_overlap(new_vehicle_rect_proposal, placed_vehicles):
                        valid_candidate_positions.append(new_vehicle_rect_proposal)
            
            # Dari kandidat yang valid, pilih yang paling optimal berdasarkan jarak ke CG kapal
            for proposed_rect in valid_candidate_positions:
                temp_placed = copy.deepcopy(placed_vehicles)
                temp_placed.append({'tipe': vehicle_type, 'rect': proposed_rect})
                
                cg_x, cg_y = calculate_combined_cg(temp_placed)
                distance = np.sqrt((cg_x - ship_balance_point[0])**2 + (cg_y - ship_balance_point[1])**2)
                
                if distance < min_distance:
                    min_distance = distance
                    best_position = proposed_rect
        
        if best_position:
            # Tempatkan kendaraan jika posisi terbaik ditemukan
            placed_vehicles.append({'tipe': vehicle_type, 'rect': best_position, 'id': i})
            
            # Hasilkan titik kandidat baru dari sudut kendaraan yang baru ditempatkan
            vx, vy, vw, vh = best_position
            
            newly_generated_points = []
            newly_generated_points.append((vx + vw, vy)) # Sudut kanan-bawah dari kotak kendaraan
            newly_generated_points.append((vx, vy + vh)) # Sudut kiri-atas dari kotak kendaraan
            
            # Tambahkan juga titik yang dihasilkan dari sudut-sudut lain dari kotak kendaraan yang baru ditempatkan
            # Ini bisa membantu menemukan slot di antara kendaraan.
            newly_generated_points.append((vx + vw, vy + vh)) # Sudut kanan-atas dari kotak kendaraan
            newly_generated_points.append((vx, vy)) # Sudut kiri-bawah kendaraan itu sendiri (jika ada ruang di kiri/bawahnya)

            # Gabungkan dan saring titik kandidat
            unique_candidate_points = set(candidate_points) # Mulai dengan yang sudah ada
            
            for ncp in newly_generated_points:
                # Hanya tambahkan jika di dalam batas kapal dan tidak tumpang tindih dengan kendaraan yang sudah ada
                if 0 <= ncp[0] <= ship_length and 0 <= ncp[1] <= ship_width:
                    is_inside_placed = False
                    for pv in placed_vehicles:
                        px, py, pw, ph = pv['rect']
                        # Jika titik kandidat berada dalam (atau di batas) kendaraan yang ditempatkan, jangan tambahkan
                        if px < ncp[0] < px + pw and py < ncp[1] < py + ph: # Gunakan < untuk memastikan tidak di batas
                            is_inside_placed = True
                            break
                    if not is_inside_placed:
                        unique_candidate_points.add(ncp)
            
            candidate_points = list(unique_candidate_points)
            # Sortir untuk konsistensi (membantu stabilitas algoritma greedy)
            candidate_points.sort(key=lambda p: (p[0], p[1]))

        else:
            # Jika tidak ada posisi yang cocok ditemukan, tambahkan kendaraan ke daftar yang tidak dapat ditempatkan
            unplaced_vehicles.append(vehicle_type)
    
    return placed_vehicles, unplaced_vehicles

def visualize_placement(ship_dims, ship_balance_point, placed_vehicles):
    """Membuat visualisasi penempatan kendaraan di atas kapal."""
    ship_length, ship_width = ship_dims
    
    # Mengatur ukuran figure agar responsif dan proporsional.
    fig, ax = plt.subplots(figsize=(12, max(6, ship_width / ship_length * 12))) 
    
    # Menggambar dek kapal sebagai persegi panjang
    ship_deck = patches.Rectangle((0, 0), ship_length, ship_width, linewidth=2, edgecolor='black', facecolor='lightgray')
    ax.add_patch(ship_deck)

    # Menggambar setiap kendaraan yang ditempatkan sebagai persegi panjang berwarna
    for vehicle in placed_vehicles:
        x, y, w, h = vehicle['rect']
        color = VEHICLE_DATA["warna"][vehicle['tipe']]
        rect = patches.Rectangle((x, y), w, h, linewidth=1.5, edgecolor='black', facecolor=color, alpha=0.9)
        ax.add_patch(rect)
        # Menambahkan label tipe kendaraan di tengahnya
        ax.text(x + w/2, y + h/2, vehicle['tipe'], ha='center', va='center', fontsize=8, weight='bold')

    # Menandai titik seimbang kapal dengan tanda 'X' merah
    ax.plot(ship_balance_point[0], ship_balance_point[1], 'rX', markersize=12, label='Titik Seimbang Kapal', mew=2)
    
    # Menandai titik berat muatan jika ada kendaraan yang berhasil ditempatkan
    if placed_vehicles:
        cg_x, cg_y = calculate_combined_cg(placed_vehicles)
        ax.plot(cg_x, cg_y, 'bo', markersize=10, label='Titik Berat Muatan', alpha=0.8)

    # Mengatur batas sumbu plot dan memastikan aspek rasio yang sama untuk tampilan yang akurat
    ax.set_xlim(0, ship_length)
    ax.set_ylim(0, ship_width)
    ax.set_aspect('equal', adjustable='box')
    plt.xlabel("Panjang Kapal (meter)")
    plt.ylabel("Lebar Kapal (meter)")
    plt.title("Visualisasi Simulasi Muat Kapal")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6) # Menambahkan grid untuk referensi
    plt.tight_layout() # Memastikan semua elemen pas dalam figure
    return fig

# --- UI STREAMLIT ---

st.set_page_config(layout="wide") # Mengatur tata letak halaman menjadi lebar penuh
st.title("🚢 Aplikasi Simulasi Muat Kapal Optimal (Real-time)")

# Inisialisasi session state untuk menjaga status aplikasi antar interaksi pengguna
if 'vehicles_to_load' not in st.session_state:
    st.session_state.vehicles_to_load = []
if 'simulation_result' not in st.session_state:
    st.session_state.simulation_result = ([], [])
if 'last_params' not in st.session_state:
    st.session_state.last_params = None

# --- SIDEBAR UNTUK INPUT ---
with st.sidebar:
    st.header("1. Parameter Kapal")
    ship_length = st.number_input("Masukkan Panjang Kapal (meter)", min_value=1.0, value=50.0, step=0.5, format="%.1f")
    ship_width = st.number_input("Masukkan Lebar Kapal (meter)", min_value=1.0, value=15.0, step=0.5, format="%.1f")
    balance_point_x = st.number_input("Titik Seimbang Panjang (meter)", min_value=0.0, max_value=ship_length, value=ship_length/2, step=0.5, format="%.1f")
    balance_point_y = ship_width / 2 # Titik seimbang lebar selalu di tengah
    st.info(f"Titik Seimbang Kapal (P, L): ({balance_point_x:.2f} m, {balance_point_y:.2f} m)")
    
    st.header("2. Tambah Kendaraan")
    vehicle_options = list(VEHICLE_DATA["dimensi"].keys())
    
    # Selectbox untuk memilih jenis kendaraan yang akan ditambahkan
    st.selectbox(
        "Pilih Golongan Kendaraan", 
        options=vehicle_options, 
        key='selected_vehicle' # Menggunakan key untuk mengakses nilai dari session_state
    )
    
    # Fungsi callback saat tombol 'Tambah Kendaraan' ditekan
    def add_vehicle():
        st.session_state.vehicles_to_load.append(st.session_state.selected_vehicle)

    # Fungsi callback saat tombol 'Reset Daftar' ditekan
    def reset_vehicles():
        st.session_state.vehicles_to_load = []
        st.session_state.simulation_result = ([], []) # Juga reset hasil simulasi
        st.session_state.last_params = None # Penting: Atur ke None untuk memaksa simulasi ulang

    # Tombol untuk menambah dan mereset kendaraan
    st.button("➕ Tambah Kendaraan", on_click=add_vehicle)
    st.button("🗑️ Reset Daftar", on_click=reset_vehicles)

# --- LOGIKA SIMULASI REALTIME ---
# Memeriksa apakah parameter input (dimensi kapal, titik seimbang, atau daftar kendaraan) telah berubah
# untuk memicu simulasi ulang. Ini membuat aplikasi responsif terhadap perubahan input.
current_params = (ship_length, ship_width, balance_point_x, tuple(sorted(st.session_state.vehicles_to_load)))
if st.session_state.last_params != current_params:
    st.session_state.last_params = current_params
    if st.session_state.vehicles_to_load:
        with st.spinner("Mensimulasikan ulang penempatan..."):
            ship_dims = (ship_length, ship_width)
            ship_balance_point = (balance_point_x, balance_point_y)
            # Pastikan find_optimal_placement menerima salinan untuk menghindari modifikasi langsung
            placed, unplaced = find_optimal_placement(ship_dims, ship_balance_point, list(st.session_state.vehicles_to_load))
            st.session_state.simulation_result = (placed, unplaced)
    else:
        st.session_state.simulation_result = ([], []) # Reset hasil jika daftar kendaraan kosong

# --- AREA UTAMA DENGAN LAYOUT BARU ---
# Menggunakan st.container() dengan width=True untuk membuat bagian ini mengisi lebar penuh horizontal
with st.container():
    st.header("Hasil Simulasi")
    placed_vehicles, unplaced_vehicles = st.session_state.simulation_result
    
    if placed_vehicles:
        fig = visualize_placement((ship_length, ship_width), (balance_point_x, balance_point_y), placed_vehicles)
        st.pyplot(fig, use_container_width=True) # Menggunakan use_container_width agar plot menyesuaikan lebar container
    else:
        st.info("Tambahkan kendaraan dari sidebar untuk memulai simulasi.")
        # Menampilkan visualisasi dek kapal kosong jika belum ada kendaraan yang ditambahkan
        fig, ax = plt.subplots(figsize=(12, max(6, ship_width / ship_length * 12))) # Ukuran konsisten dengan visualisasi penuh
        ship_deck = patches.Rectangle((0, 0), ship_length, ship_width, linewidth=2, edgecolor='black', facecolor='lightgray')
        ax.add_patch(ship_deck)
        ax.plot(balance_point_x, balance_point_y, 'rX', markersize=12, label='Titik Seimbang Kapal', mew=2)
        ax.set_xlim(0, ship_length)
        ax.set_ylim(0, ship_width)
        ax.set_aspect('equal', adjustable='box')
        plt.title("Dek Kapal Kosong")
        plt.legend()
        st.pyplot(fig, use_container_width=True) # Menggunakan use_container_width

# --- Notifikasi Kendaraan Tidak Dapat Dimuat ---
# Memberikan umpan balik yang jelas jika ada kendaraan yang tidak dapat ditempatkan
if unplaced_vehicles:
    st.error(f"⚠️ Peringatan: {len(unplaced_vehicles)} kendaraan tidak dapat ditempatkan: {', '.join(unplaced_vehicles)}")
else:
    # Hanya tampilkan pesan sukses jika memang ada kendaraan yang diusulkan untuk dimuat
    if st.session_state.vehicles_to_load: 
        st.success("🎉 Semua kendaraan berhasil ditempatkan!")

st.markdown("---") # Garis pemisah untuk layout

# --- Daftar Muatan ---
st.header("Daftar Muatan")
if not st.session_state.vehicles_to_load:
    st.write("Belum ada kendaraan yang ditambahkan.")
else:
    # Membuat DataFrame dengan detail kendaraan yang lebih lengkap (dimensi dan berat)
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
