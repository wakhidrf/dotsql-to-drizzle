import streamlit as st
import datetime
import re

if "conversion_logs" not in st.session_state:
    st.session_state.conversion_logs = []

def add_log(message, log_type="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.conversion_logs.append(f"[{timestamp}] [{log_type}] {message}")

st.set_page_config(
    page_title="SQL to Drizzle Studio Migrator", 
    page_icon="⚡", 
    layout="centered"
)

st.title("⚡ SQL to Drizzle Studio Migrator")
st.write("Ubah `.sql` MySQL menjadi `schema.ts` dengan Fitur Logging Analisis Super Detail.")

uploaded_file = st.file_uploader("Unggah file .sql MySQL Anda", type=["sql"])

st.markdown("---")

def clean_name(name):
    return name.strip().replace("`", "").replace('"', "").replace("'", "")

def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def map_mysql_to_drizzle(mysql_type, col_name):
    mysql_type = mysql_type.upper()
    if col_name.lower() == "id" and ("INT" in mysql_type or "SERIAL" in mysql_type):
        return 'serial("' + col_name + '").primaryKey()'
    if "INT" in mysql_type or "TINYINT" in mysql_type or "SMALLINT" in mysql_type:
        return 'integer("' + col_name + '")'
    if "BIGINT" in mysql_type:
        return 'bigint("' + col_name + '", { mode: "number" })'
    if "VARCHAR" in mysql_type or "CHAR" in mysql_type:
        length_match = re.search(r'\((\d+)\)', mysql_type)
        length = length_match.group(1) if length_match else "255"
        return 'varchar("' + col_name + '", { length: ' + length + ' })'
    if "TEXT" in mysql_type or "LONGTEXT" in mysql_type or "MEDIUMTEXT" in mysql_type:
        return 'text("' + col_name + '")'
    if "TIMESTAMP" in mysql_type or "DATETIME" in mysql_type:
        return 'timestamp("' + col_name + '", { mode: "string" })'
    if "DATE" in mysql_type:
        return 'date("' + col_name + '")'
    if "DECIMAL" in mysql_type or "NUMERIC" in mysql_type or "DOUBLE" in mysql_type or "FLOAT" in mysql_type:
        return 'numeric("' + col_name + '")'
    if "BOOLEAN" in mysql_type or "BIT" in mysql_type:
        return 'boolean("' + col_name + '")'
    return 'text("' + col_name + '")'

def tokenize_sql_values(values_str):
    tokens = []
    current = []
    in_string = False
    string_char = None
    escaped = False
    i = 0
    n = len(values_str)
    
    while i < n:
        char = values_str[i]
        if escaped:
            current.append(char)
            escaped = False
            i += 1
            continue
        if char == '\\':
            current.append(char)
            escaped = True
            i += 1
            continue
        if char == "'" or char == '"':
            if not in_string:
                in_string = True
                string_char = char
                current.append(char)
            elif char == string_char:
                in_string = False
                string_char = None
                current.append(char)
            else:
                current.append(char)
            i += 1
            continue
        if char == ',' and not in_string:
            tokens.append("".join(current).strip())
            current = []
            i += 1
            continue
        current.append(char)
        i += 1
    if current:
        tokens.append("".join(current).strip())
    return tokens

def extract_rows_from_values_block(values_body):
    rows = []
    current_row = []
    in_string = False
    string_char = None
    escaped = False
    bracket_level = 0
    
    i = 0
    n = len(values_body)
    while i < n:
        char = values_body[i]
        if escaped:
            if bracket_level > 0:
                current_row.append(char)
            escaped = False
            i += 1
            continue
        if char == '\\':
            if bracket_level > 0:
                current_row.append(char)
            escaped = True
            i += 1
            continue
        if char == "'" or char == '"':
            if not in_string:
                in_string = True
                string_char = char
            elif char == string_char:
                in_string = False
                string_char = None
            if bracket_level > 0:
                current_row.append(char)
            i += 1
            continue
        if not in_string:
            if char == '(':
                bracket_level += 1
                if bracket_level == 1:
                    current_row = []
                    i += 1
                    continue
            elif char == ')':
                bracket_level -= 1
                if bracket_level == 0:
                    rows.append("".join(current_row).strip())
                    current_row = []
                    i += 1
                    continue
        if bracket_level > 0:
            current_row.append(char)
        i += 1
    return rows

def generate_drizzle_and_seed(sql_text):
    add_log("=== TAHAP 1: PEMETAAN STRUKTUR SCHEMA & KOLEKSI TIPE DATA ===", "INFO")
    
    table_matches = re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([^\s(]+)\s*\((.*?)\)\s*(?:ENGINE|=[^;]*|;)', sql_text, re.DOTALL | re.IGNORECASE)
    existing_tables = [clean_name(t[0]) for t in table_matches]
    
    table_numeric_column_indices = {}
    table_column_names_map = {}
    
    for table_raw, columns_raw in table_matches:
        table_name = clean_name(table_raw)
        lines = columns_raw.split(',\n')
        if len(lines) == 1:
            lines = columns_raw.split(',')
            
        col_idx = 0
        numeric_indices = set()
        column_names = []
        
        for line in lines:
            line_clean = line.strip()
            if not line_clean or any(line_clean.upper().startswith(x) for x in ["PRIMARY KEY", "KEY", "UNIQUE", "CONSTRAINT"]):
                continue
                
            tokens = line_clean.split()
            if len(tokens) < 2:
                continue
                
            col_name = clean_name(tokens[0])
            if ')' in col_name or '(' in col_name or col_name.isdigit() or col_name == "":
                continue
                
            type_full_match = re.match(r'^([^\s]+)', line_clean[len(tokens[0]):].strip())
            col_type = type_full_match.group(1).upper() if type_full_match else tokens[1].upper()
            
            column_names.append(col_name)
            if any(x in col_type for x in ["INT", "SERIAL", "DECIMAL", "NUMERIC", "DOUBLE", "FLOAT"]):
                numeric_indices.add(col_idx)
                
            col_idx += 1
            
        table_numeric_column_indices[table_name] = numeric_indices
        table_column_names_map[table_name] = column_names
        
        # LOG DETAIL SKEMA TABEL
        numeric_cols_picked = [column_names[i] for i in numeric_indices]
        add_log(f"Tabel [{table_name}]: Ditemukan {len(column_names)} kolom total. Kolom tipe angka terdeteksi: {numeric_cols_picked}", "SKEMA")

    add_log("=== TAHAP 2: PROSES PARSING DATA INSERT INTO & SANITISASI ===", "INFO")
    
    insert_matches = re.finditer(r'(INSERT\s+INTO\s+([^\s(]+)\s*\(.*?\)\s*VALUES)\s*(.*?);', sql_text, re.IGNORECASE | re.DOTALL)
    insert_statements = []
    
    for match in insert_matches:
        header_part = match.group(1).replace("`", '"')
        table_name = clean_name(match.group(2))
        values_body = match.group(3).strip()
        
        numeric_indices = table_numeric_column_indices.get(table_name, set())
        col_names = table_column_names_map.get(table_name, [])
        
        row_contents = extract_rows_from_values_block(values_body)
        add_log(f"Memproses tabel [{table_name}] -> Ditemukan {len(row_contents)} baris (rows) data data seed.", "MIGRASI_DATA")
        
        cleaned_rows = []
        row_num = 1
        
        for row in row_contents:
            tokens = tokenize_sql_values(row)
            
            for idx in range(len(tokens)):
                if idx in numeric_indices and not tokens[idx].startswith("'") and not tokens[idx].startswith('"'):
                    old_val = tokens[idx]
                    
                    # Eksekusi regex pembersihan
                    tokens[idx] = re.sub(r'\b0+(?=\d+\.\d+)', '', tokens[idx])
                    tokens[idx] = re.sub(r'\b0(?=0\.\d+)', '', tokens[idx])
                    
                    if tokens[idx].lower() == "b'0'": tokens[idx] = "0"
                    if tokens[idx].lower() == "b'1'": tokens[idx] = "1"
                    
                    # CETAK LOG HANYA JIKA TERJADI PERUBAHAN ANGKA DESIMAL
                    if old_val != tokens[idx]:
                        col_name_error = col_names[idx] if idx < len(col_names) else f"index_{idx}"
                        add_log(f"   ↳ [Row {row_num}] Kolom '{col_name_error}': Berhasil memotong leading-zeros desimal '{old_val}' ➔ '{tokens[idx]}'", "SANITISASI")
            
            cleaned_rows.append("\t(" + ", ".join(tokens) + ")")
            row_num += 1
            
        new_insert_statement = header_part + "\n" + ",\n".join(cleaned_rows) + ";"
        insert_statements.append(new_insert_statement)
        
    add_log("=== TAHAP 3: STRUKTUR CODE GENERATION FINISHED ===", "SUCCESS")

    # --- PENYUSUNAN SCHEMA.TS ---
    schema_code = 'import { relations } from "drizzle-orm";\n'
    schema_code += 'import {\n  integer,\n  pgTable,\n  serial,\n  text,\n  timestamp,\n  varchar,\n  numeric,\n  bigint,\n  boolean\n} from \"drizzle-orm/pg-core\";\n\n'
    
    for table_raw, columns_raw in table_matches:
        table_name = clean_name(table_raw)
        schema_code += f'export const {table_name} = pgTable("{table_name}", {{\n'
        lines = columns_raw.split(',\n')
        if len(lines) == 1: lines = columns_raw.split(',')
        
        seen_cols = set()
        for line in lines:
            line_clean = line.strip()
            if not line_clean or any(line_clean.upper().startswith(x) for x in ["PRIMARY KEY", "KEY", "UNIQUE", "CONSTRAINT"]):
                continue
            tokens = line_clean.split()
            if len(tokens) < 2: continue
            col_name = clean_name(tokens[0])
            if ')' in col_name or '(' in col_name or col_name.isdigit() or col_name == "" or col_name in seen_cols: continue
            seen_cols.add(col_name)
            
            type_full_match = re.match(r'^([^\s]+)', line_clean[len(tokens[0]):].strip())
            col_type = type_full_match.group(1) if type_full_match else tokens[1]
            drizzle_line = map_mysql_to_drizzle(col_type, col_name)
            if "NOT NULL" in line_clean.upper() and "primaryKey()" not in drizzle_line: drizzle_line += ".notNull()"
            
            schema_code += f'  {to_camel_case(col_name)}: {drizzle_line},\n'
        schema_code += "});\n\n"

    # --- PENYUSUNAN SQL SEED RUNNER ---
    studio_sql_runner_code = (
        "START TRANSACTION;\n"
        "SET CONSTRAINTS ALL DEFERRED;\n\n"
        "-- --- KODE INSERTS DATA ---\n"
    )
    studio_sql_runner_code += "\n".join(insert_statements)
    studio_sql_runner_code += "\n\n-- --- SINKRONISASI SEQUENCES ---\n"
    for t_name in existing_tables:
        studio_sql_runner_code += f"SELECT setval(pg_get_serial_sequence('{t_name}', 'id'), COALESCE(max(id), 1)) FROM \"{t_name}\";\n"
    studio_sql_runner_code += "\nCOMMIT;\n"

    return schema_code, studio_sql_runner_code

if uploaded_file is not None:
    try:
        st.session_state.conversion_logs = []
        sql_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
        add_log("Berkas dump .sql berhasil dibaca masuk ke buffer Streamlit.", "INFO")
        
        drizzle_ts, studio_sql = generate_drizzle_and_seed(sql_text)
        st.success("🎉 Konversi Berhasil! Detail modifikasi data tercatat lengkap pada Log di bawah.")
        
        st.subheader("1. Salin Kode Ini ke `schema.ts` Anda")
        st.code(drizzle_ts, language="typescript", line_numbers=True)
        st.markdown("---")
        st.subheader("2. Jalankan Kode SQL Ini di SQL Runner / Studio")
        st.code(studio_sql, language="sql", line_numbers=True)
        
    except Exception as e:
        add_log(f"Kritis Gagal Konversi: {str(e)}", "ERROR")
        st.error(f"Gagal memproses file SQL: {e}")
else:
    st.info("Silakan unggah file `.sql` MySQL Anda.")

st.markdown("---")
with st.expander("🪵 Penampil Log Aktivitas Komprehensif", expanded=True):
    st.code("\n".join(st.session_state.conversion_logs), language="text")