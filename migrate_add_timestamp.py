import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

try:
    c.execute("ALTER TABLE pengajuan ADD COLUMN created_at TEXT")
    print("✅ Kolom created_at berhasil ditambahkan.")
except sqlite3.OperationalError as e:
    print("⚠️ Kolom created_at sudah ada.")

try:
    c.execute("ALTER TABLE pengajuan ADD COLUMN updated_at TEXT")
    print("✅ Kolom updated_at berhasil ditambahkan.")
except sqlite3.OperationalError as e:
    print("⚠️ Kolom updated_at sudah ada.")

conn.commit()
conn.close()
