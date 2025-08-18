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

def attempt_place_single_vehicle(ship_dims, ship_balance_point, current_placed_vehicles, vehicle_type_to_add):
    """
    Mencoba menempatkan satu kendaraan baru ke kapal, dengan mempertimbangkan kendaraan yang sudah ada.
    Mengembalikan (True, best_position) jika berhasil, atau (False, None) jika tidak.
    Prioritas diberikan pada posisi yang meminimalkan jarak CG gabungan ke titik seimbang kapal.
    """
    ship_length, ship_width = ship_dims
    panjang_kendaraan, lebar_kendaraan = VEHICLE_DATA["dimensi"][vehicle_type_to_add]

    best_position = None
    min_distance = float('inf')

    # Hasilkan titik-titik kandidat untuk penempatan kendaraan baru.
    # Dimulai dengan (0,0) dan sudut-sudut di sebelah kanan dan di atas kendaraan yang sudah ditempatkan.
    candidate_points = [(0, 0)]
    for pv in current_placed_vehicles:
        px, py, pw, ph = pv['rect']
        # Titik di kanan kendaraan yang ditempatkan
        candidate_points.append((px + pw, py))
        # Titik di atas kendaraan yang ditempatkan
        candidate_points.append((px, py + ph))
        # Titik di kanan atas (untuk slot diagonal)
        candidate_points.append((px + pw, py + ph))

    # Saring titik kandidat yang unik dan berada di dalam batas kapal.
    # Juga pastikan titik kandidat tidak berada di dalam kendaraan yang sudah ditempatkan.
    unique_candidate_points = set()
    for cp in candidate_points:
        if 0 <= cp[0] <= ship_length and 0 <= cp[1] <= ship_width:
            is_inside_any_placed = False
            for pv in current_placed_vehicles:
                px, py, pw, ph = pv['rect']
                # Periksa apakah titik kandidat berada di dalam area kendaraan yang sudah ditempatkan
                if px < cp[0] < px + pw and py < cp[1] < py + ph:
                    is_inside_any_placed = True
                    break
            if not is_inside_any_placed:
                unique_candidate_points.add(cp)
    
    candidate_points = list(unique_candidate_points)
    candidate_points.sort(key=lambda p: (p[0], p[1])) # Urutkan untuk pencarian yang konsisten

    # Iterasi melalui titik kandidat yang valid dan temukan posisi terbaik
    for cx, cy in candidate_points:
        # Periksa apakah kendaraan muat dari titik kandidat ini dalam batas kapal
        if cx + panjang_kendaraan <= ship_length and cy + lebar_kendaraan <= ship_width:
            new_vehicle_rect_proposal = (cx, cy, panjang_kendaraan, lebar_kendaraan)
            
            # Periksa tumpang tindih dengan kendaraan yang sudah ditempatkan
            if not check_overlap(new_vehicle_rect_proposal, current_placed_vehicles):
                # Buat salinan sementara dari semua kendaraan (saat ini + yang baru diusulkan)
                temp_all_vehicles = copy.deepcopy(current_placed_vehicles)
                temp_all_vehicles.append({'tipe': vehicle_type_to_add, 'rect': new_vehicle_rect_proposal})

                # Hitung CG gabungan dari semua kendaraan dan jaraknya ke titik seimbang kapal
                cg_x, cg_y = calculate_combined_cg(temp_all_vehicles)
                distance = np.sqrt((cg_x - ship_balance_point[0])**2 + (cg_y - ship_balance_point[1])**2)

                # Jika jarak ini lebih kecil, update posisi terbaik
                if distance < min_distance:
                    min_distance = distance
                    best_position = new_vehicle_rect_proposal

    if best_position:
        return True, best_position
    else:
        return False, None

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
if 'vehicles_to_load_request' not in st.session_state:
    st.session_state.vehicles_to_load_request = [] # Ini adalah daftar permintaan user
if 'placed_vehicles_on_ship' not in st.session_state:
    st.session_state.placed_vehicles_on_ship = [] # Ini adalah daftar kendaraan yang berhasil ditempatkan
if 'last_placement_status' not in st.session_state:
    st.session_state.last_placement_status = "" # Untuk pesan notifikasi

