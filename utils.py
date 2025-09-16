import sqlite3

# Tambahkan user default jika belum ada
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Tabel User
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Tabel Pengajuan Ijazah
    c.execute('''
        CREATE TABLE IF NOT EXISTS pengajuan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_mdt TEXT,
            jenjang TEXT,
            tahun TEXT,
            jumlah_santri INTEGER,
            file_lulusan TEXT,
            status TEXT DEFAULT 'diajukan',
            alasan_batal TEXT
        )
    ''')

    # Cek dan tambahkan user default
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        users_default = [
            ('mdt1', '123', 'mdt'),
            ('kemenag1', '123', 'kankemenag'),
            ('kanwil1', '123', 'kanwil')
        ]
        c.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", users_default)
        print("✅ User default berhasil ditambahkan.")

    conn.commit()
    conn.close()

def kode_jenjang(jenjang):
    mapping = {
        'Ula': 'I',
        'Wustha': 'II',
        'Ulya': 'III',
        'Al-Jami’ah': 'IV'
    }
    return mapping.get(jenjang, 'X')

def generate_nomor_ijazah(kode, tahun, urut):
    return f"MDT-12-{kode}-{tahun}-{urut:06d}"

# Panggil fungsi saat file dijalankan langsung
if __name__ == '__main__':
    init_db()
    print("✅ Database berhasil dibuat.")
