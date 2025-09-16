import sqlite3

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
            status TEXT DEFAULT 'diajukan'
        )
    ''')

    conn.commit()
    conn.close()

# Panggil fungsi saat file dijalankan langsung
if __name__ == '__main__':
    init_db()
    print("✅ Database berhasil dibuat.")
    
def tambah_user_awal():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # username: mdt1 / kemenag1 / kanwil1
    users = [
        ('mdt1', '123', 'mdt'),
        ('kemenag1', '123', 'kankemenag'),
        ('kanwil1', '123', 'kanwil')
    ]
    c.executemany('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', users)
    conn.commit()
    conn.close()
    print("✅ User awal ditambahkan.")

if __name__ == '__main__':
    init_db()
    tambah_user_awal()
    print("✅ Database berhasil dibuat dan user awal ditambahkan.")