# --- SIDEBAR UNTUK INPUT ---
with st.sidebar:
    st.header("1. Parameter Kapal")
    # Simpan parameter kapal di session state agar bisa diakses oleh callback
    st.session_state.ship_length = st.number_input("Masukkan Panjang Kapal (meter)", min_value=1.0, value=50.0, step=0.5, format="%.1f")
    st.session_state.ship_width = st.number_input("Masukkan Lebar Kapal (meter)", min_value=1.0, value=15.0, step=0.5, format="%.1f")
    st.session_state.balance_point_x = st.number_input("Titik Seimbang Panjang (meter)", min_value=0.0, max_value=st.session_state.ship_length, value=st.session_state.ship_length/2, step=0.5, format="%.1f")
    st.session_state.balance_point_y = st.session_state.ship_width / 2 # Titik seimbang lebar selalu di tengah
    st.info(f"Titik Seimbang Kapal (P, L): ({st.session_state.balance_point_x:.2f} m, {st.session_state.balance_point_y:.2f} m)")
    
    st.header("2. Tambah Kendaraan")
    vehicle_options = list(VEHICLE_DATA["dimensi"].keys())
    
    # Selectbox untuk memilih jenis kendaraan yang akan ditambahkan
    st.selectbox(
        "Pilih Golongan Kendaraan", 
        options=vehicle_options, 
        key='selected_vehicle' # Menggunakan key untuk mengakses nilai dari session_state
    )
    
    # Fungsi callback saat tombol 'Tambah Kendaraan' ditekan
    def add_vehicle_callback():
        ship_dims = (st.session_state.ship_length, st.session_state.ship_width)
        ship_balance_point = (st.session_state.balance_point_x, st.session_state.balance_point_y)
        
        # Coba tempatkan kendaraan baru secara inkremental
        success, position = attempt_place_single_vehicle(
            ship_dims,
            ship_balance_point,
            st.session_state.placed_vehicles_on_ship, # Kendaraan yang sudah ada sebagai hambatan
            st.session_state.selected_vehicle
        )

        if success:
            # Jika berhasil, tambahkan ke daftar kendaraan yang benar-benar ditempatkan
            st.session_state.placed_vehicles_on_ship.append({
                'tipe': st.session_state.selected_vehicle,
                'rect': position,
                'id': len(st.session_state.vehicles_to_load_request) # Gunakan id unik, bisa index
            })
            # Tambahkan juga ke daftar permintaan (ini akan menjadi "Daftar Muatan")
            st.session_state.vehicles_to_load_request.append(st.session_state.selected_vehicle)
            st.session_state.last_placement_status = "success"
        else:
            st.session_state.last_placement_status = "failed"
            # Jangan tambahkan ke daftar permintaan atau daftar ditempatkan jika gagal
    
    # Fungsi callback saat tombol 'Reset Daftar' ditekan
    def reset_vehicles_callback():
        st.session_state.vehicles_to_load_request = []
        st.session_state.placed_vehicles_on_ship = [] # Penting: Bersihkan juga daftar kendaraan di kapal
        st.session_state.last_placement_status = ""

    # Tombol untuk menambah dan mereset kendaraan
    st.button("➕ Tambah Kendaraan", on_click=add_vehicle_callback)
    st.button("🗑️ Reset Daftar", on_click=reset_vehicles_callback)

# --- AREA UTAMA DENGAN LAYOUT BARU ---
# Menggunakan st.container() dengan width=True untuk membuat bagian ini mengisi lebar penuh horizontal
with st.container():
    st.header("Hasil Simulasi")
    
    placed_vehicles = st.session_state.placed_vehicles_on_ship # Ambil dari state yang benar
    ship_dims = (st.session_state.ship_length, st.session_state.ship_width)
    ship_balance_point = (st.session_state.balance_point_x, st.session_state.balance_point_y)

    if placed_vehicles:
        fig = visualize_placement(ship_dims, ship_balance_point, placed_vehicles)
        st.pyplot(fig, use_container_width=True) # Menggunakan use_container_width agar plot menyesuaikan lebar container
    else:
        st.info("Tambahkan kendaraan dari sidebar untuk memulai simulasi.")
        # Menampilkan visualisasi dek kapal kosong jika belum ada kendaraan yang ditambahkan
        fig, ax = plt.subplots(figsize=(12, max(6, ship_dims[1] / ship_dims[0] * 12))) # Ukuran konsisten
        ship_deck = patches.Rectangle((0, 0), ship_dims[0], ship_dims[1], linewidth=2, edgecolor='black', facecolor='lightgray')
        ax.add_patch(ship_deck)
        ax.plot(ship_balance_point[0], ship_balance_point[1], 'rX', markersize=12, label='Titik Seimbang Kapal', mew=2)
        ax.set_xlim(0, ship_dims[0])
        ax.set_ylim(0, ship_dims[1])
        ax.set_aspect('equal', adjustable='box')
        plt.title("Dek Kapal Kosong")
        plt.legend()
        st.pyplot(fig, use_container_width=True) # Menggunakan use_container_width

# --- Notifikasi Kendaraan Tidak Dapat Dimuat ---
# Memberikan umpan balik yang jelas dari status penempatan terakhir
if st.session_state.last_placement_status == "failed":
    st.error(f"⚠️ Peringatan: Kendaraan {st.session_state.selected_vehicle} tidak dapat ditempatkan. Kapal mungkin penuh atau tidak ada ruang yang cocok.")
elif st.session_state.last_placement_status == "success":
    st.success("🎉 Kendaraan berhasil ditempatkan!")
st.session_state.last_placement_status = "" # Reset status setelah ditampilkan

st.markdown("---") # Garis pemisah untuk layout

# --- Daftar Muatan ---
st.header("Daftar Muatan")
if not st.session_state.vehicles_to_load_request:
    st.write("Belum ada kendaraan yang ditambahkan.")
else:
    # Membuat DataFrame dengan detail kendaraan yang lebih lengkap (dimensi dan berat)
    data_for_df = []
    for vehicle_type in st.session_state.vehicles_to_load_request:
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
placed_vehicles = st.session_state.placed_vehicles_on_ship # Gunakan data yang benar
if placed_vehicles:
    luas_kapal = st.session_state.ship_length * st.session_state.ship_width
    luas_terpakai = sum(v['rect'][2] * v['rect'][3] for v in placed_vehicles)
    persentase_terpakai = (luas_terpakai / luas_kapal) * 100 if luas_kapal > 0 else 0
    
    cg_x, cg_y = calculate_combined_cg(placed_vehicles)
    jarak_cg = np.sqrt((cg_x - st.session_state.balance_point_x)**2 + (cg_y - st.session_state.balance_point_y)**2)

    st.metric("Jumlah Kendaraan Ditempatkan", f"{len(placed_vehicles)} dari {len(st.session_state.vehicles_to_load_request)}")
    st.metric("Penggunaan Area Dek", f"{persentase_terpakai:.2f} %")
    st.metric("Jarak Titik Berat Muatan ke Titik Seimbang Kapal", f"{jarak_cg:.2f} m")
else:
    st.metric("Jumlah Kendaraan Ditempatkan", "0")
    st.metric("Penggunaan Area Dek", "0.00 %")
    st.metric("Jarak Titik Berat Muatan ke Titik Seimbang Kapal", "N/A")
