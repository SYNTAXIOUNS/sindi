from flask import Flask, render_template, request, redirect, url_for, session, send_file, send_from_directory, abort, flash
import sqlite3, os, pandas as pd, openpyxl
from werkzeug.utils import secure_filename
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime

from utils import init_db, kode_jenjang, generate_nomor_ijazah

app = Flask(__name__)
app.secret_key = 'rahasia123'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username=? AND password=?', (u, p)).fetchone()
        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Berhasil login!', 'success')
            return redirect(f"/dashboard_{user['role']}")
        flash('Login gagal. Cek username dan password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Berhasil logout.', 'success')
    return redirect('/')

@app.route('/dashboard_mdt')
def dashboard_mdt():
    if session.get('role') != 'mdt': return redirect('/')
    db = get_db()
    user = session['username']
    pengajuan_total = db.execute("SELECT COUNT(*) FROM pengajuan WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now') AND nama_mdt=?", (user,)).fetchone()[0]
    pengajuan_menunggu = db.execute("SELECT COUNT(*) FROM pengajuan WHERE status='diajukan' AND nama_mdt=?", (user,)).fetchone()[0]
    pengajuan_revisi = db.execute("SELECT COUNT(*) FROM pengajuan WHERE status='dibatalkan' AND nama_mdt=?", (user,)).fetchone()[0]
    pengajuan_ditetapkan = db.execute("SELECT COUNT(*) FROM pengajuan WHERE status='ditetapkan' AND nama_mdt=?", (user,)).fetchone()[0]
    data = db.execute("SELECT * FROM pengajuan WHERE nama_mdt=?", (user,)).fetchall()
    return render_template('dashboard_mdt.html', user=user, data=data,
                           pengajuan_total=pengajuan_total,
                           pengajuan_menunggu=pengajuan_menunggu,
                           pengajuan_revisi=pengajuan_revisi,
                           pengajuan_ditetapkan=pengajuan_ditetapkan)

@app.route('/dashboard_kankemenag')
def dashboard_kankemenag():
    if session.get('role') != 'kankemenag': return redirect('/')
    db = get_db()
    user = session['username']
    pengajuan_masuk = db.execute("SELECT COUNT(*) FROM pengajuan WHERE status='diajukan'").fetchone()[0]
    revisi_diajukan = db.execute("SELECT COUNT(*) FROM pengajuan WHERE status='dibatalkan'").fetchone()[0]
    diverifikasi = db.execute("SELECT COUNT(*) FROM pengajuan WHERE status='diverifikasi'").fetchone()[0]
    verifikasi_sla = db.execute("SELECT AVG(julianday(updated_at) - julianday(created_at)) FROM pengajuan WHERE status='diverifikasi'").fetchone()[0] or 0
    return render_template('dashboard_kankemenag.html', user=user,
                           pengajuan_masuk=pengajuan_masuk,
                           revisi_diajukan=revisi_diajukan,
                           diverifikasi=diverifikasi,
                           verifikasi_sla=round(verifikasi_sla, 1))

@app.route('/dashboard_kanwil')
def dashboard_kanwil():
    if session.get('role') != 'kanwil': return redirect('/')
    db = get_db()
    user = session['username']
    menunggu_penetapan = db.execute("SELECT COUNT(*) FROM pengajuan WHERE status='diverifikasi'").fetchone()[0]
    ditetapkan_hari_ini = db.execute("SELECT COUNT(*) FROM pengajuan WHERE status='ditetapkan' AND DATE(updated_at)=DATE('now')").fetchone()[0]
    total_terbit_bulan_ini = db.execute("SELECT COUNT(*) FROM pengajuan WHERE status='ditetapkan' AND strftime('%Y-%m', updated_at)=strftime('%Y-%m', 'now')").fetchone()[0]
    sla_penetapan = db.execute("SELECT AVG(julianday(updated_at) - julianday(created_at)) FROM pengajuan WHERE status='ditetapkan'").fetchone()[0] or 0
    return render_template('dashboard_kanwil.html', user=user,
                           menunggu_penetapan=menunggu_penetapan,
                           ditetapkan_hari_ini=ditetapkan_hari_ini,
                           total_terbit_bulan_ini=total_terbit_bulan_ini,
                           sla_penetapan=round(sla_penetapan, 1))

