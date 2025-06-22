import requests
from bs4 import BeautifulSoup

def scrape_kompas_search(query):

    search_url = f"https://search.kompas.com/search?q={query}"
    
    # --- PERBAIKAN 2: Menambahkan header User-Agent agar tidak diblokir. ---
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()  # Cek jika ada error HTTP (spt 404, 500)
    except requests.exceptions.RequestException as e:
        print(f"Error saat mengakses URL pencarian: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all('div', {'class': 'articleItem'})
    
    scraped_data = []
    
    print(f"Menemukan {len(articles)} artikel untuk kata kunci '{query}'. Memulai scraping...")

    for article in articles:
        link_tag = article.find('a', {'class': 'article-link'}) 
        if not link_tag or not link_tag.has_attr('href'):
            continue
            
        article_url = link_tag['href']
        
        # Melewatkan link non-artikel
        #
        #
        if not article_url.startswith("https://"):
            print(f"  -> [SKIPPED] Melewatkan link non-artikel: {article_url}")
            continue
        # --- AKHIR PERBAIKAN ---

        try:
            article_response = requests.get(article_url, headers=headers)
            article_response.raise_for_status()
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            
            title_tag = article_soup.find('h1', {'class': 'read__title'})
            judul = title_tag.get_text(strip=True) if title_tag else "Judul tidak ditemukan"

            body_tag = article_soup.find('div', {'class': 'read__content'})
            if body_tag:
                paragraphs = body_tag.find_all('p')
                unwanted_phrases = ["Baca juga:", "Lihat juga:", "KOMPAS.com -", "Halaman selanjutnya", "Editor:", "Penulis:", "Simak Video", "Lihat Juga", "Baca juga:", "Tonton juga Video", "[Gambas:Video 20detik]"]
                isi_berita_list = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and not any(unwanted in text for unwanted in unwanted_phrases):
                        isi_berita_list.append(text)
                
                isi_berita = "\n".join(isi_berita_list)
            else:
                isi_berita = "" # Set ke string kosong jika body tidak ada

            if isi_berita: # Hanya tambahkan jika isi_berita tidak kosong
                scraped_data.append({
                    'judul': judul,
                    'url': article_url,
                    'isi_berita': isi_berita.strip()
                })
                print(f"  -> [SUCCESS] Berhasil scrape: {judul}")
            else:
                print(f"  -> [SKIPPED] Tidak ada konten teks utama yang valid di: {judul}")

        except requests.exceptions.RequestException as e:
            print(f"Error saat mengakses artikel {article_url}: {e}")
            continue
            
    return scraped_data