import requests
from bs4 import BeautifulSoup

def scrape_detik_search_filtered(query):

    search_url = f"https://www.detik.com/search/searchall?query={query}"

    # --- PERBAIKAN 2: Menambahkan header User-Agent agar tidak diblokir. ---
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(search_url)
        response.raise_for_status() # Cek jika ada error HTTP (spt 404, 500)
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengakses URL pencarian: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all('article')
    
    scraped_data = []
    
    print(f"Menemukan {len(articles)} total konten untuk kata kunci '{query}'. Mulai memfilter dan scraping...")

    for article in articles:
        link_tag = article.find('a')
        if not link_tag or not link_tag.has_attr('href'):
            continue
            
        article_url = link_tag['href']
        
        # --- FILTER YANG DIPERBAIKI ---
        # Memeriksa subdomain '20.detik.com' untuk video
        # Memeriksa '/foto' (tanpa slash di akhir) untuk semua jenis galeri foto
        if "20.detik.com" in article_url or "/foto" in article_url:
            print(f"  -> [FILTERED] Melewatkan link video/foto: {article_url.split('?')[0]}")
            continue
        # --- AKHIR PERBAIKAN ---
            
        try:
            article_response = requests.get(article_url)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            
            title_tag = article_soup.find('h1', {'class': 'detail__title'})
            judul = title_tag.get_text(strip=True) if title_tag else "Judul tidak ditemukan"

            body_tag = article_soup.find('div', {'class': 'detail__body-text'})
            if body_tag:
                paragraphs = body_tag.find_all('p')
                unwanted_texts = ["Baca juga:", "Lihat juga:", "KOMPAS.com -", "Halaman selanjutnya", "Editor:", "Penulis:", "Simak Video", "Lihat Juga", "Baca juga:", "Tonton juga Video", "[Gambas:Video 20detik]"]
                isi_berita_list = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and not any(unwanted in text for unwanted in unwanted_texts):
                        isi_berita_list.append(text)
                
                isi_berita = "\n".join(isi_berita_list)
            else:
                isi_berita = "" # Set ke string kosong jika body tidak ada

            if isi_berita: # Hanya tambahkan jika isi_berita tidak kosong
                scraped_data.append({
                    'judul': judul,
                    'url': article_url,
                    'isi_berita': isi_berita
                })
                print(f"  -> [SUCCESS] Berhasil scrape: {judul}")
            else:
                print(f"  -> [SKIPPED] Tidak ada konten teks utama di: {judul}")

        except requests.exceptions.RequestException as e:
            print(f"Error saat mengakses artikel {article_url}: {e}")
            continue
            
    return scraped_data