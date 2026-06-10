# ⚡ SQL to Drizzle Studio Migrator

Sebuah aplikasi [Streamlit](https://streamlit.io/) sederhana untuk mengonversi dump database MySQL (`.sql`) menjadi skema [Drizzle ORM](https://orm.drizzle.team/) (`schema.ts`) dan file SQL untuk seeding data yang kompatibel dengan PostgreSQL.

## ✨ Fitur Utama
- **Konversi Tipe Data Cerdas:** Mengonversi tipe data MySQL ke tipe data PostgreSQL yang didukung oleh Drizzle ORM secara otomatis.
- **Deteksi Primary Key:** Mengenali kolom `id` atau `PRIMARY KEY` dan mengubahnya menjadi `serial().primaryKey()`.
- **CamelCase Mapping:** Opsional (dalam logika) untuk pemetaan nama tabel dan kolom.
- **Sanitasi Data `INSERT`:** Membersihkan leading-zeros pada nilai desimal dan menangani nilai string yang kompleks melalui tokenisasi SQL manual.
- **Sinkronisasi Sequence:** Menghasilkan script SQL untuk me-reset PostgreSQL sequence agar sesuai dengan nilai `id` tertinggi setelah import data.
- **Logging Analisis Detail:** Menyediakan log langkah-demi-langkah dari proses parsing dan konversi.

## 📁 Struktur Proyek
```text
dotsql-to-drizzle/
├── app.py              # Logika utama aplikasi Streamlit
├── requirements.txt    # Daftar dependensi Python
├── README.md           # Dokumentasi proyek
└── .gitignore          # File pengecualian Git
```

## 🚀 Persiapan
Pastikan Anda telah menginstal [Python 3.10+](https://www.python.org/).

1. **Clone repositori ini:**
   ```bash
   git clone https://github.com/wakhidrf/dotsql-to-drizzle.git
   cd dotsql-to-drizzle
   ```

2. **Buat Virtual Environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Instal dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

## 📖 Cara Penggunaan
1. Jalankan aplikasi Streamlit:
   ```bash
   streamlit run app.py
   ```
2. Aplikasi akan terbuka di browser Anda (biasanya di `http://localhost:8501`).
3. **Unggah File:** Pilih file `.sql` dump dari MySQL.
4. **Analisis Log:** Periksa tab logging untuk memastikan proses berjalan lancar.
5. **Salin Hasil:**
   - Salin kode TypeScript yang dihasilkan ke file `schema.ts` proyek Drizzle Anda.
   - Jalankan script SQL yang dihasilkan di database PostgreSQL target untuk seeding data.
