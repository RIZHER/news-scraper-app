import os
import uuid
import sqlite3
from flask import Flask, render_template, request, jsonify, session, g

# Import fungsi scraping dari folder 'scraping'
# Pastikan ada file __init__.py kosong di dalam folder 'scraping'
from scraping.detik import scrape_detik_search_filtered
from scraping.kompas import scrape_kompas_search

app = Flask(__name__)
app.secret_key = os.urandom(24) 

# Nama file database SQLite
DATABASE = 'news_data.db'

def get_db():
    """
    Fungsi untuk mendapatkan koneksi database.
    Jika koneksi belum ada dalam konteks permintaan Flask (g),
    maka akan dibuat koneksi baru.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row # Mengembalikan baris sebagai objek mirip dict
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """
    Fungsi untuk menutup koneksi database setelah permintaan selesai.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """
    Fungsi untuk menginisialisasi database: membuat tabel jika belum ada.
    """
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                judul TEXT NOT NULL,
                url TEXT NOT NULL,
                isi_berita TEXT NOT NULL
            )
        ''')
        db.commit()
    print("Database inisialisasi: Tabel 'articles' sudah siap.")

# Panggil init_db() saat aplikasi pertama kali dijalankan
with app.app_context():
    init_db()

@app.route('/')
def index():
    """
    Rute utama untuk menampilkan halaman pencarian.
    """
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """
    Rute untuk melakukan scraping berdasarkan kata kunci dan sumber berita.
    Menyimpan hasil ke database SQLite.
    """
    query = request.form['query']
    source = request.form['source']
    
    scraped_articles = []

    if source == 'detik':
        scraped_articles = scrape_detik_search_filtered(query)
    elif source == 'kompas':
        scraped_articles = scrape_kompas_search(query)
    elif source == 'both':
        results_detik = scrape_detik_search_filtered(query)
        results_kompas = scrape_kompas_search(query)
        scraped_articles = results_detik + results_kompas
    
    # Buat ID unik untuk sesi scraping ini
    current_session_id = str(uuid.uuid4())
    session['current_session_id'] = current_session_id # Simpan di sesi cookie

    db = get_db()
    cursor = db.cursor()
    
    # Simpan setiap artikel ke database dengan session_id yang sama
    for article in scraped_articles:
        try:
            cursor.execute(
                "INSERT INTO articles (session_id, judul, url, isi_berita) VALUES (?, ?, ?, ?)",
                (current_session_id, article['judul'], article['url'], article['isi_berita'])
            )
        except Exception as e:
            print(f"Error saat menyimpan artikel ke DB: {e}")
            # Anda bisa menambahkan logika penanganan kesalahan yang lebih baik di sini
            continue # Lanjutkan ke artikel berikutnya jika ada error

    db.commit() # Komit transaksi setelah semua artikel disimpan

    return jsonify({"status": "success", "session_id": current_session_id, "num_results": len(scraped_articles)})

@app.route('/results')
def show_results():
    """
    Rute untuk menampilkan daftar berita hasil scraping.
    Mengambil data dari database SQLite berdasarkan session_id.
    """
    current_session_id = session.get('current_session_id')
    if not current_session_id:
        # Jika tidak ada session_id, berarti belum ada scraping yang dilakukan
        return render_template('results.html', articles=[], error="Belum ada pencarian yang dilakukan.")

    db = get_db()
    cursor = db.cursor()
    
    # Ambil hanya judul, url, dan id dari database untuk daftar hasil
    cursor.execute(
        "SELECT id, judul, url FROM articles WHERE session_id = ?",
        (current_session_id,)
    )
    articles = cursor.fetchall() # Mengembalikan list of sqlite3.Row objects

    # Konversi sqlite3.Row objects menjadi dictionary untuk kemudahan akses di template
    articles_list = [{'id': row['id'], 'judul': row['judul'], 'url': row['url']} for row in articles]
    
    return render_template('results.html', articles=articles_list)

@app.route('/detail/<int:article_id>')
def show_detail(article_id):
    """
    Rute untuk menampilkan detail berita berdasarkan ID artikel dari database.
    Mengambil data dari database SQLite.
    """
    current_session_id = session.get('current_session_id')
    if not current_session_id:
        return render_template('results.html', articles=[], error="Sesi tidak valid.")

    db = get_db()
    cursor = db.cursor()

    # Ambil detail artikel berdasarkan article_id DAN session_id untuk keamanan
    cursor.execute(
        "SELECT judul, url, isi_berita FROM articles WHERE id = ? AND session_id = ?",
        (article_id, current_session_id)
    )
    article = cursor.fetchone() # Mengambil satu baris

    if article:
        # Konversi sqlite3.Row object menjadi dictionary
        article_dict = dict(article)
        return render_template('detail.html', article=article_dict)
    else:
        # Jika artikel tidak ditemukan atau session_id tidak cocok
        return render_template('results.html', articles=[], error="Artikel tidak ditemukan atau tidak diizinkan.")

if __name__ == '__main__':
    app.run(debug=True)