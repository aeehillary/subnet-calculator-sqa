---
title: "Fitur Alokasi VLSM (Variable Length Subnet Mask)"
labels: ["feature"]
---

## Deskripsi Fitur
Menambahkan kalkulator alokasi Variable Length Subnet Mask (VLSM) untuk membagi satu blok jaringan IPv4 (format CIDR) ke beberapa subnet berdasarkan daftar kebutuhan host.

## Spesifikasi Kebutuhan
1. **Fungsi Alokasi (`alokasi_vlsm`)**:
   - Menerima `network` berupa CIDR (contoh: `192.168.1.0/24`) dan `kebutuhan_host` berupa list bilangan bulat positif (contoh: `[100, 50, 20, 2]`).
   - Mengalokasikan blok subnet dimulai dari kebutuhan host terbesar ke terkecil (best-fit decreasing order), tetapi hasil akhir dikembalikan sesuai urutan input asli.
   - Mengembalikan daftar dictionary dengan struktur:
     - `network_cidr`: Alamat jaringan dan prefix baru (contoh: `192.168.1.0/25`)
     - `mask`: Subnet mask desimal bertitik (contoh: `255.255.255.128`)
     - `broadcast`: Broadcast address
     - `first_host`: Host usable pertama
     - `last_host`: Host usable terakhir
     - `usable_hosts`: Jumlah host yang dapat dipakai
   - Validasi error (melempar `ValueError`):
     - Format network tidak valid atau bukan CIDR
     - Prefix di luar 0–32
     - Daftar kebutuhan host kosong
     - Kebutuhan host <= 0
     - Total kapasitas network tidak mencukupi untuk menampung seluruh subnet yang diminta.

2. **Endpoint API**:
   - `POST /api/vlsm`
   - Request Body JSON: `{"network": "192.168.1.0/24", "kebutuhan_host": [100, 50, 20, 2]}`
   - Response: JSON list alokasi subnet
   - HTTP 400 Bad Request jika input tidak valid.

3. **Antarmuka Web**:
   - Tab navigasi untuk beralih antara Subnet Calculator dan VLSM.
   - Form input network CIDR dan kebutuhan host.
   - Tabel hasil perhitungan subnet VLSM yang responsif.
