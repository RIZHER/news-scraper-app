import os
import uuid # Import modul uuid untuk membuat ID unik
from flask import Flask, render_template, request, jsonify, session

# Import fungsi scraping dari folder 'scraping'
from scraping.detik import scrape_detik_search_filtered
from scraping.kompas import scrape_kompas_search

app = Flask(__name__)
# Menggunakan os.urandom(24) untuk membuat secret key yang kuat.
# Ini penting untuk sesi Flask.
app.secret_key = os.urandom(24) 

# Kamus global untuk menyimpan data hasil scraping di server-side
# Kunci: scrape_id (string UUID), Nilai: daftar artikel yang discrape
scraped_data_store = {}

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
    """
    query = request.form['query']
    source = request.form['source']
    
    results = []

    if source == 'detik':
        results = scrape_detik_search_filtered(query)
    elif source == 'kompas':
        results = scrape_kompas_search(query)
    elif source == 'both':
        results_detik = scrape_detik_search_filtered(query)
        results_kompas = scrape_kompas_search(query)
        results = results_detik + results_kompas
    
    # Buat ID unik untuk hasil scraping ini
    scrape_id = str(uuid.uuid4())
    
    # Simpan hasil scraping ke kamus global scraped_data_store
    scraped_data_store[scrape_id] = results
    
    # Hanya simpan scrape_id di sesi. Ini akan sangat kecil dan tidak akan melebihi batas cookie.
    session['current_scrape_id'] = scrape_id
    
    # Mengembalikan konfirmasi sebagai JSON (tidak perlu mengirimkan data lengkap)
    return jsonify({"status": "success", "scrape_id": scrape_id, "num_results": len(results)})

@app.route('/results')
def show_results():
    """
    Rute untuk menampilkan daftar berita hasil scraping.
    Mengambil data dari scraped_data_store menggunakan ID sesi.
    """
    scrape_id = session.get('current_scrape_id')
    # Ambil data scraping dari scraped_data_store menggunakan scrape_id
    articles = scraped_data_store.get(scrape_id, [])
    
    return render_template('results.html', articles=articles)

@app.route('/detail/<int:index>')
def show_detail(index):
    """
    Rute untuk menampilkan detail berita berdasarkan indeksnya.
    Mengambil data dari scraped_data_store menggunakan ID sesi.
    """
    scrape_id = session.get('current_scrape_id')
    scraped_data = scraped_data_store.get(scrape_id, [])

    if 0 <= index < len(scraped_data):
        article = scraped_data[index]
        return render_template('detail.html', article=article)
    else:
        # Jika indeks tidak valid atau tidak ada data, kembali ke halaman hasil
        return render_template('results.html', articles=scraped_data, error="Artikel tidak ditemukan.")

if __name__ == '__main__':
    app.run(debug=True)
