# SQL to Drizzle Studio Migrator

Sebuah aplikasi [Streamlit](https://streamlit.io/) sederhana untuk mengonversi dump database MySQL (`.sql`) menjadi skema [Drizzle ORM](https://orm.drizzle.team/) (`schema.ts`) dan file SQL untuk seeding data.

## Fitur
- Konversi otomatis tipe data MySQL ke tipe data PostgreSQL untuk Drizzle.
- Deteksi otomatis kolom `PRIMARY KEY` (serial).
- Sanitasi data `INSERT` (pembersihan leading-zeros pada desimal).
- Sinkronisasi sequence PostgreSQL untuk kolom `id`.
- Logging proses konversi secara detail.

## Persiapan
Pastikan Anda telah menginstal [Python 3.13+](https://www.python.org/).

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

## Cara Penggunaan
1. Jalankan aplikasi Streamlit:
   ```bash
   streamlit run app.py
   ```
2. Aplikasi akan terbuka di browser Anda (biasanya di `http://localhost:8501`).
3. Unggah file `.sql` dump MySQL Anda.
4. Salin kode yang dihasilkan untuk `schema.ts` dan jalankan script SQL seeding di database PostgreSQL Anda.