@app.route('/pengajuan', methods=['GET', 'POST'])
def pengajuan():
    if session.get('role') != 'mdt': return redirect('/')
    db = get_db()
    data_batal = db.execute("SELECT * FROM pengajuan WHERE nama_mdt = ? AND status = 'dibatalkan'", (session['username'],)).fetchone()
    if request.method == 'POST':
        form = request.form
        tahun = form['tahun']
        if not (tahun.isdigit() and len(tahun) == 4):
            flash('Tahun harus berupa 4 digit angka!', 'danger')
            return redirect(request.url)
        file = request.files['file_lulusan']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        now = datetime.now().isoformat(sep=' ')
        if data_batal:
            db.execute('''UPDATE pengajuan SET jenjang=?, tahun=?, jumlah_santri=?, file_lulusan=?, status='diajukan', alasan_batal=NULL, created_at=?, updated_at=? WHERE id=?''',
                       (form['jenjang'], form['tahun'], form['jumlah_santri'], filename, now, now, data_batal['id']))
        else:
            db.execute('''INSERT INTO pengajuan (nama_mdt, jenjang, tahun, jumlah_santri, file_lulusan, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (session['username'], form['jenjang'], form['tahun'], form['jumlah_santri'], filename, now, now))
        db.commit()
        flash('Pengajuan berhasil dikirim!', 'success')
        return redirect('/dashboard_mdt')
    return render_template('pengajuan.html', user=session['username'], data_batal=data_batal)

@app.route('/verifikasi', methods=['GET', 'POST'])
def verifikasi():
    if session.get('role') != 'kankemenag': return redirect('/')
    db = get_db()
    if request.method == 'POST':
        now = datetime.now().isoformat(sep=' ')
        if request.form['aksi'] == 'verifikasi':
            db.execute("UPDATE pengajuan SET status='diverifikasi', updated_at=? WHERE id=?", (now, request.form['id_pengajuan']))
            flash('Pengajuan berhasil diverifikasi.', 'success')
        elif request.form['aksi'] == 'batalkan':
            db.execute("UPDATE pengajuan SET status='dibatalkan', alasan_batal=?, updated_at=? WHERE id=?", (request.form['alasan'], now, request.form['id_pengajuan']))
            flash('Pengajuan dibatalkan.', 'warning')
        db.commit()
    data = db.execute("SELECT * FROM pengajuan WHERE status='diajukan'").fetchall()
    return render_template('verifikasi.html', user=session['username'], data=data)

@app.route('/penetapan', methods=['GET', 'POST'])
def penetapan():
    if session.get('role') != 'kanwil': return redirect('/')
    db = get_db()
    if request.method == 'POST':
        idp = request.form['id']
        p = db.execute('SELECT * FROM pengajuan WHERE id=?', (idp,)).fetchone()
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], p['file_lulusan'])
        nomor_list = [generate_nomor_ijazah(kode_jenjang(p['jenjang']), p['tahun'], i+1) for i in range(p['jumlah_santri'])]
        wb = openpyxl.load_workbook(excel_path)
        ws = wb.active
        ws.cell(row=1, column=ws.max_column + 1).value = "Nomor Ijazah"
        for i, nomor in enumerate(nomor_list, start=2):
            ws.cell(row=i, column=ws.max_column).value = nomor
        wb.save(excel_path)
        now = datetime.now().isoformat(sep=' ')
        db.execute('UPDATE pengajuan SET status="ditetapkan", updated_at=? WHERE id=?', (now, idp))
        db.commit()
        txt_path = os.path.join(app.config['UPLOAD_FOLDER'], f"hasil_{idp}.txt")
        with open(txt_path, 'w') as f:
            for no in nomor_list:
                f.write(no + '\n')
        flash('Penetapan berhasil dilakukan dan nomor ijazah ditambahkan ke file.', 'success')
    data = db.execute("SELECT * FROM pengajuan WHERE status='diverifikasi'").fetchall()
    return render_template('penetapan.html', user=session['username'], data=data)

@app.route('/hasil')
def hasil():
    if session.get('role') != 'mdt': return redirect('/')
    db = get_db()
    page = int(request.args.get('page', 1))
    per_page = 5
    offset = (page - 1) * per_page
    total = db.execute("SELECT COUNT(*) FROM pengajuan WHERE status='ditetapkan' AND nama_mdt=?", (session['username'],)).fetchone()[0]
    data = db.execute("SELECT * FROM pengajuan WHERE status='ditetapkan' AND nama_mdt=? LIMIT ? OFFSET ?", (session['username'], per_page, offset)).fetchall()
    total_pages = (total + per_page - 1) // per_page
    return render_template('hasil.html', user=session['username'], data=data, page=page, total_pages=total_pages)

@app.route('/lihat_file/<int:id>')
def lihat_file(id):
    try:
        db = get_db()
        row = db.execute("SELECT * FROM pengajuan WHERE id = ?", (id,)).fetchone()
        if not row:
            return "❌ Data tidak ditemukan."

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], row['file_lulusan'])
        if not os.path.exists(filepath):
            return "❌ File tidak ditemukan di folder uploads."

        df = pd.read_excel(filepath)
        data = [df.columns.tolist()] + df.values.tolist()

        if request.args.get('modal') == 'true':
            return render_template("lihat_file_modal.html", data=data, filename=row['file_lulusan'])
        else:
            return render_template("lihat_file.html", data=data, filename=row['file_lulusan'], role=session.get('role'))
    except Exception as e:
        return f"❌ Gagal membuka file: {str(e)}"


@app.route('/unduh_pdf/<int:idp>')
def unduh_pdf(idp):
    db = get_db()
    p = db.execute("SELECT * FROM pengajuan WHERE id=?", (idp,)).fetchone()
    daftar = open(os.path.join(app.config['UPLOAD_FOLDER'], f"hasil_{idp}.txt")).read().splitlines()
    html = render_template("pdf_template.html", nama=p['nama_mdt'], jenjang=p['jenjang'], tahun=p['tahun'], nomor_list=daftar)
    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name=f"NomorIjazah_{p['nama_mdt']}.pdf")

@app.route('/unduh_excel/<int:idp>')
def unduh_excel(idp):
    db = get_db()
    p = db.execute("SELECT * FROM pengajuan WHERE id=?", (idp,)).fetchone()
    daftar = open(os.path.join(app.config['UPLOAD_FOLDER'], f"hasil_{idp}.txt")).read().splitlines()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["No", "Nomor Ijazah"])
    for i, no in enumerate(daftar, 1):
        ws.append([i, no])
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"NomorIjazah_{p['nama_mdt']}.xlsx")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.context_processor
def inject_now():
    return {'now': lambda: datetime.now()}

if __name__ == '__main__':
    app.run(debug=True)
