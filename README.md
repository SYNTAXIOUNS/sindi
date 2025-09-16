# 📘 Aplikasi Penomoran Ijazah MDT

Sistem berbasis Flask untuk mengelola proses pengajuan, verifikasi, dan penetapan nomor ijazah Madrasah Diniyah Takmiliyah (MDT).

## 🚀 Fitur Utama
- Autentikasi 3 role: `mdt`, `kankemenag`, `kanwil`
- Upload & pratinjau file lulusan (.xlsx)
- Verifikasi dan pembatalan oleh Kankemenag
- Penetapan otomatis nomor ijazah oleh Kanwil
- Export hasil ke PDF dan Excel

## 🏗️ Struktur Role
- **MDT**: Mengajukan data lulusan
- **Kankemenag**: Verifikasi / batalkan pengajuan
- **Kanwil**: Tetapkan nomor ijazah

## ⚙️ Instalasi Lokal

1. Clone repo:
```bash
git clone https://github.com/USERNAME/penomoran-ijazah.git
cd penomoran-ijazah
